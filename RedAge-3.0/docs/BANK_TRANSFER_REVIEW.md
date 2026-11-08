# ATM bank-transfer confirmation — static review

Обновлено: 2026-11-07. Traced `atmVal` transfer setup → generic `dialogCallback("AcceptBankTransfer", true)` → `ATM.AcceptTransfer` → `Bank.Transfer`. Narrow personal-account transfer review; no code changes, build or RAGE/DB tests.

## MONEY-003 — accepted transfer state is reusable, so confirmation replay repeats the transfer

**Приоритет: низкий/средний; cooldown/one-shot policy bypass, static path confirmed, runtime untested.**

- `atmVal` validates a destination account, sets `sessionData.CurrentBankTransferSumAccBankInfo`, destination account and amount, opens an `AcceptBankTransfer` confirmation, and sets a 10-second `NextBankTransfer` cooldown for ordinary characters (`MoneySystem/Bank.cs:667-730`).
- `Main.RemoteEvent_DialogCallback` accepts the generic `AcceptBankTransfer` callback and calls `ATM.AcceptTransfer(player)` when `yes` is true (`Main.cs:2830-2832`).
- `AcceptTransfer` calls `Bank.Transfer` with those stored values but does not check its result, clear/consume the pending fields, or apply the cooldown at acceptance (`Bank.cs:741-751`). A repeated direct confirmation callback reuses the same stored transfer tuple; `Bank.Transfer` will debit/credit the same amount again while the source account still has funds (`:125-155`). The intended 10-second limit is only checked when preparing a new request, not on acceptance/replay.
- The source account is set server-side from the caller's own `characterData.Bank`; destination selection rejects non-personal accounts for non-admins. This slice does not show a way to debit another player's source account. The direct impact is repeated movement of the caller's own money to the already selected recipient and bypass of the per-request cooldown/one-confirmation intent, not money creation.

**Remediation (not implemented):** make each confirmation a one-shot, expiring server intent with an ID; atomically consume it before transfer, revalidate source account ownership, cooldown, amount and destination, and report success only if `Bank.Transfer` succeeds. Clear pending state on accept, cancel, timeout and account/session changes.

**Regression:** ordinary transfer once; duplicate/replayed `AcceptBankTransfer` callback; callback with no pending tuple; cancel then stale replay; insufficient funds; destination deleted/changed; cooldown boundary; ensure one confirmation moves at most the stored amount once and no callback transfers after expiry. Requires RAGE staging; policy/UX confirmation is needed.

## Boundaries

No cross-player source-account ID was found in this call path. ATM location/eligibility remains separately tracked in `ATM_REVIEW.md` (`MONEY-004`); other phone/online banking transfers are not covered.


## Дополнительный риск settlement: bool может означать отказ после изменения баланса

При повторном чтении общего wallet/bank API обнаружен важный нюанс, который усиливает MONEY-003 и должен учитываться при любом retry/compensation:

- Wallet.Change сначала меняет characterData.Money, ставит крупную сумму в Money.AddMoneyUpdate, обновляет EarnedMoney, и только затем вызывает Trigger.ClientEvent. Внешний catch возвращает false для любого исключения (MoneySystem/Wallet.cs:18-42). Следовательно, исключение при уведомлении после мутации может дать вызывающему коду false, хотя баланс уже изменён. Это не подтверждено runtime fault injection; вывод следует из порядка операций и общей границы try/catch.
- Аналогично Bank.Change меняет bank.Balance и выставляет IsSave, а затем вызывает BankNotify/Trigger.ClientEvent; внешний catch также возвращает false (MoneySystem/Bank.cs:48-91). Поэтому false не является гарантией отсутствия mutation.
- Bank.Transfer трактует false от Change(firstAccID, -amount) как отсутствие списания и немедленно возвращает. Если исключение произошло после фактического изменения firstAcc.Balance, перевод может завершиться без зачисления получателю. Кроме того, результат Change(lastAccID, amount) вообще не проверяется, после чего метод логирует перевод как успешный и возвращает true (Bank.cs:125-155).
- Значит, простой повтор debit/credit либо автоматический refund на основании false может усугубить неопределённый результат. До появления transaction ID/ledger нельзя безопасно трактовать bool как receipt.

