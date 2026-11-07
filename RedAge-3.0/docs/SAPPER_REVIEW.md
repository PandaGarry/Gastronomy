# Sapper mini-game remote-flow review

Статус: статический review `server.sapper.bet/end`, RedBucks helper, CEF minigame and BattlePass task hook. **В исходники не вносились изменения.** Live RB exploit, DB effects, C# compilation и RAGE runtime tests не выполнялись.

## MONEY-008 — отрицательная ставка напрямую начисляет RedBucks

**Уверенность: высокая по server-side arithmetic; приоритет: критичный для premium currency.**

`Chars/Repository.cs`, `SappeGame` (`[RemoteEvent("server.sapper.bet")]`, около 8404–8423) принимает signed `int amount`; проверяет только `SappeData != -1` и `accountData.RedBucks < amount`. Positive minimum/max guards нет. Затем делает `UpdateData.RedBucks(player, -amount, ...)` и сохраняет `amount` в session. `UpdateData.RedBucks` просто складывает `value` с account balance (около 25–38), не запрещая credit/debit по sign.

Для `amount=-100` balance check `RedBucks < -100` обычно ложен; `-amount` становится `+100`, что начисляет 100 RB. Session получает `SappeData=-100`; вызов `server.sapper.end(-2)` пропускает refund/payout branch и очищает состояние в `-1`, оставляя выданные RB. CEF ограничивает поле значениями `$10..$5,000`, но этот предел не проверяется server-side.

**Remediation:** positive, configured min/max stake validation на сервере; checked bounds и successful atomic debit перед записью активной game state. Не использовать client-supplied signed amount как арифметическую основу до validation.

**Проверки:** `amount=-1`, `-100`, `int.MinValue`, zero, ниже/на/выше server min/max, обычные positive bets, account balance на границах. Invalid request — no-op: balance/session/log unchanged. Проверить replay/concurrent bet and account cache/durable DB.

## MONEY-009 — клиент выбирает выигрышный множитель или refund проигрыша

**Уверенность: высокая по server/client data flow; приоритет: критичный для RedBucks.**

CEF `src_cef/src/views/donate/sapper/index.svelte` выполняет RNG через `Math.random()` и после хода отправляет client-side `type`; bridge `src_client/player/donatemenu.js` передаёт число в remote `server.sapper.end`. Server `SappeEnd` (`Chars/Repository.cs`, около 8441–8468) проверяет только наличие `SappeData != -1`, затем умножает stake на `SappeCoef[type - 1]` для `type` от 1 до 7. Нет authoritative board, revealed-slot count или proof of successful choices. Поэтому игрок с положительной ставкой `S` может отправить forged `type=7`: сервер кредитует `3S` после debit `S` (чистый прирост `2S`) независимо от реально раскрытых ячеек.

На проигрыше CEF штатно отправляет `type=-2`, что пропускает payout/refund. Но сервер трактует любые `type<=0`, кроме `-2`, как полный возврат ставки. Modified client может заменить проигрышный `-2` на `-1` и вернуть проигранную ставку. Active CEF exit также отправляет `-1`, но сервер не различает незавершённую игру/уже проигранную игру.

**Remediation:** RNG, mines, safe picks, progress and cash-out outcome must be server-owned. Для каждого round — unique server nonce/state, validate each selection/transition, then atomic exactly-once payout/refund. Client events только сообщают действие/selection; не принимать итоговый multiplier или win/loss. Disconnect/exit policy должна следовать server-owned commit state.

**Проверки:** после валидного bet вызвать `end` с каждым значением `-2,-1,0,1..7,8`, повторно/параллельно; попытаться подменить проигрыш на win/refund; закрыть UI/disconnect до и после каждого server-confirmed safe pick. Verify balance delta соответствует ровно одному server-derived outcome; неподтверждённые/повторные args — no-op.

## PROG-001 — Sapper завершение начисляет BattlePass progress до проверки активной игры

**Уверенность: высокая по порядку server code; приоритет: средний для progression integrity.**

В `SappeEnd` после account/session null checks вызывается `BattlePass.Repository.UpdateReward(player, 3)`, и только затем проверяется `if (sessionData.SappeData == -1) return;`. Активная Season4 task ID 3 — «Сыграть в сапера (F9)», count 1. Поэтому клиент может напрямую вызвать `server.sapper.end` без успешного wager/active game и засчитать это задание в текущий daily/weekly/mission track. Вызов count-limited после completion, но обходит требование сыграть.

**Remediation:** сначала проверить активную server-owned round/state и валидный однократный settlement; начислять task progress только после успешного завершения. Не обновлять progress перед early-return и settlement validation.

**Проверки:** `end` без bet с любым `type`; `end` после проигрыша/выигрыша и повторный `end`; неверный/истёкший round ID. Никакого progress без успешно завершённой партии; ровно один progress на один валидный результат.

## Границы

Выводы статические. Server-authoritative redesign, экономика и refund behavior не патчились. Все три findings остаются открыты до изолированных account/DB/RAGE regression tests.
