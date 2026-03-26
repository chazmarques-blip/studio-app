"""Centralized Cache System — 3-layer backend caching for AgentZZ.

Layer 1: ImageCache — Disk-persistent, SHA256-keyed, dedup, pre-warming
Layer 2: ProjectCache — Read-through, write-behind batching, dirty tracking, locks
Layer 3: LLMCache — Content-addressable prompt+image hash, auto-invalidation
"""
import hashlib
import io
import json
import logging
import os
import threading
import time
from collections import OrderedDict
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path("/tmp/agentzz_cache")
IMAGE_CACHE_DIR = CACHE_DIR / "images"
LLM_CACHE_DIR = CACHE_DIR / "llm"
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_CACHE_MB = 500
MAX_LLM_CACHE_MB = 200


# ═══════════════════════════════════════════════════════════
# LAYER 1: IMAGE CACHE — Disk + Memory for hot avatars
# ═══════════════════════════════════════════════════════════

class ImageCache:
    """Disk-persistent image cache with SHA256 dedup and in-memory hot layer."""

    def __init__(self):
        self._hot = OrderedDict()  # URL -> bytes (for avatars, small & frequent)
        self._hot_max = 50  # Max images in memory
        self._lock = threading.Lock()
        self._access_log = {}  # path -> last_access timestamp

    def _url_hash(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:24]

    def _disk_path(self, url_hash: str) -> Path:
        return IMAGE_CACHE_DIR / f"{url_hash}.bin"

    def get(self, url: str) -> bytes | None:
        """Get image bytes from cache (memory first, then disk)."""
        with self._lock:
            if url in self._hot:
                self._hot.move_to_end(url)
                return self._hot[url]

        h = self._url_hash(url)
        path = self._disk_path(h)
        if path.exists():
            data = path.read_bytes()
            self._access_log[str(path)] = time.time()
            # Promote small images to hot cache
            if len(data) < 512 * 1024:  # < 512KB → keep in memory
                self._promote_to_hot(url, data)
            return data
        return None

    def put(self, url: str, data: bytes, hot: bool = False):
        """Store image in cache. hot=True forces in-memory retention."""
        h = self._url_hash(url)
        path = self._disk_path(h)
        if not path.exists():
            path.write_bytes(data)
        self._access_log[str(path)] = time.time()

        if hot or len(data) < 512 * 1024:
            self._promote_to_hot(url, data)

    def _promote_to_hot(self, url: str, data: bytes):
        with self._lock:
            self._hot[url] = data
            self._hot.move_to_end(url)
            while len(self._hot) > self._hot_max:
                self._hot.popitem(last=False)

    def has(self, url: str) -> bool:
        if url in self._hot:
            return True
        return self._disk_path(self._url_hash(url)).exists()

    def prewarm(self, urls: list):
        """Pre-download a batch of URLs into cache (blocking)."""
        import urllib.request
        import tempfile

        supabase_url = os.environ.get("SUPABASE_URL", "")
        loaded = 0
        for url in urls:
            if self.has(url):
                loaded += 1
                continue
            full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
            try:
                tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
                urllib.request.urlretrieve(full_url, tmp.name)
                with open(tmp.name, "rb") as f:
                    data = f.read()
                os.unlink(tmp.name)
                if data:
                    self.put(url, data, hot=True)
                    loaded += 1
            except Exception as e:
                logger.warning(f"ImageCache prewarm failed for {url[:60]}: {e}")
        logger.info(f"ImageCache: pre-warmed {loaded}/{len(urls)} images")
        return loaded

    def download(self, url: str) -> bytes:
        """Download with cache — replaces all _download_image() calls."""
        cached = self.get(url)
        if cached:
            return cached

        import urllib.request
        import tempfile

        supabase_url = os.environ.get("SUPABASE_URL", "")
        full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
        tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
        try:
            urllib.request.urlretrieve(full_url, tmp.name)
            with open(tmp.name, "rb") as f:
                data = f.read()
            if data:
                self.put(url, data)
            return data
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def invalidate(self, url: str):
        """Remove a specific URL from cache (e.g., after image was re-generated)."""
        with self._lock:
            self._hot.pop(url, None)
        h = self._url_hash(url)
        path = self._disk_path(h)
        if path.exists():
            path.unlink()

    def cleanup(self):
        """Evict oldest files when disk usage exceeds limit."""
        total = sum(f.stat().st_size for f in IMAGE_CACHE_DIR.iterdir() if f.is_file())
        if total < MAX_IMAGE_CACHE_MB * 1024 * 1024:
            return
        files = sorted(IMAGE_CACHE_DIR.iterdir(), key=lambda f: self._access_log.get(str(f), 0))
        while total > MAX_IMAGE_CACHE_MB * 1024 * 1024 * 0.7 and files:
            f = files.pop(0)
            if f.is_file():
                total -= f.stat().st_size
                f.unlink()
        logger.info(f"ImageCache: cleanup done, {total // (1024*1024)}MB remaining")

    def stats(self) -> dict:
        disk_files = list(IMAGE_CACHE_DIR.iterdir())
        disk_size = sum(f.stat().st_size for f in disk_files if f.is_file())
        return {
            "hot_count": len(self._hot),
            "disk_count": len(disk_files),
            "disk_size_mb": round(disk_size / (1024 * 1024), 1),
        }