Решение: отдельно определить API contract: либо разделить mutation/persistence result и notification, чтобы клиентские уведомления не меняли исход финансовой операции; либо возвращать типизированный результат с однозначными состояниями NotApplied, AppliedPendingPersistence, Committed, Unknown. Перевод должен быть одной DB transaction/ledger operation с idempotency key; in-memory cache и уведомления обновлять только после commit или через outbox.

Дополнительные regression/fault cases: искусственно вызвать исключение на Trigger.ClientEvent/BankNotify после mutation; проверить, что вызывающий код не делает повторный debit/refund; отказ debit до mutation; отказ credit; exception после debit до credit; partial DB persistence; повтор того же operation ID; concurrent confirmations. Эти проверки требуют тестового harness/RAGE staging и disposable DB; они не запускались.


## Дополнительный риск: ConcurrentDictionary не защищает баланс счёта от гонок

`Bank.Accounts` объявлен как ConcurrentDictionary, однако значения `Data` — изменяемые объекты с обычными полями `Balance`, `IsSave` и `IsSaveHolder`. В `Bank.Change` выполняются отдельные операции `bank.Balance + amount < 0` и `bank.Balance += amount` без per-account lock/atomic compare-and-swap. Потокобезопасность контейнера защищает операции с ключами/значениями словаря, но не делает составную проверку и изменение полей объекта атомарными.

Параллельные withdrawals/transfer confirmations для одного счёта могут одновременно прочитать один баланс, оба пройти проверку, а затем перезаписать изменения друг друга или допустить итог ниже ожидаемого ограничения. Точный исход зависит от interleaving; runtime reproduction отсутствует. Дополнительно Bank.Transfer состоит из двух независимых вызовов Change, поэтому даже сериализация каждого отдельного изменения не обеспечит атомарность пары debit/credit.

**Решение:** не ограничиваться lock вокруг одного метода без общей settlement-модели. Для runtime cache минимум единый per-account synchronization и единый lock-order для двух счетов; для корректности после restart — DB transaction с row locking/conditional debit, idempotency key и durable ledger/receipt. Cache должен обновляться из committed результата. Нужны тесты 2..100 параллельных withdrawals с балансом на границе, разнонаправленные transfers A→B/B→A, повтор confirmation, DB save concurrently with mutation и invariant: сумма денег между счетами сохраняется, баланс не уходит ниже нуля.


## 2026-11-08 implementation update — MONEY-003 (partial source patch)

The following bounded changes are now applied in `MoneySystem/Bank.cs`:

1. `Bank.Change` serializes balance check/mutation under a shared account lock, uses checked arithmetic, and isolates notification exceptions from the applied in-memory mutation result.
2. `Bank.Transfer` rejects non-positive amounts, identical/missing accounts, insufficient funds, server-stop debits and overflow. It validates both resulting balances and mutates both account caches inside one critical section rather than calling `Change` twice. Both accounts are marked dirty, including small personal-account transfers. Notifications and logging run after mutation and cannot report the completed in-memory transfer as rejected.
3. `ATM.AcceptTransfer` copies and clears the pending confirmation tuple before attempting the transfer, validates that the source account still equals the current character's bank, and reports a failed transfer rather than silently continuing. A replayed generic confirmation no longer has a reusable tuple.
4. Bank save now snapshots balance/holder/revision under the same lock, does not clear dirty flags before DB success, requeues the account after exceptions, preserves dirty state when a concurrent mutation changes the revision, and refuses a balance outside the current DB `INT` range without silently clearing the pending save.

**Important remaining limits:** this is still an in-memory settlement guarded by a process-local lock. It is not an atomic MySQL transaction and has no durable operation ID/ledger, so crash between memory mutation and DB persistence can still lose or leave one side stale. Concurrent asynchronous saves may temporarily write an older snapshot after a newer one; revision tracking keeps the account dirty for a later save, but does not provide crash-safe ordering. The generic confirmation tuple is one-shot in the session but has no explicit expiry/nonce and no durable idempotency key. Other bank mutation paths and account creation/deletion still need review.

**Validation status:** source-level assertions only. No .NET SDK/MSBuild is installed in the current execution environment; no C# build, MySQL integration/fault injection, RAGE staging, duplicate callback, or concurrency test has run. Keep MONEY-003 open.

