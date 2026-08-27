import { readdir, readFile } from "node:fs/promises";
import { join, relative } from "node:path";

const roots = ["apps", "packages", "services/ai-worker/src", "scripts"];
const ignored = new Set(["node_modules", ".next", "dist", ".venv"]);
const extensions = new Set([".js", ".mjs", ".ts", ".py"]);

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (ignored.has(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(path)));
    else if (extensions.has(path.slice(path.lastIndexOf(".")))) files.push(path);
  }
  return files;
}

const files = (await Promise.all(roots.map(walk))).flat();
const violations = [];
for (const file of files) {
  const text = await readFile(file, "utf8");
  if (text.includes("\r")) violations.push(`${relative(process.cwd(), file)}: CRLF`);
  if (!text.endsWith("\n")) violations.push(`${relative(process.cwd(), file)}: missing final newline`);
}

if (violations.length) {
  console.error(violations.join("\n"));
  process.exitCode = 1;
} else {
  console.log(`lint_smoke_ok files=${files.length}`);
}
