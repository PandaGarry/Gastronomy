# Legacy `/dice` remote-flow review

Статус: статический review, не runtime verification. Проверены `/dice`, pair state (`DiceData`), generic dialog callback `DICE_PLAY`, `AcceptDice`, `Wallet.Change` и BattlePass task mapping. Исходники не менялись.

## Поток и границы

`CMD_dice` разрешает player ID и сумму, затем вызывает `callDice`. Предложение проверяет начальное расстояние `<=2`, range `Main.MinDice..Main.MaxDice`, уровень обоих игроков `>=5`, `InCasino`, наличие другой casino game, доступный баланс и наличие текущего Dice offer. Целевая сторона принимает через общий remote `dialogCallback("DICE_PLAY", true)`; сервер достаёт сумму и opponent из её session-bound `DiceData`, затем `AcceptDice` проверяет ссылки на пару, средства, casino markers и актуальные суммы в обоих DiceData перед settlement.

## CAS-020 — неатомарный wager settlement игнорирует ошибки Wallet

**Уверенность: высокая по коду; приоритет: высокий для целостности денег. Runtime/race не воспроизводились.**

В `Core/Commands.cs` (`AcceptDice`, примерно 6630–6647) победителю сначала вызывается `Wallet.Change(winner, +price)`, затем проигравшему `Wallet.Change(loser, -price)`. Оба `bool` результата игнорируются; GameLog и success/loss notifications выполняются как будто обе операции прошли. `MoneySystem/Wallet.cs` (`Change`, около 20–44) возвращает `false`, если расчёт `int temp = (int)characterData.Money + amount` отрицателен или debit не разрешён при shutdown.

Воспроизводимый по арифметике edge case: если баланс победителя находится у верхнего signed-int диапазона, начисление ставки может переполниться/дать отрицательный `temp` и вернуть `false`, после чего debit проигравшего всё равно выполнится. Обратный порядок/конкурирующее изменение баланса также допускает debit без credit либо credit без debit. Лог/уведомления при этом могут не соответствовать фактическим кошелькам.

**Remediation:** серверный wager escrow/ledger с атомарным reserve обеих сторон и exactly-once settlement; checked balance arithmetic и подтверждённые операции до уведомления/logging. Не менять денежную семантику без владельца экономики.

**Проверки:** forced winner-credit failure у лимита int; loser balance меняется между validation и debit; failure/shutdown; tie then win; assert оба баланса и durable money records в сумме соответствуют ровно одному проигрышу/выигрышу; никаких false success logs.

## CAS-021 — acceptance не повторяет ряд offer-time eligibility checks

**Уверенность: высокая по коду; приоритет: средний/высокий, если proximity/state restrictions задуманы как инварианты.**

`callDice` проверяет расстояние, level и cuff/death только на инициаторе и только в момент отправки offer (примерно 6687–6713). В `Main.RemoteEvent_DialogCallback`/`AcceptDice` на принятии повторно проверяются баланс, casino flags/markers и пара, но не расстояние между игроками, level, cuff/death и актуальные `MinDice/MaxDice`. Поэтому после получения offer игроки могут разойтись/перейти в cuff/death state, а старое предложение остаётся принимаемым, пока оба `CharacterData.InCasino` остаются true.

**Remediation:** подтвердить intended rules; повторно проверять серверные proximity, alive/cuffed, level, casino location/session и configured wager limits непосредственно перед reserve/roll. Использовать expiry/nonce для предложения и очищать его при изменении eligibility.

**Проверки:** переместить участников после offer; cuff/death одного участника; изменить min/max пока offer открыт; stale/replayed callback; валидное принятие в пределах разрешённого радиуса.

## CAS-022 — self-target допускает игру без оппонента и чистого риска

**Уверенность: высокая по flow; приоритет: низкий/средний, policy-dependent.**

`CMD_dice` передаёт `Main.GetPlayerByID(id)` в `callDice`; явного `target == player` rejection нет. При собственном ID session pair указывает на одного игрока. Для обычного ненулевого баланса две операции `+price` и `-price` применяются к тому же кошельку последовательно и имеют net zero. Затем `AcceptDice` вызывает `BattlePass.Repository.UpdateReward(player, 102)` и `UpdateReward(target, 102)` для того же персонажа. В Season4 task 102 — «Кинуть кости в казино (/dice)», count 1; выполнение может закрыть это задание без второго игрока и без чистого wager loss.

Это не даёт повторно завершать одноразовую задачу: `UpdateReward` помечает её done. Вопрос — должен ли `/dice` требовать отдельного оппонента/реального риска.

**Remediation:** если это не задумано, отвергать self-target и подтверждать distinct character UUID непосредственно перед settlement.

**Проверки:** self ID rejected/no state or wallet mutation; два разных игрока сохраняют штатный BattlePass progress и settlement; прогресс не начисляется при неуспешном settlement.

## CAS-023 — ничья реализована неограниченной рекурсией

**Уверенность: высокая по коду; приоритет: низкий (robustness).**

`AcceptDice` генерирует значения через `Main.rnd.Next(2, 13)` и при равенстве вызывает себя рекурсивно (`Commands.cs` около 6618–6627). Новые броски происходят до окончательного не-ничейного результата; нет итеративного цикла/лимита попыток. Для двух независимых равномерных результатов вероятность одной ничьей за попытку — `1/11`; глубокая рекурсия очень маловероятна, но теоретически может закончиться stack exhaustion и нарушить server process. BattlePass calls стоят после recursive call и идут при каждом unwind, однако task 102 имеет count 1 и отмечается завершённым при первом эффективном вызове, поэтому duplicate task completion здесь не подтверждён.

**Remediation:** заменить recursion на bounded/iterative reroll loop, ограничить/логировать число повторов и гарантировать единый cleanup/settlement.

**Проверки:** deterministic RNG test с серией ничьих и затем win; максимальная серия; единственный settlement, один итоговый game-result и корректная очистка DiceData.

## Ограничения

Выводы сделаны статически по checkout; C# compilation, тестовая БД и RAGE runtime отсутствуют. Вопросы proximity, self-play и минимального/максимального wager требуют подтверждения gameplay policy. Никакие изменения не внесены; findings не закрыты.
