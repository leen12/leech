# leech

A small OpenAI-compatible gateway over the **use.ai** free web models, plus a
minimal file-editing **agent** that works reliably even on models that struggle
with tool calls.

It signs up throwaway accounts on demand (kept warm in a pool) and streams
replies over use.ai's WebSocket, so any of the current models are reachable
through a plain HTTP API.

## Run it

```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Then point any OpenAI SDK client at `http://localhost:8000/v1`. No API key is
needed.

## Models

The current use.ai catalog — GPT-5.6 (Sol / Terra / Luna), GPT-5.5, Claude Opus
4.6–4.8, Sonnet 5 / 4.6, Gemini 3.1 Pro / 3 Pro, DeepSeek V4 / R1, Grok 4 / 4.3,
Qwen, Kimi, Llama, GLM. See `worker/config.py` for the full list. Default:
`gpt-5-6-sol`.

## API

| endpoint | what it does |
|----------|--------------|
| `POST /v1/chat/completions` | OpenAI-compatible chat, streaming and non-streaming |
| `POST /agent` | run a file task in the workspace; returns `{"text", "events"}` |
| `POST /chat` | stateful chat (server keeps the history) |
| `POST /v1/chat` | stateless chat, simplified response shape |
| `GET /models` | list available model ids |
| `GET /health` | liveness |
| `GET /bank` | number of warm accounts in the pool |

## The agent

The agent runs inside a `workspace/` folder — set `LEECH_WORKDIR` to point it
somewhere else. Every path it touches is resolved and checked against that
folder, so it cannot read or write outside it.

It has twelve tools:

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

Just ask for what you want, in any language. There is no command syntax to
learn — the model decides which tool to use, so paraphrases and non-English
requests work the same as the phrasings a keyword matcher would have known.

Under the hood it tries three strategies, in order, so that weak models still
get the job done:

1. **Fast path** — a few unambiguous inputs (`ls`, a bare filename, `run
   pytest`) are handled by the app with no model call at all.
2. **Routing call** — one short call asks the model to pick a tool and answer
   in a single line, e.g. `edit_file path=config.py old_string=… new_string=…`.
   One line instead of JSON, because a flat line can't come back malformed —
   no nesting to balance, no escaping to get wrong. Chatter and code fences
   around the answer are tolerated.
3. **Tool loop** — anything else falls through to a normal tool-calling loop,
   with JSON repair and code-block harvesting as safety nets. Open-ended edits
   to a single file take a shortcut here: the model rewrites the whole file in
   one shot and the result is written back.

The routing call is grounded and checked. Its prompt carries the real workspace
listing, so the model can only name paths that exist, and the reply is validated
before anything runs: unknown tool, missing required argument, a `path` that
isn't an exact hit in the listing, or any path escaping the workspace is
rejected and falls through to step 3. The tool menu, the argument names and the
required-argument checks are all derived from the Python signatures in
`worker/tools.py`, so adding a tool there updates the prompt and the validator
automatically — and an unrecognised tool is validated strictly, not waved
through.

| variable | effect |
|----------|--------|
| `LEECH_WORKDIR` | where the agent works (default `workspace/`) |
| `LEECH_CLASSIFY=0` | skip step 2, fall back to the old keyword matcher |
| `LEECH_CLASSIFY_MODEL` | use a cheaper/faster model for the routing call only |

## Layout

```
backend/   FastAPI app + endpoints
worker/    use.ai gateway (direct.py), account pool, agent, tools, config
frontend/  optional chat UI (Vite)
```

## License

MIT — see [LICENSE](LICENSE).
