using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Database;
using LinqToDB;
using Redage.SDK;

namespace NeptuneEvo.Database.Models
{
    public class Money
    {
        private static readonly nLog Log = new nLog("Database.Money");
        private static readonly object QueueLock = new object();

        public static void Start()
        {
            var thread = new Thread(Worker);
            thread.IsBackground = true;
            thread.Name = "MoneySave";
            thread.Start();
        }

        private static async void Worker()
        {
            while (true)
            {
                List<object[]> donateBatch = new List<object[]>();
                List<object[]> moneyBatch = new List<object[]>();

                try
                {
                    // Snapshot and clear are atomic with respect to all producers.
                    lock (QueueLock)
                    {
                        donateBatch = DonateUpdateList.Values.ToList();
                        DonateUpdateList.Clear();

                        moneyBatch = MoneyUpdateList.Values.ToList();
                        MoneyUpdateList.Clear();
                    }

                    if (donateBatch.Count > 0 || moneyBatch.Count > 0)
                    {
                        await using var db = new ServerBD("MainDB");

                        if (donateBatch.Count > 0 && !await DonateUpdate(db, donateBatch))
                            RequeueDonate(donateBatch);

                        if (moneyBatch.Count > 0 && !await MoneyUpdate(db, moneyBatch))
                            RequeueMoney(moneyBatch);
                    }
                }
                catch (Exception e)
                {
                    Log.Write($"LogsWorker Exception: {e}");
                    // A failed connection/context creation must not discard the detached batches.
                    RequeueDonate(donateBatch);
                    RequeueMoney(moneyBatch);
                }

                Thread.Sleep(1000);
            }
        }

        private static readonly Dictionary<string, object[]> DonateUpdateList = new Dictionary<string, object[]>();

        public static void AddDonateUpdate(string login, int amount)
        {
            if (string.IsNullOrWhiteSpace(login))
                return;

            lock (QueueLock)
            {
                DonateUpdateList[login] = new object[] { login, amount };
            }
        }

        private static void RequeueDonate(List<object[]> batch)
        {
            if (batch == null || batch.Count == 0)
                return;

            lock (QueueLock)
            {
                foreach (var saveData in batch)
                {
                    var login = saveData[0].ToString();
                    // Preserve a newer value queued while this batch was being written.
                    if (!DonateUpdateList.ContainsKey(login))
                        DonateUpdateList[login] = saveData;
                }
            }
        }

        private static async Task<bool> DonateUpdate(ServerBD db, List<object[]> donateUpdateList)
        {
            try
            {
                foreach (var saveData in donateUpdateList)
                {
                    var affectedRows = await db.Accounts
                        .Where(v => v.Login == saveData[0].ToString())
                        .Set(v => v.Redbucks, Convert.ToInt32(saveData[1]))
                        .UpdateAsync();

                    if (affectedRows != 1)
                    {
                        Log.Write($"DonateUpdate: expected one account row for '{saveData[0]}', affected {affectedRows}");
                        return false;
                    }
                }

                return true;
            }
            catch (Exception e)
            {
                Log.Write($"DonateUpdate Exception: {e}");
                return false;
            }
        }

        private static readonly Dictionary<int, object[]> MoneyUpdateList = new Dictionary<int, object[]>();

        public static void AddMoneyUpdate(int uuid, long amount)
        {
            lock (QueueLock)
            {
                MoneyUpdateList[uuid] = new object[] { uuid, amount };
            }
        }

        private static void RequeueMoney(List<object[]> batch)
        {
            if (batch == null || batch.Count == 0)
                return;

            lock (QueueLock)
            {
                foreach (var saveData in batch)
                {
                    var uuid = Convert.ToInt32(saveData[0]);
                    // Preserve a newer absolute balance queued while this batch was being written.
                    if (!MoneyUpdateList.ContainsKey(uuid))
                        MoneyUpdateList[uuid] = saveData;
                }
            }
        }

        private static async Task<bool> MoneyUpdate(ServerBD db, List<object[]> moneyUpdateList)
        {
            try
            {
                foreach (var saveData in moneyUpdateList)
                {
                    var affectedRows = await db.Characters
                        .Where(v => v.Uuid == Convert.ToInt32(saveData[0]))
                        .Set(v => v.Money, Convert.ToInt32(saveData[1]))
                        .UpdateAsync();

                    if (affectedRows != 1)
                    {
                        Log.Write($"MoneyUpdate: expected one character row for UUID {saveData[0]}, affected {affectedRows}");
                        return false;
                    }
                }

                return true;
            }
            catch (Exception e)
            {
                Log.Write($"MoneyUpdate Exception: {e}");
                return false;
            }
        }
    }
}