### Regression matrix for the patch

- [ ] positive transfer A→B; exact source/destination deltas and total conservation
- [ ] reject zero/negative amount, same account, missing source/destination, insufficient source
- [ ] reject source debit during server stop; reject destination overflow and source arithmetic boundary
- [ ] 2..100 parallel withdrawals at balance boundary; no negative balance or lost update
- [ ] concurrent A→B and B→A transfers; no deadlock and conserved total
- [ ] duplicate AcceptBankTransfer callback; exactly one in-memory transfer
- [ ] callback after cancel/no pending tuple; no transfer
- [ ] source account changed between request and confirmation; reject
- [ ] notification and GameLog exceptions after mutation; transfer remains applied and never gets retried as rejected
- [ ] DB fails before/during save; dirty flag remains and retry succeeds after reconnect
- [ ] mutate account while async save is in flight; newer revision remains dirty
- [ ] balance outside DB INT range; no cast wrap/dirty-flag loss; explicit migration/reconciliation required
- [ ] restart after memory mutation before DB commit; document/recover via future durable ledger/outbox

## 2026-11-08 follow-up — bank account creation bounds and synchronized reads

A further source patch was applied in `MoneySystem/Bank.cs`:

- `GetBalance` now reads the account balance under the same `AccountSync` lock used by balance mutations, avoiding an unsynchronized read of the mutable `Data.Balance` field.
- `Create` rejects empty holders, negative balances and account types outside the current signed `TINYINT` representation before DB insertion.
- Initial balance is converted with `checked(Convert.ToInt32(balance))` before insert, and the cache is initialized from that exact validated DB value. This prevents silent truncation where MySQL stores one value but the in-memory cache holds another.
- A failed cache registration after DB insert is logged as an error rather than silently returning a successful account ID.

**Limits:** the schema remains `INT` for balance; balances above `Int32.MaxValue` require a coordinated schema migration, not a wider cache alone. The cache-registration failure path can leave a DB row requiring reconciliation; it is considered exceptional and needs explicit failure-injection coverage. The returned mutable `Data` object from `Get(int)` is still a legacy escape hatch and needs a broader caller audit before changing its contract.

**Validation:** source patch only. No .NET build, MySQL integration test, concurrent read/write test, or RAGE staging run has been performed.


## 2026-11-08 follow-up — account lifecycle synchronization

The shared account lock is now also used for `GetBalance`, holder lookup by name, cache insertion after `Create`, removal from the account dictionary, and holder mutation. This prevents these dictionary lifecycle operations from interleaving with the locked transfer/change critical sections. `Create` validation and checked INT conversion, plus synchronized `GetBalance`, were already present in the current source and are retained.

**Remaining escape hatch:** `Bank.Get(int)` and `Bank.Get(string)` now return snapshots copied under `AccountSync`, so callers cannot mutate the live `Data` through these lookup methods. The public `Bank.Accounts` dictionary still exposes mutable `Data` values; all direct external reads/writes to its properties require caller audit. Account initialization is expected during startup; runtime reload semantics are not established.

Additional tests: [ ] concurrent transfer vs account removal; [ ] transfer vs holder rename; [ ] Create with negative/overflow balance and invalid type/empty holder; [ ] concurrent GetBalance during transfer; [ ] audit every `Bank.Get(int)` caller for direct mutable property writes.


## 2026-11-08 follow-up — bank save worker and small balance changes

A further persistence gap was fixed in source:

- `Bank.Change` now marks every successful balance mutation dirty, including small personal-account changes. Previously a personal-account mutation below the 10,000 threshold could remain outside the save worker until another qualifying change.
- `Bank.GetDirtyAccountIds()` snapshots dirty account IDs under `AccountSync`; the background worker no longer enumerates mutable `Data.IsSave` fields without the lock.
- The account deletion queue is now a `ConcurrentQueue<int>`. The worker drains a batch and requeues failed deletes; if DB setup/batch processing fails, pending IDs are requeued. Repeating a DELETE for an already-deleted row is safe.

