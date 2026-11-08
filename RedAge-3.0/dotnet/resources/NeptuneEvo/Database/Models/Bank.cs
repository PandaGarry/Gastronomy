using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Threading;
using Database;
using LinqToDB;
using Redage.SDK;

namespace NeptuneEvo.Database.Models
{
    public class Bank
    {
        private static readonly nLog Log = new nLog("Database.GameLog");
                
        public static void Start()
        {
            var thread = new Thread(Worker);
            thread.IsBackground = true;
            thread.Name = "BankSave";
            thread.Start();
        }
        private static async void Worker()
        {
            while (true)
            {
                var pendingDeletes = new List<int>();
                try
                {
                    var banks = MoneySystem.Bank.GetDirtyAccountIds();

                    while (DellList.TryDequeue(out int deletedBankId))
                        pendingDeletes.Add(deletedBankId);

                    if (banks.Count > 0 || pendingDeletes.Count > 0)
                    {
                        await using var db = new ServerBD("MainDB");

                        foreach (var bankId in banks)
                            await MoneySystem.Bank.Save(db, bankId);

                        foreach (var bankId in pendingDeletes)
                        {
                            try
                            {
                                await db.Money
                                    .Where(m => m.Id == bankId)
                                    .DeleteAsync();
                            }
                            catch (Exception e)
                            {
                                // DELETE is idempotent; retry failed entries on the next worker pass.
                                DellList.Enqueue(bankId);
                                Debugs.Repository.Exception(e);
                            }
                        }
                    }
                }
                catch (Exception e)
                {
                    // The connection may fail before the delete batch is processed. Requeueing
                    // already-deleted IDs is safe because deleting a missing row is idempotent.
                    foreach (var bankId in pendingDeletes)
                        DellList.Enqueue(bankId);
                    Debugs.Repository.Exception(e);
                }

                Thread.Sleep(1000 * 30);
            }
        }

        // Concurrent queue prevents account removals racing with the background worker.
        private static readonly ConcurrentQueue<int> DellList = new ConcurrentQueue<int>();

        public static void OnDell(int id) => DellList.Enqueue(id);

    }
}