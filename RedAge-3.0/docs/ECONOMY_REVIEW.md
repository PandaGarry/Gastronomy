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

## MONEY-002 — гонки и потеря отложенных денежный записей

**Уверенность: высокая; приоритет: высокий.** Файл `Database/Models/Money.cs`.

- `DonateUpdateList` и `MoneyUpdateList` — обычные `Dictionary`, куда пишут игровые операции.
- `Worker` на отдельном потоке делает `Values.ToList()` и затем `Clear()` без общей синхронизации с `AddDonateUpdate`/`AddMoneyUpdate`.
- При add во время snapshot/clear возможны race/exception или потеря только что добавленной записи.
- Worker очищает очередь до завершения БД-записи. Если `DonateUpdate`/`MoneyUpdate` ловит ошибку, snapshot не возвращается в очередь — повторной попытки нет.
- При аварийной остановке между обновлением кэша и фоновой записью pending changes могут потеряться.

**Исправление (не внедрено):** thread-safe queue/immutable batch с атомарным swap; не терять failed batch (bounded retry + dead-letter/alert); транзакционные flush batches; тесты на concurrent producers, DB outage и restart/recovery. Не менять семантику «сохраняется последнее абсолютное значение» без проверки всех call sites.

## MONEY-003 — банковский transfer callback повторно применим к сохранённому session state

**Уверенность: высокая по статическому потоку; эксплуатацию нужно подтвердить на staging.**

Файлы: `MoneySystem/Bank.cs:125-160, 741-751`, `Main.cs:2373-3084`, `Players/Models/SessionData.cs:118-120`.

- `Main.RemoteEvent_DialogCallback` принимает от клиента callback string + `yes` и dispatch-ит действия. Один из callback paths вызывает `ATM.AcceptTransfer`.
- Банк хранит source account, target account и сумму в `SessionData`; значения записываются при подготовке перевода.
- `AcceptTransfer` проверяет только session и ненулевые/положительные поля, затем вызывает `Bank.Transfer`. Найденных сбросов этих полей после завершения/отмены нет.
- Клиент может повторно вызвать remote callback. Пока на source account достаточно средств, повторный вызов может повторять один и тот же transfer.
- `Bank.Transfer` списывает source balance и затем вызывает `Change` для target, но не проверяет результат target credit; `AcceptTransfer` также игнорирует bool result. Целевая запись и списание не объединены DB transaction.
- В `AcceptTransfer` объект target account индексируется до проверки `ContainsKey`, поэтому исчезнувший/невалидный target приводит к исключению.

**Исправление (не внедрено):** одноразовый server-side transfer intent/nonce с коротким expiry; consume/clear до выполнения; проверки принадлежности source счёта, target type/permissions и подтверждённой суммы; транзакционный атомарный перевод с row locks/conditional update; уведомлять только после commit; replay/concurrency tests.

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
