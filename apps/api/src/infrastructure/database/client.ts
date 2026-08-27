import { drizzle, type NodePgDatabase } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import { databaseSchema } from "./schema.js";

export type AppDatabase = NodePgDatabase<typeof databaseSchema>;

export interface DatabaseHandle {
  db: AppDatabase;
  pool: Pool;
}

export function createDatabase(connectionString = process.env.DATABASE_URL): DatabaseHandle {
  if (!connectionString) {
    throw new Error("DATABASE_URL is required to create the PostgreSQL client");
  }

  const pool = new Pool({ connectionString });
  return { db: drizzle(pool, { schema: databaseSchema }), pool };
}