**Remaining:** the worker still has a fixed 30-second polling interval; this is not a durable delete outbox, so queued deletes can still be lost on process crash. Account balance saves are still separate UPDATEs, not one transaction for both transfer legs. The mutable `Bank.Get(int)` data escape remains open. Validate DB reconnect, partial delete batch, crash/restart and write-volume/performance before closure.


### Snapshot API regression

- [ ] `Bank.Get(int)` and `Bank.Get(string)` return consistent snapshots while concurrent transfer/holder mutation occurs.
- [ ] Mutating a returned snapshot does not mutate the live account or bypass dirty/revision tracking.
- [ ] Audit direct `Bank.Accounts[id]` consumers for writes to Balance/Holder/IsSave/Revision outside AccountSync.


## 2026-11-08 follow-up — direct bank balance writes routed through synchronized API

A source audit found legacy code bypassing `AccountSync` and dirty revision tracking by mutating `Bank.Data.Balance` directly. Added `Bank.SetBalance` for bounded non-negative absolute balance replacement and `Bank.ApplyBalanceAdjustment` for checked adjustments that preserve the existing temporary-negative-balance property-tax/repossess flow.

Updated call sites: business purchase initial balance (`Core/Businesses.cs`); house purchase initial balance (`Houses/HouseManager.cs`); auction house/business ownership balance initialization; hourly business and house tax deductions and zeroing after repossession (`Main.cs`). Each successful operation now changes balance under `AccountSync`, increments `Revision`, and sets `IsSave`. Tax adjustments preserve the legacy negative-balance check; they are not silently converted to normal `Bank.Change` semantics, which reject overdrafts.

**Limits:** these remain cache mutations with asynchronous DB persistence, not a durable transaction joining property ownership, tax/faction credit, owner refund and bank balance. Property acquisition ordering between buyer debit, owner assignment and bank initialization remains open. The mutable `Bank.Data` escape and any remaining direct writes stay open until all callers are audited.

**Validation:** source-level patch only. No build, MySQL failure injection, concurrent tax/transfer test, auction staging or property purchase staging has run.

### Regression cases
- [ ] business/house purchase initializes and persists the expected bank balance;
- [ ] auction house/business award initializes the expected balance;
- [ ] hourly business/house tax reduces balance once and credits city tax once;
- [ ] negative post-tax balance follows repossession, then resets bank balance to zero;
- [ ] concurrent transfer/withdrawal during tax does not lose either mutation;
- [ ] invalid/missing bank ID leaves related side effects unapplied or reconciled;
- [ ] DB failure during save retains dirty state and eventually persists latest revision;
- [ ] search all call sites for direct writes to bank Balance, IsSave and Revision.


## Property purchase ordering follow-up — business and house

The property acquisition call sites were checked after routing bank balance writes through the shared API. Both `HouseManager` and `Core/Businesses` previously continued ownership and success side effects without checking `Wallet.Change`. The paths now initialize the property bank balance first, require `Wallet.Change` to succeed, and only then assign ownership / emit purchase success side effects. If the debit is rejected, they attempt to restore the previous property-account balance and log if that compensation fails.

**Limits:** the bank-balance initialization and player debit are still separate in-memory operations, not one DB transaction. If compensation itself fails, manual reconciliation is required. Auction award paths still need the same ordering review. These changes have not been build/runtime tested.


## 2026-11-08 follow-up — synchronized bank API adoption

The audit found several callers directly mutating `Bank.Data.Balance` or `IsSave`, bypassing the new lock/revision contract. Current branch changes route hourly house/business tax through `ApplyBalanceAdjustment`; admin bank grants now use a snapshot lookup and require `Bank.Change` success; house/business auction awards initialize account balances through `Bank.SetBalance` before ownership/auction-state commit; house purchase checks the buyer debit before ownership effects and rolls back the preinitialized bank balance on debit rejection. `Core/Businesses.buyBusinessCommand` already uses `Bank.SetBalance` for business-account initialization.

`Bank.Get(int)`/`Get(string)` return snapshots, not live objects. `Bank.Accounts` remains a public mutable dictionary, so direct external property mutation is still possible and needs a complete call-site audit. The reviewed `Main.cs` tax path no longer writes Balance directly. Cross-ledger settlement (bank + wallet + ownership + faction credits) remains non-atomic.
