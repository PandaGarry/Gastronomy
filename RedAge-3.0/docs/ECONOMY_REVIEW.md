# Предварительный аудит экономики и транзакций

Статический review без запуска сервера или БД. Секретные строки/значения не включались в отчёт. До отдельного тестирования функциональность не менялась. Внешний payment-receipt lifecycle и DonatePack отдельно разобраны в `PAYMENTS_REVIEW.md`.

## MONEY-001 — перевод RedBucks игроку может списать средства без зачисления

**Уверенность: высокая; приоритет: критичный для донатной валюты.**

Файлы: `MoneySystem/Donations.cs:252-324`, `Chars/UpdateData.cs:25-43`, `Accounts/Repository.cs:55-69`.

Путь `GiftDonate`:

1. Находит целевой аккаунт в БД и читает его текущий баланс.
2. Сразу списывает сумму у отправителя через `UpdateData.RedBucks`.
3. Затем ищет получателя через `GetPlayerToLogin`, который ищет только среди online players и возвращает `null`, если игрок offline.
4. Следом без null-check вызывает `target.GetAccountData()`. Для offline target возникает исключение уже после списания; outer catch только логирует и не делает refund/rollback.
5. Даже в ветке `targetAccountData == null` код пытается зачислить на target и затем читает `targetAccountData.RedBucks/ Login`; ветка с непустым `targetAccountData` изменяет БД, но не обновляет кэш объекта игрока.
6. DB writes раздельные: атомарной транзакции sender debit + recipient credit нет. `MySQL.Query` скрывает ошибки внутри себя и не возвращает успешность операции; вызывающий код после этого отправляет уведомление об успехе.

**Риск:** offline transfers likely fail after debit; онлайн-баланс может расходиться между памятью и БД; DB/connection errors или concurrent transfers могут привести к потере или несогласованности средств.

**Исправление (не внедрено):** единая сервисная операция с DB transaction; проверка получателя и валидности до списания; атомарные conditional updates (`sender balance >= amount`, recipient increment); проверка affected rows; commit только если обе стороны успешны; затем синхронизировать кэши/уведомления. Идемпотентный transaction ID + аудит ledger. Нужны tests на offline receiver, insufficient funds, DB failure, concurrent duplicate request, rollback.

## MONEY-002 — гонки и потеря отложенных денежных записей

**Уверенность: высокая; приоритет: высокий.** Файл `Database/Models/Money.cs`.

Исходный дефект:
- `DonateUpdateList` и `MoneyUpdateList` были обычными `Dictionary`; игровые producers и отдельный worker обращались к ним без общей синхронизации.
- Worker делал snapshot и `Clear()` до завершения DB write. Исключения внутри `DonateUpdate`/`MoneyUpdate` только логировались; batch не возвращался на retry.
- `Wallet.Change` меняет `CharacterData.Money` в памяти, а при изменении не менее 10 000 вызывает `AddMoneyUpdate`. Поэтому `Wallet.Change(true)` не означает DB commit.

**Внесённый source patch (ещё не runtime-validated):**
- Добавлен общий `QueueLock`; producers записывают последние абсолютные значения через indexer под lock.
- Worker атомарно копирует и очищает обе очереди под тем же lock.
- DB flush возвращает bool; при исключении worker возвращает неуспешный batch в очередь.
- Requeue не перезаписывает более новое значение, добавленное producer во время DB flush.
- Повторный flush использует абсолютный `SET balance = value`, поэтому повтор успешных строк из частично упавшего batch не повторяет денежное начисление/списание как delta.

**Ограничения и остаточные риски:**
- Очередь остаётся только в памяти: аварийный процессный crash до flush по-прежнему теряет pending update.
- Нет durable outbox/ledger, DB transaction для batch, bounded retry/backoff или dead-letter/alert policy.
- Ошибка на одной строке прерывает соответствующий batch; batch будет повторён целиком. Это безопасно только пока операция остаётся абсолютной записью баланса.
- Не проверяется отсутствие строки по UUID/login; affected-row count намеренно не используется, поскольку unchanged absolute value может сообщать 0 changed rows в зависимости от MySQL режима.
- `Wallet.Change` остаётся in-memory-first и его bool не подтверждает долговременную запись.

**Обязательные проверки:** параллельные producers и snapshot/clear; добавление нового значения во время flush; failure первой/средней/последней строки; DB disconnect/reconnect; успешная часть batch + retry; process kill/restart до flush; длительный DB outage и очередь retry. C# build и MySQL fault injection не выполнялись.

### MONEY-002 follow-up — worker lifecycle and invalid snapshots (2026-11-08)

- `Money.Start()` is now idempotent per process via `Interlocked` guard; duplicate lifecycle calls cannot create multiple polling workers.
- Worker is now `Task`-based and uses `await Task.Delay(1000)` instead of blocking a thread-pool thread with `Thread.Sleep`.
- `AddMoneyUpdate` rejects nonpositive UUIDs, negative balances and values above `Int32.MaxValue` before enqueue. This prevents an out-of-range `long` snapshot from repeatedly failing `Convert.ToInt32` and poisoning every retry batch.
- The existing queue lock, snapshot/clear, failed-batch retry and newer-value-wins behavior are retained.

**Still open:** queue is process-memory only; no durable outbox, bounded retry/backoff/dead-letter or DB transaction. A process crash can still lose pending snapshots. No C# build, concurrency execution or MySQL fault injection has been run.

**Additional tests:** call `Start()` repeatedly/concurrently and assert one worker; enqueue `0`, negative, `Int32.MaxValue`, `Int32.MaxValue + 1` and long extremes; verify invalid values do not enter retry loop; confirm valid snapshot still retries after DB outage and newer producer value wins.

