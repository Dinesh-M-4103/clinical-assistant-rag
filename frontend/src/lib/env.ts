/** Build-time configuration, read once so the rest of the app never touches `import.meta.env`. */

export const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/+$/,
  '',
);

export const API_PREFIX = '/api/v1';

export const MAX_UPLOAD_MB = 25;
