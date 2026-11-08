# LS Customs tuning remote session and stale context — static review

Обновлено: 2026-11-08. Traced business interaction, personal/organization tuning entry, client event IDs, exit callback, purchase remote and character position resolution. Static-only; RAGE event reachability and vehicle state effects were not runtime-tested.

## VEH-010 — organization tuning exit leaves a reusable personal tuning context

**Приоритет: средний/высокий; stale state and missing remote-session validation are statically confirmed; gameplay impact requires staging.**

- StartTuning sets CharacterData.TuningShop = bizId when entering personal vehicle tuning (Core/Businesses.cs:1435). The organization vehicle branch also assigns the same field before opening the UI with event ID 1 (around 1470).
- The client custom UI stores the supplied event ID and sends it to server.custom.exit when exiting (src_client/shop/custom/index.js:49-65, 192-208). For organization tuning the server receives eventType=1.
- RemoteEvent_exitTuning case 0/2 returns the vehicle and resets CharacterData.TuningShop = -1. Case 1 (organization) returns the organization vehicle and reapplies its customization, but does not reset TuningShop (Core/Businesses.cs:1506-1565). This leaves the business ID from the tuning session in character state after the UI closes.
- RemoteEvent_buyTuning (server.custom.buy) reads CharacterData.TuningShop and only checks that BizList contains that ID, that the player is in a vehicle, and that VehicleManager.canAccessByNumber allows the current plate (Core/Businesses.cs:1620-1655). It does not require an active tuning intent, Type==12, current proximity, matching dimension or that the player is still in the tuning interior.
- Therefore, after organization tuning exit, a direct invocation of the personal server.custom.buy remote can reuse the stale business ID and attempt to reserve that business' Запчасти and customize the caller's currently accessible personal vehicle away from LS Customs. The later purchase still uses shared STOCK-002 settlement paths; this review records the missing tuning-session authorization, not the unchecked wallet/stock effects.
- Character.Repository resolves a non--1 CharacterData.TuningShop to the business EnterPoint when calculating CurPosition (Character/Repository.cs:68-73). A stale value can therefore also influence subsequent position resolution. Exact disconnect/reconnect impact depends on the caller/order and must be tested.

**Impact boundary:** the state leak and absent server-side session/type/location checks are visible statically. The direct remote call sequence, current vehicle marshalling and whether later lifecycle code clears TuningShop require disposable RAGE staging. No successful exploit or unauthorized purchase is claimed as reproduced.

**Remediation (not implemented):** replace the long-lived TuningShop integer with a short-lived server-issued tuning intent bound to player, Type==12 business, current vehicle identity/plate, position, dimension and expiry. Require and consume that intent in every tuning purchase remote; verify the current vehicle still matches. Reset intent and TuningShop on all exit paths, including organization exit, UI cancellation, failed initialization, vehicle change, disconnect and resource stop. Keep organization tuning separate from personal business-stock purchases. Make character position resolution ignore expired/invalid tuning state.

## Regression matrix

- Enter organization tuning (event ID 1), exit normally, then call server.custom.buy directly while in an accessible personal vehicle away from LS Customs: reject without stock, bank, wallet, customization or position mutation.
- Enter personal Type==12 tuning, leave range/change dimension/swap vehicle, then call the purchase remote: reject.
- Call purchase remote with no prior tuning session, with stale/deleted/non-Type==12 business ID and after disconnect/reconnect: reject.
- Verify eventType 0, 1 and 2 all clear the tuning intent; test repeated exit and malformed eventType.
- Confirm organization tuning continues to save only organization vehicle customization and cannot reuse the personal business purchase endpoint.
- Verify character CurPosition after normal exit, organization exit, disconnect and reconnect; stale TuningShop must never force a business EnterPoint.
- Test stock/wallet failure and duplicate/concurrent tuning purchases under STOCK-002; no partial stock, bank, wallet or customization mutation.

## Scope boundary

VEH-010 is separate from VEH-004/VEH-005 entity-argument tuning/vehicle-action paths and STOCK-002 business stock/customer settlement. It specifically covers the stale personal tuning context left by organization tuning exit and the unbound server.custom.buy remote.