## MONEY-003 — банковский transfer callback повторно применим к сохранённому session state

**Уверенность: высокая по статическому потоку; эксплуатацию нужно подтвердить на staging.**

Файлы: `MoneySystem/Bank.cs:125-160, 741-751`, `Main.cs:2373-3084`, `Players/Models/SessionData.cs:118-120`.

- `Main.RemoteEvent_DialogCallback` принимает от клиента callback string + `yes` и dispatch-ит действия. Один из callback paths вызывает `ATM.AcceptTransfer`.
- Банк хранит source account, target account и сумму в `SessionData`; значения записываются при подготовке перевода.
- `AcceptTransfer` проверяет только session и ненулевые/положительные поля, затем вызывает `Bank.Transfer`. Найденных сбросов этих полей после завершения/отмены нет.
- Клиент может повторно вызвать remote callback. Пока на source account достаточно средств, повторный вызов может повторять один и тот же transfer; `NextBankTransfer` проверяется при создании запроса, но не при acceptance.
- Source ID задаётся сервером из `characterData.Bank`, не берётся из клиента на confirm. В просмотренном call path это собственный счёт вызывающего; cross-player source debit не найден. Основное подтверждённое последствие повторного callback — повторное перемещение собственных средств к уже выбранному получателю и обход cooldown, а не создание денег.
- `Bank.Transfer` списывает source balance и затем вызывает `Change` для target, но не проверяет результат target credit; `AcceptTransfer` также игнорирует bool result. Целевая запись и списание не объединены DB transaction.
- В `AcceptTransfer` объект target account индексируется до проверки `ContainsKey`, поэтому исчезнувший/невалидный target приводит к исключению.

**Исправление (не внедрено):** одноразовый server-side transfer intent/nonce с коротким expiry; consume/clear до выполнения; проверки принадлежности source счёта, target type/permissions, cooldown и подтверждённой суммы; транзакционный атомарный перевод с row locks/conditional update; уведомлять только после commit; replay/concurrency tests. Более подробная трассировка ATM transfer confirmation и regression cases: `BANK_TRANSFER_REVIEW.md`. Уровень риска/политика требуют staging и владельческого подтверждения.


## MONEY-004 — ATM remote events не проверяют server-side proximity/активность ATM

**Уверенность: высокая в отсутствии проверки в этих handlers; приоритет: средний (обход игрового ограничения, если услуги должны быть доступны только у ATM).**

Файл: `MoneySystem/Bank.cs:470-740, 794-919`.

- `ClientEvent_ATMCB` принимает тип/индекс от клиента и для menu type 1 выставляет `sessionData.ATMData.Type` (в т.ч. deposit/withdraw); в handler нет проверки позиции игрока/активного ATM.
- `ClientEvent_ATMVAL` доверяет этому session type и выполняет операции по кошельку/счёту; также нет проверки положения игрока около ATM. Поэтому forged remote calls могут открыть ATM-путь вне физического ATM, если это ограничение задумано дизайном.
- Оба handler-а используют `params object[]` и читают `args[0]`/`args[1]` до проверки количества/типа; exception ловится и логируется.
- Сумма проходит через `Math.Abs`; `int.MinValue` способен вызвать overflow exception. Проверка rate limit/частоты не установлена в этих методах.

**Исправление (не внедрено):** сверить с intended gameplay; если нужен физический ATM — серверный interaction token/короткий session state с entity/position/dimension и повторной proximity-проверкой при каждой операции. Добавить строгую проверку args, диапазонов и rate limit. Тестировать spoofed calls вне ATM, пустые/неверные args, overflow boundary и повторные операции на staging.

## Тесты перед исправлениями

- offline/online receiver transfer; target not found; sender balance exactly/less than amount;
- injected DB failure between debit and credit; assert full rollback and no success notification;
- 2–100 concurrent identical transfers; assert one debit/one credit per unique operation ID;
- replay transfer confirmation callback; assert second application rejected;
- background money batch with concurrent producers and DB failure; assert no lost updates and recovery after restart;
- malformed ATM payloads and out-of-range amount; assert no state change and bounded logs.

## MONEY-005 — покупка DonatePack может частично выдать набор бесплатно или списать деньги без полной выдачи

**Уверенность: высокая; приоритет: высокий.** Файл `Chars/Donate.cs:418-1207`, `UpdatePrice` (`:75-100`).

`BuySet` поэлементно вызывает `AddNewItem`, а списание через `UpdatePrice` расположено в разном порядке в разных пакетах:

- В нескольких пакетах товары добавляются до списания. Если ранний `AddNewItem` прошёл, а следующий возвращает `-1` из-за заполненного инвентаря, handler выходит до `UpdatePrice`; ранее добавленный товар остаётся у игрока бесплатно.
- В поздних стадиях одного набора (например, case 10) стоимость уже списана и часть наград уже выдана, а последующие `AddNewItem` всё ещё могут вернуть `-1`; handler выходит без возврата валюты/повторной доставки оставшихся товаров.
- Несколько добавлений `SimCard` не проверяют возвращаемый ID, поэтому пакет может считаться успешным даже если предмет не выдан.
- `UpdatePrice` ловит исключение и не сообщает вызывающему коду об отказе. `BuySet` после вызова продолжает выдачу VIP/денег/опыта/лицензий и success notification, даже если списание не прошло.
- Результат `Wallet.Change` также не проверяется. Текущая покупка — несколько независимых side effects без общей транзакции/receipt.

