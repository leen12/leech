"""
Central config for the leech worker.

MODEL BACKEND: this build talks to OpenAI-compatible AI gateways with a single
API token each -- no throwaway-account signup, no browser, no proxies. Two
providers are wired in:

  * puter -> https://api.puter.com/puterai/openai/v1  (token: PUTER_AUTH_TOKEN)
             get one at https://puter.com/dashboard#account -> Create token
  * nim   -> https://integrate.api.nvidia.com/v1       (key:   NVIDIA_API_KEY)
             free key at https://build.nvidia.com -> your profile -> API key

Each model in MODELS names its provider. Tokens are read from env vars first
(preferred -- keeps keys out of the repo), then the literal fallback below.
The old use.ai signup/harvester/browser machinery is left in the tree but is
OFF (DIRECT_WS_ENABLED / PROXY_TOR = False) and never touched on the hot path.
"""
import os

TARGET_URL = "https://use.ai"

# ---- Providers (OpenAI-compatible gateways) ---------------------------------
PUTER_ENABLED = True          # master switch: use the gateway backend (not use.ai)

PUTER_BASE_URL = "https://api.puter.com/puterai/openai/v1"
NIM_BASE_URL   = "https://integrate.api.nvidia.com/v1"

# Literal fallbacks. Leave as the placeholder and set the env var instead. A real
# key MUST NOT be committed to a public repo.
PUTER_API_TOKEN = "PUTER_TOKEN_PLACEHOLDER"     # or set env PUTER_AUTH_TOKEN
NIM_API_TOKEN   = "nvapi-PLACEHOLDER"           # or set env NVIDIA_API_KEY

# provider name -> (base_url, env-var-name, literal-fallback)
_PROVIDER_BASE    = {"puter": PUTER_BASE_URL, "nim": NIM_BASE_URL}
_PROVIDER_ENV     = {"puter": "PUTER_AUTH_TOKEN", "nim": "NVIDIA_API_KEY"}
_PROVIDER_LITERAL = {"puter": PUTER_API_TOKEN, "nim": NIM_API_TOKEN}


def provider_conf(name: str):
    """(base_url, token) for a provider. Token comes from the env var first, then
    the literal fallback in this file. Read fresh so env changes take effect."""
    base = _PROVIDER_BASE.get(name, PUTER_BASE_URL)
    token = os.environ.get(_PROVIDER_ENV.get(name, ""), "") or _PROVIDER_LITERAL.get(name, "")
    return base, token


PUTER_TIMEOUT   = 300          # seconds; upper bound for a full (streamed) reply
PUTER_IDLE_TIMEOUT = 90        # give up only if NO token arrives for this long

# ---- Browser behavior -------------------------------------------------------
HEADLESS = True              # spike.py flips this to False so you can watch
HUMANIZE = True              # cloakbrowser human-like mouse/keyboard/scroll
# GUEST_MODE: two ways to get a free message, both VERIFIED working:
#   False (recommended) = SIGN UP a throwaway account (instant, passwordless, no
#     verification). 1 free message PER ACCOUNT, unlimited accounts per IP, and
#     you bank a real harvestable token. This is the volume vector.
#   True = skip signup, use the anonymous guest's 1 free message (per guest
#     identity). Simpler but no token, and fewer messages per identity.
# NOTE: the cap is per-account/per-guest, NOT per-IP -> PROXIES ARE OPTIONAL.
GUEST_MODE = False
NAV_TIMEOUT_MS = 30_000
ACTION_TIMEOUT_MS = 15_000
RESPONSE_TIMEOUT_MS = 90_000  # how long to wait for the AI reply

# ---- Concurrency ------------------------------------------------------------
# Each browser is a full Chromium. Keep this modest or you'll OOM the box.
MAX_CONCURRENT_BROWSERS = 4

# ---- Email / password generation (must satisfy the site's email regex) ------
EMAIL_LOCAL_MIN = 8
EMAIL_LOCAL_MAX = 14
EMAIL_DOMAIN_MIN = 5
EMAIL_DOMAIN_MAX = 9
EMAIL_TLDS = ["com", "net", "org", "io", "co", "xyz"]
PASSWORD_LENGTH = 16
SIGNUP_MAX_RETRIES = 5        # reroll the email if "already in use"

# ---- Models -----------------------------------------------------------------
# Each entry: slug (UI/API id, "provider:model"), label (dropdown text + UI
# grouping by keyword), provider ("puter"|"nim"), model (raw id sent to the
# gateway). Puter ids verified against developer.puter.com/ai/models; NIM ids
# are free build.nvidia.com models. resolve()/resolve_model() map slug|alias.
DEFAULT_MODEL = "puter:openai/gpt-5.6-sol"

