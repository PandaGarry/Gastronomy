# Repository cleanup: archive-first plan

## Status

This document defines a controlled, reversible cleanup proposal. It does not authorize deletion, force-push, branch deletion, PR closure, history rewriting, or merging.

Active product repository: `PandaGarry/Gastronomy`  
Private legacy archive destination: `PandaGarry/Market-Research-Opportunity-Lab`  
Archive namespace: `archives/gastronomy-legacy/`  
Base snapshot inspected: `main` at `0d136498dcf5a3b2bdfdbb7cd21bd476a8d74f18`  
Plan branch: `chore/archive-first-repository-cleanup-plan`

The archive destination decision has been confirmed by the repository owner. This is authorization to update this plan; it is **not** evidence that archive files have been transferred or verified.

## Objective

Make the active Gastronomy repository contain only the current cooking-challenge product and the documentation/tooling required to build it, while preserving all legacy material and the complete old Git history in a separate private archive before any removal from the active repository.

The repository name `Gastronomy` is an implementation/repository identifier, not an approved product brand.

## Observed baseline

At the inspected `main` snapshot:

- `Recipes/`: 36 entries, including multipart 7z material and spreadsheet technical cards.
- `RedAge-3.0/`: 2,773 entries; includes a legacy Svelte client unrelated to the current product.
- `community/`: 20 entries.
- Root ZIP archive: `workspace-01a1a864-c674-7f57-accd-ebe7c65f5d56.zip` (reported size approximately 8.3 MB).
- Repository metadata reported approximately 457 MB.
- The active prototype and newer product/research work live on separate branches/PRs, not in the inspected `main` tree.

This is an inventory snapshot, not a content-level legal/privacy clearance. Counts and sizes must be refreshed during archival. Spreadsheet and archive contents must be reviewed privately before any decision to retain, publish, or delete them.

## Non-negotiable safety rules

1. Do not delete or overwrite legacy files until a private archive has been created and independently verified.
2. Keep legacy data only in the private `PandaGarry/Market-Research-Opportunity-Lab` repository or an equivalently access-restricted archive asset. Never copy it into a public archive folder in Gastronomy.
3. Do not merge the old Gastronomy Git history into the research repository's Git history. Preserve it as a self-contained Git mirror/bundle.
4. Do not rewrite public Git history, force-push, delete branches/tags, close existing PRs, or merge any PR as part of this cleanup without separate explicit owner approval.
5. Do not merge this plan PR. It is for review and acceptance only.
6. Preserve current product work from PRs/branches separately; do not flatten or discard it while cleaning legacy content.
7. Keep a written inventory, source commit IDs, archive verification results, and a tested restore procedure.
8. Treat possible personal data, confidential business information, third-party assets, and licensing questions as a separate review. A private copy does not retroactively remove public exposure.

## Phase 0 — freeze and inventory

- Freeze destructive repository operations.
- Record default branch, all branch names and head SHAs, tags, open PRs, and relevant workflow state.
- Classify every top-level directory/file as: current product, product documentation, legacy candidate, or unknown/needs review.
- Inspect the `arena/*` branches and all open PRs, especially #5, #6, #7 and #8, before deciding how to preserve or integrate their work.
- Record large files and archive formats without copying their contents into public documentation.
- Identify whether public history contains sensitive/proprietary material that may require a separate incident/legal review.
- Keep the current research documents in Market-Research-Opportunity-Lab intact; archive materials must live only under the dedicated archive namespace or in clearly named private release assets.

**Exit gate:** inventory signed off by the owner; no unknown branch or PR is silently discarded.

## Phase 1 — archive into the existing private research repository

Destination: `PandaGarry/Market-Research-Opportunity-Lab` (existing private repository). Do not create a third repository.

Recommended structure:

- `archives/gastronomy-legacy/README.md` — archive index, source URL/SHA, timestamp, restore procedure, verification status.
- `archives/gastronomy-legacy/manifests/` — refs, file inventory and checksums.
- `archives/gastronomy-legacy/reports/` — non-sensitive audit and restore reports.
- Full Git mirror/bundle and large binary snapshot — separate private GitHub Release assets or another owner-approved private asset store, not ordinary Git blobs in the research repository.

