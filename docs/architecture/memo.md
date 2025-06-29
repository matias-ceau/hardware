Good-Practice Memo
Subject: Building and Maintaining MCP-Based Multimodal Context Servers
Date: 01 Jul 2025
To: Core Engineering Team
From: Architecture & Enablement

────────────────────────────────────────
1. Purpose
Provide a concise, implementation-ready checklist of best practices for our upcoming Model
Context Protocol (MCP) servers that orchestrate multimodal tools (OCR, STT, web search,
conversion, embeddings, etc.). Adopt these guidelines for all new code and refactors.

2. High-Level Architecture
• One FastMCP server per bounded context (e.g. “Multimodal Utilities”).
• Each capability is exposed as an MCP **tool**; static artifacts (e.g. model manifests) are
**resources**; reusable wording is a **prompt**.
• Prefer **Streamable HTTP transport** (stateless when possible) for scale; fall back to SSE
only for legacy clients.
• Keep remote and local tool implementations side-by-side behind a thin strategy layer that
chooses the path at runtime based on:
  – `USE_LOCAL_*` env flags
  – Presence of model files on disk
  – Availability of API keys.

3. Repository & Packaging
• Use `uv` for dependency pinning (`uv init`, `uv add "mcp[cli]"`).
• All runtime deps declared in `pyproject.toml`; build-only/dev-only deps under `[tool.uv.dev-
dependencies]`.
• Enforce `ruff + mypy` in pre-commit; targets must be type-clean.

4. Tool Design Principles
✓ **Async first** (`async def`) – leverages FastMCP’s async runtime and avoids blocking.
✓ **Typed params & returns** – wrap inputs in a Pydantic model and choose an explicit, JSON-
serialisable return type (Pydantic, TypedDict, dataclass or primitive).
✓ **Concise output** – keep overall string < 4 kB; if raw data is larger, return a presigned
URL or store to resource and return its URI.
✓ **Progress & logs** – inject `Context` and call `await ctx.info()/ctx.report_progress()` for
long tasks.
✓ **Elicitation** – use `await ctx.elicit()` for optional user confirmation (e.g., destructive
actions).
✓ **Structured Output** – supply `outputSchema` implicitly via the return annotation; only
suppress with `structured_output=False` when absolut­­ely required for backward compatibility.

Example skeleton
```python
class OCRParams(BaseModel):
    url: str | None = Field(None, description="Document URL")
    file_path: str | None = Field(None, description="Local file")
    model: str = "Focus"

class OCRResult(BaseModel):
    text: str
    language: str | None = None

@mcp.tool(title="OCR", description="Extract text from images or PDFs")
async def run_ocr(params: OCRParams, ctx: Context) -> OCRResult:
    ...
```

5. Resource Patterns
• Use URI templates (`resource://{namespace}/{id}`) for dynamic resources.
• Keep resource handlers **side-effect free**; treat them like GET endpoints.
• Provide titles & descriptions for discoverability; use `get_display_name()` on the client
side.

6. Authentication & Secrets
• All external APIs require tokens in env; never hard-code.
• For protected downstream data, implement `TokenVerifier` and attach
`auth=AuthSettings(...)`.
• MCP servers may themselves expose optional OAuth scopes (`mcp:read`, `mcp:write`).

7. Transport & Deployment
• Default: `mcp.run(transport="streamable-http", stateless_http=True, port=$PORT)`
• Use ASGI mounts when embedding multiple servers into one FastAPI app.
• For local desktop workflows (e.g. Claude Desktop), still support `mcp install server.py`.

8. Error Handling & Resilience
• Wrap external calls (`httpx`) with `response.raise_for_status()` and catch
`httpx.TimeoutException`.
• Return user-friendly errors; log stack traces via `ctx.error()` for observability.
• Implement retries (exponential back-off) for transient HTTP 5xx.

9. Output Size & Privacy Controls
• Truncate or summarise large outputs; optionally store full artefacts in S3/minio and return a
signed link.
• Strip PII from logs unless explicitly whitelisted.
• Honour **EU-only data path** when `EU_COMPLIANCE=true`.

10. Local vs Remote Tooling Checklist
OCR  → Remote: Mistral OCR; Local: Tesseract + pdfimages
STT  → Remote: OpenAI Whisper; Local: Gemma3n or Whisper cpp
Embed → Remote: Jina AI Embeddings; Local: text-embeddings-ada
Convert → pandoc for markup → markdown; fallback to unoconv for office docs

Encapsulate each backend behind the same Pydantic I/O models so callers remain agnostic.

11. Testing & CI
• Unit-test every tool with `pytest-asyncio`; mock external APIs with `respx`.
• Contract-test MCP schema compliance: start the server, call `/list_tools`, validate JSON
Schema of each tool.
• Smoke test container image with `docker run` + health-check calling `/__health`.

12. Observability
• Use MCP’s built-in logging routed to stdout in JSON; ingest via Grafana Loki.
• Add `ctx.report_progress()` for long (>2 s) tasks; UI will surface spinners.
• Capture tool latency and success/error counts via Prometheus exporter.

13. Compliance & Security
• Enable streamable-HTTP “stateless” mode to avoid storing user data server-side unless
needed.
• For EU workloads, deploy only in region-locked infra and set `EU_COMPLIANCE=true`; verify
storage buckets are in-region.
• Perform regular dependency scanning (`pip-audit`, `safety`).

14. Next Steps / Action Items
1. Scaffold `multimodal_server` repo with the above layout.
2. Implement baseline tools: `web_search`, `ocr`, `stt`, `convert`, `embed`.
3. Wire automated GitHub Actions workflow (lint → type-check → test → build image → push to
registry).
4. Draft internal docs & example client notebooks.
5. Schedule security review before first production deploy.

Please ensure all new code reviews validate against this checklist. Reach out to @architecture-
team for clarifications.

────────────────────────────────────────
