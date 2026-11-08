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


## MONEY-052 — finish remote accepted before race start / away from finish

### Source path and evidence
- `Events/StreetRace.cs`: `StreetRaceFinished(ExtPlayer player)`.
- The remote event `server.streetrace.finished` is called by the client when it enters its local finish colshape (`src_client/vehicle/race_system.js`). Client-side colshape state is not an authorization boundary.
- Before this patch, the server handler checked only that the caller had a character, a `PlayerToStreetRaceId` entry and a race dictionary entry. It did not require `StreetRaceData.Status == true`, nor did it check the caller's server-side position against `StreetRaceData.Position`.
- Therefore, a participant in a pending offer could directly call the remote before the opponent accepted and receive the calculated 90% pot payout although neither stake had been debited. An active participant could also invoke the finish remote while away from the finish position. The rate is capped at 100,000 by the normal `Main.inputCallback` path; the exact exploit was not executed on a live server.

### Patch applied
- Reject finish callbacks unless the race is active (`Status == true`).
- Require the caller's server-side position to be within 10 metres of the stored finish point.
- This is a minimal authorization hardening patch. It does not prove a race was driven legitimately, and it does not make payout durable/idempotent.

### Residual risks
- `StreetRacePosition` still receives client-supplied waypoint coordinates. Validate finite/plausible coordinates and minimum distance server-side; client-side waypoint checks are not sufficient.
- Winner `Wallet.Change` result remains unchecked. Wallet's bool contract is not a durable settlement receipt; do not add naive retries without resolving possible mutation-before-false behavior.
- `ClearData` also pays the winner on death/vehicle-exit/abort paths and ignores the wallet result.
- No per-race durable settlement record, crash recovery, or exactly-once payout exists.
- No build, RAGE runtime, concurrency, exploit reproduction or DB fault-injection test has been run.

### Regression matrix
1. Invoke finish remote while offer is pending: no credit, no status mutation, no BattlePass progress.
2. Invoke after acceptance but from outside 10 metres: no credit and race remains active.
3. Enter server-side finish radius while active: normal finish path remains available.
4. Invoke finish from the non-winning participant at finish: confirm gameplay policy; if either participant can claim, race design needs authoritative winner validation.
5. Replay and concurrent finish callbacks: no duplicate payout or duplicate progression.
6. Send NaN/Infinity/implausible waypoint coordinates to `server.streetrace.position`; server must reject.
7. Inject Wallet false/exception, disconnect, shutdown and restart around winner payout and `ClearData`; verify exact balances and recoverability.
