# Статический review roulette/case remote flows

Область: `Chars/Events.cs` (`server.roullete.buy/open`), `Chars/Repository.cs` (`RouletteBuyCase`, `RouletteOpenCase`, `RouletteCreate`, `RouletteGetWallet`, `RouletteUpdateWallet`, `RemoveIndex`), `Chars/Donate.cs` (`GetPrice`, `UpdatePrice`) и CEF case purchase selector. Review этой подсистемы частичный; остальные gambling/casino handlers ещё не проверены.

## MONEY-006 — отрицательное количество в покупке кейсов зачисляло RedBucks

**Уверенность: высокая по коду; приоритет: критичный для донатной валюты.**

До локальной правки `RouletteBuyCase` принимал `count` из remote event без положительной границы. При `caseData.Price > 0` отрицательное `count` давало отрицательную сумму: `RouletteGetWallet` проверял `RedBucks < amount`, что для отрицательного amount не блокировало вызов; затем `RouletteUpdateWallet` получал `-(Price * count)`, то есть положительное значение, и `Donate.UpdatePrice` передавал его в `UpdateData.RedBucks` как начисление. До проверки/выдачи кейсов пользователь уже мог получить валюту. Переполнение unchecked `int` при очень большом положительном `count` могло создать тот же отрицательный total-price path. CEF UI скрывает этот путь, но `server.roullete.buy` принимает client-originated аргументы напрямую.

**Локальная mitigation внесена, но не собрана и не проверена в runtime:**

- `RouletteBuyCase` теперь проверяет диапазон `caseid`, принимает только `1..100` кейсов (максимум 100 совпадает с selector UI), отвергает неположительную цену и вычисляет total через `checked` до любых wallet side effects.
- `RouletteGetWallet` дополнительно отвергает отрицательную сумму.
- Расчёт discount/payment сохранён через существующие `Donate.GetPrice` и `Donate.UpdatePrice`; семантика скидки/доната намеренно не перепроектировалась.

## INV-007 — отрицательное количество открываемых кейсов дублировало предмет

**Уверенность: высокая по коду; приоритет: критичный для игрового имущества.**

До локальной правки `RouletteOpenCase` проверял только `count > aItem.Item.Count`; отрицательное количество проходило. `RouletteCreate` делал ноль итераций для отрицательного `count` и возвращал пустой список, после чего `RemoveIndex` выполнял `_Item.Count -= count`. Вычитание отрицательного значения увеличивало количество кейсов в inventory; далее remote flow запускал пустое открытие и начислял BattlePass reward. Удалённый клиент мог повторять вызов.

**Локальная mitigation внесена, но не собрана и не проверена в runtime:** `RouletteOpenCase` отвергает `count < 1` до изменения состояния; `RouletteCreate` защищён повторной проверкой; общая `RemoveIndex` теперь игнорирует `count <= 0`, чтобы отрицательный аргумент нигде не превращался в добавление предметов. Нижняя граница `caseid` также проверяется в buy/open.

## Проверки на staging

1. `server.roullete.buy`: `count = int.MinValue, -1, 0, 1, 100, 101, int.MaxValue`; для отклонённых запросов сравнить RedBucks, unique/discount state, inventory, warehouse и audit/persistence до/после. Валидные 1 и 100 проверить с обычным и first-purchase discount.
2. Проверить отрицательные и граничные `caseid` в обоих remote handlers; ни исключений с мутацией, ни изменения session/item/wallet state.
3. `server.roullete.open`: `count = int.MinValue, -1, 0, 1, owned-count, owned-count + 1`; отрицательные/нулевые не меняют item count, BattlePass, roulette session или DB rows; корректное открытие списывает ровно `count` кейсов.
4. Прямо проверить `RemoveIndex` с `count <= 0` на stack и non-stack items: полный no-op; проверить штатные вызовы с положительным count, включая расход материалов/патронов.
5. Инъецировать сбой `AddNewItem`/warehouse/database после покупки: проверить, не возникает ли debit-without-grant. Этот отдельный consistency path остаётся открытым и требует transactional/idempotent design.
6. Только test DB/test account; сверить кэш, DB item rows, RedBucks и BattlePass state после reconnect/restart.

## Ограничения проверки

Статический data-flow подтверждает исходный путь по коду; эксплуатационный тест не выполнен. .NET SDK, test DB и RAGE:MP runtime недоступны в текущем окружении. Изменения остаются unverified и не считаются закрытыми; баланс и цены не менялись.
