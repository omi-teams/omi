---
id: nextjs
summary: Next.js App Router: components, data, caching, env
applies: app/**, **/*.tsx, next.config.*
---
# nextjs

- App Router: components are server components unless they need state or browser APIs; add `"use client"` only then.
- Fetch data in server components or route handlers, not in `useEffect`.
- State caching explicitly (`revalidate`, `cache: "no-store"`) for every fetch that matters.
- Only `NEXT_PUBLIC_` env vars reach the browser; never put a secret there.
- Use `next/image` and `next/link`; add `loading.tsx` and `error.tsx` for slow or failing routes.
- Validate input in route handlers and server actions; keep TypeScript `strict` and avoid `any`.
