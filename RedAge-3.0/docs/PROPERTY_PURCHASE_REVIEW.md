# House purchase remote — static review

Обновлено: 2026-11-07. Traced `server.houseinfo.action("buy")` and the house owner/wallet debit sequence. This is a narrow purchase-flow slice; no code changes, .NET build, RAGE staging or shutdown test.

## MONEY-017 — ignored wallet rejection can grant a house without payment during shutdown

**Приоритет: низкий/средний; conditional shutdown timing, not reproduced.**

- `OnHouseInfoAction` checks the session's server-side `HouseID`, current unowned/non-auction status, positive price, player's current cash and one-house limit (`HouseManager.cs:1383-1435`). `HouseID` is assigned by the house-entry colshape and reset on leaving (`:1080-1104`). The handler does not accept a client-provided house ID.
- On the `buy` path, after those checks it calls `house.SetOwner(player.Name)` (`:1447-1456`) and only then `Wallet.Change(player, -house.Price)` (`:1462`); it ignores the boolean result. `SetOwner` schedules the owner mutation and sets `IsSave=true` (`:562-591`).
- `Wallet.Change` explicitly returns `false` for any negative amount while `Admin.IsServerStoping` is true (`MoneySystem/Wallet.cs:20-38`). If the remote is still processed during this shutdown window, the ownership mutation can proceed while the debit is rejected. The exact server-stop/event/worker ordering is untested; treat this as a conditional path, not an observed free-house exploit.

**Remediation (not implemented):** reject property purchases once shutdown begins and make the debit result a prerequisite for ownership transfer. Prefer one idempotent transaction/receipt covering the buyer debit, owner update and house balance initialization; compensate if the owner mutation fails.

**Regression:** ordinary purchase, forged buy without server-side `HouseID`, occupied/auction/zero-price/max-one-house constraints, concurrent buyers, `Wallet.Change=false` during shutdown, and DB failure/restart between debit and owner save. Assert exactly one owner and exactly one debit, and reconcile house balance, garage, player cash and notifications. Requires RAGE staging and disposable DB fault injection.

## Boundaries

No client-supplied house ID was found on this endpoint. This review does not cover business purchase, auctions, house transfers or bank/tax flows; sale settlement is tracked separately in `PROPERTY_SALE_REVIEW.md` (`MONEY-016`).


## 2026-11-08 source remediation update — MONEY-017 (partial)

The current purchase flow now initializes the property bank balance before the debit, checks `Wallet.Change(player, -house.Price)`, and does not transfer ownership or emit purchase success effects when the debit is rejected. If the debit fails, it attempts to restore the previous property-bank balance and logs a failed compensation. Ownership and bank initialization still are not a single durable DB transaction; runtime shutdown/replay/restart tests remain pending.
