# leech

A small OpenAI-compatible gateway over hosted **AI gateways** (Puter + NVIDIA
NIM), plus a minimal file-editing **agent** that works reliably even on models
that struggle with tool calls.

Each request goes straight to a provider's OpenAI-compatible endpoint with a
single API token — no account signup, no browser, no proxies.

## Providers & setup

Set the token for whichever provider(s) you want (env var preferred):

| provider | endpoint | get a token | env var |
|----------|----------|-------------|---------|
| **Puter** | `api.puter.com/puterai/openai/v1` | [puter.com/dashboard#account](https://puter.com/dashboard#account) → Create token | `PUTER_AUTH_TOKEN` |
| **NVIDIA NIM** | `integrate.api.nvidia.com/v1` | [build.nvidia.com](https://build.nvidia.com) → API key (free) | `NVIDIA_API_KEY` |

```bash
# PowerShell
$env:PUTER_AUTH_TOKEN="..."; $env:NVIDIA_API_KEY="nvapi-..."
# bash
export PUTER_AUTH_TOKEN=... NVIDIA_API_KEY=nvapi-...
```

Verify both providers actually respond:

```bash
python -m worker.selftest
```

(With no token it still hits the live endpoints and reports a `401/403` — proof
the wiring is correct; add a real token to get an actual reply.)

## Models

Each model in `worker/config.py` names its provider. Puter: GPT-5.6 (Sol / Terra
/ Luna), GPT-5.5 / 5.4-nano, Claude Opus 5 / 4.8, Sonnet 5, Gemini 3.5/3.6,
DeepSeek V4, Grok 4.5, Qwen. NVIDIA NIM (free): Llama 3.3 70B, Llama 3.1 8B,
Nemotron 70B, DeepSeek R1, Qwen2.5 Coder 32B. Default: `puter:openai/gpt-5.6-sol`.
Model ids are `provider:model` (e.g. `nim:meta/llama-3.3-70b-instruct`).

## The agent's tools

The agent runs in a `workspace/` folder (override with `LEECH_WORKDIR`) and has
six file tools:

| tool | what it does |
|------|--------------|
| `read_file`   | read a file (with line numbers) |
| `write_file`  | create or overwrite a file |
| `append_file` | add to the end of a file |
| `edit_file`   | replace exact text (fuzzy-tolerant) |
| `delete_file` | delete a file or folder |
| `list_dir`    | list the workspace as a tree |
| `grep_search` | search file contents (regex), returns `file:line` matches |
| `move_file`   | move or rename a file/folder |
| `copy_file`   | copy a file/folder |
| `make_dir`    | create a directory |
| `glob_files`  | find files by name pattern (`**/*.py`) |
| `run_command` | run a shell command in the workspace, capture output |

Common phrasings run **deterministically** — the app performs the action itself
without the model emitting a tool call, so they work on every model:

- `read config.py`
- `create note.txt with 'hello'`
- `list files`
- `in config.py the port should be 8080`
- `in config.py replace HOST with localhost`
- `append the line beta to notes.txt`
- `delete old.log`
- `search for TODO in the project`
- `rename a.py to b.py`
- `make a directory src`
- `find files named config.json`
- `run npm test`

Freeform edits (`change the greeting to say Bob`) are applied by reading the
file, having the model rewrite it in one shot, and writing the result back —
which is far more reliable on the free gateway than asking the model to hand-write
a tool call. Anything else falls back to a normal tool loop (with JSON repair and
code-block harvesting as safety nets).

## Run it

```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## API

**Agent** — run a file task:

```bash
curl -X POST localhost:8000/agent \
  -H 'content-type: application/json' \
  -d '{"message": "in config.py the port should be 8080", "model": "puter:openai/gpt-5.6-sol"}'
```

Returns `{"text": "...", "events": [{"type": "tool", "name": "edit_file", ...}]}`.

**Chat** — OpenAI-compatible, drop-in for existing SDK clients:

```bash
curl -X POST localhost:8000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model": "nim:meta/llama-3.3-70b-instruct", "messages": [{"role": "user", "content": "hi"}]}'
```

Other endpoints: `GET /models`, `GET /health`, `GET /bank` (warm-account count),
`POST /chat` (stateful), `POST /v1/chat` (stateless).

## Layout

```
backend/   FastAPI app + endpoints
worker/    gateway client (direct.py), model routing/config, agent, tools, selftest
frontend/  optional chat UI (Vite)
```

## License

MIT — see [LICENSE](LICENSE).
