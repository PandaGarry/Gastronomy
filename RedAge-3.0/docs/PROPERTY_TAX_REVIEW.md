# House property-tax and repossession — static review

Обновлено: 2026-11-07. Traced the hourly payday house-tax loop (`Main.cs:4716-4801`), house-account dirty persistence and repossession owner clearing. Narrow tax/persistence slice; no build, DB restart or runtime tests.

## MONEY-019 — hourly house-tax debits do not mark the bank account dirty

**Приоритет: средний; conditional crash/restart tax rollback, not reproduced.**

- When house tax is enabled, payday subtracts `tax` directly from each owned house account (`Main.cs:4721-4727`). The positive-balance branch continues without setting `houseBalance.IsSave` (`:4737`).
- The bank persistence worker selects only accounts with `IsSave` (`Database/Models/Bank.cs:22-41`); `Bank.Save` clears the flag before the DB update (`MoneySystem/Bank.cs:170-193`). The normal ATM house deposit does call `Bank.Change`, which marks that account dirty (`Bank.cs:563-569`, `MoneySystem/Bank.cs:79-99`), but the subsequent hourly tax subtraction does not.
- If an account has been saved after a deposit and then one or more hourly tax deductions occur without another operation marking it dirty, a process crash/restart can reload a stale, higher house balance and effectively roll back those deductions. The exact amount depends on worker timing and intervening account changes; this has not been tested against MySQL.

**Remediation (not implemented):** route tax collection through a persistence-aware bank operation or mark the account dirty after every debit; use a durable/idempotent tax ledger so restart cannot replay/refund an hour.

**Regression:** deposit house tax, wait for a successful bank save, run one/multiple hourly tax deductions without further account activity, restart and compare memory/DB/balance and city tax ledger; inject bank-save failure and concurrent deposit/tick ordering.

## PROP-003 — tax repossession clears house ownership without dirtying the house row

**Приоритет: средний; conditional restart resurrection, not reproduced.**

- When the account becomes negative, payday zeroes and marks the bank account dirty, then calls `house.ClearOwner(isSave: false)` (`Main.cs:4737-4787`).
- `ClearOwner` clears owner/roommates, but only marks `House.IsSave=true` when its `isSave` argument is true (`HouseManager.cs:513-537`). It does mark the associated garage dirty; that garage save does not persist the separate house owner column.
- `Database/Models/Houses.Worker` saves only houses where `IsSave` is true (`Database/Models/Houses.cs:26-50`). There is no later direct owner-column update in this tax branch. Unless some unrelated mutation marks the house dirty before a save, the DB house row may retain the forfeited owner's name; a restart can reload the confiscated property as owned while the bank account is zero. This is a static conditional path, not a reproduced restart result.

**Remediation (not implemented):** mark the house dirty (or persist the owner and account reset in one transaction) when confiscating; verify the house row update commits before reporting repossession. Add idempotent reconciliation for interrupted tax/forfeiture.

**Regression:** force a house account below zero for an online owner, verify in-memory owner/roommates/garage and DB row, restart before any unrelated dirty-house mutation, and ensure the property stays unowned with zero account balance. Also test offline owners (the code dereferences the absent player in the negative-balance path; the per-house catch currently logs and skips the rest of repossession) and DB failure.

## Boundaries

This is not a full bank/ATM or business-tax review. Owner-only ATM access and the house transfer/sale/purchase paths are documented separately in `PROPERTY_PURCHASE_REVIEW.md`, `PROPERTY_SALE_REVIEW.md`, and `PROPERTY_TRANSFER_REVIEW.md`. Neither tax finding was runtime-confirmed.


## 2026-11-08 source remediation update — MONEY-019 (partial)

The hourly house and business tax paths in `Main.cs` now call `Bank.ApplyBalanceAdjustment` rather than mutating `Bank.Accounts[id].Balance` directly. The helper serializes the arithmetic under `AccountSync`, checks overflow/current DB INT range, allows the legacy temporary-negative balance policy for tax/repossession, increments revision and marks the account dirty. Tax/faction/city-hall side effects occur only after the bank adjustment succeeds. This addresses the lost-dirty-flag bank-balance portion of MONEY-019.

**Still open:** bank and faction/city-hall credits are not a single DB transaction/ledger; house repossession owner persistence remains separately tracked as PROP-003; DB failure/restart behavior is not tested. Static patch only.

- Business tax follow-up: the Mafia faction credit is now applied only after `ApplyBalanceAdjustment` successfully debits the business bank. This prevents a failed bank debit from granting the associated Mafia tax share. City-hall/faction credits and bank debit still lack one durable cross-ledger transaction.
