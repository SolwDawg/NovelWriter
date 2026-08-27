import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { createDatabase } from "./client.js";

const migrationPath = fileURLToPath(
  new URL("./migrations/0001_initial.sql", import.meta.url),
);

const { pool } = createDatabase();
try {
  const migration = await readFile(migrationPath, "utf8");
  await pool.query(migration);
  console.log("database_migration_ok migration=0001_initial");
} finally {
  await pool.end();
}
