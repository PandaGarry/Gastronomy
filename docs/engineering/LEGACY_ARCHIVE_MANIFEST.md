# Legacy material inventory (initial)

Snapshot: `main` at `0d136498dcf5a3b2bdfdbb7cd21bd476a8d74f18`  
Purpose: identify legacy content for private archival and later owner-reviewed removal from the active product repository.

| Path | Observed scope | Initial classification | Action |
|---|---:|---|---|
| `Recipes/` | 36 entries | Legacy / needs content and rights review | Preserve in private archive; exclude from active product tree after verification |
| `RedAge-3.0/` | 2,773 entries | Legacy application | Preserve in private archive; exclude from active product tree after verification |
| `community/` | 20 entries | Legacy / purpose to confirm | Preserve in private archive; inspect before final classification |
| `workspace-01a1a864-c674-7f57-accd-ebe7c65f5d56.zip` | ~8.3 MB reported | Legacy archive / contents unknown | Preserve in private archive; inspect privately before final decision |

Repository metadata reported approximately 457 MB total at the time of inventory.

## Additional review required

- Inspect multipart `.7z.001-.013` files and technical-card spreadsheets privately.
- Check for personal data, confidential business data, credentials, licensed/third-party materials, and ownership restrictions.
- Do not publish file contents, extracted inventories of sensitive data, or archive copies in this repository.
- Inspect all current branches, especially `arena/*`, plus open PRs #5, #6, and #7 before selecting the product integration base.
- Do not infer that an item is safe to publish merely because it is already present in a public repository.

## Verification fields to complete before cleanup

- [ ] Private archive repository created and access checked
- [ ] Source mirror created with all refs
- [ ] Working-tree snapshot created
- [ ] File manifest and checksums generated
- [ ] Fresh clone/restore test passed
- [ ] Owner confirms archive is accessible
- [ ] Branch/PR preservation matrix completed
- [ ] Exact cleanup diff reviewed
