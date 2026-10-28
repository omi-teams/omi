"""Credentials: Windows Credential Manager, the Claude Code session login and the Codex ChatGPT login."""

import base64
import ctypes
import getpass
import json
import os
import sys
import time
from pathlib import Path

from . import core


CRED_TARGET = "omi/CLAUDE_CODE_OAUTH_TOKEN"
TOKEN_ENV = "CLAUDE_CODE_OAUTH_TOKEN"
CODEX_CRED_TARGET = "omi/OPENAI_API_KEY"
CODEX_ENV = "OPENAI_API_KEY"


class CRED(ctypes.Structure):  # CREDENTIALW
    _fields_ = [("Flags", ctypes.c_uint32), ("Type", ctypes.c_uint32), ("TargetName", ctypes.c_wchar_p),
                ("Comment", ctypes.c_wchar_p), ("LastWritten", ctypes.c_uint32 * 2),
                ("CredentialBlobSize", ctypes.c_uint32), ("CredentialBlob", ctypes.POINTER(ctypes.c_char)),
                ("Persist", ctypes.c_uint32), ("AttributeCount", ctypes.c_uint32), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", ctypes.c_wchar_p), ("UserName", ctypes.c_wchar_p)]


def advapi():
    return ctypes.WinDLL("advapi32")


def cred_write(secret, target=CRED_TARGET):
    data = secret.encode()
    buf = ctypes.create_string_buffer(data, len(data))
    c = CRED(Type=1, TargetName=target, UserName="omi", Persist=2,  # GENERIC, LOCAL_MACHINE
             CredentialBlobSize=len(data), CredentialBlob=ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    if not advapi().CredWriteW(ctypes.byref(c), 0):
        sys.exit("could not store the token in Windows Credential Manager.")


def cred_read(target=CRED_TARGET):
    p = ctypes.POINTER(CRED)()
    api = advapi()
    if not api.CredReadW(target, 1, 0, ctypes.byref(p)):
        return None
    try:
        return ctypes.string_at(p.contents.CredentialBlob, p.contents.CredentialBlobSize).decode()
    finally:
        api.CredFree(p)


def token_set(tool="claude"):
    codex = tool == "codex"
    env, target = (CODEX_ENV, CODEX_CRED_TARGET) if codex else (TOKEN_ENV, CRED_TARGET)
    if not core.WINDOWS:
        print(f"no credential store support here; export {env} in the shell that runs omi.")
        return
    secret = getpass.getpass(f"paste the {'OpenAI API key' if codex else '`claude setup-token` value'} (hidden): ").strip()
    if not secret:
        sys.exit("empty token; nothing stored.")
    cred_write(secret, target)
    print(f"stored in Windows Credential Manager as {target}")


def token(tool="claude"):
    env, target = (CODEX_ENV, CODEX_CRED_TARGET) if tool == "codex" else (TOKEN_ENV, CRED_TARGET)
    return (cred_read(target) if core.WINDOWS else None) or os.environ.get(env)


CODEX_AUTH_ENV = "OMI_CODEX_AUTH"  # not CODEX_ACCESS_TOKEN: codex reads that name itself as an agent identity token
CODEX_LOGIN_HINT = "run `codex` once on the host (or `codex login`) and retry"
# written into the container's tmpfs home before codex runs; the variable is dropped right after
CODEX_AUTH_BOOT = ('mkdir -p "$HOME/.codex" && printenv ' + CODEX_AUTH_ENV + ' > "$HOME/.codex/auth.json" && '
                   'chmod 600 "$HOME/.codex/auth.json" && unset ' + CODEX_AUTH_ENV + ' && exec "$@"')


def codex_login():
    """(slim auth.json text, None) from the host ChatGPT login, or (None, problem). Only the access token goes in;
    the refresh token is replaced by a placeholder (the schema needs the field), so the container cannot refresh."""
    path = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "auth.json"
    try:
        auth = json.loads(path.read_text(encoding="utf-8"))
        tok = auth["tokens"]
        access = tok["access_token"]
        if auth.get("auth_mode") not in (None, "chatgpt") or not access:
            raise KeyError
    except (OSError, ValueError, KeyError, TypeError):
        return None, f"no ChatGPT login at {path}: {CODEX_LOGIN_HINT}"
    try:
        part = access.split(".")[1]
        exp = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))).get("exp")
    except (IndexError, ValueError, AttributeError):
        exp = None  # not a readable JWT: let codex decide
    if isinstance(exp, (int, float)) and exp <= time.time():
        return None, f"the ChatGPT login in {path} has expired: {CODEX_LOGIN_HINT}"
    slim = {"auth_mode": "chatgpt", "OPENAI_API_KEY": None, "last_refresh": auth.get("last_refresh"),
            "tokens": {"access_token": access, "id_token": tok.get("id_token"), "account_id": tok.get("account_id"),
                       "refresh_token": "omi-no-refresh"}}
    return json.dumps(slim), None


def claude_secret():
    """(value, source, note) for claude: env override, then the Claude Code session login, then the stored token.
    Only the access token is read, at run time; the refresh token is never touched."""
    if os.environ.get(TOKEN_ENV):
        return os.environ[TOKEN_ENV], "env", None
    path = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / ".credentials.json"
    note = None
    try:
        oauth = json.loads(path.read_text(encoding="utf-8"))["claudeAiOauth"]
        access = oauth["accessToken"]
        exp = oauth.get("expiresAt")
        if access and isinstance(exp, (int, float)) and exp <= time.time() * 1000:
            note = "session login expired: use Claude Code once to refresh"
        elif access:
            return access, "session", None
    except (OSError, ValueError, KeyError, TypeError):
        pass
    stored = cred_read(CRED_TARGET) if core.WINDOWS else None
    return stored, "stored", note


def claude_auth():
    """claude_secret() as (env name, value, problem), printing the source and any expiry note once."""
    val, source, note = claude_secret()
    if note:
        print(note)
    if val:
        print(f"claude auth: {source}")
    return TOKEN_ENV, val, note


def tool_secret(tool):
    """(env name, value, problem) for a tool; codex: stored API key, env OPENAI_API_KEY, then the host ChatGPT login."""
    if tool == "claude":
        val, _, note = claude_secret()
        return TOKEN_ENV, val, note
    key = token("codex")
    if key:
        return CODEX_ENV, key, None
    auth, problem = codex_login()
    return CODEX_AUTH_ENV, auth, problem
