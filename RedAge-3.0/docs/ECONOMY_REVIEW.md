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
