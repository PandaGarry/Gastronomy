# Legacy material inventory (initial)

Snapshot: `PandaGarry/Gastronomy` `main` at `0d136498dcf5a3b2bdfdbb7cd21bd476a8d74f18`  
Archive destination: private repository `PandaGarry/Market-Research-Opportunity-Lab`  
Archive namespace: `archives/gastronomy-legacy/`

Purpose: identify legacy content for private archival and later owner-reviewed removal from the active product repository. This inventory is not proof that the archive has already been created.

| Path | Observed scope | Initial classification | Required treatment |
|---|---:|---|---|
| `Recipes/` | 36 entries | Legacy / needs content and rights review | Preserve in private archive; exclude from active product tree only after verification |
| `RedAge-3.0/` | 2,773 entries | Legacy application | Preserve in private archive; exclude from active product tree only after verification |
| `community/` | 20 entries | Legacy / purpose to confirm | Preserve in private archive; inspect before final classification |
| `workspace-01a1a864-c674-7f57-accd-ebe7c65f5d56.zip` | ~8.3 MB reported | Legacy archive / contents unknown | Preserve in private archive; inspect privately before final decision |

Repository metadata reported approximately 457 MB total at the time of inventory. These are historical observations and must be refreshed during the actual archive operation.

## Archive layout and separation

Use the existing private `PandaGarry/Market-Research-Opportunity-Lab` repository. Keep the legacy archive clearly separated from active market research:

- `archives/gastronomy-legacy/README.md` — archive index, source metadata, restore instructions and verification status.
- `archives/gastronomy-legacy/manifests/` — branch/tag manifest, file inventory and checksums; do not expose sensitive filenames or extracted contents unnecessarily.
- `archives/gastronomy-legacy/reports/` — non-sensitive verification reports.
- Full Git mirror/bundle and large binary snapshot — store as separate private archive assets (for example, private GitHub Release assets) rather than committing hundreds of megabytes or oversized files into the research repository's normal Git history.

Do not merge the old Gastronomy Git history into the research repository's history. Preserve it as a self-contained mirror/bundle so it can be restored independently. Confirm the actual asset size limits and access controls before choosing the upload mechanism.

## Additional review required

- Inspect multipart `.7z.001-.013` files and technical-card spreadsheets privately.
- Check for personal data, confidential business data, credentials, licensed/third-party materials, and ownership restrictions.
- Do not publish file contents, extracted inventories of sensitive data, or archive copies in the public Gastronomy repository.
- Inspect all current branches, especially `arena/*`, plus open PRs #5, #6, #7 and #8 before selecting the product integration base.
- Do not infer that an item is safe to publish merely because it is already present in a public repository.
- A private archive preserves material; it does not remove historical copies from the public source repository or its forks/clones.

## Verification fields to complete before cleanup

- [ ] Existing research repository confirmed private and owner access verified
- [ ] Archive namespace created without mixing with active research
- [ ] Source mirror/bundle created with all intended refs (branches and tags)
- [ ] Working-tree snapshot created for legacy paths
- [ ] File manifest and SHA-256 checksums generated
- [ ] Git bundle/mirror integrity verified
- [ ] Fresh clone/restore test passed
- [ ] Representative large files restored and checksums match
- [ ] Owner confirms archive is accessible
- [ ] Branch/PR preservation matrix completed
- [ ] Exact cleanup diff reviewed

No checklist item is complete merely because this plan was committed.
