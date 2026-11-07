# Player document remote and BattlePass task 101 — статический review

Обновлено: 2026-11-07. Scope: passport remote, request/accept flow and `UpdateReward(..., 101)`. Статический анализ; direct remote payload не воспроизводился в RAGE runtime.

## PROG-008 — passport can be offered to self to complete the “show passport” task

**Статус: открыт; низкий/средний приоритет; прямой source path подтверждён, remote entity marshalling требует staging check.** Условие: task ID 101 присутствует в активном day/week list или mission.

Evidence:

- Client normal UI sends `mp.events.callRemote('passport', global.entity)` (`src_client/player/circle.js:591-596`). Серверный `[RemoteEvent("passport")]` принимает target как `ExtPlayer` и вызывает `DocsFunction(player, target, passport)` (`GUI/Docs.cs:130-141`). Target берётся из remote payload; self-target check отсутствует.
- `DocsFunction` проверяет обе character/session state и `player.Position.DistanceTo(target.Position) <= 2`, проверяет незанятый request slot и устанавливает request в **target session** (`GUI/Docs.cs:55-90`). При `target == player` эти условия выполняются для того же игрока; valid request указывает `From = player`, срок — 10 секунд.
- `Main.RemoteEvent_acceptPressed` принимает remote без аргументов, проверяет character, active request и timeout, устанавливает `IsRequested = false` и dispatch-ит `Docs.AcceptPasport` для `acceptPass` (`Main.cs:2253-2325`). Это позволяет тому же игроку принять собственный server-created request.
- `AcceptPasport` читает request `From`, очищает request state, проверяет наличие character и снова проверяет лишь `DistanceTo <= 2`; равенство player/From не запрещено (`GUI/Docs.cs:154-199`). Затем `UpdateReward(from, 101)` вызывается после выдачи passport payload (`:186-194`).
- Текущий Season4 task 101 — «Показать паспорт кому-нибудь», count 1 (`BattlePass/Season4Models/Repository.cs`, соответствующая запись); `BattlePass.Repository.UpdateReward` увеличивает совпавший активный task count на один (`BattlePass/Repository.cs:596-635`).

Следствие: клиент, если RAGE remote marshaller сопоставляет отправленный self entity с серверным `ExtPlayer` argument (обычный формат такого event call, но в этой среде не проверялось), может вызвать `passport(self)`, затем `acceptPressed`, чтобы выполнить task 101 без второго персонажа. Request один раз принимается и сбрасывается, но нет cooldown, запрещающего повторять цикл. Не доказано, что это доступно без активного task ID; не заявляется прямое получение BattlePass prizes — лишь обход условия/наращивание progression.

**Исправление (не внедрено):** reject `target == player` сервером для документов, требующих предъявления другому игроку; при согласованной gameplay policy валидировать dimension вместе с дистанцией в обеих фазах. Сохранять one-shot request/expiry и проверять связь requestor/recipient при accept. Нельзя полагаться на CEF/client target picker.

**Regression:** на test character вызвать remote passport с собой target-ом, затем `acceptPressed`; task 101 должен остаться без изменений, request slot очищен и UI не выдаёт self-document. Контроль: два разных персонажа на <=2m и в одном измерении успешно завершают request один раз; duplicate accept/expired request/перемещение/смена dimension не дают progress. Проверить event arg marshalling на RAGE staging.

## Checked paths with no separate finding

Для разных игроков `DocsFunction` и `AcceptPasport` повторно проверяют расстояние по `Position`, запрос expires через 10 секунд, а generic `acceptPressed` отказывает без active request/после timeout и сбрасывает `IsRequested` до dispatch. Это закрывает простой повторный accept на том же request; dimension не входит в дистанционную проверку и требует policy/staging confirmation.
