---
id: nextjs-app-router
summary: Next.js App Router component, routing and data conventions
---
# Next.js App Router

Use this reference when working on an App Router application.

## Components and routes
Keep data access in server components or route handlers. Add `"use client"` at
the smallest boundary that needs state, event handlers or browser APIs. Use
layouts for shared route structure and loading/error boundaries for route feedback.

## Data and configuration
Choose caching and revalidation behavior explicitly for data whose freshness
matters, following the installed Next.js version. Validate route handler and
server action input. Keep secrets in server-only modules; NEXT_PUBLIC_ values
are exposed to the browser. Use next/link for navigation and next/image for
images when appropriate for the project.
