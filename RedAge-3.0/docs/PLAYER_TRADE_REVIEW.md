# Player cash trade and tent-market settlement review

Обновлено: 2026-11-08. Статический анализ ветки `redage/audit-continuation`; RAGE:MP, MySQL fault-injection и concurrent runtime tests не выполнялись.

## MONEY-048 — cash/item settlements ignore wallet results

**Приоритет: средний; source-level ordering/result handling confirmed; failure-window runtime reproduction pending.**

### Player-to-player inventory trade

`Chars/Repository.cs`, `ConfirmTrade(ExtPlayer player)` (around lines 7680–7900 in this snapshot):

- The method performs preflight `CanIChange` checks for both players, but these checks are separate from the later wallet mutations.
- It then iterates the first player's trade container and calls `AddItem` for the counterparty before the money leg.
- For positive `TradeData.Money`, it calls `Wallet.Change(player, -TradeData.Money)` and then `Wallet.Change(target, TradeData.Money)`; both bool results are ignored. It logs and announces the transfer regardless.
- The reverse direction follows the same pattern for the other player's offer.
- `Wallet.Change` explicitly returns false when the resulting balance is negative and when a negative change is attempted while `Admin.IsServerStoping`. It also catches exceptions and returns false. Therefore the earlier preflight is not a settlement guarantee: a state change/failure between preflight and commit can leave the item leg or recipient credit committed without a confirmed sender debit.

### Tent marketplace purchase

`Chars/Repository.cs`, `ItemBuy(ExtPlayer player, string ArrayName, int Index, int Value)` (around lines 8180–8260):

- The path calculates `int price = Item.Price * Value` without checked/long arithmetic.
- It calls `CanIChange`, then ignores both `Wallet.Change(player, -price)` and `Wallet.Change(target, +price)` results.
- It proceeds to BattlePass progress and `ItemStack(..., isBuy: true)` regardless of either wallet result.
- The item count/price calculation and inventory transfer are not tied to a durable one-shot purchase receipt. Overflow, a wallet rejection, a disconnect, or a partial item-stack mutation can therefore desynchronize funds, seller proceeds and item ownership.

### Scope and confidence

The unchecked call order and missing result handling are confirmed in source. The concrete failure modes are conditional on a wallet rejection/exception, state race, overflow or partial item operation. This review does **not** claim that a live player-to-player exploit has been reproduced.

### Remediation

1. Introduce one server-side settlement service for each trade/purchase; validate both participants, current offer, exact item IDs/counts, price and session/ownership immediately before commit.
2. Use checked `long` multiplication and enforce a documented maximum price/count before any mutation.
3. Make debit success a hard prerequisite for item movement and seller credit; check recipient credit too. Do not emit success logs, BattlePass progress or notifications before the durable settlement result.
4. Use an idempotent transaction/receipt or a durable pending-settlement + compensation/reconciliation design. Do not attempt to solve this by merely reordering two independent `Wallet.Change` calls.
5. Revoke pending offers on disconnect, context change and timeout; reject duplicate/concurrent confirmations.

### Regression matrix

- Both players offer money/items; only one side offers; zero-money item swap.
- Wallet debit returns false after preflight; recipient credit returns false; exception on either leg.
- Server-stop transition between preflight and settlement.
- Price/count at 0, 1, max allowed, `int.MaxValue`, multiplication overflow and insufficient balance.
- Full inventory, partial stack transfer, missing/deleted item, item DB insert failure.
- Duplicate/replayed and simultaneous confirmations from both sides.
- Disconnect/reconnect and process restart at every settlement boundary.
- Assert exact item counts/SQL IDs, both balances, logs, notifications and BattlePass progress; no free item, free money, double debit or lost payment.

## Related boundaries

- `Wallet.Change` uses an `int` intermediate and persists large changes through the existing int-based character-money contract; MONEY-036 remains a separate low/latent type-contract issue.
- Other unchecked wallet settlements already tracked include MONEY-035, MONEY-037, MONEY-039..044, MONEY-047, STOCK-001/002 and JOB-005. Do not duplicate those findings.
- No gameplay source patch is included in this documentation commit. C# build and runtime tests remain pending.
