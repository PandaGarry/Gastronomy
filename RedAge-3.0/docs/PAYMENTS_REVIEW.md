# Статический review выдачи доната и подтверждения покупок

Проверены `MoneySystem/Donations.cs` и `MoneySystem/DonatePack.cs`. Это анализ исходников, без доступов к платёжной системе/production DB и без runtime-проверки. Значения секретов не выводились и не сохранялись в отчёте.

## PAY-001 — обработка платежей не идемпотентна и не атомарна между двумя БД

**Уверенность: высокая; приоритет: критичный для платёжных начислений.**

`Donations.Start` запускает периодический `System.Threading.Timer`; `Tick` читает незакрытые строки `completed` из donation DB. Для каждой строки сначала происходят promo/пакетные побочные эффекты и начисление RedBucks или другой награды в основной БД/кэше, а только после них удаляется запись из donation DB.

Между payment DB и основной DB нет общей транзакции, durable processed-payment ledger или idempotency key. Ошибки `MySQL.Query` поглощаются helper-ом, но `Tick` продолжает обработку и удаляет payment row. Следствия:

- если награда применена, а процесс падает/удаление не удалось до завершения — row будет прочитан снова и награда может начислиться повторно;
- если основная DB-операция не прошла, но helper скрывает ошибку, payment row всё равно удаляется — платёж может остаться без награды;
- `CheckPromoDonate` также вызывается до удаления row, обновляет агрегаты промокода/стримера без ключа платежа и может повторить эти побочные эффекты;
- два экземпляра сервера с одним `ServerNumber` или перекрывающиеся `Tick` могут прочитать одну и ту же строку до её удаления. В методе не найдено claim/lease/lock или singleton guard.
- сумма из внешней таблицы читается как `long`, затем местами приводится к `int`; явный общий positive/range validation до promo/award path не обнаружен.

**Исправление (не внедрено):** durable payment inbox/ledger в основной БД с unique key (server + provider transaction ID); атомарная DB transaction, которая сначала вставляет receipt с уникальным ограничением и применяет единственную награду; повторный receipt возвращает уже обработанный результат без повторной выдачи. Отмечать/удалять source row только после подтверждённого commit. Проверять affected rows, currency/range, product mapping и результат всех helper-операций. Promo reward также deduplicate по тому же receipt ID. Добавить crash-point, DB outage, overlap и multi-instance tests.

## PAY-002 — периодический payment worker использует shared state из background timer

**Уверенность: высокая по потоку выполнения; runtime последствия требуют проверки на используемой версии RAGE:MP. Приоритет: высокий.**

`System.Threading.Timer` вызывает `Tick` на thread-pool потоке; параллельно remote handlers и игровые callbacks работают с player/session state. В ходе `Tick` вызываются `GetPlayerToLogin`, account/player accessors и `UpdateData.RedBucks`. RAGE API thread affinity нужно подтвердить по runtime-документации/тесту.

`DonatePack.PacksBuy` — общий `List<PackBuy>` без lock; `ConfirmDonate` меняет её из remote-event path, а `IsDonate`/`DeleteTime` читают и удаляют записи из других путей. Одновременные `FirstOrDefault`/`Remove`/`Add` могут дать race, потерю/дублирование intent либо коллекционное исключение.

**Исправление (не внедрено):** timer должен только читать/claim-ить DB receipt и класть работу в контролируемую очередь; game-thread actions dispatch-ить через поддержанный RAGE механизм. Защитить обработчик от overlap, а pending pack intent хранить в thread-safe transactional state (или синхронизировать единым lock, если latency/масштаб это допускают). Тестировать reconnect, slow DB и одновременные callbacks.

## PAY-003 — DonatePack intent не валидирует ID и живёт только в RAM

**Уверенность: высокая; приоритет: средний.**

- Remote `ConfirmDonate(player, id)` кладёт переданный клиентом `id` в `PacksBuy` без проверки диапазона `Packs`.
- При подходящей сумме `IsDonate` делает `Packs[packBuy.Id]` до проверки диапазона. Некорректный клиентский ID приводит к исключению при обработке его payment row; row остаётся в completed и может повторно падать до истечения intent.
- `Open(player, id)` также индексирует `Packs[id]` без range check.
- Pending intent — только память процесса и действует 30 минут. Перезапуск/задержка внешнего платежа может потерять связь между покупкой набора и receipt; сумма затем может обработаться как обычное пополнение.
- `IsDonate` удаляет intent до завершения `Confirm`/выдачи premium; нет durable state, позволяющего однозначно восстановить продукт после исключения/рестарта.

**Исправление (не внедрено):** allowlist product ID из server config; проверка диапазона во всех входах; persisted purchase intent/receipt correlation, TTL с определённой политикой и одноразовое consume только внутри транзакционной выдачи. Не считать сам вызов `ConfirmDonate` доказательством оплаты.

## Проверки на изолированном staging

- остановить процесс после award commit, но до source-row acknowledgement; повторная обработка должна дать ровно одну награду;
- имитировать отказ основной DB, promo DB и delete/ack step по отдельности; receipt не должен теряться или начисляться дважды;
- запускать два worker-а/экземпляра на одной строке; ровно один ledger/award;
- повторный webhook/payment row с тем же provider transaction ID; повторно не выдавать RedBucks/premium/promo rewards;
- прислать invalid/negative/overflow amount и недопустимый DonatePack ID; никакой выдачи, exception storm или вечного блокирования платежа;
- перезапустить сервер между подтверждением набора, поступлением receipt и выдачей; восстановить исходный выбранный продукт;
- проверить thread-affinity player/NAPI calls и конкурентные ConfirmDonate/IsDonate/DeleteTime.
