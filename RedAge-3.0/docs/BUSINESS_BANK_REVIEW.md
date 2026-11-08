# Business bank account operations — static review

Обновлено: 2026-11-08. Narrow trace of ATM business-account deposit selection and settlement. Static-only; no RAGE/DB failure injection. An interim check-and-compensate source patch is now present; durable settlement remains unresolved.

## MONEY-039 — ATM business deposit debits the player before checking the business-bank credit

**Приоритет: средний; unchecked settlement result statically confirmed, runtime failure not reproduced.**

- ATM business-account selection is handled by atmCB case 3. It resolves the selected business through characterData.BizIDs[index] and stores the index in sessionData.ATMData.BizID (MoneySystem/Bank.cs:878-917).
- Original finding: atmVal case 3 debited the player's wallet and ignored the business-bank credit result. The current branch now checks `Bank.Change(biz.BankID, +myamount)`; if it rejects, it attempts `Wallet.Change(player, +myamount)`, logs a critical error if compensation fails, notifies failure and returns before success log/message/UI refresh.
- The check/refund narrows the ordinary in-process failure path, but does not provide durable cross-ledger atomicity. A process crash after wallet debit or failed compensation can still leave a partial settlement; no idempotency receipt or restart reconciliation exists.
- The selection path also trusts the index into BizIDs and relies on the stored session type; bounds and owner reconciliation are not repeated at atmVal. This is an adjacent robustness/authorization boundary; the direct demonstrated integrity issue is the unchecked second leg of the deposit.
- The general ATM remote also lacks a server-side active-location/eligibility intent (`MONEY-004`, `ATM_REVIEW.md`); this review does not duplicate that finding.

**Interim patch present; final remediation not implemented:** require Bank.Change success before logging/reporting success and attempt wallet refund on rejection. Replace this with atomic DB-backed/idempotent settlement and durable receipt. Revalidate the selected BizID against authoritative current ownership and validate the index/type at the final event.

**Regression:** inject missing business account, Bank.Change false/exception and balance-boundary failure after successful Wallet.Change; assert player balance is restored or pending receipt is durable, business balance and log agree, and duplicate atmVal cannot repeat. Test stale BizIDs, negative/zero/int boundary amounts, invalid index, replay and far-from-ATM direct remotes on disposable RAGE/MySQL staging.

## Scope and confidence

Static source ordering and return contract confirmed. No live exploit, DB failure or runtime reproduction claimed.\n\n## 2026-11-08 — interim source patch\n\n`MoneySystem/Bank.cs` now checks the business-bank credit after the wallet debit. On credit rejection it attempts to refund the wallet, logs a critical error if that refund fails, notifies the player and returns before success effects. Static assertions passed for the guard, compensation call and log ordering. No C# build, RAGE runtime, MySQL fault injection, crash/restart or concurrency test was run. Keep MONEY-039 open.