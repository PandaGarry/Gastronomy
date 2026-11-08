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