**Исправление (не внедрено):** формировать immutable reward plan; сначала проверить валидность/цену/все capacity limits, затем атомарно списать валюту и создать durable purchase receipt/выдачу; при невозможности атомарной DB/game-state операции — compensation/retry по idempotent receipt, не `return` после частичной выдачи. Сделать `UpdatePrice` возвращающим проверяемый результат или использовать transaction service; проверять каждый grant result. Тесты: заполнение инвентаря на каждом шаге каждого набора, exception в debit/grant, duplicate remote call, reconnect/restart и проверка полного баланса/наград.

## MONEY-006 — отрицательный/overflow count в покупке roulette-кейсов начислял RedBucks

В `RouletteBuyCase` отрицательный remote count превращался в положительную сумму для `Donate.UpdatePrice`/`UpdateData.RedBucks`; unchecked multiplication также допускала отрицательный результат при переполнении. Внесены локальные guards для диапазона count, positive case price, checked total и negative wallet amount. Точная трассировка, ограничения и regression matrix: [ROULETTE_REVIEW.md](ROULETTE_REVIEW.md). До C# build и test-account staging данный патч не закрыт.


## MONEY-007 — NewCasino Roulette outcome-dependent disconnect refund

`ContinueGame` sends the winning number in the `START_GAME` client payload and sets a five-second `rData.Time` window; `Roullete.Disconnect` returns the player’s stake while that window remains active, irrespective of disconnect type. A modified client can inspect the delivered result and disconnect on a losing outcome. The related `DESTROY_LAST_BET` active-phase bypass received a narrow server-side phase guard (`CAS-001`), but the disconnect settlement policy remains open pending owner decision and durable exactly-once test design. Evidence and staging matrix: [CASINO_REVIEW.md](CASINO_REVIEW.md). Do not change the refund policy or gameplay balance before staging and approval.


## MONEY-008 — Sapper negative stake credits RedBucks

`server.sapper.bet` accepts a signed amount without positive/max validation; a negative stake passes the balance comparison and is negated into a positive `UpdateData.RedBucks` credit. Detailed proof and test matrix: [SAPPER_REVIEW.md](SAPPER_REVIEW.md). Critical; open pending server-side stake validation and test-account regression testing.

## MONEY-009 — Sapper client selects outcome and payout

CEF controls RNG and `server.sapper.end` trusts a client multiplier index; forged `type=7` pays 3x stake, and a losing `-2` can be replaced with `-1` to refund. The server has no authoritative board/progress record. Detailed proof and tests: [SAPPER_REVIEW.md](SAPPER_REVIEW.md). Critical; open pending server-owned round/RNG and exactly-once settlement.

## MONEY-010 — wedding divorce fee can be debited without unlinking after spouse disconnect

For a married player whose spouse is online but more than 5m away, the confirmation session uses the one-sided `$300,000` path. If the spouse disconnects between prompt creation and confirmation, `Wedding.OnDivorcio` calls `Wallet.Change(-price)` before re-resolving that spouse; `GetPlayerByUUID` can then return null and `target.GetCharacterData()` throws before marriage fields are cleared. The generic dialog callback catches/logs the exception but does not refund. Detailed evidence and regression matrix: [WEDDING_REVIEW.md](WEDDING_REVIEW.md). Medium; open pending ordering/transaction fix and disconnect/failure tests.

## MONEY-011 — time-based online rewards may replay after a stale character checkpoint

`Main.cs:3706-3762` increments `TodayTime`/`MonthTime` and grants RB/cases on exact thresholds. `TimeInfo` persists in `Characters.Time` only through `Character.Save.Repository.SaveSql`; `SaveServer` is scheduled hourly, with disconnect/admin save paths, not a per-minute checkpoint. RB queue writes and warehouse case inserts are independent DB operations, not a transaction with the time checkpoint. A crash or partial DB failure can therefore persist a reward while leaving the old threshold in `Characters.Time`; on reconnect/tick it may be paid again. The reverse ordering may lose the reward. Graceful saves reduce but do not eliminate the gap; no remote-triggerable server crash was established. Medium, open; source-level durability gap is clear, practical replay requires DB/RAGE fault-injection. Use durable idempotent claim/receipt per character/period/threshold and transactional grant/outbox. Detailed evidence and crash/retry matrix: [ONLINE_REWARDS_REVIEW.md](ONLINE_REWARDS_REVIEW.md).

## MONEY-012 — client-supplied taxi mileage can trigger passenger fares

`server.vehicle.updateMileage` trusts remote `centimeters` after only checking that sender is in the named current vehicle. The handler caps each positive mileage result at 3 but does not validate the delta against server-measured movement, rate, or ride total. For an active TaxiData passenger association it calls `TaxiPay`; each fabricated update can transfer `$30..$90` from passenger to driver. It is not a money mint claim: it is unverified metering in the billing path. The same call grants tasks 2/59/159 to the driver and 95 to passenger before unchecked wallet changes (see `PROG-007`). Medium, open; needs disposable ride/test-account RAGE validation. Server-owned distance and idempotent fare settlement are required. Full source trace and tests: [TAXI_MILEAGE_REVIEW.md](TAXI_MILEAGE_REVIEW.md).


## MONEY-003 addendum — ambiguous false result after wallet/bank mutation

The shared APIs do not provide a reliable no-mutation guarantee when returning false. Wallet.Change mutates the character balance and queues large absolute balances before sending the client balance event; an exception in that later event is caught by the outer method and converted to false. Bank.Change similarly mutates the in-memory bank balance and marks it dirty before BankNotify/client event work, then may return false from its catch. Bank.Transfer interprets a false source Change as a failed debit and returns, even though the source balance may already have changed; it also ignores the destination Change result and can report success after a failed/uncertain credit. This is a source-ordering risk, not a runtime-reproduced fault.

