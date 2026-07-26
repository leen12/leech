"""
Live connectivity + reply self-test for both gateway providers.

Run:  python -m worker.selftest
Set real tokens first to get actual replies:
    Windows PowerShell:  $env:PUTER_AUTH_TOKEN="..."; $env:NVIDIA_API_KEY="nvapi-..."
    bash:                export PUTER_AUTH_TOKEN=... NVIDIA_API_KEY=nvapi-...

With placeholder tokens it still hits the real endpoints and reports the HTTP
status (a 401/403 confirms the URL + request shape are correct; you just need a
real key). With real tokens it prints the model's actual reply.
"""
import asyncio

import httpx

from . import config, direct

PROMPT = "Reply with exactly: pong"

# one free/default model per provider
TARGETS = [
    ("puter", "puter:openai/gpt-5.4-nano"),
    ("nim",   "nim:meta/llama-3.1-8b-instruct"),
]


async def _probe(provider: str, slug: str) -> None:
    prov, model_id, base, token = direct._route(slug)
    masked = (token[:6] + "..." + token[-4:]) if len(token) > 12 else token
    placeholder = token in direct._PLACEHOLDERS
    print(f"\n=== {provider}  ({model_id}) ===")
    print(f"  endpoint : {base}/chat/completions")
    print(f"  token    : {masked}  {'(PLACEHOLDER - set the env var for a real reply)' if placeholder else '(real)'}")

    body = {"model": model_id,
            "messages": [{"role": "user", "content": PROMPT}],
            "stream": False, "max_tokens": 32}
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{base}/chat/completions",
                             headers={"Authorization": f"Bearer {token}",
                                      "Content-Type": "application/json"},
                             json=body)
        print(f"  HTTP     : {r.status_code}")
        if r.status_code == 200:
            j = r.json()
            reply = (j.get("choices") or [{}])[0].get("message", {}).get("content", "")
            print(f"  REPLY    : {reply!r}")
            print("  RESULT   : OK - got a real reply")
        elif r.status_code in (401, 403):
            print(f"  body     : {r.text[:200]}")
            print("  RESULT   : endpoint reachable + request well-formed; auth "
                  "rejected (expected with a placeholder token)")
        else:
            print(f"  body     : {r.text[:300]}")
            print("  RESULT   : unexpected status - see body above")
    except Exception as e:
        print(f"  RESULT   : request failed: {type(e).__name__}: {e}")


async def _stream_probe(provider: str, slug: str) -> None:
    """Only meaningful with a real token; shows streaming works end-to-end."""
    prov, model_id, base, token = direct._route(slug)
    if token in direct._PLACEHOLDERS:
        return
    print(f"  stream   : ", end="", flush=True)
    try:
        got = []
        async for d in direct.stream(slug, prompt=PROMPT):
            got.append(d)
        print(repr("".join(got))[:120], "-> OK" if got else "-> empty")
    except Exception as e:
        print(f"stream failed: {type(e).__name__}: {e}")


async def main() -> None:
    print("Gateway self-test (Puter + NVIDIA NIM)")
    print("enabled():", direct.enabled())
    for provider, slug in TARGETS:
        await _probe(provider, slug)
        await _stream_probe(provider, slug)


if __name__ == "__main__":
    asyncio.run(main())
