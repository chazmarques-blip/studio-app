/**
 * Safely extract error message string from API error responses.
 * Handles Pydantic validation errors (arrays of objects) that would crash React if rendered directly.
 */
export const getErrorMsg = (err, fallback = 'Erro') => {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const msgs = detail.map(d => (typeof d === 'string' ? d : d?.msg || '')).filter(Boolean);
    return msgs.length > 0 ? msgs.join('; ') : fallback;
  }
  return fallback;
};