Do not implement retry/refund based only on these bools. Separate financial mutation/persistence from notifications and return an explicit operation state; use an idempotent DB transaction/ledger operation for transfer, then update caches and notify after commit/outbox. Add fault-injection at notification-after-mutation, source debit, destination credit, DB persistence, duplicate confirmation and concurrent confirmation. See BANK_TRANSFER_REVIEW.md.


## Wallet.Change follow-up — result after balance mutation

A bounded source patch was applied in `MoneySystem/Wallet.cs`: the method now records whether the in-memory balance has changed and returns that state from its outer exception handler. The client balance notification has its own exception boundary, so a notification failure is logged without reporting an already-applied balance mutation as rejected. This reduces the risk that callers retry or compensate an applied debit/credit based on a misleading `false`.

**Limits:** `true` still means the in-memory balance mutation was applied, not that MySQL durably committed it. `Wallet.Change` remains non-transactional and the existing `long`/`int` cast and arithmetic boundary needs separate end-to-end review. The patch is static-only; build, notification fault injection, queue failure and RAGE tests remain pending. Do not treat this as settlement/idempotency closure.


## MONEY-036 — единый signed-INT контракт для cash wallet (частичный patch)

- `CharacterData.Money` — `long`, но `characters.money` в `ServerStruct.generated.cs` отображён как nullable `int?` (`int(11)`). Это подтверждённый schema/type mismatch; BIGINT migration не выполнялась.
- Старый `Wallet.Change` делал `(int)characterData.Money + amount` до проверки диапазона. Теперь он складывает в `long`, отклоняет отрицательный результат и результат выше `Int32.MaxValue`, а затем только записывает `CharacterData.Money`. Это сохраняет существующий DB contract и не делает silent narrowing.
- `Character.Save.Repository.SaveSql` теперь проверяет `0..Int32.MaxValue` до запуска связанных save операций и до `Convert.ToInt32`. Invalid state логируется и не сохраняется.
- `Database.Models.Money.AddMoneyUpdate` уже валидирует UUID и signed INT range до помещения в retry queue. Однако сама очередь остаётся volatile.
- **Незакрытый риск:** Money worker пишет абсолютное значение `characters.money` отдельным SQL UPDATE, параллельно с полным `SaveSql`; offline auction fallback также имел прямой UPDATE (теперь добавлена range validation). Без общего per-character serialization/version token старый batch, задержавшийся в DB, теоретически может перезаписать более новое значение полного save. Это требует отдельного решения; не объявлять MONEY-002 закрытым.
- Проверки: статические source assertions only. Нет C# build, DB round-trip, worker concurrency или RAGE UI test.


## MONEY-002 — detached worker hand-off race (2026-11-08, partial patch)

The worker/full-save ordering now has a process-local coordination layer:

- `Money` keeps a fixed striped `SemaphoreSlim` set and per-UUID revision tokens; unrelated UUIDs may share a stripe.
- `Character.Save.Repository.SaveSql` writes the main character row through `ExecuteCharacterSave`. It acquires the UUID stripe, snapshots the latest in-memory balance under `GetCharacterMoneySyncLock`, advances the revision and invalidates older queued snapshots before SQL. On save failure it restores the captured absolute balance only if no newer wallet mutation was queued.
- `Wallet.Change` uses the same per-UUID monitor while mutating the balance and advancing the revision. Small changes are queued when a save or worker write is active; large changes retain eager queueing.
- **New hand-off fix:** the worker marks each UUID `ActiveMoneyWrites` while detaching `MoneyUpdateList`, under `QueueLock`, before DB context creation. Previously the marker appeared only after the worker acquired the semaphore. A small wallet mutation in the detach→SQL window could advance the version, not enqueue (no active marker yet), and cause the detached snapshot to be skipped with no replacement. Snapshot-time marking closes that gap. Failed context/batch requeue removes the marker and only restores a still-current revision.
- Worker and full-save writes are still not crash-durable; the queue and revisions are in-memory. No durable outbox, retry backoff or dead-letter policy exists.
- **Other direct DB cash writers remain outside this coordinator:** `Character.Save.Repository.AddMoney`, `Players.Phone.Auction.Repository` offline refund, `Main.cs` referral reward and business-tax repossession, `Core.Admin.OffGiveMoney`, and `Accounts.Merger.Repository.MergerToOrganization`. These require a coordinated follow-up; do not mark MONEY-002 closed.
- Static inspection only. Required tests include detach/SQL hand-off, full-save ordering, wallet mutation during save, save failure requeue, DB context failure, partial batch retry, reconnect and process restart. No C# build or MySQL fault injection has run.


## MONEY-036 — offline direct cash writers range follow-up (2026-11-08)

- `Character.Save.Repository.AddMoney` now widens the DB balance plus delta to `long`, rejects negative/corrupt current balance and rejects a result above `Int32.MaxValue` before narrowing.
- `Core.Admin.OffGiveMoney` now computes in `long`, retains the existing floor-at-zero behavior, rejects above-max grants and only then casts to `int`.
- `Main.CheckMyPromoCode` offline referral reward now widens the sum and rejects negative/out-of-range result before writing the signed INT column.
- These are range guards only. They do **not** put these direct writers under the Money worker/full-save coordinator; read-modify-write lost-update races and offline→online transition races remain open. Business-tax repossession and Merger direct writes also need range/ordering review.
- Static review only; test null DB balance, zero/negative reward, exact max, max+1, `int.MinValue` debit and concurrent pending queue/full save. No C# build or MySQL test.


