Below is a ready-to-run “starter kit” that continues the work we began: a single FastMCP server exposing five multimodal utilities, each able to switch automatically between a cloud API and a
local fallback.

The code follows the best-practice memo you just received, uses only publicly documented 2025-07-01 APIs, and is split into small, easily testable modules.

Directory layout
```
multimodal_mcp/
├── __init__.py
├── config.py          # env + feature flags
├── core.py            # FastMCP instance
├── tools/
│   ├── ocr.py         # Mistral OCR   | Tesseract fallback
│   ├── stt.py         # OpenAI Whisper| Whisper-cpp fallback
│   ├── search.py      # Tavily search
│   ├── convert.py     # Pandoc / unoconv
│   └── embed.py       # Jina embeddings | local model
└── main.py            # `python -m multimodal_mcp`
```

Install (uv or pip)
```bash
uv init multimodal-mcp        # or poetry/pip
uv add "mcp[cli]" httpx pydantic[tuned] python-dotenv
uv add tesserocr pypandoc jinaai tavily==0.9.2  # runtime deps
# optional local models
uv add whisper-cpp-cffi sentence-transformers  # if you want local fallbacks
```

config.py
```python
import os
from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # cloud keys
    mistral_api_key: str | None = Field(None, env="MISTRAL_API_KEY")
    tavily_api_key: str | None = Field(None, env="TAVILY_API_KEY")
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY")
    jina_api_key: str | None = Field(None, env="JINA_API_KEY")

    # feature flags
    use_local_ocr: bool = Field(False, env="USE_LOCAL_OCR")
    use_local_stt: bool = Field(False, env="USE_LOCAL_STT")
    use_local_embed: bool = Field(False, env="USE_LOCAL_EMBED")

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # cached singleton
```

core.py
```python
from mcp.server.fastmcp import FastMCP
from .config import get_settings

settings = get_settings()

mcp = FastMCP(
    "Multimodal Utilities",
    description="OCR · STT · Web search · Document conversion · Embeddings",
    dependencies=[
        "httpx", "tesserocr", "pypandoc", "jinaai", "tavily"
    ],
    stateless_http=True,          # scale-out friendly
)
```

tools/ocr.py
```python
import io, asyncio, httpx, os, subprocess, tempfile, tesserocr, PIL.Image as Image
from pydantic import BaseModel
from mcp.server.fastmcp import Context
from ..core import mcp, settings


class OCRParams(BaseModel):
    url: str | None = None
    data: bytes | None = None       # raw image/PDF bytes
    model: str = "Focus"            # Mistral default


@mcp.tool(title="OCR", description="Extract text from images or PDF files")
async def run_ocr(params: OCRParams, ctx: Context) -> str:
    """Tries Mistral OCR first, falls back to Tesseract."""
    if not params.url and not params.data:
        return "Either url or data is required."

    if not settings.use_local_ocr and settings.mistral_api_key:
        try:
            from mistralai import Mistral
            await ctx.info("Using Mistral OCR")
            async with Mistral(api_key=settings.mistral_api_key) as client:
                res = await client.ocr.process(
                    model=params.model,
                    document={"url": params.url, "type": "document_url"}
                )
            return res["text"]
        except Exception as e:
            await ctx.warn(f"Mistral OCR failed: {e}. Falling back to Tesseract")

    # -------- local fallback ----------
    await ctx.info("Running local Tesseract")
    if params.url:
        async with httpx.AsyncClient() as cl:
            params.data = (await cl.get(params.url)).content

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(params.data)
        tmp.flush()
        text = tesserocr.file_to_text(tmp.name)
    return text.strip()
```

