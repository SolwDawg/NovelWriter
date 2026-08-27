console.log("[workflow-worker] startup shell ready; Temporal workflows are not registered yet");

const keepAlive = setInterval(() => {}, 60_000);
const shutdown = () => {
  clearInterval(keepAlive);
  process.exit(0);
};

process.once("SIGTERM", shutdown);
process.once("SIGINT", shutdown);
