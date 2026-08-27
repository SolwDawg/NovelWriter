import http from "node:http";

const port = Number(process.env.API_PORT ?? 3001);

const server = http.createServer((request, response) => {
  if (request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ok", service: "api", version: "0.1.0" }));
    return;
  }

  response.writeHead(404, { "content-type": "application/json" });
  response.end(JSON.stringify({ error: "not_found" }));
});

server.listen(port, () => {
  console.log(`[api] listening on http://localhost:${port}`);
});

process.once("SIGTERM", () => server.close());
process.once("SIGINT", () => server.close());
