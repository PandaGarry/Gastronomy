# Quest remote and progression review

Статус: частичный статический проход по generic quest remotes в `Quests/qMain.cs`, отдельным pickup/mission remotes в Granny и Defender of the Fatherland Day (Dada/Edward), BattlePass hooks и client bridge `src_client/player/npc_dialogs.js`. **Исходники не менялись.** C# build, DB/RAGE tests и live remote calls не выполнялись. Не все quest modules/endpoints прослежены; это не полный аудит Quests/Achievements.

## PROG-002 — `server.quest.clear` начисляет task 97 без активного разговора

**Уверенность: высокая по прямому control flow; приоритет: средний для progression integrity.**

`Quests/qMain.cs:165–173`: remote handler проверяет только `player.IsCharacterData()`, затем без `GetQuest()`/null check вызывает `BattlePass.Repository.UpdateReward(player, 97)` и только после этого `player.ClearQuest()`. В Season4 catalog task 97 — «Поговорить с любым квестовым персонажем», count 1, 500 XP (`BattlePass/Season4Models/Repository.cs:88`). `UpdateReward` продвигает matching unfinished daily/week task и matching selected mission (если задача активна), без знания о реальном NPC interaction. `server.quest.clear` — клиентский remote; штатный UI вызывает его при закрытии, но сервер не требует UI/NPC session.

Следовательно, authenticated character может вызвать remote напрямую даже при `GetQuest()==null` и засчитать task 97, если она назначена в его активной daily/week/mission slots. Награда/прогресс для данного task capped `Count=1`; не утверждается бесконечная XP выдача из-за spam.

**Remediation:** проверять и извлекать конкретную server-owned active quest/dialog token до progress update; начислять task только на законном открытии/завершении подходящего interaction; завершать/погашать token exactly once. Отсутствующая/повторная session — no-op. Не начислять до precondition guard.

**Regression:** прямой `server.quest.clear` без `GetQuest`, повторный clear, clear после реального UI close, forged event после movement/disconnect/reconnect; проверять `GetQuest`, active BP daily/week/mission count, XP, уведомления и идемпотентность. Без валидного server interaction прогресс неизменен.

## INV-008 — `server.take_quest_item` создаёт Bear без quest/location/pickup validation

**Уверенность: высокая по item-grant path; ценность/торгуемость предмета отдельно не подтверждены. Приоритет: средний.**

`Quests/ValentineDay/Granny.cs:178–222`: `[RemoteEvent("server.take_quest_item")]` принимает client `int index`. Guards проверяют `SessionData`, character, `AntiAnimDown`, admin/demorgan и свободный inventory slot; server-side active `npc_granny` quest/line, ожидаемый pickup index, расстояние, dimension или server-owned pickup state не проверяются. После `Main.OnAntiAnim` ставится 5-секундный callback; он проверяет только что персонаж ещё есть и есть место, затем вызывает `AddNewItem(..., ItemId.Bear, 1)`, увеличивает client index и записывает его в quest data. Источник вызова — `src_client/player/main.js` от `global.selectBear`, который устанавливается локальным client colshape в `npc_dialogs.js`; это не server authority. `AntiAnimDown` ограничивает параллельные вызовы до окончания callback, но не подтверждает pickup; повторные вызовы после снятия flag по-прежнему могут выдавать предмет.

Серверный `ItemId.Bear` имеет item definition в `Chars/Repository.cs` и используется как условие/расходник в Granny quest. Поэтому remote гарантированно injects quest items и позволяет обходить предусмотренный сбор предметов; дальнейшая денежная/торговая ценность здесь не доказана. Отдельная несогласованность: `Granny.Open` помечает Bear step complete при `>=5` Bear, но `Granny.Get` переходит дальше и удаляет всего 2 (`Granny.cs:78–86, 163–173`); intended quantity надо подтвердить.

**Remediation:** держать pickup quest state/index на сервере и проверять нужный активный quest line, уникальный незабранный pickup, актуальные server position/dimension/interaction radius и cooldown; сначала commit единственного pickup, затем grant. Client `index` — только hint, не источник истины. Не выдавать новый предмет на повтор/replay или если quest stage не тот.

**Regression:** событие без quest, с quest в другой line, любой index включая negative/large, удалённый pickup, неправильная dimension, быстрый repeat/parallel, teleport/disconnect во время 5-секундного callback, inventory full, DB/item insert failure; verify at-most-once item, quest progress and cache/DB consistency. Проверить legitimate collection и назначенную цель count 2 vs 5.

## PROG-003 — Dada/Edward objective callbacks позволяют подделать `Complete`

**Уверенность: высокая для подмены флага; downstream progression/reward effect не доказан. Приоритет: низкий/средний.**

Dada remote `server.update.npc_dfday_mission` (`Quests/defenderFatherlandDay/Dada.cs:145–158`) принимает событие без параметров и вызывает `UpdateQuestsComplete(player, "npc_fd_dada", Boat, true)`. Helper в `qMain.cs:447–464` проверяет лишь наличие сохранённой строки actor/line; он не проверяет ремонт лодки, активную interaction, distance, dimension или server-side progress. Edward `server.update.npc_fd_edward` (`Edward.cs:127–141`) аналогично ставит `npc_fd_edward/Docs` complete без server-side подтверждения пяти document pickups; client считает прогресс локально.

