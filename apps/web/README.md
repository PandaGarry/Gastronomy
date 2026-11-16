# Web prototype

Isolated Next.js App Router prototype for the new product concept. The repository name is not the product brand. The Russian UI label «Кулинарная лига» is a temporary concept placeholder, not approved naming.

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
- `/challenges/perfect-breakfast/submit` — submission composer demo
- `/profile` — demo profile placeholder

## Demo flow
Landing → challenge catalog → challenge detail → join (client state) → submission composer → local demo confirmation.

## Prototype limitations
- Challenge content is local demo data.
- Join state is client-only and is not persisted.
- Search and filter controls are presentation-only.
- Selected files are not uploaded or persisted.
- No authentication, database, storage, email, analytics, moderation backend, notifications, or XP ledger is connected.
- No real user data or UGC should be used.

This prototype is for UX review and usability testing only. Backend and production implementation require separate validation, privacy review, security work, and operational readiness.
