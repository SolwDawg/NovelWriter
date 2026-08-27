import type { NodePgDatabase } from "drizzle-orm/node-postgres";
import type { databaseSchema } from "./schema.js";

export type TransactionContext = NodePgDatabase<typeof databaseSchema>;

export interface UnitOfWork {
  transaction<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T>;
}

export class DrizzleUnitOfWork implements UnitOfWork {
  constructor(private readonly db: TransactionContext) {}

  transaction<T>(fn: (tx: TransactionContext) => Promise<T>): Promise<T> {
    return this.db.transaction(async (tx) => fn(tx as unknown as TransactionContext));
  }
}
