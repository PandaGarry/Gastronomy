# Статический review NewCasino remote flows

Фокус этого файла: NewCasino Roulette (`NewCasino/Roulette/Roullete.cs`), client bridge `src_client/casino/roulette.js` и общий disconnect lifecycle. Проверены remote events `CHARACTER_OCCUPY_PLACE`, `CHARACTER_LEAVE_PLACE`, `CREATE_BET`, `DESTROY_LAST_BET`, `CLEAR_TABLE`, а также `ContinueGame`, `OnClearTable` и `Disconnect`. Blackjack разбирается отдельно в `BLACKJACK_REVIEW.md`; Spin, Horses и остальные casino entry points пока не покрыты.

## CAS-001 — remote cancel возвращал ставку после закрытия betting phase

**Уверенность: высокая по code path; приоритет: высокий. Локальный patch внесён, не собран и не проверен на runtime.**

`ContinueGame` выставляет `table.Process = true`, выбирает исход, задаёт каждому игроку `rData.Time = DateTime.Now.AddSeconds(5)` и отправляет `START_GAME`. `OnDestroyLastBet` — remote event — до patch проверял лишь наличие персонажа/`PlayerData`/ставки, затем удалял chip object, возвращал всю сумму через `Wallet.Change(player, mybet)` и удалял ставку из `AllBets`, не сверяя `table.Process`. Клиент блокировал отмену через `betState = false`, но forged `server.roullete.DESTROY_LAST_BET` обходил эту UI-проверку.

**Patch:** `OnDestroyLastBet` теперь до refund проверяет диапазон `SelectedTable` и отвергает отмену, когда `RouletteTables[SelectedTable].Process == true`. До начала раунда (в разрешённой betting phase) возврат ставки остаётся возможен. Требуются compile/staging tests на легальный cancel до старта и невозможность отмены после `table.Process=true`; race/order semantics на RAGE runtime всё ещё не проверены.

## CAS-002 — максимальная/минимальная ставка задана только в CEF

**Уверенность: высокая в различии клиентского и серверного лимитов; приоритет: высокий, если значения CEF являются intended table rules.**

`src_client/casino/roulette.js` задаёт клиентские min/max в зависимости от модели стола: 50/25,000 для обычного стола и 7,500/100,000 для high-stakes модели. Однако remote `OnCreateBet` (`Roullete.cs`) блокирует только `bet < 20`, проверяет текущий баланс через `CanIChange`, а server-side table-specific maximum не проверяет. Прямой remote вызов поэтому принимает, например, 20 на high-stakes table или ставку больше CEF maximum, пока игрок может оплатить её.

В `OnClearTable` выплата вычисляется через `Convert.ToInt32(target_data.Bet * coefficient)` и суммируется в `int WinMoney`. Ставка существенно выше UI max при коэффициенте single-number `36x` может превысить `Int32` на выплате и выбросить exception; catch находится снаружи settlement loop, поэтому способен прервать обработку остальных игроков после того, как `table.Process` уже сброшен. Суммы, меньшие индивидуального overflow threshold, тоже требуют проверки на суммарное переполнение нескольких выигрышных ставок.

**Patch не внесён:** клиентские min/max выглядят как intended rules, но серверная policy и допустимый maximum balance должны быть подтверждены владельцем. Не вводить новый cap/менять ставки без staging и согласования. Целевое исправление — единый server-owned table config для min/max, checked payout arithmetic с явной верхней границей и безопасным per-player/per-round settlement, плюс тесты на максимуме, overflow и partial failure.

## MONEY-007 — disconnect refund можно было выбрать по уже раскрытому исходу

**Уверенность: высокая по static data-flow; приоритет: критичный для игровой валюты. Runtime exploit не воспроизводился; patch не внесён из-за gameplay/disconnect policy.**

