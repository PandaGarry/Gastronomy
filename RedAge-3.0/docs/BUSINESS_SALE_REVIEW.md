# Phone business government sale — static review

Обновлено: 2026-11-07. Traced `server.phone.business.sell` → generic `dialogCallback` confirmation → payout, BizIDs mutation and business save worker. Static-only; no build, hard-crash replay or DB/RAGE staging.

## MONEY-026 — stale BizIDs can replay business sale payout after a partial-save restart

**Приоритет: средний; conditional crash/restart sequence confirmed in source, not reproduced.**

- `server.phone.business.sell` only opens a generic dialog (`Players/Phone/Property/Businesses/Events.cs:23-24`; repository `:480-503`). The generic `dialogCallback("BIZ_SELL_TOGOV", true)` dispatches directly to `OnSellConfirm` (`Main.cs:2372-2384, 2689-2691`); there is no server-owned one-shot sale intent.
- `OnSellConfirm` checks that the selected ID occurs in `characterData.BizIDs`, but does **not** verify `biz.Owner == player.Name` or that the business is still privately owned (`Repository.cs:505-533`). It credits `Wallet.Change(player, price)` without checking the result, removes the ID only in memory, then calls `biz.ClearOwner()`.
- `biz.ClearOwner()` marks the business dirty. The business worker polls dirty rows every 30 seconds; `Business.Save` clears `IsSave` before its asynchronous DB update (`Database/Models/Business.cs:20-46`, `Core/Businesses.cs:4132-4154`). For a normal business sale the VIP-adjusted payout is at least $10,000 in the bundled seed examples, so `Wallet.Change` separately queues the character balance through the one-second money worker (`MoneySystem/Wallet.cs:20-38`, `Database/Models/Money.cs:23-49, 91-118`). `BizIDs` is not written in this phone sale method; it is serialized by the character save on disconnect/restart, not by the business worker (`Character/Save/Repository.cs:48-65, 111-132`).
- A hard crash after the business owner and wallet writes reach DB but before the character `Biz` list is saved can therefore leave `Owner="Государство"` while the former owner's persisted `BizIDs` still contains that business. Character load deserializes that list without checking it against `Business.Owner` (`Character/Load/Repository.cs:151-158`). After reconnect, the stale ID passes `GetData`'s membership check and sets `SelectedBiz` (`Players/Phone/Property/Businesses/Repository.cs:18-36`); a direct positive generic callback then passes `OnSellConfirm`'s same stale-ID check and credits the sale price again despite the business already being government-owned. No exact crash point or repeat payout was runtime-reproduced.
- This is conditional on a hard-crash/partial-save window. The code does not establish that a normal graceful restart leaves stale IDs; the shutdown path attempts character saves.

**Remediation (not implemented):** require current `biz.Owner == player.Name` at every business-owner endpoint, consume a server-issued one-shot sale intent, and persist sale receipt, owner change and seller `BizIDs` removal atomically/idempotently. Reconcile BizIDs against authoritative owners at login.

**Regression:** sell a business normally and replay the dialog callback; then fault-inject/crash after wallet+business writes but before character `Biz` save. Reconnect with a stale BizID, load the business, and try direct callback. Assert no second payout or management access; reconcile `Owner`, `BizIDs`, wallet and sale receipt across restart. Also inject failed wallet/business/character writes.

## Scope boundary

This review covers phone government sale only. Player-to-player business transfer, auction award and order delivery have separate review notes; no full phone/business remote coverage is claimed.
