"""Persistencia de resultados: Google Sheets (Apps Script) o archivo JSON local."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st


class _PostRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Mantiene el método POST y limita los redirects a dominios de Google."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if code not in (301, 302, 303, 307, 308) or req.get_method() != "POST":
            return super().redirect_request(req, fp, code, msg, headers, newurl)

        parsed = urlparse(newurl)
        host = (parsed.hostname or "").lower()
        allowed = host == "script.google.com" or host.endswith(".googleusercontent.com")
        if parsed.scheme != "https" or not allowed:
            return None

        return urllib.request.Request(
            newurl,
            data=req.data,
            headers=dict(req.header_items()),
            method="POST",
        )


def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.environ.get(name.upper(), "").strip()


def _webhook() -> str:
    return _secret("results_webhook")


def _token() -> str:
    return _secret("results_token")


def _data_file() -> Path:
    override = os.environ.get("HGPS_RESULTS_FILE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "data" / "results.json"


def backend_name() -> str:
    return "Google Sheets" if _webhook() else "Archivo local"


def admin_password() -> str:
    return _secret("admin_password")


def _post_json(payload: dict) -> dict:
    url = _webhook()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("results_webhook debe ser una URL HTTPS válida.")

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(_PostRedirectHandler())
    with opener.open(req, timeout=15) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def save_result(record: dict) -> bool:
    """Guarda un resultado. Devuelve False si la nube no está disponible."""
    if not record.get("id"):
        return False

    if _webhook():
        try:
            response = _post_json({"token": _token(), "action": "save", "record": record})
            return bool(response.get("ok"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return False

    path = _data_file()
    try:
        records = _read_local(path)
        records = [item for item in records if item.get("id") != record.get("id")]
        records.append(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return True
    except OSError:
        return False


def _read_local(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def load_results() -> tuple[list[dict], str]:
    """Devuelve (resultados, error). El error queda vacío si todo fue bien."""
    if _webhook():
        try:
            response = _post_json({"token": _token(), "action": "list"})
            if not response.get("ok"):
                return [], "Google Sheets rechazó la solicitud. Revisa el token."
            records = response.get("records", [])
            if not isinstance(records, list):
                return [], "La respuesta de Google Sheets no tiene el formato esperado."
            return records, ""
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            return [], f"No se pudo conectar con Google Sheets: {exc}"

    return _read_local(_data_file()), ""
