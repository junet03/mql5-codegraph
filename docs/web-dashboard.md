# Local Web Dashboard

The dashboard is a same-origin local application over the canonical MQL5 CodeGraph engine. It does
not upload source, require an account, or replace the deterministic JSON/CLI contracts.

## Start

```powershell
mql5-codegraph serve --root C:\work\Example-MQL5
```

Useful options:

- `--include-root <path>` adds an MQL5 include lookup root.
- `--graph <graph.json>` opens a saved graph; add an explicit `--root` to enable source viewing.
- `--port 0` requests an available loopback port.
- `--no-browser` starts without opening the default browser.
- `--host` accepts only loopback addresses. Remote exposure is not a supported dashboard mode.

Repository and include roots are authorized only by these startup arguments. The browser displays them
read-only, and changing either path requires restarting the process.

## Product workflow

1. Start the process with a source root and optional MetaTrader include root.
2. Analyze or re-index. A failed re-index retains the last valid graph.
3. Search for a symbol or inspect the repository projection.
4. Select nodes to view evidence, incoming/outgoing relationships, context, and upstream impact.
5. Filter diagnostics and open the exact source line in the protected viewer.

The browser receives at most 2,000 nodes per projection while the Python process retains the complete
canonical graph. This separates analysis scale from visualization scale.

## Security boundary

- The default listener is loopback-only and emits no permissive CORS headers.
- Non-loopback binds and non-loopback `Host` authorities are rejected. Browser `Origin` requests must target
  the same loopback port.
- Request bodies are limited to 64 KiB.
- Request reads have a two-second idle timeout and a ten-second absolute deadline, so a slow-drip client
  cannot retain a finite request slot indefinitely.
- HTTP requests cannot add or change the startup-authorized repository and include roots.
- Source reads select only indexed `.mq5` and `.mqh` files from the active graph, then re-resolve and
  recheck containment, type, and size at request time.
- Saved graph metadata is not trusted to select that source root. Loading `--graph` without an explicit
  `--root` leaves intelligence available but disables the source viewer.
- Source viewer files are capped at 2 MiB.
- Static responses include CSP, same-origin resource, referrer, and content-type protections.

The server has no authentication because it is not a network service. Any future remote or multi-user
deployment requires a separately designed authenticated adapter or trusted reverse proxy boundary.

## Frontend development

Run the Python dashboard API on port `8765`, then:

```powershell
cd web
npm run dev
```

The Vite development server proxies `/api` to the local Python server. Production builds are emitted
to `src/mql5_codegraph/web_static/` for the CLI server.
