# Статический review NewCasino Spin / slot machine

Проверены `NewCasino/Spin/Spin.cs`, `SpinPlayerData.cs`, client bridge `src_client/casino/spin.js`, slot configuration `src_client/casino/cfg/main.js` и CEF `src_cef/src/views/casino/jacpot/index.svelte`. Это статический проход; RAGE runtime, server build и test-account workflow не запускались.

## CAS-008 — исход Spin раскрывается до окончания refund grace

**Уверенность: высокая по code flow; приоритет: критичный для денежной целостности. Не исправлено.**

`server.spin.bet` синхронно выбирает и сохраняет три символа в `sData.Spins`, вычисляет результат и задаёт `sData.Time = DateTime.Now.AddSeconds(2)`. Через 600 ms сервер отправляет этому же игроку точные rotations всех трёх символов в `client.spin.SPIN`; серверный payout выполняется через 10 секунд. В течение этих двух секунд `server.spin.LEAVE_SLOT` вызывает `Disconnect`, а `Disconnect` возвращает `sData.Cash`, если `sData.Time >= DateTime.Now`, затем удаляет игрока из `PlayerData`. Таймеры после удаления записи прекращают обработку.

CEF блокирует кнопку выхода после ставки, но прямой remote call не защищён серверной фазой. Игрок узнаёт win/loss за ~600 ms и может вызвать `server.spin.LEAVE_SLOT` до истечения двух секунд: проигрыш отменяется с полным возвратом, выигрыш можно оставить на обычное settlement. Это outcome-dependent refund, несмотря на то что вызывается leave, а не disconnect.

**Исправление не внесено:** требуется определить, что считается окончательно принятой ставкой и как обрабатывать аварийный disconnect до/после commit; возможное решение — неизменяемое server round/bet state, без refund после раскрытия исхода, exactly-once settlement и сохранение offline payout. Не просто удалять grace без проверки intended crash/timeout behavior.

## CAS-009 — Spin join принимает произвольные координаты и телепортирует игрока

**Уверенность: высокая; приоритет: критичный для server authority. Не исправлено.**

`server.spin.OCCUPY_SLOT` принимает от клиента `id`, `PosX/PosY/PosZ/Rotation`, индексирует `SpinsState[id]`, затем резервирует ID и напрямую задаёт `player.Position`/`Rotation`. Проверяются наличие session/character, отсутствие записи в `Spin.PlayerData`, `FunctionsAccess.IsWorking("spin")` и занятость slot ID; casino entry, interior/dimension, proximity и соответствие координат слоту сервером не подтверждаются. Клиентский `spin.js` рассчитывает позицию из `slots_positions`, но это client-owned data. Вызов remote вне обычного colshape path может резервировать slot и телепортировать игрока.

`SpinsState` содержит 53 элемента, а client `slots_positions` — 54 позиции. Поэтому client slot с `id == 53` индексирует список вне диапазона; исключение попадает в общий catch, и последний клиентский автомат не может быть занят сервером. Для остальных индексов bounds также фактически проверяются только через случайный `IndexOutOfRangeException`, а не явной проверкой. Это отдельная функциональная inconsistency и не является пространственной авторизацией. Требуются единая server-owned slot map, корректная явная ID validation, серверный destination/rotation, casino/access/proximity checks.

## CAS-010 — Spin bet validation, debit result и arithmetic ограничены CEF

**Уверенность: высокая; приоритет: высокий при заявленных CEF rules. Не исправлено до подтверждения политики ставок.**

CEF ограничивает ставку диапазоном `$25..$10,000`. Серверный `spin` проверяет лишь `UpdateData.CanIChange`, `SpinsWorking` и `sData.Spins.Count`; `CanIChange` запрещает отрицательное значение и сумму выше текущего баланса, но принимает ноль. Server-side min/max и проверка `MoneySystem.Wallet.Change(player, -money)` отсутствуют. После этого всё равно выдаются BattlePass reward `55`, квестовый прогресс и создаётся spin state. Нулевой remote bet поэтому запускает бесплатный раунд/прогресс; positive bet выше CEF max принимается при достаточном балансе.