### MONEY-002 follow-up — failed SQL hand-off window (2026-11-08)

A second interleaving was found in `MoneyUpdate`: the detached row's `ActiveMoneyWrites` marker was removed in `finally` immediately after releasing the UUID semaphore, even when `UpdateAsync` threw. `Worker` only called `RequeueMoney` after `MoneyUpdate` returned `false`. A small `Wallet.Change` in that interval could see no pending/in-flight marker, choose not to enqueue, then the failed old row would be rejected by version comparison during retry — losing the latest balance snapshot from the retry path.

**Patch:** `MoneyUpdate` now distinguishes a completed write, a superseded snapshot, and a failed write. It removes the in-flight marker after success or supersession only. On SQL failure it leaves the marker registered until `Worker` calls `RequeueMoney`, which atomically requeues only the still-current version and removes the marker under `QueueLock`. This closes the identified in-process failure/requeue window by source inspection; no runtime interleaving test has run.

**Remaining direct writers requiring safe migration:** `Character.Save.Repository.AddMoney`, `Players.Phone.Auction.Repository.ReturnMoney` offline cash fallback, `Main.CheckMyPromoCode` referral reward, `Main` business repossession proceeds, `Core.Admin.OffGiveMoney`, and `Accounts.Merger.Repository` organization merge refund. They perform independent SQL reads/writes and do not share the per-UUID semaphore/version protocol. Do not blindly wrap these with the coordinator: first decide whether the target can be online and whether the operation is an absolute assignment or additive credit, then preserve any queued in-memory snapshot and make DB mutation/notification ordering explicit. `Accounts.Merger` currently appears to set an absolute `moneyTo` value and needs separate semantic review.


### MONEY-002 follow-up — durability boundary and direct-writer sequencing (2026-11-08)

The current `MoneyUpdateList` worker is a retryable **snapshot persistence queue**, not a durable transaction outbox. Moving the same in-memory snapshots into a new DB table from the background worker would not close the crash window: the process can still stop after `Wallet.Change` mutates the in-memory balance and before the worker records the outbox row.

A crash-durable design therefore cannot be introduced only inside `Money.cs`. The write path must change at the mutation boundary:

1. Give each logical cash operation a stable operation ID and immutable payload (character UUID, signed delta, reason/source, creation time).
2. In one InnoDB transaction, insert a uniquely keyed operation/receipt and apply the balance delta with conditional bounds. Duplicate operation IDs return the stored result and do not apply the delta again.
3. Commit before the caller reports durable success or triggers irreversible side effects. Keep the in-memory character cache synchronized only after commit (or expose a pending state with explicit recovery semantics).
4. Reconcile/replay committed-but-unacknowledged operations from the receipt/ledger after restart; do not replay an operation whose unique receipt already exists.
5. Migrate every cash writer—including `Wallet.Change`, full character save, offline `AddMoney`, bank/property/auction/merger/admin paths—to the same coordinator. A partial migration would retain last-writer-wins races between old and new writers.

**Immediate safe follow-up:** the offline `Character.Save.Repository.AddMoney` and referral reward paths still perform read-then-absolute-write. They need an atomic conditional SQL increment to prevent concurrent lost updates and signed-`INT` overflow, but that alone is not idempotent and does not solve payout replay. Keep this as a separately tested transitional fix; do not present it as the durable ledger.

**Decision gate before implementation:** confirm all relevant balance tables use InnoDB; inspect exact LinqToDB 3.3 transaction/affected-row APIs; define operation-ID ownership for lottery/referral/auction payouts; identify online/offline cache handoff; and provide a migration/rollback plan. Do not add a background outbox table and claim crash safety without moving the transaction boundary to the original mutation.

### MONEY-002 follow-up — offline admin payout acknowledgement (2026-11-08)

Core/Admin.cs OffGiveMoney previously emitted the money/admin logs and success notification before awaiting the characters.money UPDATE. A database exception therefore left the operator with a success message for an unpersisted grant. The method now awaits the UPDATE first, requires exactly one affected character row, and only then emits success logs/notification; zero/ambiguous affected-row results are reported as failure.

This is a bounded acknowledgement-order fix only. The method still performs a read-then-absolute-write, so concurrent offline grants and races with the online wallet worker/full character save can lose updates. It has no durable operation ID/receipt and is not crash-idempotent. Static patch only; no C# build or DB test.

**Library/API reconnaissance (verified against the pinned package source):** `NeptuneEvo.csproj` pins `linq2db.MySql` 3.3.0, and generated `ServerBD` derives from `LinqToDB.Data.DataConnection`. The matching LinqToDB `v3.3.0` source exposes `BeginTransactionAsync`, `CommitTransactionAsync` and `RollbackTransactionAsync`, so an explicit transaction can be owned by the existing `ServerBD` context without introducing `TransactionScope`. Important version-specific behavior: `BeginTransactionAsync` disposes an already attached transaction (rolling it back) before starting another; therefore coordinator code must own one transaction per context and must not assume nested calls throw. This confirms API availability only—not MariaDB engine/DDL compatibility, InnoDB status, commit durability settings or runtime behavior.


## MONEY-002 follow-up — direct cash-writer inventory (2026-11-08)

The next source pass re-opened the active branch versions of `Money.cs`, `Wallet.cs`, `Character/Save/Repository.cs`, `Main.cs` and `MoneySystem/Bank.cs`. This is a targeted cash-writer inventory, not proof that every money mutation in the repository has been enumerated.

