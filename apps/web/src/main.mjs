import http from "node:http";

const port = Number(process.env.WEB_PORT ?? 3000);

const server = http.createServer((request, response) => {
  if (request.url === "/health") {
    response.writeHead(200, { "content-type": "application/json" });
    response.end(JSON.stringify({ status: "ok", service: "web", version: "0.1.0" }));
    return;
  }

  response.writeHead(200, { "content-type": "text/plain; charset=utf-8" });
  response.end("NovelWriter web shell is ready.\n");
});

server.listen(port, () => {
  console.log(`[web] listening on http://localhost:${port}`);
});

process.once("SIGTERM", () => server.close());
process.once("SIGINT", () => server.close());
