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