### Confirmed direct character-cash writers

1. **Online wallet path — `MoneySystem/Wallet.cs:Change`.** The current patch mutates `characterData.Money` under the striped character sync lock and queues an absolute snapshot. Small changes are not necessarily queued unless a prior write/save is active; they therefore depend on a later full character save. This is still an in-memory-first path and is not crash-durable. The boolean result means the in-memory mutation was accepted, not that the DB commit completed.
2. **Offline/admin-style helper — `Character/Save/Repository.cs:AddMoney`.** It starts a fire-and-forget task, reads `characters.money`, computes a new absolute value and writes it. There is no affected-row/result returned to the caller, no operation ID, and no transaction spanning read/update. Two concurrent calls can read the same starting value and overwrite one another. It also has no explicit online-character/cache handoff; a login/full save racing the detached task can overwrite or stale-load the balance. Do not replace this with a blind SQL increment until online/offline ownership is serialized.
3. **Referral cash reward — `Main.cs` referral completion block.** It reads the referrer's current cash, computes an absolute balance and writes it separately from referral success and account RedBucks/VIP updates. These writes are not one transaction and have no idempotent referral payout receipt. A retry/crash can leave partial reward state; concurrent cash writers can lose an increment. The code also needs a stable identity for the referral reward before any coordinator migration.
4. **Lottery payday payout — `Main.payDayTrigger`.** Online winners use `Wallet.Change`; offline winners use `AddMoney`. Round state/logging/reset is performed independently of a durable payout acknowledgment. This remains the documented `CAS-026`/lottery settlement gap, not a separate safe writer.

### Persistence and schema evidence boundary

- `Money.cs` worker uses absolute `characters.money` updates; `SaveSql` also writes the whole character row, including money. Any new coordinator must prevent these legacy absolute writers from racing its balance updates.
- `MoneySystem/Bank.cs` has a separate in-memory bank-account cache and dirty-save worker. It is a separate balance domain and should not be mixed into the first character-cash coordinator without a distinct migration plan.
- Repository code pins `linq2db.MySql` 3.3.0 and generated `ServerBD` derives from `DataConnection`, but API availability does not establish the engine or transaction properties of production tables.
- The attempted repository code search did not return authoritative DDL for `characters` / cash tables. A hit for `ENGINE=InnoDB` in `mainlogs.sql` concerns other tables and is not evidence for `characters`. **InnoDB for the participating tables remains unverified.** Do not create ledger tables or claim transactional durability until the exact DDL/engine for `characters`, `accounts`, `refferals` and the proposed receipt table is inspected.

### Coordinator design constraints confirmed by this pass

- All online wallet, offline award, referral, lottery, full-character-save and legacy snapshot-worker writes to `characters.money` must share one serialization/ownership boundary during migration.
- A transitional offline atomic increment is not safe until a per-UUID online/offline handoff is established; SQL atomicity alone does not stop a stale online cache/full save from overwriting it.
- Referral and lottery require domain-level stable payout IDs, not merely a generic balance increment. The receipt and balance update must commit together, and caller-visible success/reset must follow the durable result.
- No C# source was changed in this pass. No build, MariaDB transaction test, concurrency test, or RAGE staging test was run. MONEY-002 remains open.


### MONEY-002 follow-up — direct offline AddMoney writer (2026-11-08)

A fresh source pass confirms that `Character.Save.Repository.AddMoney(int uuid, int money)` remains outside the wallet/character-save coordinator:

- It asynchronously reads `characters.money`, calculates `currentMoney + delta` in application code, then writes an absolute value in a separate SQL statement. There is no transaction, row lock, compare-and-swap predicate, or per-UUID money lock around the read/write pair. Two concurrent calls can read the same starting balance and the later absolute UPDATE can erase the earlier increment.
- The method does not establish that the character is offline and does not synchronize the online `CharacterData.Money` cache. If the character is online or logs in while the task is running, the direct DB write can race with wallet snapshots/full character save and can be overwritten by a stale cached balance (or leave memory and DB divergent). This is a source-level race; exact timing/reproduction still requires staging.
- The range checks protect the computed value but do not make the read-modify-write atomic. The UPDATE result is not checked for an affected row, and exceptions are only logged.
- Current call-site examples include offline lottery payout and referral reward. They are not safe to convert to a plain SQL increment until online/offline handoff and retry/idempotency semantics are defined.

**Disposition:** no source patch in this slice. Do not replace this with `SET money = money + delta` alone: it would avoid the lost-update read/write race but still race with online absolute wallet/full-save writes and would not make a retry idempotent. Route all writers through the eventual per-character money coordinator; for durable settlement, use a stable operation ID/unique receipt and balance mutation in the same transaction. Until then, MONEY-002 remains open.


### MONEY-002 follow-up — expanded direct-writer inventory (2026-11-08)

The wider repository search found additional paths outside Wallet.Change/the money worker:

