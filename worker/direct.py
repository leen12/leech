"""
Model runner -> OpenAI-compatible AI gateways (Puter + NVIDIA NIM).

Each model names its provider (see config.MODELS). One API token per provider
authenticates every request (Bearer). No account signup, no browser, no proxies.
  puter -> https://puter.com/dashboard#account -> Create token  (env PUTER_AUTH_TOKEN)
  nim   -> https://build.nvidia.com -> API key                  (env NVIDIA_API_KEY)

Public surface (unchanged so leech.py / agent.py keep working):
  enabled()                              -> is a gateway backend usable?
  stream(model, prompt=|messages=)       -> async generator of text deltas
  complete(model, prompt=|messages=)     -> full reply string

Per request:
  POST {provider base_url}/chat/completions
  Authorization: Bearer <provider token>
  body: {"model": "<raw id>", "messages": [{role, content}], "stream": true}
  SSE reply: `data: {choices:[{delta:{content:"..."}}]}` ... `data: [DONE]`
"""
import json
import logging

import httpx

from . import config

log = logging.getLogger("direct")

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")

_PLACEHOLDERS = {"", "PUTER_TOKEN_PLACEHOLDER", "nvapi-PLACEHOLDER"}


def _route(model: str):
    """(provider, model_id, base_url, token) for a requested model name."""
    provider, model_id = config.resolve(model)
    base, token = config.provider_conf(provider)
    return provider, model_id, base.rstrip("/"), (token or "").strip()


def enabled() -> bool:
    """True if the gateway backend is on and at least one provider has a real
    (non-placeholder) token configured."""
    if not getattr(config, "PUTER_ENABLED", False):
        return False
    for prov in ("puter", "nim"):
        _, token = config.provider_conf(prov)
        if (token or "").strip() not in _PLACEHOLDERS:
            return True
    return False


def _to_messages(messages: list | None, prompt: str | None) -> list:
    """Normalize to OpenAI [{role, content}]. Empty turns dropped; a bare prompt
    becomes a single user turn; roles other than system/user/assistant -> user."""
    src = messages if messages else [{"role": "user", "content": prompt or ""}]
    out = []
    for m in src:
        content = (m.get("content") or "").strip()
        if not content:
            continue
        role = m.get("role")
        if role not in ("system", "user", "assistant"):
            role = "user"
        out.append({"role": role, "content": content})
    if not out:
        out.append({"role": "user", "content": prompt or ""})
    return out


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": _UA,
    }


def _delta_from(obj: dict) -> str:
    """Pull the text delta out of an OpenAI-style stream chunk."""
    try:
        choices = obj.get("choices") or []
        if not choices:
            return ""
        ch = choices[0]
        delta = ch.get("delta") or {}
        # streaming shape: choices[0].delta.content
        if isinstance(delta.get("content"), str):
            return delta["content"]
        # some gateways send the full message on the last chunk
        msg = ch.get("message") or {}
        if isinstance(msg.get("content"), str):
            return msg["content"]
    except Exception:
        pass
    return ""


async def stream(model: str, prompt: str | None = None,
                 messages: list | None = None, acct: dict | None = None):
    """Async generator of text deltas. `acct` is accepted and ignored (kept for
    signature compatibility with the old use.ai path)."""
    provider, model_id, base, token = _route(model)
    if not token or token in _PLACEHOLDERS:
        env = config._PROVIDER_ENV.get(provider, "?")
        raise RuntimeError(
            f"{provider} backend not configured: set {env} to a real token")

    body = {
        "model": model_id,
        "messages": _to_messages(messages, prompt),
        "stream": True,
    }
    url = base + "/chat/completions"
    idle = getattr(config, "PUTER_IDLE_TIMEOUT", 90)

    timeout = httpx.Timeout(connect=30.0, read=idle, write=30.0, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout) as c:
        async with c.stream("POST", url, headers=_headers(token), json=body) as r:
            if r.status_code != 200:
                text = (await r.aread()).decode("utf-8", "replace")[:500]
                raise RuntimeError(f"{provider} HTTP {r.status_code}: {text}")
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(f"{provider} error: {obj['error']}")
                d = _delta_from(obj)
                if d:
                    yield d


async def _nonstreaming(model: str, messages: list) -> str:
    """Fallback: non-streamed POST, return the whole content at once."""
    provider, model_id, base, token = _route(model)
    body = {"model": model_id, "messages": messages, "stream": False}
    url = base + "/chat/completions"
    async with httpx.AsyncClient(timeout=getattr(config, "PUTER_TIMEOUT", 300)) as c:
        r = await c.post(url, headers={"Authorization": f"Bearer {token}",
                                       "Content-Type": "application/json",
                                       "User-Agent": _UA}, json=body)
        r.raise_for_status()
        j = r.json()
        return (j.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


async def complete(model: str, prompt: str | None = None,
                   messages: list | None = None, acct: dict | None = None) -> str:
    """Buffered variant: collect the whole reply."""
    out = []
    try:
        async for d in stream(model, prompt=prompt, messages=messages):
            out.append(d)
    except Exception as e:
        # if streaming is unavailable, try one plain request before giving up
        log.warning("stream failed (%r) -> trying non-streaming", e)
        reply = await _nonstreaming(model, _to_messages(messages, prompt))
        if reply.strip():
            return reply.strip()
        raise
    reply = "".join(out).strip()
    if not reply:
        raise RuntimeError("empty reply")
    return reply