# ═══════════════════════════════════════════════════════════
# LAYER 2: PROJECT CACHE — Read-through, Write-behind
# ═══════════════════════════════════════════════════════════

class ProjectCache:
    """In-memory project cache with write-behind batching to Supabase.

    Reduces DB reads from 160+ to ~5 during batch operations.
    Write-behind: accumulates changes, flushes every FLUSH_INTERVAL or on demand.
    """

    FLUSH_INTERVAL = 3.0  # seconds
    TTL = 300  # 5 minutes

    def __init__(self):
        self._cache = {}  # tenant_id -> {"settings": ..., "ts": ..., "dirty": bool}
        self._locks = {}  # tenant_id -> Lock
        self._global_lock = threading.Lock()
        self._flush_timer = None
        self._dirty_tenants = set()

    def _get_lock(self, tenant_id: str) -> threading.Lock:
        with self._global_lock:
            if tenant_id not in self._locks:
                self._locks[tenant_id] = threading.Lock()
            return self._locks[tenant_id]

    def get_settings(self, tenant_id: str) -> dict:
        """Read-through: return from cache if fresh, else fetch from DB."""
        lock = self._get_lock(tenant_id)
        with lock:
            entry = self._cache.get(tenant_id)
            if entry and (time.time() - entry["ts"]) < self.TTL:
                return entry["settings"]

        # Cache miss — fetch from Supabase
        from core.deps import supabase
        for attempt in range(3):
            try:
                r = supabase.table("tenants").select("settings").eq("id", tenant_id).single().execute()
                settings = r.data.get("settings", {}) if r.data else {}
                with lock:
                    self._cache[tenant_id] = {"settings": settings, "ts": time.time(), "dirty": False}
                return settings
            except Exception as e:
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"ProjectCache get_settings failed: {e}")
                    raise

    def save_settings(self, tenant_id: str, settings: dict, flush_now: bool = False):
        """Write-behind: update cache immediately, batch DB writes."""
        from datetime import datetime, timezone
        settings["updated_at"] = datetime.now(timezone.utc).isoformat()

        lock = self._get_lock(tenant_id)
        with lock:
            self._cache[tenant_id] = {"settings": settings, "ts": time.time(), "dirty": True}
            self._dirty_tenants.add(tenant_id)

        if flush_now:
            self._flush_tenant(tenant_id)
        else:
            self._schedule_flush()

    def _schedule_flush(self):
        """Schedule a batched flush if not already pending."""
        if self._flush_timer and self._flush_timer.is_alive():
            return
        self._flush_timer = threading.Timer(self.FLUSH_INTERVAL, self._flush_all)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _flush_tenant(self, tenant_id: str):
        """Flush a single tenant's settings to Supabase."""
        from core.deps import supabase
        lock = self._get_lock(tenant_id)
        with lock:
            entry = self._cache.get(tenant_id)
            if not entry or not entry.get("dirty"):
                return
            settings = entry["settings"]

        for attempt in range(3):
            try:
                supabase.table("tenants").update({"settings": settings}).eq("id", tenant_id).execute()
                with lock:
                    if self._cache.get(tenant_id):
                        self._cache[tenant_id]["dirty"] = False
                self._dirty_tenants.discard(tenant_id)
                return
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    logger.warning(f"ProjectCache flush retry {attempt+1} for {tenant_id}: {e}")
                else:
                    logger.error(f"ProjectCache flush FAILED for {tenant_id}: {e}")

    def _flush_all(self):
        """Flush all dirty tenants to DB."""
        dirty = list(self._dirty_tenants)
        for tid in dirty:
            self._flush_tenant(tid)
        if dirty:
            logger.info(f"ProjectCache: flushed {len(dirty)} tenant(s)")

    def get_project(self, tenant_id: str, project_id: str):
        """Cached version of _get_project."""
        settings = self.get_settings(tenant_id)
        projects = settings.get("studio_projects", [])
        project = next((p for p in projects if p.get("id") == project_id), None)
        return settings, projects, project

    def save_project(self, tenant_id: str, settings: dict, projects: list, flush_now: bool = False):
        """Cached version of _save_project."""
        settings["studio_projects"] = projects
        self.save_settings(tenant_id, settings, flush_now=flush_now)

    def invalidate(self, tenant_id: str):
        """Force cache invalidation for a tenant."""
        lock = self._get_lock(tenant_id)
        with lock:
            # Flush any dirty data first
            entry = self._cache.get(tenant_id)
            if entry and entry.get("dirty"):
                self._flush_tenant(tenant_id)
            self._cache.pop(tenant_id, None)

    def force_flush(self):
        """Force flush all dirty data (call on shutdown)."""
        self._flush_all()

    def stats(self) -> dict:
        return {
            "cached_tenants": len(self._cache),
            "dirty_tenants": len(self._dirty_tenants),
            "entries": {tid: {"dirty": e.get("dirty", False), "age_s": round(time.time() - e["ts"])}
                        for tid, e in self._cache.items()},
        }


