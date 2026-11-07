# House furniture purchase/craft and phone-property path — static review

Обновлено: 2026-11-07. Traced phone house load/actions into `server.house.*` plus the separate furniture shop buy/craft and sell remotes. Cross-referenced existing house ACL/property findings. Static source only; no direct RAGE inventory/furniture reproduction, database fault injection or owner-policy confirmation.

## INV-009 — furniture crafting can count ingredients outside the location it consumes

**Приоритет: низкий/средний; source mismatch confirmed; direct move→craft sequence requires RAGE regression test.**

- `server.furniture.buy(name,type)` reaches `HouseManager.OnFurnitureBuy` (`HouseManager.cs:1857-1860`). For any nonzero `type`, it checks each recipe using `Chars.Repository.getCountItem($"char_{UUID}", itemId, bagsToggled:false)` (`:1912-1921`) and then calls `Chars.Repository.Remove(player, $"char_{UUID}", "inventory", itemId, count)` (`:1923-1927`) without checking a consumption result, before creating the furniture and marking it dirty (`:1930-1931`).
- `getCountItem` iterates every sub-location in the character item map (`Chars/Repository.cs:4485-4513`), whereas `Remove` is explicitly restricted to the supplied `Location` (`:3410-3445`). A recipe ingredient present in a non-`inventory` character slot can therefore satisfy the count check while the subsequent inventory-only removal finds nothing; the furniture creation still proceeds.
- The CEF inventory policy disallows `newItemType.None` resources such as `Iron`/wood in fast slots (`src_cef/.../inventory.svelte:964-980`), but the direct `server.gamemenu.inventory.move` handler passes locations to `ItemsMove`, which swaps/sets the data without those item-type checks (`Chars/Events.cs:185-205`, `Chars/Repository.cs:4933-4983`). This establishes a plausible direct-call chain (move recipe items to `fastSlots`, then craft) relying on the separately open server inventory policy gap `INV-003`. The chain and resulting inventory/furniture state have not been reproduced.
- The immediate effect is furniture without consuming the recipe material; no arbitrary other-player inventory access or profitable resale is asserted. House ownership/location and the furniture count cap remain required server checks.

**Remediation work:** implement a single server-side craft operation that validates the exact recipe and atomically consumes the required quantities from explicitly allowed inventory locations before creating furniture; check the actual removal result and roll back/compensate on furniture-save failure. Do not use client UI move restrictions as a server policy. Test direct `inventory.move` of each recipe material to fast slots/accessories and direct furniture craft, including insufficient/partial stacks, repeated calls and DB failure/restart.

## Existing house/property boundaries confirmed in the phone route

- The phone house UI calls `server.phone.house.load`, then delegates resident actions to `server.house.resident.access` and `.dell` (`src_client/phone/property/house.js:6-8,101-108`). Those handlers are already covered by `PROP-001`: they resolve the caller's owner-or-roommate house and do not verify owner/delegated rights before changing/removing the named roommate. No duplicate finding is added here.
- The house/property read endpoints accept no arbitrary target house ID and derive data from the caller's own house/business membership; the specific read-only path is documented in `PHONE_DISPATCH_REVIEW.md`. The phone's garage actions still depend on separately reviewed garage/property ACLs (`VEH-002`, `PROP-001`).
- Owner-side home upgrades, government sale, house sale/purchase and their conditional settlement behavior are cross-covered by `MONEY-016..017`, `MONEY-019`, `PROP-002..003` and existing property reviews. This slice does not close their staging/failure tests.

## Boundaries

No conclusion about crafting item move policy beyond the traced fast-slot path, other containers, all furniture recipes, item save queue recovery, home UI permissions, shared-house privacy, or all house/property remotes. `INV-009` and linked findings remain open until direct RAGE and DB tests validate the preconditions and behavior.
