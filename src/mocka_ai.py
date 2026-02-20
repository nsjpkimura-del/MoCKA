# src/mocka_ai.py
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AIResult:
    text: str
    raw: Dict[str, Any]
    usage: Optional[Dict[str, Any]] = None


class ProviderError(RuntimeError):
    pass


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return default
    v = str(v)
    return v if v != "" else default


def _now_ms() -> int:
    return int(time.time() * 1000)


def _as_int(v: Optional[str], default: int) -> int:
    try:
        if v is None or v == "":
            return default
        return int(v)
    except Exception:
        return default


def _redact_secrets_text(s: str) -> str:
    """
    outbox へ落ちる可能性がある文字列から秘密情報っぽいものを伏字化する。
    過剰に伏字化してもよい。漏洩ゼロを優先する。
    """
    if not s:
        return s

    # OpenAI API keys (sk-..., sk-proj-..., etc.)
    s = re.sub(r"\bsk-[A-Za-z0-9_\-]{8,}\b", "sk-[REDACTED]", s)

    # Bearer tokens
    s = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9_\-\.]{8,}\b", "Bearer [REDACTED]", s)

    # Common JSON fields
    s = re.sub(r'(?i)"api_key"\s*:\s*"[^"]+"', '"api_key":"[REDACTED]"', s)
    s = re.sub(r'(?i)"authorization"\s*:\s*"[^"]+"', '"authorization":"[REDACTED]"', s)
    s = re.sub(r'(?i)"token"\s*:\s*"[^"]+"', '"token":"[REDACTED]"', s)

    return s


def _redact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    request/metadata を outbox に残すための辞書フィルタ。
    鍵やトークンになり得るものは落とす/伏字化する。
    """
    deny_substrings = ("authorization", "api_key", "apikey", "key", "token", "secret", "password")
    out: Dict[str, Any] = {}
    for k, v in d.items():
        lk = str(k).lower()
        if any(x in lk for x in deny_substrings):
            out[k] = "[REDACTED]"
            continue
        if isinstance(v, str):
            out[k] = _redact_secrets_text(v)
        else:
            out[k] = v
    return out


def call_ai(prompt: str, *, provider: Optional[str] = None, timeout_ms: Optional[int] = None) -> AIResult:
    """
    MoCKA から AI を呼ぶ唯一の入口。
    失敗は必ず例外として送出する (main_loop 側で exception を outbox に保存するため)。
    """
    provider = provider or _env("MOCKA_PROVIDER", "openai_http")
    timeout_ms = timeout_ms if timeout_ms is not None else _as_int(_env("MOCKA_AI_TIMEOUT_MS"), 30000)

    if provider == "stub":
        return AIResult(
            text="[stub] " + prompt,
            raw={"meta": {"provider": "stub", "ts_ms": _now_ms()}, "response": {"text": prompt}},
            usage=None,
        )

    if provider == "openai_http":
        return _call_openai_http(prompt, timeout_ms=timeout_ms)

    raise ProviderError("Unknown provider: " + str(provider))


def _call_openai_http(prompt: str, *, timeout_ms: int) -> AIResult:
    """
    OpenAI HTTP API を標準ライブラリで呼ぶ最小実装。
    outbox に秘密情報が落ちないことを最優先し、エラー本文は伏字化する。
    """
    api_key = _env("OPENAI_API_KEY")
    if not api_key:
        raise ProviderError("OPENAI_API_KEY is not set")

    model = _env("OPENAI_MODEL", "gpt-4.1-mini")
    url = "https://api.openai.com/v1/responses"

    payload: Dict[str, Any] = {
        "model": model,
        "input": prompt,
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + api_key)

    t0 = _now_ms()
    try:
        with urllib.request.urlopen(req, timeout=max(1, timeout_ms // 1000)) as resp:
            resp_bytes = resp.read()
            t1 = _now_ms()

            raw_resp = json.loads(resp_bytes.decode("utf-8"))
            text = _extract_text_from_responses(raw_resp)
            usage = raw_resp.get("usage")

            meta = {
                "provider": "openai_http",
                "model": model,
                "timing_ms": {"provider_call_ms": t1 - t0},
                "request": _redact_dict({"model": model, "timeout_ms": timeout_ms}),
            }

            return AIResult(
                text=text,
                raw={"meta": meta, "response": raw_resp},
                usage=usage if isinstance(usage, dict) else None,
            )

    except urllib.error.HTTPError as e:
        # エラー本文を読み取り、伏字化してから例外に入れる (outbox 漏洩防止)
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        redacted = _redact_secrets_text(err_body)

        # できるだけ要点を残す (status と code)
        msg = "OpenAI HTTPError " + str(e.code) + ": " + redacted
        raise ProviderError(msg) from e

    except urllib.error.URLError as e:
        # ネットワーク・DNS・プロキシなど
        raise ProviderError("OpenAI URLError: " + _redact_secrets_text(str(e))) from e

    except Exception as e:
        raise ProviderError("OpenAI unknown error: " + _redact_secrets_text(str(e))) from e


def _extract_text_from_responses(raw: Dict[str, Any]) -> str:
    """
    Responses API の返却からテキストを取り出す。
    形式変化に耐えるように複数経路を試す。
    """
    v = raw.get("output_text")
    if isinstance(v, str) and v:
        return v

    out = raw.get("output")
    if isinstance(out, list):
        chunks = []
        for item in out:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                ctype = c.get("type")
                if ctype in ("output_text", "text"):
                    txt = c.get("text")
                    if isinstance(txt, str) and txt:
                        chunks.append(txt)
        if chunks:
            return "\n".join(chunks)

    # 最後の保険 (ただし巨大化しやすいので注意)
    try:
        return json.dumps(raw, ensure_ascii=False)
    except Exception:
        return str(raw)