tools/stt.py
```python
import httpx, os, tempfile, subprocess, json, asyncio
from pydantic import BaseModel
from mcp.server.fastmcp import Context
from ..core import mcp, settings


class STTParams(BaseModel):
    url: str | None = None
    data: bytes | None = None
    language: str | None = None


@mcp.tool(title="Speech-to-Text", description="Transcribe audio")
async def speech_to_text(params: STTParams, ctx: Context) -> str:
    if not params.url and not params.data:
        return "Provide url or data."

    if not settings.use_local_stt and settings.openai_api_key:
        await ctx.info("Using OpenAI Whisper API")
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        files = {"file": params.data or (await httpx.AsyncClient().get(params.url)).content}
        data = {"model": "whisper-1", "language": params.language}
        async with httpx.AsyncClient() as cl:
            r = await cl.post("https://api.openai.com/v1/audio/transcriptions",
                              headers=headers, data=data, files=files, timeout=60)
        r.raise_for_status()
        return r.json()["text"]

    # ---- local whisper-cpp fallback ----
    await ctx.info("Using local whisper-cpp")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(params.data or (await httpx.AsyncClient().get(params.url)).content)
        tmp.flush()
        # assume whisper.cpp model present in ./models/ggml-base.en.bin
        result = subprocess.check_output([
            "whisper-cpp", "-m", "models/ggml-base.en.bin", "-f", tmp.name,
            "-of", "json", "-l", params.language or "en"
        ], text=True)
        j = json.loads(result)
        return " ".join(seg["text"] for seg in j["segments"])
```

tools/search.py
```python
from pydantic import BaseModel
import httpx, textwrap
from ..core import mcp, settings
from mcp.server.fastmcp import Context


class SearchParams(BaseModel):
    query: str
    max_results: int = 3


@mcp.tool(title="Web Search", description="Tavily current-web search")
async def web_search(params: SearchParams, ctx: Context) -> str:
    if not settings.tavily_api_key:
        return "TAVILY_API_KEY missing."

    payload = {
        "api_key": settings.tavily_api_key,
        "query": params.query,
        "max_results": params.max_results,
        "include_answer": True,
        "include_raw_content": False
    }
    async with httpx.AsyncClient(timeout=10) as cl:
        r = await cl.post("https://api.tavily.com/search", json=payload)
    r.raise_for_status()
    data = r.json()
    lines = []
    if answer := data.get("answer"):
        lines.append(f"Answer: {answer}")
    for i, res in enumerate(data.get("results", [])[: params.max_results], 1):
        snippet = textwrap.shorten(res["content"], 150)
        lines.append(f"{i}. {res['title']} – {snippet}\n{res['url']}")
    return "\n\n".join(lines)
```

tools/convert.py
```python
import pypandoc, tempfile, httpx, os
from pydantic import BaseModel
from ..core import mcp
from mcp.server.fastmcp import Context


class ConvertParams(BaseModel):
    url: str | None = None
    data: bytes | None = None
    from_format: str | None = None
    to_format: str = "markdown"


@mcp.tool(title="Convert Document", description="Use Pandoc to convert between markup formats")
async def convert_doc(params: ConvertParams, ctx: Context) -> str:
    if not params.url and not params.data:
        return "Provide url or data"
    if params.url:
        async with httpx.AsyncClient() as cl:
            params.data = (await cl.get(params.url)).content
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(params.data); tmp.flush()
        out = pypandoc.convert_file(tmp.name,
                                    to=params.to_format,
                                    format=params.from_format)
    return out[:4000]  # truncate to 4 kB
```

tools/embed.py
```python
from pydantic import BaseModel
from typing import List
import httpx, numpy as np, json, os
from ..core import mcp, settings
from mcp.server.fastmcp import Context


class EmbedParams(BaseModel):
    texts: List[str]


@mcp.tool(title="Embeddings", description="Get sentence embeddings")
async def embed_text(params: EmbedParams, ctx: Context) -> list[list[float]]:
    if not params.texts:
        return []
    # cloud first
    if not settings.use_local_embed and settings.jina_api_key:
        async with httpx.AsyncClient() as cl:
            r = await cl.post(
                "https://api.jina.ai/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.jina_api_key}"},
                json={"model": "jina-embeddings-v2-base-en", "input": params.texts},
            )
        r.raise_for_status()
        return r.json()["data"]
    # -------- local fallback -----------
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(params.texts).tolist()
```

main.py
```python
from .core import mcp

if __name__ == "__main__":
    # Single entry-point
    mcp.run(transport="streamable-http", port=int(os.getenv("PORT", 8080)))
```

Usage
```bash
# .env   (example)
MISTRAL_API_KEY=sk-mistral...
TAVILY_API_KEY=tvly_...
OPENAI_API_KEY=sk-openai...
JINA_API_KEY=jina_...

# override to force local fallbacks
export USE_LOCAL_OCR=true
export USE_LOCAL_STT=true

# dev
uv run mcp dev -v .env -m multimodal_mcp.main
```

Quick client smoke-test
```bash
curl -X POST http://localhost:8080/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"params":{"query":"Claude 4 release date","max_results":2}}'
```
