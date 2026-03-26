import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Layer 4: Frontend Intelligent Cache
 * - SWR (stale-while-revalidate) pattern
 * - Optimistic updates
 * - Image preloading
 */

// ═══ In-memory SWR cache ═══
const cache = new Map();
const STALE_TIME = 30_000; // 30s — serve stale data while revalidating
const CACHE_TIME = 300_000; // 5min — max cache lifetime

function getCacheEntry(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > CACHE_TIME) {
    cache.delete(key);
    return null;
  }
  return entry;
}

function setCacheEntry(key, data) {
  cache.set(key, { data, ts: Date.now() });
  // Evict oldest if too many entries
  if (cache.size > 100) {
    const oldest = cache.keys().next().value;
    cache.delete(oldest);
  }
}

/**
 * useSWRFetch — SWR data fetching hook.
 * Returns cached data instantly, revalidates in background.
 */
export function useSWRFetch(url, options = {}) {
  const { enabled = true, interval = 0 } = options;
  const [data, setData] = useState(() => getCacheEntry(url)?.data || null);
  const [loading, setLoading] = useState(!data);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async (silent = false) => {
    if (!url || !enabled) return;
    if (!silent) setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const json = await res.json();
      if (mountedRef.current) {
        setData(json);
        setCacheEntry(url, json);
        setError(null);
        setLoading(false);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err);
        setLoading(false);
      }
    }
  }, [url, enabled]);

  useEffect(() => {
    mountedRef.current = true;
    const entry = getCacheEntry(url);
    if (entry) {
      setData(entry.data);
      setLoading(false);
      // If stale, revalidate in background
      if (Date.now() - entry.ts > STALE_TIME) {
        fetchData(true);
      }
    } else {
      fetchData();
    }
    return () => { mountedRef.current = false; };
  }, [url, fetchData]);

  // Polling interval
  useEffect(() => {
    if (!interval || !enabled) return;
    const timer = setInterval(() => fetchData(true), interval);
    return () => clearInterval(timer);
  }, [interval, enabled, fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Image preloader — preload next frames while user views current.
 */
const preloadedImages = new Set();

export function preloadImages(urls) {
  urls.forEach(url => {
    if (!url || preloadedImages.has(url)) return;
    const img = new window.Image();
    img.src = url;
    preloadedImages.add(url);
  });
}

/**
 * useImagePreloader — automatically preload adjacent frames.
 */
export function useImagePreloader(panels, currentScene) {
  useEffect(() => {
    if (!panels?.length) return;

    // Preload current scene's frames
    const current = panels.find(p => p.scene_number === currentScene);
    if (current?.frames) {
      preloadImages(current.frames.map(f => f.image_url).filter(Boolean));
    }

    // Preload next 2 scenes
    const currentIdx = panels.findIndex(p => p.scene_number === currentScene);
    for (let i = 1; i <= 2; i++) {
      const next = panels[currentIdx + i];
      if (next?.frames) {
        preloadImages(next.frames.map(f => f.image_url).filter(Boolean));
      }
    }
  }, [panels, currentScene]);
}

/**
 * Invalidate cache entries matching a prefix.
 */
export function invalidateCache(urlPrefix) {
  for (const key of cache.keys()) {
    if (key.includes(urlPrefix)) {
      cache.delete(key);
    }
  }
}

/**
 * Optimistic update — update cache immediately before API call completes.
 */
export function optimisticUpdate(url, updater) {
  const entry = getCacheEntry(url);
  if (entry) {
    const newData = updater(entry.data);
    setCacheEntry(url, newData);
    return newData;
  }
  return null;
}
