# Street race stake settlement review

Date: 2026-11-08
Status: source patch applied; C# build and RAGE:MP concurrency/failure tests pending.

## MONEY-051 — race started without confirmed two-sided stake debits

### Source path
- `Events/StreetRace.cs`
- `StreetRace.Accept(ExtPlayer player)`
- `StreetRace.ClearData` and `StreetRaceFinished` are downstream settlement paths.

### Evidence
Before the patch, `Accept` checked both balances with `UpdateData.CanIChange`, then set `StreetRaceData.Status = true`, called both `Wallet.Change(..., -rate)` operations without checking their bool results, and started the race.

`Wallet.Change` can return false, including on server shutdown, missing character data or caught exceptions. The race could therefore start even if one stake debit was rejected. Later finish/abort logic treats `Status=true` as a funded race and may credit the winner with the calculated pot payout.

This is a source-level ordering defect; no live money exploit or failure injection is claimed.

### Patch applied
- The first player's stake must debit successfully or the offer is cancelled.
- The second player's stake must also debit successfully.
- If the second debit fails, the first debit is compensated with a wallet credit; the offer is cancelled and the race does not start.
- If compensation itself fails, a detailed error is logged for manual reconciliation.
- `Status=true`, timers and client race-start events now occur only after both debits succeed.

### Residual risks
- The compensating refund is not a durable receipt/outbox and can itself fail; manual reconciliation is currently only logged.
- This patch does not add a per-race lock/round nonce. Concurrent duplicate accept/finish callbacks and exactly-once winner payout still need separate review/staging.
- `StreetRaceFinished` winner credit result is still unchecked; this remains a separate settlement gap and should be handled with a durable payout receipt/retry design, not by assuming a successful stake debit guarantees payout.
- Zero-stake race policy remains unchanged; confirm whether zero should be allowed or require a positive minimum.

### Regression matrix
1. Both stake debits succeed: race starts once and both balances decrease by the agreed stake.
2. First debit returns false/throws: race is cancelled; no second debit, timers or start event.
3. Second debit returns false/throws: first stake is refunded, race is cancelled, no timers/start event/payout.
4. Force first-stake compensation to fail: error is logged with race/player/stake context; ensure no race starts and reconcile balance manually.
5. Trigger server shutdown between preflight and either debit.
6. Duplicate/concurrent accept and finish callbacks; verify one debit per participant and no duplicate winner payout.
7. Disconnect/reconnect/restart around both debit and refund boundaries.

No C# build, RAGE runtime, MySQL fault injection or live exploit test has been run.
