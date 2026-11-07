# Taxi meter, remote vehicle mileage and progression — статический review

Обновлено: 2026-11-07. Проверена цепочка client mileage accumulator → `server.vehicle.updateMileage` → Taxi fare → BattlePass task progress. Нет C# build, RAGE runtime, disposable DB или test accounts; выводы основаны на исходниках.

## MONEY-012 — forged client mileage can bill a taxi passenger for nonexistent distance

**Приоритет: средний; source path подтверждён.** Нужен активный taxi ride: водитель управляет taxi-work vehicle, passenger pointer был выставлен обычным серверным seating flow, и у passenger есть средства.

- `src_client/vehicle/mileage.js:13-20, 28-41` client сам суммирует скорость (`vehicle.getSpeed()`) и раз в 10 секунд отправляет `server.vehicle.updateMileage(vehicle.remoteId, this.centimeters)`. Это клиентский расчёт, а не server-measured delta.
- `dotnet/resources/NeptuneEvo/Core/VehicleSync.cs:327-360` remote проверяет character, что sender находится в vehicle с переданным ID, и наличие `VehicleLocalData`. Он без проверки диапазона/знака/частоты прибавляет client `centimeters` к `Centimeters`, вычисляет miles из того же значения, ограничивает каждое сообщение тремя miles и для taxi driver вызывает `TaxiPay`.
- `Players/Phone/Taxi/Orders/Repository.cs:209-215` устанавливает TaxiData driver/passenger pointers, когда пассажир садится в taxi. Exit cleanup есть на `:258-280`; этим finding не утверждается отсутствие требуемого ride state.
- `TaxiPay` (`:318-368`) получает fare из client-derived mileage: `$30` за mile, то есть до `$90` за каждое сообщение. Проверяет наличие средств через `CanIChange`, затем отображает сумму и выполняет `Wallet.Change(driver, +price)` и `Wallet.Change(passenger, -price)` без проверки результатов; нет server-side traveled-distance reconstruction или per-ride bill cap/rate gate в этих двух methods. Повторные поддельные remote calls во время ride могут начислять водителю реальные тарифные суммы и списывать их с passenger за неподтверждённую поездку.

**Рамки:** required active ride ограничивает сценарий; не доказано, что произвольный посторонний игрок может стать `TaxiData.Passager` без seat/ride flow. Зафиксирован client-controlled meter в доверенной server billing path, а не money mint: fee — transfer passenger→driver. Наличие общего remote anti-cheat за пределами обработчика не исследовано.

**Remediation (не внедрено):** не принимать денежный fare из client delta. Измерять server-side progression по авторитетным position/time snapshots, привязанным к текущему taxi vehicle и passenger; задавать допустимый speed/distance delta и ride total cap, не применять отрицательные/wrapped значения, ограничить cadence. Сначала атомарно/подтверждённо выполнить debit+credit per fare receipt; только затем продвигать quest/BattlePass и показывать новый fare. Завершать ride/intent одноразово.

## PROG-007 — the same forged taxi mileage advances passenger and driver BattlePass tasks

**Приоритет: средний; progression bypass следует из того же remote path.**

В `TaxiPay` до wallet mutations вызываются `UpdateReward(player, 59)`, `UpdateReward(target, 95)`, `UpdateReward(player, 2)` и `UpdateReward(player, 159)` (`Orders/Repository.cs:361-367`). Текущий Season4 catalog определяет соответствующие цели как 15, 10, 5 и 20 миль на taxi ride/в роли taxi passenger (`BattlePass/Season4Models/Repository.cs:16,58,87,118`). `BattlePass.Repository.UpdateReward` при каждом вызове увеличивает счётчик дневной/недельной задачи ровно на один (`BattlePass/Repository.cs:596-635`); server не подтверждает фактический маршрут в этой функции.

Поэтому после допустимого входа пассажира в taxi клиентский водитель может многократно прислать mileage updates на текущий vehicle ID без реального движения; каждая прошедшая `CanIChange` billing попытка вызывает те же четыре progress updates. Один forged update `centimeters=100000` проходит как один mile для fare, а счётчик progress наращивается на один; повторные calls могут удовлетворить соответствующие daily/weekly tasks, если нужные IDs присутствуют в активных списках, либо выбранную mission с совпадающим ID. Даже если последующий wallet operation откажет, progress уже изменён.

**Remediation:** progress выдавать только из одной server-owned fare/distance receipt после проверки реального distance increment и успешного завершения оплаты; task criteria считать по серверным distance totals, а не по числу client callbacks. Один receipt должен применяться ровно один раз к пассажиру и водителю.

## Regression / failure matrix

- Установить тестовый taxi ride и зафиксировать odometer, passenger/driver balances, quest/BattlePass counts.
- Forged calls для current `vehicleId`: `centimeters = 0`, `-1`, `99,999`, `100,000`, `300,000`, `int.MaxValue`; repeated calls быстрее клиентского 10s cadence; смена vehicle ID / sender outside vehicle / чужое авто.
- Контроль: только подтверждённое физическое движение в допустимой скорости повышает измеренный пробег и fare; нет charge/progress при stationary vehicle или сверхлимитном delta.
- Пассажир без средств, disconnect/exit during request, смена водителя/авто, повтор/параллельные callbacks; injected debit/credit failure и server restart. Сверить wallet caches, persistent balances, fare receipts, logs и `TasksDay`/`TasksWeek`/mission counters.
- Документировать допустимую тарифную policy и поведение при аварийном disconnect до изменения settlement.

## Границы

- Client file показывает штатный формат события, но modified-client и staging reproduction не выполнялись.
- Нужны C# build, disposable DB и RAGE staging; issue открыт и source code не менялся.
