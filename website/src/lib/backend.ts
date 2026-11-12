// Single source of truth for the shared backend's address.
// 1. NEXT_PUBLIC_BACKEND_URL wins if set (Vercel env var, or start-local.sh).
// 2. Otherwise: the Railway backend in production builds, the Flask dev server locally.
const RAILWAY_BACKEND = "https://backend-code-production-77c7.up.railway.app";

export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (process.env.NODE_ENV === "production" ? RAILWAY_BACKEND : "http://127.0.0.1:5050");
