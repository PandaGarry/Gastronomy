# Vehicle trunk inventory access and session binding — static review

Обновлено: 2026-11-08. Traced vehicleSelected → LoadOtherItemsData → generic inventory move/stack/use endpoints. Static-only; no RAGE/CEF runtime or disposable DB tests.

## INV-012 — vehicle trunk inventory lacks per-operation session/access revalidation

**Приоритет: средний/высокий; missing repeated checks are statically confirmed. Whether a physically open trunk is intentionally public requires gameplay-owner confirmation.**

- Core/Selecting.cs:372-381 checks that the supplied vehicle is within 5m. In vehicleSelected branch 3 (around :471-520), the server permits Personal/Garage/Fraction/Organization/OrganizationGarage vehicle containers. For non-admins it checks that the trunk is open, but does not repeat the owner/key, faction membership, organization membership or minimum-rank checks used by branch 1 when opening the trunk.
- The branch sets vehicleLocalData.BagInUse, stores the vehicle in sessionData.SelectData.SelectedVeh, and calls LoadOtherItemsData with the vehicle SQL ID/plate. Chars/Repository.cs:2877-2903 calls OtherClose and stores only sessionData.InventoryOtherLocationName; it does not create a short-lived vehicle inventory authorization bound to entity, range, dimension, door or ACL.
- Generic inventory remotes server.gamemenu.inventory.move, .move.stack and .use (Chars/Events.cs:185-219) call ItemsMove, ItemsMoveStack and ItemsUse. These methods (Chars/Repository.cs:4882-4965, 4933+, 5305+) check the special read-only tent state but do not revalidate vehicle owner/key/rank, distance, dimension, door state or current selected vehicle. ItemsUse with ArrayName == "other" adds the selected item to the caller's character inventory and clears the other slot.
- Thus, once a vehicle container is open, subsequent item operations rely on the mutable session location string. A modified client can attempt extraction after moving away, changing dimension, closing/replacing the vehicle context or losing membership/access. The initial 5m and trunk-open checks do not protect later operations. Exact event reachability and public-open-trunk policy require staging and gameplay-owner confirmation.

**Impact boundary:** no claim of confirmed theft or successful cross-owner extraction. Static evidence establishes missing per-operation context revalidation and an item extraction path. If open-trunk public access is intended, the missing proximity/session freshness checks remain a separate concern.

**Remediation (not implemented):** issue a short-lived vehicle-inventory intent bound to player, exact vehicle entity/plate, access class, holder/key or faction/org membership and rank, position/dimension, trunk state and expiry. Validate it on every move/stack/use/drop endpoint; revoke on movement, dimension change, door close, vehicle deletion/replacement, membership/key revocation, timeout and disconnect. Keep physically open trunk policy explicit; never let stale InventoryOtherLocationName alone authorize mutation.

## Regression matrix

- Open own, key-shared, foreign, faction, organization and organization-garage trunks; confirm intended public-open policy and min-rank/role rules.
- After opening, move beyond 5m, change dimension, close trunk, despawn/replace vehicle, revoke keys or leave faction/organization; direct move/stack/use/drop remotes using other must reject without item/cache/DB mutation.
- Test vehicleSelected branch 3 with foreign entity/plate, open/closed trunk, dead vehicle, invalid class and simultaneous BagInUse; ensure no unauthorized session is issued.
- Verify close/revoke/timeout/disconnect clears InventoryOtherLocationName and SelectedVeh/BagInUse; no stale container survives reconnect or vehicle replacement.

## Scope boundary

INV-012 is a concrete vehicle-container case within the broader INV-003 server-side container policy gap. It does not claim the physical-open-trunk design is inherently insecure; the missing per-operation session, range and context revalidation is the specific finding.


## Related lifecycle finding

The authorization/session issue above is tracked as INV-012. A separate cleanup defect is tracked as VEH-012 in `VEHICLE_TRUNK_LIFECYCLE_REVIEW.md`: closing only the auxiliary pane invokes `OtherClose` but currently does not release the selected vehicle's `BagInUse` reservation. Keep access revalidation and reservation release as separate fixes and regression suites.
