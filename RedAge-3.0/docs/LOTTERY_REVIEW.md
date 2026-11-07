# Legacy Lottery purchase/draw review

Статус: статический review; runtime, DB failure injection и payout reconciliation не выполнялись. Изучены 24/7 shop interaction/callback, lottery ticket state, async persistence, payday draw и `/lottery` display.

## CAS-024 — lottery/shop callback доверяет устаревшему BizID без location check

**Уверенность: высокая по коду; приоритет: средний/высокий, если покупки должны быть ограничены физическим магазином.**

`OnBusinessAction` записывает `sessionData.BizID = ID` при взаимодействии с бизнесом (`Core/Businesses.cs` около 1035–1054); сам комментарий помечает это состояние как требующее переделки. `Event_ShopCallback` (`server.sm.shop`, около 3450–3463) проверяет только наличие session/character и что `BizID` всё ещё есть в `BizList`, после чего использует client-supplied product index. В просмотренном flow `BizID` не сбрасывается при выходе из магазина, а callback не повторяет proximity/dimension/shop-session validation. После открытия 24/7 UI игрок может отправлять purchase remote calls, находясь в другом месте; ticket purchase проходит общий balance/stock flow.

**Remediation:** server-owned expiring shop session/nonce, с привязкой к конкретному business и server-side location/dimension; сброс при выходе, disconnect и смене контекста. Проверять product index и ограничивать callback активной сессией.

**Проверки:** открыть 24/7, уйти/телепортироваться/сменить dimension, вызвать callback напрямую/повторно; все calls должны быть no-op без debit, ticket, stock/business mutation или quest progress. Проверить штатную покупку на месте.

## CAS-025 — ticket debit, in-memory entry и durable ticket insert не единая операция

**Уверенность: высокая по последовательности; приоритет: высокий для целостности покупки. Runtime failure не воспроизводился.**

В `Core/Businesses.cs` (около 3486–3544) lottery branch сначала уменьшает business stock через `takeProd`, добавляет UUID в `LotteryBought`, увеличивает jackpot (`Price`), затем игнорирует bool `Wallet.Change(player, -500)`, пишет money log и обновляет BattlePass/quest. Durable запись `LotteryPlayers` ставится отдельной async задачей через `Trigger.SetTask`; insert exception только логируется. Следовательно, wallet failure не компенсирует ticket/grant state, а process/DB failure до завершения async insert может потерять купленный билет для последующего рестарта (при этом текущий process уже считает его действительным).

**Remediation:** валидировать/списать успешно и создать durable ticket receipt/entry в одной транзакционной/idempotent последовательности; отложить quest/notification до commit; иметь retry/reconciliation или компенсацию для неопределённого результата.

**Проверки:** fault injection на stock/bank mutation, wallet debit, DB insert до/после commit, process restart; проверить отсутствие бесплатных билетов/потерянных оплаченных билетов, дублей ticket ID, повторных quest claims и рассогласования jackpot.

## CAS-026 — draw очищает раунд, не проверив и не подтвердив payout

**Уверенность: высокая по коду; приоритет: высокий при outage/overflow.**

В `Main.payDayTrigger` (около 4333–4378) выбирается ticket и для online winner результат `Wallet.Change(target, (int)Lottery.Price)` игнорируется. Для offline winner вызывается `Character.Save.Repository.AddMoney`, который только ставит async DB read/modify/write и ловит/logs exception без результата/receipt. Затем код немедленно пишет GameLog/announce, увеличивает lottery ID, обнуляет jackpot и очищает `LotteryBought`; асинхронное обновление `lottery.number` также не подтверждается до reset. Если online credit отклонён (например int-range edge), либо offline DB update/round-ID update падает/не успевает до restart, нет durable pending payout/retry/reconciliation; выигрыш может быть потерян или старый раунд восстановится из БД.

**Remediation:** durable draw record + unique payout ID и transactional/idempotent payout ledger; не объявлять/reset-ить раунд до записи результата или сохранять pending settlement для retry. Использовать checked amount bounds и безопасный atomic DB increment для offline balances.

**Проверки:** online wallet credit failure, offline DB failure/restart, DB commit success before process crash, round ID update failure, повторная выдача payday callback; доказать exactly-once winner payout и exactly-once round transition.

## Дополнительные наблюдения

- В startup `Lottery.OnResourceStart` восстанавливает текущий раунд из `lottery_players` и рассчитывает `Price = 350 * ticketCount`; новый ticket `mynumb` берётся как `LotteryBought.Count + 1`. Таблица не имеет unique key на `(number,ticket)`; целостность последовательности и вставок следует покрыть миграционными/DB tests.
- Текущий flow использует фиксированный ticket price `$500`, а pool составляет `$350` на каждый ticket. Экономический смысл доли бизнеса/синк/суммы jackpot — решение владельца, не вывод о корректности баланса.
- `/lottery` вычисляет шансы по числу билетов игрока / общему количеству в памяти; отображение не является независимым источником durable state.

## Границы

Все findings статические и не проверены с MySQL/RAGE runtime. Никакой gameplay/economy policy не менялась. Требуются test DB, fault injection, reconnect/restart и exactly-once payout tests; не считать эти пути закрытыми до выполнения проверок.
