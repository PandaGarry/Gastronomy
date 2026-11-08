# CEF build mode and production output review

Date: 2026-11-08
Status: configuration patch applied; clean build and RAGE:MP CEF validation pending.

## PERF-002 — build scripts could silently default to development mode

### Source evidence
- `src_cef/package.json` originally invoked webpack without setting `NODE_ENV` for `build`, `buildtest` and `builden`.
- All three webpack configurations use `const mode = process.env.NODE_ENV || 'development'`.
- They set `devtool: prod ? false : 'source-map'`.
- All three Svelte loader configurations originally set `hotReload: true` unconditionally.
- `cross-env` is already a declared devDependency.

When an operator runs a build script from a clean shell with `NODE_ENV` unset, webpack therefore selects development mode, emits source maps and leaves Svelte hot reload enabled. An external deployment environment may already set production, so this is a reproducibility/deployment-default risk, not proof that a production server currently ships a development bundle.

### Patch applied
- `build`, `buildtest`, and `builden` now prefix webpack with `cross-env NODE_ENV=production`.
- `dev` now explicitly sets `NODE_ENV=development`.
- Each webpack config sets Svelte `hotReload: !prod`, so hot reload is disabled in production and retained in development.
- No dependency was added; the existing `cross-env` package is reused.

Webpack's production mode should activate its production optimizations and production Svelte compilation; `devtool` is already configured to disable source maps when `prod` is true.

### What is not claimed
- No bundle-size reduction has been measured.
- No CEF build was run after the patch.
- No RAGE:MP client startup, UI interaction, cache/CDN or source-map exposure test was run.
- CSS minification and tree-shaking effectiveness remain separate profiling tasks; do not assume the unused `cssnano`/CSS optimization dependencies are active merely because they are declared.

### Validation plan
1. In clean shells with `NODE_ENV` unset, run `npm run build`, `npm run buildtest`, and `npm run builden`.
2. Confirm each webpack compiler uses production mode; emitted config must have no source maps and Svelte hot reload disabled.
3. Verify expected language output paths and HTML references for each build.
4. Compare raw and gzip/brotli JS/CSS size to the previous baseline; inspect bundle analyzer output before removing dependencies or changing chunks.
5. Launch each generated CEF variant in RAGE:MP and smoke-test login, HUD, inventory, phone, dialogs and resource navigation.
6. Keep the explicit dev command working and confirm hot reload remains active there.

This is a deterministic build-configuration improvement. It is not yet a verified production bundle optimization until the build and runtime steps pass.
