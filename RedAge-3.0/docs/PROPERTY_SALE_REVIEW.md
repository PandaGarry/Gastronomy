# House sale-to-government settlement — static review

Обновлено: 2026-11-07. Traced `server.house.action("sell")` → generic `dialogCallback("HOUSE_SELL_TOGOV", true)` → `House.ClearOwner` → wallet/house persistence. Property sale is a single path, not a full property audit. No code changes, build or DB/RAGE tests.

## MONEY-016 — house-sale payout and owner clearing persist independently

**Приоритет: средний; conditional crash/restart duplicate-sale risk, not reproduced.**

- `HouseManager.OnHouseAction` (`HouseManager.cs:1513-1593`) restricts non-open/leave actions to `GetHouse(player, true)`, so only the current owner can start the sale offer. However the UI confirmation uses generic `dialogCallback`; `Main.cs:2686-2688` calls `acceptHouseSellToGov(player)` without a server-owned one-shot sale intent. The acceptance method does re-resolve the current owner house and rejects if the player is in a garage (`:1600-1622`); this is not a cross-player ownership bypass, but the prompt itself is not an authorization boundary.
- `acceptHouseSellToGov` schedules `house.ClearOwner()` (`:1623`), then calculates and credits the sale price through `Wallet.Change(player, price)` (`:1629-1645`). There is no transaction or durable sale receipt connecting owner clearing to payout; the wallet result is not checked.
- `House.ClearOwner` sets `Owner = String.Empty`, clears roommates and marks the house dirty (`HouseManager.cs:484-537`). `Database/Models/Houses.cs:26-72` polls dirty houses only every 30 seconds, while wallet persistence is a separate queue/worker (`MoneySystem/Wallet.cs:20-37`, `Database/Models/Money.cs:23-50`). `House.Save` resets `IsSave=false` before the DB update and only logs failures (`HouseManager.cs:425-451`).
- If payout becomes durable but the house row has not yet been saved (e.g. a crash before the next dirty-house worker pass) or its update fails, restart can load the old owner state while the player retains the proceeds, allowing another sale. The value/timing and actual repeat payout depend on house value, wallet-save behavior and failure ordering; this has not been fault-injected. Do not report a confirmed money exploit.

**Remediation (not implemented):** use an atomic sale transaction with conditional owner/version update and a unique payout receipt, or durable idempotent outbox/reconciliation. Only report success after the committed state is durable. If a confirmation prompt is intended as a workflow guard, bind it to an expiring one-shot intent, but still revalidate ownership and commit both effects atomically.

**Regression:** owner sale once; forged callback without prompt; ownership change before confirmation; garage-inside rejection; repeated/concurrent callbacks; crash after wallet persistence but before house row update; injected `House.Save` DB failure; restart/replay. Reconcile house owner/roommates, bank/garage state, player money, receipt and notifications. Requires disposable MySQL fault injection and RAGE staging.

## Boundaries

Owner ACL is rechecked at acceptance, so this is not evidence that a non-owner can sell the property. Broader property buying, transfer, tax, auction, bank and storage flows remain unreviewed; see `HOUSE_RESIDENT_REVIEW.md`.