- Players/Phone/Auction/Repository.ReturnMoney: online recipients are credited to their bank or wallet; offline recipients are read from characters and cash fallback uses SELECT → application-side addition → absolute UPDATE. It has the same lost-update and login/save handoff risks as Character.Save.Repository.AddMoney. The payout is also not tied to a durable per-auction refund receipt, so retry/restart semantics remain open.
- Main.CheckMyPromoCode offline referral-owner reward: reads the character cash row and later writes an absolute new balance. Referral success and account RB/VIP writes occur as separate operations; this is not an atomic reward settlement. Online branch uses Wallet.Change, but its result is not used to gate the referral success state/notification.
- Core.Admin.OffGiveMoney: it checks whether the target is online before entering an asynchronous task, then reads and writes the DB balance. A target can log in after the check and before the UPDATE; the method has no atomic offline claim/handoff with login or full save. It does check that one row was affected, which is useful but does not solve the race or idempotency.
- Accounts.Merger.Repository creates destination character rows with a composed MoneyTo value (source cash plus converted property/business balances). Treat this as a one-time migration/import writer with its own idempotency and rollback requirements, not as a normal wallet delta.
- Generated mapping confirms characters.money is nullable signed int(11); generated metadata reports MariaDB 10.4.12. This confirms the type contract only. The available search did not establish the storage engine for characters; InnoDB must be verified against the actual deployed DDL/runtime metadata before relying on transactional guarantees.

**Current disposition:** no source change in this pass. The coordinator migration inventory must include wallet online mutations, full character save, worker flush, offline AddMoney, auction refund, referral reward, admin offline grant, lottery payout and account/server merger. Bank-account balance writers are a separate ledger and must be mapped before cross-ledger operations are designed.


### MONEY-002 follow-up — character login publication race (2026-11-08)

The login path confirms the cache handoff gap: Character.Load.Repository reads the Characters row and materializes CharacterData.Money near the start of the load, performs additional asynchronous loading work, and only later calls player.SetCharacterData(characterData). The reviewed path does not acquire Money.GetCharacterMoneySyncLock or the money semaphore around the DB read-to-cache-publication interval. An offline direct writer can therefore update the DB after the SELECT but before SetCharacterData; the newly published in-memory cache can start with the stale pre-update balance. The same missing login-side coordination means a future offline atomic increment alone is not sufficient.

**Coordinator requirement:** login must participate in the same per-UUID serialization protocol as offline money operations and full saves, covering the authoritative balance read through cache publication. Offline writers must atomically establish that no login/cache publication is in progress before changing the DB row. Recheck this requirement during implementation; no source change was made here.


### MONEY-002 follow-up — repository DDL and referral settlement ordering (2026-11-08)

A direct read of the repository's current `RedAge-3.0/database/main.sql` dump now confirms the **checked-in schema snapshot** defines `characters`, `money`, `accounts` and `refferals` as `ENGINE=InnoDB`. The `characters.money` column is nullable signed `int(11)`; the dump header identifies MariaDB 10.10.2. This supersedes the earlier statement that no repository DDL evidence was available.

Important boundary: this proves only the engine/type in the checked-in dump. It does not prove that the deployed database uses this exact dump or has not drifted. Production/staging `SHOW CREATE TABLE` (or equivalent metadata) and server version are still required before relying on transaction semantics. The generated mapping's older MariaDB 10.4.12 comment is historical build metadata, not proof of the live server version.

The referral owner-reward path was traced further in `Main.CheckMyPromoCode`:
- For an online referrer, VIP/coin/cash/RedBucks rewards are applied through separate APIs, notification is sent, and only then is the `refferals.success` row updated. Wallet/RedBucks/VIP/item results are not consistently checked as one settlement.
- For an offline referrer, the referral success row is updated first, then account RedBucks/VIP are updated, then cash is read and written as an absolute value in a separate query. These are not one transaction. A failure after the success marker can permanently suppress retry while one or more reward legs are missing; a retry around an uncertain acknowledgement can also duplicate a leg.
- The offline cash SELECT/absolute UPDATE remains exposed to concurrent credits and login/cache publication races.

The repository DDL makes an InnoDB receipt+balance transaction technically plausible for these tables, but implementation still requires a single transaction owner/context, unique stable operation IDs, and migration of every cash writer. Do not mark production durability proven from the checked-in dump alone. No C# source was changed and no build/runtime/DB test was run in this pass.


### MONEY-002 — proposed coordinator contract (design gate, not implemented)

The next implementation must use one API boundary for every character-cash mutation. Proposed contract:

- `ApplyAsync(MoneyOperation operation)` returns a typed result (`Applied`, `Duplicate`, `Rejected`, `RetryableFailure`, `UnknownCommitOutcome`) with the committed balance/revision when known. A caller must never infer durable success from an in-memory `bool`.
- `MoneyOperation` is immutable and carries a stable globally unique `OperationId`, character UUID, signed delta, domain/source, reason/reference and creation time. IDs are minted at the logical business-event boundary and reused unchanged on retry. Referral, lottery, auction refund and admin grant each need domain-stable identities.
- One coordinator-owned, per-operation `ServerBD` context owns exactly one explicit transaction. Insert a unique operation receipt and apply the bounded cash delta to `characters` in the same InnoDB transaction. A duplicate ID returns the prior committed receipt/result without reapplying the delta. If the conditional balance update affects anything other than exactly one row, roll back the receipt and return a typed rejection/failure.
- The balance update must enforce `money IS NOT NULL` and `0 <= money + delta <= Int32.MaxValue` in SQL; no application-side SELECT → absolute UPDATE. The transaction owner must not rely on nested `BeginTransactionAsync` behavior or share a context with unrelated work.
- The per-character async gate spans DB commit and in-process cache handoff. After commit, update the online `CharacterData.Money` cache while still holding the gate; on restart, DB is authoritative. Login must take the same gate for its final authoritative balance read and `SetCharacterData` publication. Offline credit must take the same gate, so it cannot race the login SELECT/publication interval.
- Remove legacy absolute cash writers from the path: `MoneyUpdate` worker snapshots and `SaveSql` must no longer be able to overwrite coordinator-managed cash. Full character save should persist non-cash fields without setting `characters.money`; the cash ledger owns that column. Transitional compatibility must be explicit and time-bounded, never mixed unsafely with new writes.
- `Wallet.Change` is currently synchronous and mutates RAM before background persistence. A durable coordinator is asynchronous; migrate critical call sites to await the typed result before granting items, marking referrals/lottery rounds complete, logging success or notifying success. Do not preserve the old signature as a misleading durable facade.
- Keep bank-account `money.balance` as a separate ledger/domain. Cross-cash/bank operations require an explicit multi-ledger transaction/compensation design; they are not implicitly covered by this character-cash coordinator.

