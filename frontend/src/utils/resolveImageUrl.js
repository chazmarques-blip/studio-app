/**
 * Resolves an image URL — returns full Supabase Storage URLs as-is,
 * prepends REACT_APP_BACKEND_URL for legacy relative paths (/api/uploads/...).
 */
export function resolveImageUrl(url) {
  if (!url) return '';
  // Add cache-busting for Supabase Storage URLs to prevent CDN serving stale images
  if (url.startsWith('http') && url.includes('supabase')) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}t=${Date.now()}`;
  }
  if (url.startsWith('http')) return url;
  return `${process.env.REACT_APP_BACKEND_URL}${url}`;
}