Required archive contents:

1. A full Git mirror (or verified Git bundle) of the source Gastronomy repository, preserving all intended refs, branches, tags and reachable history.
2. A separate working-tree snapshot of the legacy paths from the recorded source commit.
3. A manifest containing source URL, source commit IDs, refs, file counts, sizes, checksums, archive timestamp and restore commands.
4. A record of any refs that could not be included and why. Do not silently omit them.

Operational safeguards:

- Do not upload a ~457 MB archive blindly into ordinary Git history; inspect GitHub asset/file limits and choose a suitable private asset mechanism.
- Do not assume this connector can upload binary release assets. If it cannot, use a controlled local/Arena Git workflow and have the owner provide the resulting URLs and logs for independent verification.
- Confirm the destination repository is still private and that only intended collaborators can access the archive.
- Do not put sensitive extracted contents or detailed sensitive filenames in public documentation.

Verification:

- Clone the private mirror/bundle into a fresh location.
- Verify expected refs and commit reachability against the source manifest.
- Restore the working-tree snapshot and compare SHA-256 checksums.
- Test a representative large file and a complete checkout.
- Retain an independent backup copy until the cleanup is accepted.

Do not proceed on the basis of a successful upload alone.

**Exit gate:** private access confirmed; mirror/bundle integrity verified; manifest and checksums match; fresh restore succeeds; owner confirms access.

## Phase 2 — prepare the clean active product tree

Only after Phase 1 passes:

- Start from an explicitly selected product integration base, not automatically from legacy-only `main`.
- Preserve current UX prototype and product/engineering/research documents from their existing PRs/branches. Review overlap and dependencies before integrating.
- Establish a clean root layout, expected to include:
  - `apps/web/` — current web application;
  - `docs/` — approved product, architecture, research, and engineering documentation;
  - root project files required for development, CI, security, and contribution guidance.
- Remove legacy `Recipes/`, `RedAge-3.0/`, `community/`, and the root ZIP only in a dedicated cleanup PR after archive verification.
- Do not copy legacy recipe archives, technical cards, or unrelated Svelte code into the active tree.
- Keep the private archive outside the active repository.

The exact integration base and retained documentation list must be shown in the cleanup PR before removals are proposed. Existing PRs #5, #6, #7 and #8 must remain available for review until an explicit integration/closure plan is approved.

## Phase 3 — validation and owner acceptance

Required evidence in the cleanup PR:

- Before/after tree inventory and file-count/size comparison.
- Exact list of moved/removed paths and rationale.
- Private archive repository URL, archive asset URLs, source SHA, archive SHA/ref, manifest and checksum report.
- Restore-test result, including fresh clone and representative file restoration.
- Git diff showing no accidental edits to product code or approved documents.
- Build/typecheck/lint/test results for the resulting product tree, where runnable.
- Confirmation that all open PRs and branches were reviewed and remain intact unless separately approved.
- Known limitations, including the fact that public Git history still contains legacy objects unless a separate history purge is approved.

The owner must inspect the PR, verify archive access, and run the product locally before approving a merge.

## Phase 4 — optional public Git history remediation (separate decision)

Removing paths from the current tree does **not** remove their historical copies from Git. If the owner decides to purge public history:

- first confirm that the private mirror is complete and restorable;
- identify all affected refs, forks, PRs, releases, and clones;
- assess whether exposed content requires credential rotation, takedown, or other response;
- prepare a dedicated history-rewrite plan with exact paths and expected consequences;
- obtain explicit approval before rewriting refs or force-pushing.

This phase is out of scope for the current plan PR. Archiving privately is not equivalent to removing public exposure.

## Current state and next gate

This PR updates the plan and inventory only. It does not create the archive, transfer files, change the research repository, remove legacy content, or modify public Git history.

Next operational step: perform a source-ref inventory and create the private mirror/bundle plus legacy working-tree snapshot using a workflow capable of transferring and verifying binary data. Record evidence before proposing any cleanup PR.
