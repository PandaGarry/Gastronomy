# Repository cleanup: archive-first plan

## Status

This document proposes a controlled, reversible cleanup. It does not authorize deletion, force-push, branch deletion, PR closure, or history rewriting.

Target repository: `PandaGarry/Gastronomy`  
Base snapshot inspected: `main` at `0d136498dcf5a3b2bdfdbb7cd21bd476a8d74f18`  
Plan branch: `chore/archive-first-repository-cleanup-plan`

## Objective

Make the active repository contain only the current cooking-challenge product and the documentation/tooling required to build it, while preserving all legacy material in a separate private archive before any removal from the active repository.

The repository name `Gastronomy` is an implementation/repository identifier, not an approved product brand.

## Observed baseline

At the inspected `main` snapshot:

- `Recipes/`: 36 entries, including multipart 7z material and spreadsheet technical cards.
- `RedAge-3.0/`: 2,773 entries; includes a legacy Svelte client unrelated to the current product.
- `community/`: 20 entries.
- Root ZIP archive: `workspace-01a1a864-c674-7f57-accd-ebe7c65f5d56.zip` (reported size approximately 8.3 MB).
- Repository metadata reported approximately 457 MB.
- The active prototype and newer product/research work live on separate branches/PRs, not in the inspected `main` tree.

This is an inventory snapshot, not a content-level legal/privacy clearance. Spreadsheet and archive contents must be reviewed in the private archive before any decision to retain, publish, or delete them.

## Non-negotiable safety rules

1. Do not delete or overwrite legacy files until a private archive has been created and independently verified.
2. Do not put legacy materials into a public `archive/` directory. The archive destination must be a private repository or an equivalently access-restricted storage location.
3. Do not rewrite Git history, force-push, delete branches/tags, close existing PRs, or merge any PR as part of this cleanup without a separate explicit owner approval.
4. Do not merge this plan PR. It is for review and acceptance only.
5. Preserve current product work from PRs/branches separately; do not flatten or discard it while cleaning legacy content.
6. Keep a written inventory, source commit IDs, archive verification results, and a restore procedure.
7. Treat possible personal data, confidential business information, third-party assets, and licensing questions as a separate review. A private copy does not retroactively remove public exposure.

## Phase 0 — freeze and inventory

- Freeze destructive repository operations.
- Record default branch, all branch names and head SHAs, tags, open PRs, and relevant workflow state.
- Classify every top-level directory/file as: current product, product documentation, legacy candidate, unknown/needs review.
- Inspect the two `arena/*` branches and all open PRs before deciding whether they contain unmerged work.
- Record large files and archive formats without copying their contents into public documentation.
- Identify whether the existing public history contains sensitive/proprietary material that may require a separate incident/legal review.

**Exit gate:** inventory signed off by the owner; no unknown branch or PR is silently discarded.

## Phase 1 — create and verify private archive

Preferred approach:

- Create a dedicated **private** archive repository outside the active product repository.
- Make a mirror backup of the source repository so all refs and history are preserved; also retain a separately accessible working-tree snapshot of the legacy paths.
- Include source repository URL, source default-branch SHA, branch/tag manifest, archive timestamp, and file manifest.
- Verify the archive by cloning it into a fresh location and checking refs, commit reachability, file counts, and checksums for large files.
- Test restoration of a representative file and a complete checkout.
- Keep at least one independent backup copy until the cleanup is accepted.

Do not proceed on the basis of a successful upload alone. Archive verification must be evidenced.

**Exit gate:** private access confirmed; mirror clone succeeds; manifest and checksums match; restore test succeeds.

## Phase 2 — prepare the clean active project tree

Only after Phase 1 passes:

- Start from an explicitly selected product integration base, not automatically from legacy-only `main`.
- Preserve the current UX prototype and product/engineering/research documents from their existing PRs/branches. Review overlap and dependencies before integrating.
- Establish a clean root layout, expected to include:
  - `apps/web/` — current web application;
  - `docs/` — approved product, architecture, research, and engineering documentation;
  - root project files required for development, CI, security, and contribution guidance.
- Remove legacy `Recipes/`, `RedAge-3.0/`, `community/`, and the root ZIP only in the dedicated cleanup PR after archive verification.
- Do not copy legacy recipe archives, technical cards, or unrelated Svelte code into the active tree.
- Keep the archive private and outside the active repository.

The exact integration base and retained documentation list must be shown in the PR before removals are proposed.

## Phase 3 — validation and owner acceptance

Required evidence in the cleanup PR:

- Before/after tree inventory and file-count/size comparison.
- Exact list of moved/removed paths and rationale.
- Archive repository URL (private; visible to owner), source SHA, archive SHA/ref, manifest and checksum report.
- Restore-test result.
- Git diff showing no accidental edits to product code.
- Build/typecheck/lint/test results for the resulting product tree, where runnable.
- Confirmation that all open PRs and branches were reviewed and remain intact unless separately approved.
- Known limitations, including the fact that Git history still contains legacy objects unless a separate history purge is approved.

The owner must inspect the PR, verify archive access, and run the product locally before approving a merge.

## Phase 4 — optional public Git history remediation (separate decision)

Removing paths from the current tree does **not** remove their historical copies from Git. If the owner decides to purge public history:

- first confirm that the private mirror is complete and restorable;
- identify all affected refs, forks, PRs, releases, and clones;
- assess whether any exposed content requires credential rotation, takedown, or other response;
- prepare a dedicated history-rewrite plan with exact paths and expected consequences;
- obtain explicit approval before rewriting refs or force-pushing.

This phase is out of scope for the current plan PR.

## Current decision requested

Review and approve the archive-first sequence and the inventory/classification approach. Approval of this document alone does not authorize file deletion, history rewriting, branch deletion, or PR merging.