Migration order: (1) create/verify receipt DDL and deployed InnoDB; (2) implement coordinator + duplicate/retry semantics; (3) coordinate login and cache publication; (4) remove/disable legacy worker and money field in full save; (5) migrate AddMoney, auction refund, referral, lottery and admin offline grant; (6) migrate all online Wallet.Change callers that require durable success; (7) run concurrency, crash-point and mixed-version tests before rollout. No source implementation has been started.



### MONEY-002 follow-up — direct cash writer findings revalidated (2026-11-08)

A fresh read of the active branch confirms these remaining bypasses and their exact semantics:

- `Character.Save.Repository.AddMoney(uuid, money)` is still an async fire-and-forget method. It SELECTs `characters.money`, converts the nullable value with `Convert.ToInt32`, adds the delta in application memory, then writes an absolute value. There is no transaction, row lock, operation receipt, per-UUID gate, or affected-row acknowledgement. Concurrent credits can lose increments. Because null converts to zero here, a NULL legacy balance is silently treated as zero rather than handled by an explicit migration policy. The method's current callers include offline promo-owner reward and payday lottery payout; the caller's earlier online-presence decision is not held atomically through this async write.
- `Main.CheckMyPromoCode` referral-owner settlement has two different paths. The online path calls VIP/warehouse/wallet/RedBucks APIs independently and then updates the referral success row; cash and other reward legs are not one durable settlement. The offline path updates referral success and account RB/VIP separately, then SELECTs and absolute-writes cash. A partial failure can leave a success marker with missing reward legs. Its offline cash update can also race a recipient login/cache publication.
- `Players.Phone.Auction.Repository.ReturnMoney` first resolves the player, then schedules offline work if absent. The fallback reads the character and bank ID; when no loaded bank account is found it applies a validated signed-INT cash absolute UPDATE. The earlier range guard prevents overflow, but it does not provide atomic increment, idempotency, affected-row confirmation, or login/cache handoff. When a bank account is found, it schedules a separate bank-cache mutation instead; that is a distinct ledger path.
- `Accounts.Merger.Repository` computes an aggregate imported `MoneyTo` from character cash, business value and house/account value, then creates the destination character with that amount. This is a migration/import writer rather than an ordinary delta. It needs a stable merge identity and restart-safe import checkpoint so retry cannot duplicate destination cash/assets. The current accumulator is `int`; its aggregate arithmetic and source/destination partial-completion behavior require a separate bounded/idempotent review.
- The admin offline grant has a separate async persistence path. Its recent acknowledgement patch waits for the DB update and checks the affected-row count before success logging/notification, but the online-presence check and DB mutation still need to be serialized with login and the shared cash coordinator. Awaiting an absolute write is not equivalent to an atomic/idempotent grant.

No new C# changes were made. The checked-in DDL evidence and referral ordering recorded above remain valid only for the repository snapshot; deployed schema must still be checked. Do not apply an isolated SQL increment to any of these paths until login publication, online cache, queued snapshots, and stable operation identity share one coordinator boundary.


## MONEY-054 — referral cash reward can be marked complete before cash is credited

**Уверенность: высокая по порядку операций; эксплуатация/частота зависят от бизнес-правил и данных. Приоритет: высокий.**

Файл: `Main.cs`, `CheckMyPromoCode` (referral success async block).

Порядок внутри одного async DB task:
1. Читается account пригласившего и рассчитывается RB/VIP reward.
2. Строка `Refferals` обновляется на `Success=true` и получает `Successdate`.
3. Затем обновляется account: `Redbucks`, `Viplvl`, `Vipdate`.
4. Только после этого читается `characters.money` пригласившего. Если balance отрицательный/некорректный или `currentMoney + refferalData.Money` выходит за signed INT range, код только пишет лог и пропускает cash UPDATE.
5. Ошибки внешнего DB task ловятся общим catch; нет транзакции, durable pending state или retry receipt.

**Следствие:** referral может стать окончательно отмеченным успешным, RB/VIP могут быть выданы, а денежная часть reward — потеряна. DB exception после записи Success/RB/VIP, но до cash credit, создаёт тот же частичный результат. Это не утверждение о создании денег: конкретный подтверждённый риск — неполная выдача согласованного referral reward и невозможность безопасного автоматического повтора.

**Исправление (не внедрено):** создать referral settlement с уникальным referral/reward ID; в одной DB transaction фиксировать success state, RB/VIP и cash ledger/receipt либо durable pending legs, с чёткими retry/reconciliation semantics. Cash leg должен проходить через общий MONEY-002 coordinator; не использовать SELECT → absolute UPDATE. Проверять результат каждой DB операции и уведомлять об успехе только после durable commit.

**Тесты:** cash delta на границе `Int32.MaxValue`; DB failure после каждого шага; повторная проверка того же referral ID; duplicate/concurrent processing; проверка, что повтор не дублирует RB/VIP и не теряет cash; online/offline inviter и reconnect/restart. Пока только статический анализ; source не менялся, build/DB/RAGE tests не запускались.