MODELS = [
    # --- Puter ---------------------------------------------------------------
    {"slug": "puter:openai/gpt-5.6-sol",    "label": "GPT-5.6 Sol",       "provider": "puter", "model": "openai/gpt-5.6-sol"},
    {"slug": "puter:openai/gpt-5.6-terra",  "label": "GPT-5.6 Terra",     "provider": "puter", "model": "openai/gpt-5.6-terra"},
    {"slug": "puter:openai/gpt-5.6-luna",   "label": "GPT-5.6 Luna",      "provider": "puter", "model": "openai/gpt-5.6-luna"},
    {"slug": "puter:openai/gpt-5.5",        "label": "GPT-5.5",           "provider": "puter", "model": "openai/gpt-5.5"},
    {"slug": "puter:openai/gpt-5.4-nano",   "label": "GPT-5.4 Nano",      "provider": "puter", "model": "openai/gpt-5.4-nano"},
    {"slug": "puter:anthropic/claude-opus-5",   "label": "Claude Opus 5",   "provider": "puter", "model": "anthropic/claude-opus-5"},
    {"slug": "puter:anthropic/claude-opus-4.8", "label": "Claude Opus 4.8", "provider": "puter", "model": "anthropic/claude-opus-4.8"},
    {"slug": "puter:anthropic/claude-sonnet-5", "label": "Claude Sonnet 5", "provider": "puter", "model": "anthropic/claude-sonnet-5"},
    {"slug": "puter:google/gemini-3.6-flash",   "label": "Gemini 3.6 Flash","provider": "puter", "model": "google/gemini-3.6-flash"},
    {"slug": "puter:google/gemini-3.5-flash",   "label": "Gemini 3.5 Flash","provider": "puter", "model": "google/gemini-3.5-flash"},
    {"slug": "puter:deepseek/deepseek-v4-pro",  "label": "DeepSeek V4 Pro", "provider": "puter", "model": "deepseek/deepseek-v4-pro"},
    {"slug": "puter:x-ai/grok-4.5",         "label": "Grok 4.5",          "provider": "puter", "model": "x-ai/grok-4.5"},
    {"slug": "puter:qwen/qwen3.7-max",      "label": "Qwen 3.7 Max",      "provider": "puter", "model": "qwen/qwen3.7-max"},
    # --- NVIDIA NIM (free models) --------------------------------------------
    {"slug": "nim:meta/llama-3.3-70b-instruct",           "label": "Llama 3.3 70B (NVIDIA)",     "provider": "nim", "model": "meta/llama-3.3-70b-instruct"},
    {"slug": "nim:meta/llama-3.1-8b-instruct",            "label": "Llama 3.1 8B (NVIDIA)",      "provider": "nim", "model": "meta/llama-3.1-8b-instruct"},
    {"slug": "nim:nvidia/llama-3.1-nemotron-70b-instruct","label": "Nemotron 70B (NVIDIA)",      "provider": "nim", "model": "nvidia/llama-3.1-nemotron-70b-instruct"},
    {"slug": "nim:deepseek-ai/deepseek-r1",               "label": "DeepSeek R1 (NVIDIA)",       "provider": "nim", "model": "deepseek-ai/deepseek-r1"},
    {"slug": "nim:qwen/qwen2.5-coder-32b-instruct",       "label": "Qwen2.5 Coder 32B (NVIDIA)", "provider": "nim", "model": "qwen/qwen2.5-coder-32b-instruct"},
]

MODEL_ALIASES = {
    "default": "puter:openai/gpt-5.6-sol",
    "fast":    "nim:meta/llama-3.1-8b-instruct",
    "smart":   "puter:anthropic/claude-opus-5",
    # short-name back-compat so old callers keep working
    "gpt-5-6-sol":     "puter:openai/gpt-5.6-sol",
    "claude-opus-4-8": "puter:anthropic/claude-opus-4.8",
    "claude-sonnet-5": "puter:anthropic/claude-sonnet-5",
}

_BY_SLUG = {m["slug"]: m for m in MODELS}
# also index the bare model id so a raw "openai/gpt-5.6-sol" still resolves
_BY_MODEL = {m["model"]: m for m in MODELS}


def resolve(name: str):
    """Map a UI/API model name (slug, alias, or raw model id) -> (provider, model_id)."""
    if not name:
        name = DEFAULT_MODEL
    name = MODEL_ALIASES.get(name, name)
    m = _BY_SLUG.get(name) or _BY_MODEL.get(name)
    if m:
        return m["provider"], m["model"]
    # accept an explicit "provider:model" even if not in the catalog
    if ":" in name:
        prov, mid = name.split(":", 1)
        if prov in _PROVIDER_BASE:
            return prov, mid
    d = _BY_SLUG[DEFAULT_MODEL]
    return d["provider"], d["model"]


