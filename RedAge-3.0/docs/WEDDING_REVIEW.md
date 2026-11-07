# Wedding remote, consent and settlement review

Статус: статически прослежены `server.wedding.married` → generic `dialogCallback` → marriage/divorce settlement. **Исходники не менялись.** Live RAGE callbacks, wallet/DB fault injection и gameplay-policy confirmation не выполнялись.

## MONEY-010 — divorce fee списывается до проверки доступности spouse; callback exception не компенсирует списание

**Уверенность: высокая для TOCTOU control flow; приоритет: средний, потеря до `$300,000` при disconnect race.**

Когда character уже состоит в браке, `Wedding.OpenDialog` (`Quests/Wedding.cs:150–177`) получает spouse по `WeddingUUID`; если spouse online, но дальше 5m, создаёт `WeddingData { type = 2 }` с ценой `DivorcioOnePrice = 300_000`. Подтверждение идёт через `Main.RemoteEvent_DialogCallback`: case `Wedding` передаёт управление `Quests.Wedding.OnDivorcio(player, isOne: true)` (`Main.cs:2866–2900`).

В `OnDivorcio` (`Wedding.cs:267–319`) сервер проверяет собственный character/marriage и баланс, затем вызывает `Wallet.Change(player, -price)` и пишет log (около 278–281). **После списания** повторно резолвит spouse через `Main.GetPlayerByUUID` и сразу вызывает `target.GetCharacterData()` (около 283–286), не проверяя `target == null`. Если spouse disconnects после появления out-of-range divorce dialog, `GetPlayerByUUID` возвращает null; dereference бросает исключение. Исключение ловится общим `dialogCallback` catch (`Main.cs:3080–3083`), но нет rollback/compensation: payer уже дебетован, а `WeddingUUID/WeddingName` clear происходят ниже, поэтому remain married. Это редкий, но реальный failure window. Для spouse offline ещё до открытия dialog есть аналогичный null dereference в `OpenDialog` до установки session state (около 152–158); в этом случае подтверждение/списание не начинается.

**Remediation:** перед debit разрешить spouse/state и определить, допускается ли offline unilateral divorce; затем выполнять проверенный debit и unlink одним проверяемым operation/transaction либо durable pending/compensation. Проверять результат `Wallet.Change`; не оставлять исключение между debit и marriage-state commit. Guard null, stale UUID, target disconnect, changed spouse relation and duplicate callback.

**Regression:** spouse online >5m → открыть one-sided divorce prompt → disconnect spouse before confirm → confirm; ожидается либо корректный single unlink по documented offline policy, либо отказ без списания. Также spouse remains online; disconnect immediately before/after callback; insufficient balance/failed `Wallet.Change`; duplicate yes; reconnect and verify both online memory and durable DB `WeddingUUID/WeddingName`, wallet balance and exactly-once GameLog.

## WEDDING-001 — forged player name/id can hit null dereference before target validation

**Уверенность: высокая для null path; server-wide impact не проверен. Приоритет: низкий robustness.**

`[RemoteEvent("server.wedding.married")] OpenDialog` принимает client `name`, `typeSurname`; для unmarried инициator ищет target по ID/name, затем вызывает `target.GetCharacterData()` до null guard (`Wedding.cs:122–139`). Для married initiator в offline spouse case также dereferences null до проверки (`152–158`). Метод не имеет local try/catch. Invalid/stale target input therefore reaches an exception path; от этого не следует утверждать crash ресурса или server-wide DoS без RAGE runtime evidence.

**Remediation/tests:** validate parse/find result and session/character before member access; enforce `typeSurname` allowlist `{0,1,2}`; test invalid ID, unknown/ambiguous name, disconnect between lookup and character access, empty/oversized name, null-like RPC argument, and ensure handler is bounded/no repeated unhandled exceptions.

## Policy/consent items — не записаны как подтверждённые security bypasses

- `OpenDialog` не проверяет church proximity; `OnBoda` проверяет, что оба character single и players в пределах 5m, но не сверяет dimension/церковь. Target получает отдельный `Boda` dialog; фактический `OnBoda` не вызывается без target callback. Нужно подтвердить, обязателен ли church/текущая dimension по design.
- `WeddingData` хранится в session без явного expiration/nonce. При `yes=false` отдельный wedding cleanup case в `dialogCallback` не найден; stale session invitation может оставаться. Пока это не классифицировано как чужое принятие: callback может отправить только сам target, который тем самым снова подтверждает; проверить revoke/timeout/partner-consent semantics.
- `OnBoda` и `OnDivorcio` не проверяют return value `Wallet.Change`; после prior `CanIChange` проверка достаточности существует, но atomicity under concurrent money mutations / server stop не подтверждена. Долговременное exactly-once coupling wallet, marriage fields and logs не исследовано полностью.

## Ограничения

Нет RAGE runtime, concurrent callback test, disposable database или server compiler. `MONEY-010` остаётся открытым до воспроизводимой disconnect/failure test; `WEDDING-001` — low-priority robustness observation. Не патчить marriage pricing/consent policy без owner confirmation.
