"""Video Provider — Sora 2 video generation implementation."""
import os
import time
import logging
import requests
from .base import VideoProvider
from core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class Sora2Provider(VideoProvider):
    """OpenAI Sora 2 video generation via direct API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"

    def generate(self, prompt: str, reference_image_path: str = None,
                 size: str = "1280x720", duration: int = 12) -> bytes:
        auth_header = {"Authorization": f"Bearer {self.api_key}"}

        # Start render job
        if reference_image_path and os.path.exists(reference_image_path):
            resp = self._start_with_image(prompt, reference_image_path, size, duration, auth_header)
        else:
            resp = requests.post(
                f"{self.base_url}/videos",
                headers={**auth_header, "Content-Type": "application/json"},
                json={"model": "sora-2", "prompt": prompt, "size": size, "seconds": str(duration)},
                timeout=60,
            )

        resp.raise_for_status()
        job = resp.json()
        video_id = job.get("id")
        if not video_id:
            raise Exception(f"No video ID in response: {job}")

        logger.info(f"Sora 2 job created: {video_id}")

        # Poll until completed
        return self._poll_and_download(video_id, auth_header, max_wait=600)

    def _start_with_image(self, prompt, image_path, size, duration, auth_header):
        from PIL import Image as PILImage
        import io

        img = PILImage.open(image_path)
        w, h = [int(x) for x in size.split("x")]
        if img.size != (w, h):
            canvas = PILImage.new("RGB", (w, h), (0, 0, 0))
            ratio = min(w / img.width, h / img.height)
            nw, nh = int(img.width * ratio), int(img.height * ratio)
            resized = img.resize((nw, nh), PILImage.LANCZOS)
            canvas.paste(resized, ((w - nw) // 2, (h - nh) // 2))
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            img_data = buf
        else:
            img_data = open(image_path, "rb")

        files = {"input_reference": ("reference.png", img_data, "image/png")}
        data = {"model": "sora-2", "prompt": prompt, "size": size, "seconds": str(duration)}
        resp = requests.post(f"{self.base_url}/videos", headers=auth_header, data=data, files=files, timeout=60)

        if hasattr(img_data, 'close'):
            img_data.close()

        if resp.status_code == 400:
            err_text = resp.text.lower()
            if "face" in err_text or "moderation" in err_text:
                logger.warning(f"Sora 2: Image rejected, falling back to text-only")
                resp = requests.post(
                    f"{self.base_url}/videos",
                    headers={**auth_header, "Content-Type": "application/json"},
                    json={"model": "sora-2", "prompt": prompt, "size": size, "seconds": str(duration)},
                    timeout=60,
                )
        return resp

    def _poll_and_download(self, video_id, auth_header, max_wait=600):
        start = time.time()
        while time.time() - start < max_wait:
            time.sleep(10)
            poll = requests.get(f"{self.base_url}/videos/{video_id}", headers=auth_header, timeout=30)
            if poll.status_code != 200:
                continue

            pdata = poll.json()
            status = pdata.get("status", "")

            if status == "completed":
                for attempt in range(3):
                    try:
                        dl = requests.get(
                            f"{self.base_url}/videos/{video_id}/content",
                            headers=auth_header, timeout=300, stream=True,
                        )
                        dl.raise_for_status()
                        chunks = [c for c in dl.iter_content(chunk_size=1024 * 1024)]
                        video_bytes = b"".join(chunks)
                        logger.info(f"Sora 2 [{video_id[:12]}]: Downloaded {len(video_bytes) // 1024}KB")
                        return video_bytes
                    except Exception as dl_err:
                        if attempt < 2:
                            time.sleep(5)
                        else:
                            raise Exception(f"Sora 2 download failed: {dl_err}")

            elif status == "failed":
                error = pdata.get("error", {})
                msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                raise Exception(f"Sora 2 failed: {msg}")

        raise Exception(f"Sora 2 timeout after {max_wait}s")