def resolve_model(name: str) -> str:
    """Back-compat: return just the raw model id."""
    return resolve(name)[1]


# Back-compat: some older code/tests still read MODEL_MAP[...] directly.
MODEL_MAP = {**MODEL_ALIASES, **{m["slug"]: m["slug"] for m in MODELS}}

# ---- SELECTORS: VERIFIED LIVE 2026-06-17 ------------------------------------
# use.ai is a Next.js/radix app. Radix auto-ids (radix-_r_xx_) change per render,
# so every selector below uses the site's stable data-testid hooks instead.
# Leave a value as "REPLACE_ME" and the worker will skip/relax that step.
SELECTORS = {
    # model switch (works pre-signup)
    "model_dropdown":    '[data-testid="model-selector"]',
    "model_option":      '[data-testid="model-option-gateway-%s"]',  # %s = MODEL_MAP slug
    # auth (PASSWORDLESS, two-step: open modal -> reveal email field -> submit)
    "signup_button":     '[data-testid="header-sign-in-button"]',     # opens auth modal
    "email_reveal":      '[data-testid="signin-with-email-button"]',  # "continue with email" -> shows the field
    "email_input":       '[data-testid="email-input"]',
    "password_input":    "REPLACE_ME",   # NO password field exists (SSO / email-OTP) -> skipped
    "signup_submit":     '[data-testid="signin-with-email-button"]',  # same button submits the email
    "email_taken_error": "REPLACE_ME",   # N/A: email is OTP login, no "already in use" path -> skipped
    # chat
    "prompt_input":      '[data-testid="chat-input-textarea"]',
    "prompt_submit":     '[data-testid="send-button"]',
    "response_block":    '[data-testid="message-assistant"]',  # text inside: [data-testid="message-content"]
    "response_done":     '[data-testid="message-upvote"]',     # vote btns render only when the stream ends
}

# ---- Auth harvesting --------------------------------------------------------
# VERIFIED 2026-06-17: signup is instant + passwordless + NO email verification
# (fake email accepted; emailVerified stays null). It mints a real better-auth
# session. The token lives in an httpOnly cookie:
#   __Secure-better-auth.session_token   (value e.g. "Km5wpqjm5OnyOMZPgYQh3BJanHRzxwqi")
# (a companion cookie __Secure-better-auth.session_data is a JWT carrying an
#  embedded accessToken + planType). GET api.use.ai/v1/auth/get-session echoes it.
# The free cap is PER-ACCOUNT (1 message each), NOT per-IP -> harvest many.
AUTH_TOKEN_STORAGE = "cookie"     # "local" (localStorage), "cookie", or "none"
AUTH_TOKEN_KEY = "__Secure-better-auth.session_token"   # cookie name holding the token

# ---- Headless WS path (use.ai legacy, OFF) ----------------------------------
# Old use.ai path: signup over HTTP -> budget-agent WebSocket. Superseded by the
# Puter backend above. Keep False so no throwaway-account signup ever runs.
DIRECT_WS_ENABLED = False
AUTH_BASE     = "https://api.use.ai/v1/auth"          # email-login / sign-in/credentials / get-session
WS_AGENT_BASE = "wss://agents.use.ai/agents/budget-agent"
MODEL_PREFIX  = "gateway-"                             # selectedModel = gateway-<slug>
WS_OPEN_TIMEOUT = 30                                   # seconds to establish the socket
WS_REPLY_TIMEOUT = 90                                  # (legacy total cap; streaming uses idle)
WS_IDLE_TIMEOUT = 90                                   # give up only if NO token for this long
                                                       # (resets per token -> long code gens are fine)
DIRECT_WS_RETRIES = 2                                  # fresh-account retries on cap/empty
# Keep the old browser path off unless you explicitly enable it. When direct WS
# fails, browser fallback currently depends on local proxy/Tor state and can hide
# the real runner failure behind ERR_PROXY_CONNECTION_FAILED.
BROWSER_FALLBACK_ENABLED = False
# Warm account pool (sub-second latency: signup leaves the hot path)
ACCOUNT_POOL_SIZE = 8                                   # ready accounts kept warm
ACCOUNT_POOL_REFILL_SEC = 3                             # how often to top the pool up
ACCOUNT_TTL_SEC = 600                                   # drop pooled accounts older than this
# No Chromium in the WS path -> serve many at once (browser path stays capped low)
DIRECT_MAX_CONCURRENCY = 24                             # concurrent WS completions

