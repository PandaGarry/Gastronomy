# Web prototype

This is the isolated Next.js App Router prototype for the new product concept. The repository name is not the product brand.

## Requirements
- Node.js 20.9+
- pnpm 10+

## Run locally
```bash
cd apps/web
pnpm install
pnpm dev
```

Open http://localhost:3000.

## Available routes
- `/` — concept landing page
- `/challenges` — challenge catalog
- `/challenges/perfect-breakfast` — challenge details
- `/profile` — demo profile placeholder

## Prototype limitations
- All challenge content is local demo data.
- Join/leave is client-only state and is not persisted.
- Search and filters are presentation-only.
- No authentication, database, storage, email, analytics, moderation backend, or XP ledger is connected.
- Do not use with real personal data or real user-generated content.

This prototype exists for UX review and usability testing only. Backend and production implementation require separate validation and security work.