1. `ContinueGame` выбирает `table.Win`, строит `bet_string = "exit_<win>_"`, задаёт `rData.Time = DateTime.Now.AddSeconds(5)` и немедленно отправляет `client.roullete.START_GAME` с этой строкой (`Roullete.cs`, около строк 360–381). Client handler получает `text` и использует его при запуске анимации (`src_client/casino/roulette.js`, около 128–145 и `startRouletteWheel`). Известный результат уже присутствует в аргументе client event; модифицированный клиент может его наблюдать до показа анимации.
2. `Disconnect` суммирует ставки и возвращает их, если `!table.Process || rData.Time >= DateTime.Now` (`Roullete.cs`, около 764–810). Это включает пять секунд после отправки `START_GAME` и результата. Метод вызывается общим disconnect handler (`Players/Disconnect/Repository.cs`, около 234); решение о возврате не различает `DisconnectionType`. `OnPlayerDeath` также вызывает этот `Disconnect` helper.
3. Поэтому модифицированный клиент потенциально может прочитать результат из `START_GAME` и разорвать соединение/инициировать соответствующий disconnect в grace window при нежелательном исходе; при удачном исходе остаться до `OnClearTable`. Это делает ставку outcome-dependent и может превратить gambling в практически безрисковый выбор.

**Исправление отложено:** disconnect refund может быть намеренной защитой от аварийного разрыва; менять денежную/gameplay семантику без решения владельца и staging-теста нельзя. Целевой инвариант требует, чтобы после commit исхода disconnect не отменял escrow и не терял причитающуюся выплату: ставка должна settle ровно один раз по серверному round/bet ID, а уже причитающаяся offline-выплата должна быть сохранена durable. Нужно отдельно решить, возвращается ли disconnect до commit и как компенсируется авария. Не полагаться на client event secrecy, время клиента или сообщённый тип разрыва.

## Дополнительные риски, пока без отдельного finding

- `CREATE_BET` принимает `spot`, `x`, `y`, `z` с клиента; server-side проверки spot против `TableChipsOffsets.Count` и координат относительно выбранного стола не найдены. Неверный spot, вероятно, приводит к проигрышной ставке, но входные границы и entity-spawn impact требуют отдельного trace.
- `CHARACTER_OCCUPY_PLACE` проверяет только верхнюю границу `tableIndex`, а `placeID` индексирует `table.Seats` без проверки диапазона. Invalid IDs попадают в outer catch; частичной записи до индексации не видно. Server-side proximity/dimension validation также не найдена; intended access policy нужно проверить.
- `OnCreateBet` проверяет средства через `CanIChange`, затем игнорирует bool result `Wallet.Change`; обычный последовательный flow предварительно проверяет баланс, но concurrency/event serialization нужно проверить на runtime.
- `CLEAR_TABLE` доступен игроку в `PlayerData` стола при `table.Process == true`; отдельного round nonce/animation-complete proof нет. Доказанного повторного payout не найдено: `Process` сбрасывается, а `AllBets` очищаются. Возможность раннего settlement/race требует runtime review.

## Что проверить на staging (только test account / test DB)

1. Валидная отмена ставки в countdown/betting phase до `table.Process=true`; отмена не должна работать после начала раунда и не должна менять ставку/баланс.
2. Прямые remote calls на `DESTROY_LAST_BET` до/после process transition, включая повторные и конкурентные вызовы; проверить chip objects, `AllBets`, wallet, logs и round settlement.
3. Зафиксировать `START_GAME` payload; проверить disconnect (`quit`, crash/timeout, network timeout и смерть игрока) до commit, немедленно после event, на границе пяти секунд и после неё. Проверить известные win/loss outcomes, exactly-once settlement и reconnect/restart.
4. Multi-seat round: один игрок cancel/disconnect, другие остаются; проверить `table.Process`, `WinSpots`, payouts, reset и seat reservation.
5. Invalid `tableIndex/placeID`, invalid/out-of-range `spot`, non-finite/extreme coordinates, duplicate bets, server-side min/max по каждому table; отсутствие wallet mutation/entity spam/log flood.
6. Inject failures вокруг debit/disconnect settlement/clear-table payout; проверить idempotency и wallet reconciliation.

## Границы

Выводы следуют из статического server/client flow; конкретный порядок RAGE callbacks и реальные disconnect paths не запускались. `CAS-001` локально исправлен, но не компилировался и не runtime-tested; `MONEY-007` остаётся открытым до решения денежной семантики. Другие casino systems, включая Spin и Horses, ещё не проверены; Blackjack имеет отдельный частичный review в `BLACKJACK_REVIEW.md`.