# ---- Direct API (FAST PATH; skips the browser on the hot path) --------------
# VERIFIED 2026-06-17: use.ai streams replies over a WEBSOCKET (Cloudflare Agents
# + Vercel AI SDK frames), NOT a REST endpoint. Full protocol is captured:
#
#   CONNECT: wss://agents.use.ai/agents/budget-agent/<chatId>
#              ?userId=<userId>&userType=regular&userEmail=<email>&planType=free&isTestUser=false
#   SEND (one JSON frame):
#     {"chatId":"<uuid>","userId":"<uuid>","userType":"regular","planType":"free",
#      "selectedModel":"gateway-<slug>","locale":"en",
#      "messages":[{"id":"<rand>","role":"user","parts":[{"type":"text","text":"<PROMPT>"}]}],
#      "trigger":"submit-message","source":"chat_page"}
#   RECV (concatenate chunk.delta where chunk.type=="text-delta"):
#     data-chat-metadata -> stream-start -> {chunk:{start, start-step, text-start,
#       text-delta(delta=...), text-end, finish-step, finish}} -> stream-complete
#     (cap -> {"type":"rate-limit-error","messageMetadata":{...}})
#
# This HTTP-replay path can't carry that; direct.py needs a websockets client
# instead. The session cookie/token above authenticates the socket. Until that
# client is written, keep URL "" to stay browser-only (DIRECT_API_BODY etc below
# are the old REST template, unused for WS).
DIRECT_API_URL = ""               # WebSocket, not REST -> empty until ws client lands
DIRECT_API_METHOD = "POST"
# {model} and {prompt} get substituted (auto JSON-escaped). Match the real body.
DIRECT_API_BODY = '{"model": "{model}", "messages": [{"role": "user", "content": "{prompt}"}]}'
DIRECT_API_AUTH_HEADER = "Authorization"
DIRECT_API_AUTH_FORMAT = "Bearer {token}"
# dotted path into the JSON reply, e.g. "choices.0.message.content"
DIRECT_API_RESPONSE_PATH = "choices.0.message.content"

# ---- Account bank -----------------------------------------------------------
BANK_PATH = "bank/accounts.db"        # sqlite store of harvested accounts/tokens
STORAGE_STATE_DIR = "bank/states"     # saved cookies/localStorage per account
BANK_MIN_FRESH = 10                   # keep at least this many warm + ready
BANK_PREWARM_BATCH = 5                # how many to harvest per top-up cycle
PREWARM_INTERVAL_SEC = 30             # how often the backend tops the bank up
# HARD RULE: each account is worth exactly ONE message. On a banked-account
# failure we retire it and claim a fresh one -- never a 2nd send through one acct.
MAX_BANKED_ATTEMPTS = 2               # how many fresh accounts to try before cold signup

# ---- Proxy rotation ---------------------------------------------------------
# cloakbrowser hides the BROWSER; proxies hide the IP so a flood of signups
# doesn't all come from one address. Empty = disabled (runs on your direct IP).
# Line formats: "1.2.3.4:8000", "http://1.2.3.4:8000",
#               "socks5://user:pass@1.2.3.4:1080", "user:pass@host:port"
PROXIES = []                    # inline list of proxies
PROXY_FILE = ""                 # optional: path to a file, one proxy per line (# ok)
PROXY_ROTATION = "round_robin"  # "round_robin" or "random"
PROXY_DEFAULT_SCHEME = "http"   # used when a proxy line omits the scheme

# ---- FREE proxy options (no paid account) -----------------------------------
# Option A: Tor -- free rotation via the Tor network. Start the daemon with
# start_tor.bat (uses the tor.exe bundled in Tor Browser, no browser needed),
# then this rotates the exit IP before each signup. NEWNYM is rate-limited to
# ~10s, so keep BANK_PREWARM_BATCH small (2-3).  >>> pre-wired for your machine.
PROXY_TOR = False                # Puter needs no proxies/Tor -> off
TOR_BROWSER_DIR = r"C:\Tor Browser"   # (unused unless you re-enable the legacy path)
TOR_SOCKS = "socks5://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = ""        # "" = cookie auth (what start_tor.bat sets up)
TOR_DATA_DIR = "tor_data"        # where start_tor.bat writes tor's data + auth cookie
TOR_COOKIE_PATH = ""             # "" = auto: <TOR_DATA_DIR>/control_auth_cookie
TOR_NEWNYM_DELAY = 10            # seconds between circuit renewals (Tor's rate limit)

# Option B: free public proxy lists -- run `python -m worker.proxy_sources` to
# fetch + validate them into PROXY_FILE, then set PROXY_FILE above. Free proxies
# die fast, so re-run it periodically.