Authenticated player может вызвать эти public remotes напрямую, когда существует соответствующая quest row; это ставит `Complete=true` в in-memory quest state без доказательства цели. Однако `UpdateQuestsComplete` меняет только boolean. Проверка references ниже показала, что этот флаг сам по себе не вызывает награду или line transition; такое следствие отдельно не утверждается.

**Remediation:** хранить ремонт/pickup count и objective completion в server-owned state; проверять line, phase, location/dimension и уникальную цель на каждом переходе. Client callback — только подсказка, не доказательство.

**Regression:** `update` remote без quest/wrong quest line/на удалении/повторно; проверять, что `Complete` меняется только после валидного server-owned objective. Подтвердить по design, какие line/reward transitions зависят от этого флага.

## BUG-001 — Dada/Edward quest action methods не связаны с generic remotes

**Уверенность: высокая по call graph; приоритет: средний, functional progression bug, требуется gameplay-owner confirmation.**

Client `npc_dialogs.js` отправляет `server.quest.perform`/`server.quest.take` из quest UI для всех NPC. `qMain.QuestPerform` dispatch table (`qMain.cs:36–83`) не содержит actor cases `npc_fd_dada` или `npc_fd_edward`; `qMain.QuestTake` (`qMain.cs:84–141`) также не содержит этих cases. В полном source reference scan не найдено вызовов `Dada.Perform/Take` или `Edward.Perform/Take` вне их собственных declarations. Между тем Dada/Edward modules содержат эти методы и ожидаемые переходы (`Dada.Get/Take`, `Edward.Get/Take`) для boat repair, documents и следующего quest actor. Поэтому normal generic dialogue actions, судя по checkout, не доходят до соответствующих handlers; `QuestTake` может очистить активную quest session/обновить generic status, не выполняя actor action. Нужна проверка intended gameplay/внешних runtime hooks, но source-only code path не соединён.

Это отдельная functional gap от `PROG-003`: прямой update remote может пометить completion, однако доказанного valid turn-in/reward transition здесь нет.

**Remediation/tests:** подтвердить желаемые диалоговые действия; добавить actor-specific dispatch с server-side validation (не просто вызов `Get` по client flag). На staging пройти Dada Start → Tools → Boat → Edward Docs и Edward → Zak, выполнить legitimate objective и fail/forged/early `perform`/`take`; проверять строки, `Complete`, flags, UI, rewards и отсутствие double-transition. Провести source reference/call graph scan повторно после изменения.

## PROG-004 — admin SkipQuest обновляет progression команды на вызывающем admin, не target

**Уверенность: высокая по аргументу helper; приоритет: низкий, admin-only correctness bug.**

В `Quests/qMain.cs:708–734` command `SkipQuest(player, id)` находит и изменяет `questData` из `targetCharacterData.QuestsData` (`target`), но передаёт **`player` (admin)** в `UpdateQuestsStage` и `UpdateQuestsComplete`. В результате target получает только непосредственные `Status=1`/`Complete=true`; stage/HUD helper effects (если совпадает quest row) применяются к admin, а не target. В сценарии когда у admin есть тот же actor/line, может измениться его собственная stage state. Это не client privilege escalation: command gated через `CommandsAccess.CanUseCmd`.

**Remediation/tests:** передавать target в обе helper calls; на staging проверить admin/target с одинаковыми и различными quest rows, HUD/state, invalid ID и target disconnect. Кроме того, `target.GetCharacterData()` вызывается до null-check target, поэтому несуществующий player ID идёт в exception path; обработать `target == null` до dereference.

## Другие проверенные границы / незакрытые вопросы

- `server.quest.perform`, `take` и `action` требуют server-side `GetQuest()!=null`; `take` ветвит по server-stored ActorName, а PetShop/Police индексы имеют switch cases. Но blanket `Complete`/proximity/current-interaction validation отсутствует; отдельно изучены Dada/Edward примеры выше. Остальные actor-specific `Perform/Take` methods остаются в coverage queue.
- `server.quest.selectQuest` принимает произвольную строку и сохраняет её в `CharacterData.SelectedQuest` (`qMain.cs:699–706`); здесь найдено только клиентское изменение selected marker/admin skip selector. Length/null/persistence behavior (DB field `varchar(42)`) требует отдельного boundary test; exploitability/DB effect не утверждается.
- `Wedding.OpenDialog` (`Wedding.cs:111–195`) делает `target.GetCharacterData()` до null-check target (строки 133, 157): invalid player name/ID способен привести к exception path; метод не содержит локального try/catch. Это отмечено как robustness test, не как подтверждённый remote crash/DoS. На стадии фактического брака `OnBoda` проверяет взаимную дистанцию/состояния и target consent dialog; дальнейшая policy не подтверждалась.
- Quest save/load, all other quest modules, every actor handler and achievement endpoints не покрыты этим проходом. Не считать Quest/Progression область завершённой.

## Общие проверки до закрытия

1. Для каждого remote/event проверить actor/session state, active line/phase, server distance/dimension, caller/target ownership, type/range, cooldown/replay, and authoritative completion.
2. В DB/RAGE staging проверить objective sequence, forged/reordered/repeated remotes, callbacks after movement/disconnect, retries, partial item grant and quest save/reload.
3. Сверить intended Granny bear count, Dada boat repair and Edward pickup rules с владельцем gameplay; не менять rewards/quest design без policy approval.
4. Для `UpdateReward` producer map продолжить trace remaining callsites; completion/remotes не объявлять закрытыми только на основании статического source review.
