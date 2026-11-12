// Single source of truth for the shared backend's address.
// Production (Vercel): set NEXT_PUBLIC_BACKEND_URL to the Railway URL.
// Local dev: falls back to the Flask dev server.
export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:5000";
