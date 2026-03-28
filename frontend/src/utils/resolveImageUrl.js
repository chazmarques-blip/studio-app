/**
 * Resolves an image URL — returns full Supabase Storage URLs as-is,
 * prepends REACT_APP_BACKEND_URL for legacy relative paths (/api/uploads/...).
 */
export function resolveImageUrl(url) {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  return `${process.env.REACT_APP_BACKEND_URL}${url}`;
}