# ═══════════════════════════════════════════════════════════
# LAYER 3: LLM RESPONSE CACHE — Content-addressable
# ═══════════════════════════════════════════════════════════

class LLMCache:
    """Content-addressable cache for LLM Vision responses.

    Hash = SHA256(prompt_text + sorted image hashes)
    Automatically invalidated when source images change.
    """

    TTL = 3600  # 1 hour

    def __init__(self):
        self._lock = threading.Lock()

    def _content_hash(self, prompt: str, image_hashes: list[str]) -> str:
        content = prompt + "|" + "|".join(sorted(image_hashes))
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _cache_path(self, content_hash: str) -> Path:
        return LLM_CACHE_DIR / f"{content_hash}.json"

    def get(self, prompt: str, image_hashes: list[str]) -> str | None:
        """Get cached LLM response if available and fresh."""
        h = self._content_hash(prompt, image_hashes)
        path = self._cache_path(h)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if time.time() - data.get("ts", 0) > self.TTL:
                path.unlink()
                return None
            return data.get("response")
        except Exception:
            return None

    def put(self, prompt: str, image_hashes: list[str], response: str):
        """Store LLM response in cache."""
        h = self._content_hash(prompt, image_hashes)
        path = self._cache_path(h)
        path.write_text(json.dumps({"response": response, "ts": time.time()}))

    def invalidate_by_image(self, image_hash: str):
        """Invalidate all cached responses that used a specific image.
        Called when an image is re-generated/inpainted.
        """
        # Simple approach: clear all LLM cache (regeneration is rare)
        count = 0
        for f in LLM_CACHE_DIR.iterdir():
            if f.suffix == ".json":
                f.unlink()
                count += 1
        if count:
            logger.info(f"LLMCache: invalidated {count} entries")

    def hash_image(self, image_bytes: bytes) -> str:
        """Generate hash for image content (for cache key)."""
        return hashlib.sha256(image_bytes).hexdigest()[:16]

    def cleanup(self):
        """Remove expired entries."""
        now = time.time()
        removed = 0
        for f in LLM_CACHE_DIR.iterdir():
            if not f.suffix == ".json":
                continue
            try:
                data = json.loads(f.read_text())
                if now - data.get("ts", 0) > self.TTL:
                    f.unlink()
                    removed += 1
            except Exception:
                f.unlink()
                removed += 1
        return removed

    def stats(self) -> dict:
        files = list(LLM_CACHE_DIR.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            "entries": len(files),
            "size_kb": round(total_size / 1024, 1),
        }


# ═══════════════════════════════════════════════════════════
# SINGLETON INSTANCES
# ═══════════════════════════════════════════════════════════

image_cache = ImageCache()
project_cache = ProjectCache()
llm_cache = LLMCache()


def get_cache_stats() -> dict:
    """Get stats from all cache layers."""
    return {
        "image_cache": image_cache.stats(),
        "project_cache": project_cache.stats(),
        "llm_cache": llm_cache.stats(),
    }