Payout — `int winMoney = sData.Cash * winner`, где multiplier может быть 2, 4, 6 или 10; `Wallet.Change` также вызывается без проверки результата. Forged high bet может overflow `int` и изменить выплату/знак, а reject/failure debit не мешает продолжить ставку.

**Исправление не внесено:** подтвердить intended min/max, затем использовать server-owned limits; принимать только положительную ставку, менять game state/rewards только после подтверждённого debit; рассчитывать payout в checked `long` и валидировать возможность безопасного wallet credit. Нужны boundary/overflow, forced debit failure и race/replay tests.

## CAS-011 — рассчитанная вероятность и edge-selection defect в Spin

**Уверенность: высокая для приведённой реализации; приоритет: подтвердить у владельца игровой экономики.**

Каждый из трёх выборов использует weights `[1650,1650,1650,1650,1650,1650,100]`; после выбора выбранный weight заменяется на `Convert.ToInt32(weight / 2.75)`. Сервер платит gross 2x за пару обычных символов, 4x за пару семёрок, 6x за три обычных и 10x за три семёрки. Точная рекурсия по 343 последовательностям с правилами C# `Convert.ToInt32` (округление к ближайшему, midpoint-to-even) дала:

| Исход | Вероятность | Gross multiplier |
|---|---:|---:|
| Нет пары | 79.33985328% | 0x |
| Пара обычного символа | 20.47940131% | 2x |
| Пара семёрок | 0.01168248% | 4x |
| Три обычных символа | 0.16905870% | 6x |
| Три семёрки | 0.00000422% | 10x |

Ожидаемый gross return: **42.01992698% от ставки**; ожидаемый net result: **−57.98007302%** (до учёта других игровых эффектов). Это расчёт непосредственно по текущим весам/множителям, а не утверждение, что такой house edge принят владельцем.

В `GetRound` `Random.Next(0, total)` создаёт ID `[0,total-1]`, но накопленная сумма сравнивается через `>=`. Из-за этого первый символ получает на один ID больше, последний (семёрка) — на один меньше; исправление сравнения или interval convention слегка изменит вероятности. При идеальных weight intervals та же модель даёт gross return около **42.00537069%**. `new Random()` также используется отдельно в каждом выборе; криптографическая непредсказуемость для gambling не обеспечена и требует отдельного fairness решения.

**Следующий шаг:** владелец должен подтвердить целевой RTP/house edge и RNG требования; затем зафиксировать golden probability tests для exact distribution и payout table. Не менять payout/weights только по желанию сделать RTP «более стандартным».

## Проверки на staging / test account

1. До ставки, при валидном slot, forged `OCCUPY_SLOT` с отрицательным/большим ID, вне casino и с координатами за пределами казино; сверить slot reservation, session, position, dimension и клиентские объекты.
2. Для Spin loss и win: получить `client.spin.SPIN` и вызвать `server.spin.LEAVE_SLOT` до 600 ms, сразу после reveal, на границе двух секунд и позже; проверить один debit/refund/payout, PlayerData, slot state, logs и reconnect.
3. `money=0`, negative, 1, CEF min/max, выше `$10,000`, near-`Int32` overflow, insufficient funds, injected `Wallet.Change=false`, repeated/concurrent remote bet; проверить rewards/quests и wallet/state consistency.
4. Автоматизированный тест distribution: 343 exact paths, selected category, payout multiplier, computed RTP; отдельно проверить идентичный UI paytable и решение владельца по RNG.
5. Crash/restart/timeout до и после bet debit, outcome reveal и payout; определить, теряется ли in-memory unsettled bet или возможен повторный payout.

## Границы

Выводы относятся к статическому клиент/server flow. CAS-008/009/010 не исправлены; CAS-011 — расчёт для подтверждения, не security defect сам по себе. Не запускались build, RAGE runtime, casino client, persistent wallet DB или regression tests.
