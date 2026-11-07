# RedAge 3.0 source snapshot

- Source: https://github.com/ragemp-pro/redage_v3
- Snapshot commit: `23730b8cd464f86c47eaae6f80d182cd651092b2` (2026-03-06)
- The project owner permission was reported by the user; retain the owner's written permission and clarify what it covers before redistribution or publication.
- This is a sparse source checkout for inspection, not a runnable server package. It includes server C# source, client JavaScript, CEF/Svelte source, SQL schemas, configuration/data files, and `dotnet/resources/NeptuneEvo/meta.xml` fetched from the same upstream revision to document the RAGE:MP resource entry.
- Large platform runtimes, server binaries, built client packages, and heavy image/font/media assets were not included in the persistent project folder. Fetch only the required components from the authorized source when deployment and licensing scope are confirmed.
- Credential-bearing values found in upstream `settings/mainDB.json` and a commented website DB connection line in `Main.cs` were replaced locally. The upstream `.git` object database was removed so those original blobs are not retained in this workspace. `settings/mainDB.json` remains ignored by `.gitignore`; do not commit real credentials. If any exposed credential was live, the owner should rotate it.
- The upstream repository has no LICENSE file. The user reports direct permission from the owner; keep that written authorization with the project.
