"""CHARLA DE DISPENSACIÓN HOSPITALARIA — webapp interactiva de repaso (Streamlit).

Cada tema de la charla es un módulo con preguntas de opción múltiple.
Hospital General de la Plaza de la Salud (HGPS) · Gerencia de Farmacia.
"""

from __future__ import annotations

import base64
import hmac
import html
import inspect
import json
import random
import re
import time
import uuid
from datetime import date, datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from analytics import summarize_records
from audio import build_sound
from certificate import build_certificate
from executive_report import build_executive_pdf
from quiz_data import LETTERS, LEVELS, TOTAL_QUESTIONS, rank_for
from report import build_followup_report, build_report_pdf
from storage import admin_password, backend_name, load_results, save_result

# --------------------------------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------------------------------

_ASSETS = Path(__file__).resolve().parent / "assets"
_LOGO_PATH = _ASSETS / "hgps-logo.png"
_FAVICON_PATH = _ASSETS / "hgps-favicon.png"

st.set_page_config(
    page_title="Charla de Dispensación Hospitalaria · HGPS",
    page_icon=str(_FAVICON_PATH) if _FAVICON_PATH.is_file() else "💊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

WIDTH_KW = {"width": "stretch"} if "width" in inspect.signature(st.button).parameters else {"use_container_width": True}

BASE_LIVES = 3
ADMIN_SESSION_SECONDS = 30 * 60
ADMIN_MAX_ATTEMPTS = 5
ADMIN_LOCK_SECONDS = 60


@st.cache_data(show_spinner=False)
def logo_data_uri() -> str:
    """Devuelve el logo HGPS embebido para que funcione sin rutas externas."""
    if not _LOGO_PATH.is_file():
        return ""
    return "data:image/png;base64," + base64.b64encode(_LOGO_PATH.read_bytes()).decode()


def fmt_num(value: int) -> str:
    """Separador de miles al estilo español: 1.250."""
    return f"{value:,}".replace(",", ".")


def safe_filename(value: str, fallback: str = "participante") -> str:
    """Evita rutas o caracteres problemáticos en el nombre de una descarga."""
    cleaned = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._-")
    return cleaned[:80] or fallback
STAGE_LABELS = {1: "CONCEPTOS", 2: "PROPÓSITO", 3: "TIPOS", 4: "RECETA", 5: "7 CORRECTOS",
                6: "FLUJO", 7: "LASA", 8: "LEY", 9: "FARMACÉUTICO", 10: "AUXILIAR", 11: "SINERGIA"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700&family=Open+Sans:wght@400;500;600;700&display=swap');

/* ---------- Paleta oficial HGPS ---------- */
:root{
  --cyan:#00BCD4;
  --cyan-dark:#00A5BA;
  --cyan-ink:#006E7C;
  --cyan-soft:#E6F8FB;
  --navy:#32477B;
  --navy-deep:#24345C;
  --navy-ink:#1A2A4A;
  --lime:#BABF33;
  --lime-dark:#6B7010;
  --lime-soft:#F7F8E3;
  --ink:#22313A;
  --body:#30414F;
  --muted:#415560;
  --line:#D5E3E7;
  --line-soft:#E6EFF2;
  --canvas:#F7FBFC;
  --card:#FFFFFF;
  --soft:#F1FAFC;
  --good:#2E7D32;
  --good-soft:#EDF7EE;
  --bad:#B3261E;
  --bad-soft:#FDF1F0;
}

html, body, [class*="st-"], [data-testid="stAppViewContainer"]{
  font-family:'Open Sans','Segoe UI','Helvetica Neue',Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;
}

/* Conservar la fuente de iconos de Streamlit (expanders, flechas, etc.) */
[data-testid="stIconMaterial"], .stIconMaterial{
  font-family:'Material Symbols Rounded' !important;
  font-weight:normal !important;
  font-feature-settings:'liga' !important;
}

.stApp{
  background-color:var(--canvas);
  background-image:
    radial-gradient(900px 420px at 8% -12%, rgba(0,188,212,.10), transparent 60%),
    radial-gradient(700px 360px at 96% -8%, rgba(186,191,51,.07), transparent 55%),
    linear-gradient(180deg,#FFFFFF 0%, var(--canvas) 42%, #EFF8FA 100%);
  background-attachment:fixed;
  color:var(--body);
}

/* Filete institucional superior: azul HGPS → cyan → lima */
.stApp::before{
  content:"";
  position:fixed; top:0; left:0; right:0; height:4px; z-index:999;
  background:linear-gradient(90deg,var(--navy) 0%,var(--cyan) 58%,var(--lime) 100%);
}

#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stAppToolbar"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stHeaderActionElements"],
[data-testid="stElementToolbar"]{display:none !important;}
[data-testid="stHeader"]{background:transparent !important; height:0; min-height:0;}
[data-testid="stSidebar"]{display:none;}

.block-container{
  max-width:1000px;
  padding-top:2.4rem;
  padding-bottom:4rem;
}

/* ---------- Tipografía ---------- */
.kicker{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:.68rem; font-weight:700; letter-spacing:.16em; color:var(--cyan-ink);
  text-transform:uppercase; margin-bottom:.6rem; line-height:1.55;
}
.stApp .hero-title{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-weight:700; font-size:clamp(1.75rem,5vw,3.2rem); line-height:1.07;
  letter-spacing:-.015em; margin:0; padding:0; color:var(--navy-ink); overflow-wrap:break-word;
}
.stApp .hero-title .grad{
  color:var(--cyan-ink); background:none; -webkit-text-fill-color:currentColor;
}
.stApp .hero-sub{
  color:var(--body); font-size:clamp(.96rem,2.1vw,1.06rem);
  margin:.95rem 0 0; line-height:1.65; max-width:62ch;
}

/* ---------- Marca HGPS ---------- */
.brand{display:flex; align-items:center; gap:.85rem; margin:0 0 1.1rem;}
.brand-logo{height:52px; width:auto; flex:0 0 auto; display:block;}
.brand-text{display:flex; flex-direction:column; gap:.15rem; line-height:1.25; min-width:0;}
.brand-name{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-weight:700; font-size:clamp(.7rem,1.1vw,.88rem); letter-spacing:.01em;
  line-height:1.3; text-transform:none; color:var(--navy-ink);
}
.brand-area{
  font-size:.68rem; font-weight:600; letter-spacing:.09em;
  text-transform:uppercase; color:var(--cyan-ink);
}

/* ---------- Tarjetas ---------- */
.card{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:12px;
  padding:1.4rem 1.5rem;
  box-shadow:0 1px 2px rgba(50,71,123,.05), 0 18px 36px -30px rgba(50,71,123,.28);
  margin:.4rem 0 1rem;
}
.card-glow{
  border-color:#C9E8ED;
  border-left:3px solid var(--cyan);
  box-shadow:0 1px 2px rgba(50,71,123,.05), 0 22px 40px -30px rgba(0,188,212,.35);
}

/* ---------- HUD ---------- */
.hud{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(96px,1fr));
  gap:.55rem; margin-bottom:.75rem;
}
.hud-item{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:9px; padding:.6rem .75rem;
  box-shadow:0 1px 2px rgba(50,71,123,.05);
}
.hud-label{display:block; font-size:.63rem; letter-spacing:.11em; color:var(--muted); text-transform:uppercase; font-weight:700;}
.hud-value{
  display:block; font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:1.2rem; font-weight:700; color:var(--navy); line-height:1.3;
  font-variant-numeric:tabular-nums;
}
.hud-value .dim{color:var(--muted); font-weight:600; font-size:.85rem;}
.hud-item.lives .hud-value{color:var(--navy);}
.hud-item.lives.empty .hud-value{color:var(--bad);}
.hud-item.lives.training .hud-value{color:var(--cyan-ink);}
.hud-item.score .hud-value{color:var(--cyan-ink);}
.hud-item.streak .hud-value{color:var(--lime-dark);}
.bar{height:6px; border-radius:999px; background:#E1EEF1; overflow:hidden; margin:.3rem 0 1.3rem;}
.bar-fill{height:100%; border-radius:999px; background:linear-gradient(90deg,var(--navy),var(--cyan)); transition:width .5s ease;}

/* ---------- Encabezado de reto ---------- */
.reto-head{display:flex; gap:1rem; align-items:flex-start; margin-bottom:1rem;}
.reto-ico{
  font-size:1.8rem; line-height:1; width:60px; height:60px; flex:0 0 60px;
  display:flex; align-items:center; justify-content:center;
  background:var(--cyan-soft); border:1px solid #BFE8ED; border-radius:11px;
}
.stApp .reto-name{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:clamp(1.35rem,3.8vw,1.9rem); font-weight:700; color:var(--navy);
  margin:0; padding:0; letter-spacing:-.01em; line-height:1.15;
}
.stApp .reto-sub{color:var(--muted); margin:.2rem 0 0; font-size:.94rem; line-height:1.5;}
.pill{
  display:inline-block; font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:.62rem; letter-spacing:.13em; font-weight:700;
  color:var(--cyan-ink); background:var(--cyan-soft); border:1px solid #BFE8ED;
  padding:.3rem .65rem; border-radius:6px; text-transform:uppercase; margin-bottom:.55rem;
}
.pill.gold{color:var(--lime-dark); background:var(--lime-soft); border-color:#E2E3B8;}

/* ---------- Briefing ---------- */
.stApp .brief li{color:var(--body); margin:.5rem 0; line-height:1.65; font-size:.98rem;}
.brief b{color:var(--navy); font-weight:700;}
.tip{
  margin-top:1.1rem; padding:.85rem 1rem; border-radius:0 9px 9px 0; font-size:.92rem;
  background:var(--soft); border:1px solid #D8EEF1; border-left:3px solid var(--cyan);
  color:var(--body); line-height:1.6;
}
.tip b{color:var(--navy);}

/* ---------- Pregunta ---------- */
.qmeta{font-size:.65rem; letter-spacing:.16em; color:var(--cyan-ink); text-transform:uppercase; font-weight:700; margin-bottom:.6rem;}
.stApp .qtext{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:clamp(1.12rem,2.8vw,1.4rem); font-weight:600; color:var(--navy);
  line-height:1.42; margin:0;
}

/* ---------- Botones ---------- */
button[data-testid^="stBaseButton"]{
  background:var(--card) !important;
  border:1px solid var(--line) !important;
  border-radius:9px !important;
  color:var(--ink) !important;
  font-family:'Titillium Web','Segoe UI',sans-serif !important;
  font-weight:600 !important; font-size:1rem !important; letter-spacing:.005em;
  padding:.8rem 1.05rem !important;
  justify-content:flex-start !important; text-align:left !important;
  transition:transform .16s ease, border-color .16s ease, box-shadow .16s ease, background .16s ease;
  min-height:52px;
  box-shadow:0 1px 2px rgba(50,71,123,.05) !important;
}
button[data-testid^="stBaseButton"] > div{
  justify-content:flex-start !important; width:100%;
}
button[data-testid^="stBaseButton"] p{
  font-size:inherit; font-weight:inherit; color:inherit;
  white-space:pre-wrap !important; text-align:left !important; line-height:1.5;
  padding-left:1.6em; text-indent:-1.6em;
}
button[data-testid^="stBaseButton"]:hover{
  border-color:var(--cyan-dark) !important;
  background:var(--soft) !important;
  transform:translateX(3px);
  box-shadow:0 10px 20px -16px rgba(0,188,212,.5) !important;
  color:var(--navy) !important;
}
button[data-testid^="stBaseButton"]:focus:not(:active){
  border-color:var(--cyan-dark) !important; color:var(--navy) !important;
  box-shadow:0 0 0 2px rgba(186,191,51,.55) !important;
}

button[data-testid="stBaseButton-primary"]{
  justify-content:center !important;
  background:linear-gradient(180deg,#00C6DD 0%,var(--cyan) 100%) !important;
  border:1px solid var(--cyan-dark) !important;
  color:#0B2B33 !important;
  font-weight:700 !important; letter-spacing:.05em;
  box-shadow:0 10px 22px -14px rgba(0,165,186,.65) !important;
}
button[data-testid="stBaseButton-primary"]:hover{
  background:var(--cyan-dark) !important;
  border-color:var(--cyan-dark) !important;
  transform:translateY(-1px) !important;
  box-shadow:0 14px 26px -14px rgba(0,165,186,.7) !important;
  color:#062126 !important;
}
button[data-testid="stBaseButton-primary"] > div{justify-content:center !important;}
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-primary"] div{
  color:#0B2B33 !important; font-weight:700 !important; text-align:center !important;
  padding-left:0 !important; text-indent:0 !important;
}
button[data-testid="stBaseButton-primary"]:hover p,
button[data-testid="stBaseButton-primary"]:hover div{color:#062126 !important;}

button[data-testid="stBaseButton-primaryFormSubmit"]{
  justify-content:center !important;
  background:linear-gradient(180deg,#00C6DD 0%,var(--cyan) 100%) !important;
  border:1px solid var(--cyan-dark) !important;
  color:#0B2B33 !important;
  font-weight:700 !important; letter-spacing:.05em;
}
button[data-testid="stBaseButton-primaryFormSubmit"]:hover{
  background:var(--cyan-dark) !important; border-color:var(--cyan-dark) !important;
  color:#062126 !important;
}
button[data-testid="stBaseButton-primaryFormSubmit"] p{
  color:#0B2B33 !important; font-weight:700 !important;
}

button[data-testid="stBaseButton-tertiary"]{
  background:transparent !important; border:none !important; justify-content:center !important;
  color:var(--muted) !important; font-size:.84rem !important; font-weight:600 !important;
  min-height:34px; box-shadow:none !important; transform:none !important;
}
button[data-testid="stBaseButton-tertiary"]:hover{
  color:var(--cyan-ink) !important; text-decoration:underline; transform:none !important;
}
button[data-testid="stBaseButton-tertiary"] > div{justify-content:center !important;}
button[data-testid="stBaseButton-tertiary"] p{
  font-size:.84rem !important; font-weight:600 !important; text-align:center !important;
  padding-left:0 !important; text-indent:0 !important;
}

/* ---------- Verdadero / falso ---------- */
.verdict{
  border-radius:10px; padding:1rem 1.15rem; margin:.2rem 0 1rem;
  border:1px solid var(--line); background:var(--card); display:flex; gap:.9rem; align-items:flex-start;
}
.verdict.ok{background:var(--good-soft); border-color:#B7DFC0; border-left:3px solid var(--good);}
.verdict.ko{background:var(--bad-soft); border-color:#F0C7C3; border-left:3px solid var(--bad);}
.verdict .v-ico{font-size:1.55rem; line-height:1;}
.stApp .verdict .v-title{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-weight:700; font-size:1.08rem; color:var(--ink); margin:0; letter-spacing:-.01em;
}
.verdict.ok .v-title{color:#1B5E20;}
.verdict.ko .v-title{color:#8C1D18;}
.stApp .verdict .v-sub{color:var(--body); font-size:.9rem; margin:.2rem 0 0;}
.verdict .v-pts{margin-left:auto; font-weight:700; font-size:1.18rem; white-space:nowrap; font-variant-numeric:tabular-nums;}
.verdict.ok .v-pts{color:var(--good);}
.verdict.ko .v-pts{color:var(--bad);}

.stApp .answer-line{color:var(--body); font-size:.94rem; margin:.35rem 0;}
.answer-line .k{color:var(--muted);}
.why{
  background:var(--soft); border-left:3px solid var(--cyan);
  border-radius:0 9px 9px 0; padding:.85rem 1rem; color:var(--body);
  font-size:.93rem; line-height:1.65;
}
.why .h{color:var(--cyan-ink); font-weight:700; font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; display:block; margin-bottom:.3rem;}
.src{color:var(--muted); font-size:.78rem; margin-top:.75rem;}

/* ---------- Inicio ---------- */
.chips{display:flex; gap:.5rem; flex-wrap:wrap; margin:1.4rem 0 1.8rem;}
.chip{
  font-size:.78rem; font-weight:500; color:var(--body); background:var(--card);
  border:1px solid var(--line); padding:.42rem .8rem; border-radius:6px;
}
.chip b{color:var(--navy); font-weight:700;}
.mini{display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:.7rem; margin-top:.5rem;}
.mini .m{
  background:var(--card); border:1px solid var(--line); border-radius:10px;
  padding:.95rem 1rem; box-shadow:0 1px 2px rgba(50,71,123,.04);
}
.mini .m .ic{font-size:1.2rem;}
.mini .m .t{font-family:'Titillium Web','Segoe UI',sans-serif; font-weight:700; color:var(--navy); font-size:.95rem; margin:.4rem 0 .2rem;}
.mini .m .d{color:var(--muted); font-size:.82rem; line-height:1.55;}
.foot{color:var(--body); font-size:.86rem; margin-top:1.8rem; line-height:1.7;}
.foot b{color:var(--navy-ink); font-weight:700;}
.admin-link{
  display:inline-block; margin-top:1rem; font-size:.78rem; color:var(--muted);
  text-decoration:none; border-bottom:1px dotted var(--line);
}
.admin-link:hover{color:var(--cyan-ink); border-bottom-color:var(--cyan-ink);}
.foot-links{display:flex; gap:1.2rem; flex-wrap:wrap; margin-top:1rem;}
.foot-links .admin-link{margin-top:0;}

/* ---------- Panel de la ficha del jugador ---------- */
.st-key-playerpanel{
  background:var(--card) !important;
  border:1px solid var(--line) !important;
  border-top:3px solid var(--cyan) !important;
  border-radius:12px !important;
  padding:1.25rem 1.4rem 1.4rem !important;
  box-shadow:0 1px 2px rgba(50,71,123,.05), 0 20px 40px -32px rgba(50,71,123,.3) !important;
  margin-bottom:1rem;
}

/* ---------- Formulario ---------- */
[data-testid="stTextInput"] label, [data-testid="stCheckbox"] label{
  color:var(--body) !important; font-weight:600 !important; font-size:.9rem !important;
}
[data-testid="stTextInput"] input{
  background:var(--card) !important;
  border:1px solid #C6D8DE !important;
  border-radius:9px !important; color:var(--ink) !important;
  font-size:1rem !important; padding:.72rem .85rem !important;
  font-family:'Open Sans','Segoe UI',sans-serif !important;
}
[data-testid="stTextInput"] input:focus{
  border-color:var(--cyan) !important;
  box-shadow:0 0 0 3px rgba(0,188,212,.18) !important;
}
[data-testid="stTextInput"] input::placeholder{color:#5F7480 !important;}
[data-testid="stCheckbox"] p{color:var(--body) !important; font-weight:500 !important;}
.err{color:var(--bad); font-size:.86rem; margin:-.35rem 0 .6rem;}

/* ---------- Final ---------- */
.trophy{
  text-align:center; padding:1.7rem 1rem 1.3rem;
  background:var(--card); border:1px solid var(--line); border-radius:14px;
  box-shadow:0 1px 2px rgba(50,71,123,.05), 0 20px 40px -32px rgba(50,71,123,.3);
}
.trophy .medal{font-size:4.2rem; line-height:1; filter:drop-shadow(0 8px 20px rgba(0,188,212,.28)); animation:pop .8s cubic-bezier(.2,1.4,.4,1);}
@keyframes pop{0%{transform:scale(.3) rotate(-18deg); opacity:0;}100%{transform:scale(1) rotate(0); opacity:1;}}
.trophy .k{font-size:.66rem; font-weight:700; letter-spacing:.2em; color:var(--cyan-ink); margin-top:1rem; text-transform:uppercase;}
.trophy .rank{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:clamp(1.7rem,4.4vw,2.5rem); font-weight:700; letter-spacing:-.01em;
  margin:.55rem 0 .3rem; color:var(--navy); background:none; -webkit-text-fill-color:currentColor;
}
.trophy .who{color:var(--muted); font-size:1rem;}
.trophy .who b{color:var(--navy);}
.metrics{display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:.6rem; margin:1.2rem 0 .4rem;}
.metric{background:#F5FAFB; border:1px solid var(--line); border-radius:9px; padding:.85rem .7rem; text-align:center;}
.metric .v{
  font-family:'Titillium Web','Segoe UI',sans-serif;
  font-size:1.5rem; font-weight:700; color:var(--navy); line-height:1.1; font-variant-numeric:tabular-nums;
}
.metric .l{font-size:.63rem; letter-spacing:.11em; color:var(--muted); text-transform:uppercase; font-weight:700; margin-top:.3rem;}

.map{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:.55rem; margin-top:.6rem;}
.map .mi{background:#F7FBFC; border:1px solid var(--line); border-radius:9px; padding:.7rem .85rem;}
.map .mi.ok{border-color:#B7DFC0; background:var(--good-soft);}
.map .mi.mid{border-color:#E2E3B8; background:var(--lime-soft);}
.map .mi.bad{border-color:#F0C7C3; background:var(--bad-soft);}
.map .mi .n{font-family:'Titillium Web','Segoe UI',sans-serif; font-size:.86rem; font-weight:700; color:var(--navy);}
.map .mi .s{font-size:.9rem; letter-spacing:.08em; color:var(--lime-dark);}
.map .mi .s .off{color:#CBDDE2;}
.map .mi .c{font-size:.72rem; color:var(--muted);}

.rev{background:#F7FBFC; border:1px solid var(--line); border-radius:9px; padding:.75rem .9rem; margin:.45rem 0;}
.rev.ok{border-left:3px solid var(--good);}
.rev.ko{border-left:3px solid var(--bad);}
.rev .q{font-weight:600; color:var(--ink); font-size:.88rem; line-height:1.45;}
.rev .a{font-size:.78rem; color:var(--muted); margin-top:.35rem;}
.rev .a b{color:var(--bad); font-weight:600;}
.rev .a b.g{color:var(--good);}
.rev .w{font-size:.78rem; color:var(--body); margin-top:.35rem; line-height:1.55;}

/* ---------- Confeti ---------- */
.confetti{position:fixed; inset:0; pointer-events:none; overflow:hidden; z-index:9999;}
.confetti i{position:absolute; top:-8vh; border-radius:1px; animation:fall 6s linear forwards;}
@keyframes fall{to{transform:translateY(112vh) rotate(260deg); opacity:0;}}

/* ---------- Expander ---------- */
[data-testid="stExpander"]{margin-top:.35rem;}
[data-testid="stExpander"] details{
  background:var(--card) !important;
  border:1px solid var(--line) !important; border-radius:9px !important;
}
[data-testid="stExpander"] summary{color:var(--navy) !important; font-weight:600 !important; font-size:.9rem !important;}
[data-testid="stExpander"] summary:hover{color:var(--cyan-ink) !important;}

[data-testid="stDownloadButton"]{margin-top:.55rem;}
[data-testid="stDownloadButton"] button{
  justify-content:center !important;
  background:var(--navy) !important; border:1px solid var(--navy) !important;
  color:#FFFFFF !important; font-weight:600 !important; letter-spacing:.04em;
  box-shadow:0 10px 22px -14px rgba(50,71,123,.65) !important;
}
[data-testid="stDownloadButton"] button:hover{
  background:var(--navy-deep) !important; border-color:var(--navy-deep) !important;
  color:#FFFFFF !important; transform:none !important;
  box-shadow:0 12px 24px -14px rgba(50,71,123,.7) !important;
}
[data-testid="stDownloadButton"] button > div{justify-content:center !important;}
[data-testid="stDownloadButton"] button p{
  color:#FFFFFF !important; font-weight:600 !important; font-size:1rem !important;
  text-align:center !important; padding-left:0 !important; text-indent:0 !important;
}

[data-testid="stImage"] img{border-radius:9px; border:1px solid var(--line);}
[data-testid="stAudio"]{display:none !important; height:0 !important; margin:0 !important;}

/* ---------- Tablet ---------- */
@media (max-width:1024px){
  .block-container{
    max-width:100%;
    padding-left:1.5rem; padding-right:1.5rem;
    padding-top:2rem; padding-bottom:3rem;
  }
  .stApp .hero-title{font-size:clamp(1.7rem,5.4vw,3rem);}
  .hud{grid-template-columns:repeat(auto-fit,minmax(100px,1fr));}
  .mini{grid-template-columns:repeat(2,1fr);}
}

/* ---------- Smartphone ---------- */
@media (max-width:640px){
  .block-container{
    padding-left:1rem; padding-right:1rem;
    padding-top:1.4rem; padding-bottom:2.5rem;
  }
  .stApp{background-attachment:scroll;}
  .kicker{font-size:.6rem; letter-spacing:.1em;}
  .stApp .hero-title{font-size:clamp(1.55rem,7vw,2.2rem);}
  .hero-sub{font-size:.98rem; line-height:1.6;}
  .brand{gap:.65rem; margin-bottom:.9rem;}
  .brand-logo{height:42px;}
  .brand-name{font-size:.7rem; letter-spacing:.005em;}
  .brand-area{font-size:.62rem;}
  .hud{grid-template-columns:repeat(auto-fit,minmax(92px,1fr)); gap:.45rem;}
  .hud-item{padding:.55rem .6rem;}
  .hud-label{font-size:.58rem; letter-spacing:.09em;}
  .hud-value{font-size:1.02rem;}
  .card{padding:1.1rem 1.15rem; border-radius:10px;}
  .reto-head{gap:.75rem;}
  .reto-ico{width:50px; height:50px; flex-basis:50px; font-size:1.5rem; border-radius:9px;}
  .stApp .reto-name{font-size:1.35rem;}
  .reto-sub{font-size:.9rem;}
  .verdict{flex-wrap:wrap;}
  .verdict .v-pts{margin-left:0;}
  .chips{gap:.4rem; margin:1.2rem 0 1.4rem;}
  .chip{font-size:.72rem; padding:.35rem .65rem;}
  .mini{grid-template-columns:1fr;}
  .metrics{grid-template-columns:repeat(2,1fr);}
  .map{grid-template-columns:1fr 1fr;}
  .trophy{padding:1.3rem .8rem 1rem;}
  .trophy .medal{font-size:3.6rem;}
  .trophy .who{font-size:.94rem;}
  .foot{font-size:.82rem;}
}

@media (max-width:400px){
  .stApp .hero-title{font-size:1.5rem;}
}

@media (max-width:360px){
  .map{grid-template-columns:1fr;}
}

@media (max-width:340px){
  .stApp .hero-title{font-size:1.32rem;}
  .hud{grid-template-columns:repeat(auto-fit,minmax(82px,1fr));}
  .chip{font-size:.68rem; padding:.32rem .55rem;}
  .block-container{padding-left:.85rem; padding-right:.85rem;}
}
</style>
"""


# --------------------------------------------------------------------------------------
# Estado de la evaluación
# --------------------------------------------------------------------------------------

DEFAULTS = {
    "phase": "start",
    "level": 0,
    "q": 0,
    "score": 0,
    "lives": BASE_LIVES,
    "streak": 0,
    "best_streak": 0,
    "correct": 0,
    "answers": [],
    "last": None,
    "player": "",
    "training": False,
    "started": None,
    "name_error": False,
    "sound_event": None,
    "completed_sound_played": False,
    "participant_id": None,
    "saved": False,
    "save_ok": None,
    "admin_ok": False,
    "admin_last_seen": 0.0,
    "admin_attempts": 0,
    "admin_locked_until": 0.0,
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = [] if key == "answers" else value
    st.session_state.pop("player_name", None)


def start_game(name: str, training: bool) -> None:
    reset_game()
    st.session_state.player = name
    st.session_state.training = training
    st.session_state.lives = BASE_LIVES
    st.session_state.started = datetime.now()
    st.session_state.participant_id = uuid.uuid4().hex
    st.session_state.phase = "briefing"


def current_level() -> dict:
    return LEVELS[st.session_state.level]


def current_question() -> dict:
    return current_level()["questions"][st.session_state.q]


def go_next() -> None:
    st.session_state.last = None
    level = current_level()

    if st.session_state.q + 1 < len(level["questions"]):
        st.session_state.q += 1
        st.session_state.phase = "question"
    elif st.session_state.level + 1 < len(LEVELS):
        st.session_state.level += 1
        st.session_state.q = 0
        st.session_state.phase = "briefing"
    else:
        st.session_state.phase = "final"


def answer(index: int) -> None:
    q = current_question()
    level = current_level()
    ok = index == q["answer"]

    if ok:
        gained = 100 + 20 * st.session_state.streak
        st.session_state.score += gained
        st.session_state.streak += 1
        st.session_state.best_streak = max(st.session_state.best_streak, st.session_state.streak)
        st.session_state.correct += 1
    else:
        gained = 0
        st.session_state.streak = 0
        if not st.session_state.training:
            st.session_state.lives = max(0, st.session_state.lives - 1)

    st.session_state.answers.append(
        {
            "level": level["id"],
            "level_name": level["name"],
            "icon": level["icon"],
            "q": q["q"],
            "options": q["options"],
            "chosen": index,
            "answer": q["answer"],
            "ok": ok,
            "why": q["why"],
            "source": q["source"],
        }
    )
    st.session_state.last = {"ok": ok, "gained": gained, "chosen": index}
    st.session_state.sound_event = "ok" if ok else "ko"
    st.session_state.phase = "feedback"


def after_feedback() -> None:
    if not st.session_state.training and st.session_state.lives <= 0:
        st.session_state.phase = "gameover"
        return
    go_next()


# --------------------------------------------------------------------------------------
# Piezas de interfaz
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def sound_wav(kind: str) -> bytes:
    return build_sound(kind)


def play_sound(kind: str) -> None:
    """Reproduce un tono breve si el participante no ha silenciado la app."""
    if st.session_state.get("sound_on", True):
        st.audio(sound_wav(kind), format="audio/wav", autoplay=True, alt=f"Sonido {kind}")


def hud(level_index: int, question_index: int) -> None:
    s = st.session_state
    done = len(s.answers)
    pct = done / TOTAL_QUESTIONS * 100 if TOTAL_QUESTIONS else 0
    attempts = "∞" if s.training else f"{s.lives}<span class='dim'> / {BASE_LIVES}</span>"
    streak = f"×{s.streak}" if s.streak > 1 else "—"
    lives_class = " training" if s.training else (" empty" if s.lives == 0 else "")
    st.markdown(
        f"""
        <div class="hud">
          <div class="hud-item"><span class="hud-label">Módulo</span>
            <span class="hud-value">{level_index + 1:02d}<span class="dim"> / {len(LEVELS)}</span></span></div>
          <div class="hud-item score"><span class="hud-label">Puntos</span>
            <span class="hud-value">{fmt_num(s.score)}</span></div>
          <div class="hud-item lives{lives_class}"><span class="hud-label">Intentos</span>
            <span class="hud-value">{attempts}</span></div>
          <div class="hud-item streak"><span class="hud-label">Racha</span>
            <span class="hud-value">{streak}</span></div>
          <div class="hud-item"><span class="hud-label">Avance</span>
            <span class="hud-value">{done}<span class="dim"> / {TOTAL_QUESTIONS}</span></span></div>
        </div>
        <div class="bar"><div class="bar-fill" style="width:{pct:.1f}%"></div></div>
        """,
        unsafe_allow_html=True,
    )


def reto_head(level: dict, pill: str | None = None) -> None:
    pill_html = f'<div class="pill">{pill}</div>' if pill else ""
    st.markdown(
        f"""
        <div class="reto-head">
          <div class="reto-ico">{level["icon"]}</div>
          <div>
            {pill_html}
            <h1 class="reto-name">{html.escape(level["name"])}</h1>
            <p class="reto-sub">{html.escape(level["subtitle"])}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_start() -> None:
    logo_uri = logo_data_uri()
    logo_img = (
        f'<img class="brand-logo" src="{logo_uri}" alt="Hospital General de la Plaza de la Salud">'
        if logo_uri else ""
    )
    st.markdown(
        f"""
        <div style="margin-top:.4rem">
          <div class="brand">
            {logo_img}
            <div class="brand-text">
              <span class="brand-name">Hospital General de la Plaza de la Salud</span>
              <span class="brand-area">Gerencia de Farmacia</span>
            </div>
          </div>
          <h1 class="hero-title">CHARLA DE DISPENSACIÓN<br><span class="grad">HOSPITALARIA</span></h1>
          <p class="hero-sub">Repaso interactivo de la charla para la Gerencia de Farmacia: once módulos,
          tres intentos y un objetivo: que ningún medicamento llegue al paciente equivocado.
          Cada módulo te acerca al certificado.</p>
          <div class="chips">
            <span class="chip">📚 <b>{len(LEVELS)}</b> módulos</span>
            <span class="chip">🧠 <b>{TOTAL_QUESTIONS}</b> preguntas</span>
            <span class="chip">✅ <b>{BASE_LIVES}</b> intentos</span>
            <span class="chip">🏅 Certificado final</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="playerpanel"):
        st.markdown('<div class="kicker">▸ Ficha del participante</div>', unsafe_allow_html=True)
        name = st.text_input(
            "Nombre del participante",
            key="player_name",
            placeholder="Nombre y apellido",
            max_chars=40,
            label_visibility="visible",
        )
        training = st.checkbox("Modo práctica (sin límite de intentos)", value=False)
        st.checkbox("Activar sonidos de acierto, error y finalización", value=True, key="sound_on")
        st.caption("Tu nombre y los resultados se guardan solo para el seguimiento de esta charla.")
        if st.session_state.name_error:
            st.markdown('<div class="err">Necesitamos tu nombre para emitir el certificado.</div>', unsafe_allow_html=True)

        if st.button("▶  INICIAR EVALUACIÓN", type="primary", **WIDTH_KW):
            clean = (name or "").strip()
            if not clean:
                st.session_state.name_error = True
                st.rerun()
            start_game(clean, training)
            st.rerun()

    st.markdown(
        """
        <div class="mini">
          <div class="m"><div class="ic">🗺️</div><div class="t">Recorre los 11 módulos</div>
            <div class="d">De los conceptos básicos al cierre: sinergia y corazón de farmacia.</div></div>
          <div class="m"><div class="ic">📈</div><div class="t">Suma aciertos consecutivos</div>
            <div class="d">Cada acierto encadenado suma más puntos. Un error reinicia la racha.</div></div>
          <div class="m"><div class="ic">🛡️</div><div class="t">Cuida tus intentos</div>
            <div class="d">Tres errores finalizan la evaluación. En modo práctica puedes repetir sin riesgo.</div></div>
          <div class="m"><div class="ic">🎓</div><div class="t">Obtén tu certificado</div>
            <div class="d">Al completar la evaluación descargas tu diploma con puntuación y rango.</div></div>
        </div>
        <div class="foot"><b>Hospital General de la Plaza de la Salud (HGPS) · Gerencia de Farmacia.</b><br>
        Basado en la charla <b>«Dispensación Hospitalaria: Procesos, Seguridad y el Valor Humano»</b>.
        Contenido: conceptos, tipos de dispensación, 7 correctos, flujo operativo, LASA, Decreto 246-06, Ley 50-88,
        rol del farmacéutico y del auxiliar.</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="foot-links">'
        '<a class="admin-link" href="?ejemplo=1" target="_self">Ver ejemplo del certificado</a>'
        '<a class="admin-link" href="?admin=1" target="_self">Acceso administradores</a>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_briefing() -> None:
    level = current_level()
    hud(st.session_state.level, 0)
    reto_head(level, pill=f"Módulo {st.session_state.level + 1:02d} de {len(LEVELS)}")
    bullets = "".join(f"<li>{b}</li>" for b in level["briefing"])
    st.markdown(
        f"""
        <div class="card">
          <div class="kicker" style="color:#32477B">▸ Ideas clave del módulo</div>
          <ul class="brief" style="margin:.4rem 0 0; padding-left:1.1rem;">{bullets}</ul>
          <div class="tip"><b>Regla de oro:</b> {level["tip"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("▶  ENTRAR AL MÓDULO", type="primary", **WIDTH_KW):
        st.session_state.phase = "question"
        st.rerun()


def render_question() -> None:
    level = current_level()
    q = current_question()
    s = st.session_state
    hud(s.level, s.q)
    reto_head(level, pill=f"Pregunta {s.q + 1} de {len(level['questions'])}")

    st.markdown(
        f"""
        <div class="card card-glow" style="margin-bottom:1.1rem;">
          <div class="qmeta">▸ Elige la respuesta correcta</div>
          <p class="qtext">{html.escape(q["q"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for i, option in enumerate(q["options"]):
        if st.button(f"{LETTERS[i]}   {option}", key=f"opt_{level['id']}_{s.q}_{i}", **WIDTH_KW):
            answer(i)
            st.rerun()

    st.markdown(
        '<div style="height:.4rem"></div>'
        '<div style="text-align:center;color:#4E616E;font-size:.78rem;">'
        f"Aciertos: {s.correct} · Racha actual: ×{max(s.streak, 1)}</div>",
        unsafe_allow_html=True,
    )
    if st.button("↺  Reiniciar evaluación", type="tertiary", key=f"reset_{level['id']}_{s.q}"):
        reset_game()
        st.rerun()


def render_feedback() -> None:
    s = st.session_state
    level = current_level()
    q = current_question()
    last = s.last or {"ok": False, "gained": 0, "chosen": 0}
    chosen = last["chosen"]
    ok = last["ok"]

    hud(st.session_state.level, st.session_state.q)

    if s.sound_event:
        play_sound(s.sound_event)
        s.sound_event = None

    if ok:
        mod, ico, title = "ok", "✅", "¡CORRECTO!"
        sub = "Acierto registrado. El paciente está a salvo."
        pts = f"+{last['gained']}"
    else:
        mod, ico, title = "ko", "❌", "INCORRECTO"
        sub = "Revisa el razonamiento: aquí se aprende."
        pts = "0"

    st.markdown(
        f"""
        <div class="verdict {mod}">
          <div class="v-ico">{ico}</div>
          <div>
            <p class="v-title">{title}</p>
            <p class="v-sub">{sub}</p>
          </div>
          <div class="v-pts">{pts} pts</div>
        </div>
        <div class="card">
          <p class="answer-line"><span class="k">Tu respuesta:</span> {LETTERS[chosen]} · {html.escape(q["options"][chosen])}</p>
          <p class="answer-line"><span class="k">Respuesta correcta:</span>
             <b style="color:#2E7D32">{LETTERS[q["answer"]]} · {html.escape(q["options"][q["answer"]])}</b></p>
          <div class="why" style="margin-top:.8rem;">
            <span class="h">Por qué</span>{html.escape(q["why"])}
          </div>
          <div class="src">📍 Fuente: {html.escape(q["source"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if s.get("sound_on", True):
        if st.button("🔊  Repetir sonido", type="tertiary", key=f"sonido_{s.level}_{s.q}"):
            s.sound_event = "ok" if ok else "ko"
            st.rerun()

    label = "CONTINUAR  ▶" if (s.q + 1 < len(level["questions"]) or s.level + 1 < len(LEVELS)) else "VER RESULTADO FINAL  🏁"
    if st.button(label, type="primary", **WIDTH_KW):
        after_feedback()
        st.rerun()


def _confetti() -> str:
    colors = ["#32477B", "#00BCD4", "#00A5BA", "#BABF33"]
    rnd = random.Random(7)
    spans = "".join(
        f'<i style="left:{rnd.uniform(1, 97):.1f}%;animation-delay:{rnd.uniform(0, 2.2):.2f}s;'
        f'animation-duration:{rnd.uniform(5.0, 7.5):.2f}s;'
        f'width:{rnd.randint(5, 9)}px;height:{rnd.randint(8, 14)}px;'
        f'background:{rnd.choice(colors)};opacity:{rnd.uniform(.35, .7):.2f};"></i>'
        for _ in range(26)
    )
    return f'<div class="confetti">{spans}</div>'


@st.cache_data(show_spinner=False, max_entries=16)
def certificate_bytes(name: str, score: int, accuracy: float, correct: int, total: int, rank: str, streak: int) -> bytes:
    return build_certificate(
        name=name,
        score=score,
        accuracy=accuracy,
        correct=correct,
        total=total,
        rank_title=rank,
        streak=streak,
    )


@st.cache_data(show_spinner=False, max_entries=8)
def report_bytes(
    name: str,
    score: int,
    accuracy: float,
    correct: int,
    total: int,
    rank: str,
    streak: int,
    elapsed: int,
    training: bool,
    answers: list[dict],
) -> bytes:
    return build_followup_report(
        name=name,
        score=score,
        accuracy=accuracy,
        correct=correct,
        total=total,
        rank_title=rank,
        streak=streak,
        elapsed=elapsed,
        answers=answers,
        levels=LEVELS,
        training=training,
    )


@st.cache_data(show_spinner=False, max_entries=8)
def full_report_pdf(cert_png: bytes, report_png: bytes) -> bytes:
    return build_report_pdf(cert_png, report_png)


@st.cache_data(show_spinner=False, max_entries=4)
def executive_report_bytes(summary: dict, records: list[dict], mode: str, when: date) -> bytes:
    return build_executive_pdf(summary, records, LEVELS, mode, when)


def render_final() -> None:
    s = st.session_state
    accuracy = s.correct / TOTAL_QUESTIONS if TOTAL_QUESTIONS else 0.0
    title, icon, message = rank_for(accuracy)
    elapsed = int((datetime.now() - s.started).total_seconds()) if s.started else 0
    minutes, seconds = divmod(max(elapsed, 0), 60)

    if not s.saved:
        if not s.participant_id:
            s.participant_id = uuid.uuid4().hex
        s.save_ok = save_result(
            {
                "id": s.participant_id,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "name": s.player,
                "training": s.training,
                "score": s.score,
                "correct": s.correct,
                "total": TOTAL_QUESTIONS,
                "accuracy": accuracy,
                "best_streak": s.best_streak,
                "elapsed": elapsed,
                "rank": title,
                "answers": s.answers,
            }
        )
        s.saved = True

    st.markdown(_confetti(), unsafe_allow_html=True)

    if not s.completed_sound_played:
        play_sound("done")
        s.completed_sound_played = True

    st.markdown(
        f"""
        <div class="trophy">
          <div class="medal">{icon}</div>
          <div class="k">EVALUACIÓN COMPLETADA</div>
          <div class="rank">{html.escape(title)}</div>
          <div class="who">Otorgado a <b>{html.escape(s.player)}</b></div>
          <div class="metrics">
            <div class="metric"><div class="v">{fmt_num(s.score)}</div><div class="l">Puntos</div></div>
            <div class="metric"><div class="v">{s.correct}/{TOTAL_QUESTIONS}</div><div class="l">Aciertos</div></div>
            <div class="metric"><div class="v">{accuracy * 100:.0f}%</div><div class="l">Precisión</div></div>
            <div class="metric"><div class="v">×{s.best_streak}</div><div class="l">Mejor racha</div></div>
            <div class="metric"><div class="v">{minutes:02d}:{seconds:02d}</div><div class="l">Tiempo</div></div>
          </div>
          <div class="who" style="margin-top:.9rem;font-size:.92rem;">{html.escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if s.save_ok:
        st.caption("Resultado registrado para el panel de seguimiento.")
    else:
        st.caption("El certificado está listo. El resultado no pudo enviarse al panel de seguimiento.")

    # Mapa de módulos
    cards = []
    for level in LEVELS:
        answers = [a for a in s.answers if a["level"] == level["id"]]
        got = sum(1 for a in answers if a["ok"])
        total_lvl = len(level["questions"])
        ratio = got / total_lvl
        cls = "ok" if ratio == 1 else ("mid" if ratio >= 0.5 else "bad")
        stars = "★" * (3 if ratio == 1 else 2 if ratio >= 0.5 else 1) + "☆" * (
            0 if ratio == 1 else 1 if ratio >= 0.5 else 2
        )
        cards.append(
            f'<div class="mi {cls}"><div class="n">{level["icon"]} {html.escape(level["name"])}</div>'
            f'<div class="s">{stars}</div><div class="c">{got} de {total_lvl} aciertos</div></div>'
        )
    st.markdown(
        '<div class="card"><div class="kicker" style="color:#32477B">▸ Mapa de módulos</div>'
        f'<div class="map">{"".join(cards)}</div></div>',
        unsafe_allow_html=True,
    )

    # Certificado
    png = certificate_bytes(
        name=s.player,
        score=s.score,
        accuracy=accuracy,
        correct=s.correct,
        total=TOTAL_QUESTIONS,
        rank=title,
        streak=s.best_streak,
    )
    report_png = report_bytes(
        name=s.player,
        score=s.score,
        accuracy=accuracy,
        correct=s.correct,
        total=TOTAL_QUESTIONS,
        rank=title,
        streak=s.best_streak,
        elapsed=elapsed,
        training=s.training,
        answers=s.answers,
    )
    pdf = full_report_pdf(png, report_png)

    st.markdown('<div class="kicker">▸ Tu diploma y seguimiento</div>', unsafe_allow_html=True)
    cert_tab, follow_tab = st.tabs(["🎓  Certificado", "📈  Seguimiento"])
    safe_name = safe_filename(s.player)
    with cert_tab:
        st.image(png, width="stretch")
        st.download_button(
            "⬇  DESCARGAR CERTIFICADO (PNG)",
            data=png,
            file_name=f"certificado_dispensacion_{safe_name}.png",
            mime="image/png",
            **WIDTH_KW,
        )
    with follow_tab:
        st.image(report_png, width="stretch")

    st.download_button(
        "⬇  DESCARGAR INFORME COMPLETO (PDF · 2 PÁGINAS)",
        data=pdf,
        file_name=f"informe_dispensacion_{safe_name}.pdf",
        mime="application/pdf",
        **WIDTH_KW,
    )
    st.caption("La página 1 es el certificado en formato landscape; la página 2 es el seguimiento con mapa y áreas de mejora.")

    with st.expander("🔍  Repasar mis respuestas y explicaciones"):
        for a in s.answers:
            cls = "ok" if a["ok"] else "ko"
            mark = "✔" if a["ok"] else "✘"
            st.markdown(
                f"""
                <div class="rev {cls}">
                  <div class="q">{mark} {html.escape(a["q"])}</div>
                  <div class="a">Tu respuesta: <b class="{'g' if a['ok'] else ''}">{html.escape(a["options"][a["chosen"]])}</b></div>
                  {"" if a["ok"] else f'<div class="a">Correcta: <b class="g">{html.escape(a["options"][a["answer"]])}</b></div>'}
                  <div class="w">{html.escape(a["why"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    if st.button("↺  REPETIR EVALUACIÓN", type="primary", **WIDTH_KW):
        reset_game()
        st.rerun()


def render_gameover() -> None:
    s = st.session_state
    accuracy = s.correct / TOTAL_QUESTIONS if TOTAL_QUESTIONS else 0.0
    level = current_level()
    st.markdown(
        f"""
        <div class="trophy">
          <div class="medal">📋</div>
          <div class="k" style="color:#B3261E">EVALUACIÓN FINALIZADA</div>
          <div class="rank" style="color:#B3261E;">SIN INTENTOS</div>
          <div class="who"><b>{html.escape(s.player)}</b> se detuvo en el módulo {s.level + 1:02d}:
            {html.escape(level["name"])}</div>
          <div class="metrics">
            <div class="metric"><div class="v">{fmt_num(s.score)}</div><div class="l">Puntos</div></div>
            <div class="metric"><div class="v">{s.correct}/{TOTAL_QUESTIONS}</div><div class="l">Aciertos</div></div>
            <div class="metric"><div class="v">{accuracy * 100:.0f}%</div><div class="l">Precisión</div></div>
            <div class="metric"><div class="v">×{s.best_streak}</div><div class="l">Mejor racha</div></div>
          </div>
          <div class="who" style="margin-top:.9rem;font-size:.92rem;">
            En una farmacia real, el error no se reinicia: se previene.
            Repasa y vuelve a intentarlo.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🔍  ¿Dónde fallé?"):
        for a in s.answers[-6:]:
            if a["ok"]:
                continue
            st.markdown(
                f"""
                <div class="rev ko">
                  <div class="q">✘ {html.escape(a["q"])}</div>
                  <div class="a">Elegiste: <b>{html.escape(a["options"][a["chosen"]])}</b></div>
                  <div class="a">Correcta: <b class="g">{html.escape(a["options"][a["answer"]])}</b></div>
                  <div class="w">{html.escape(a["why"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button("↺  REINTENTAR EVALUACIÓN", type="primary", **WIDTH_KW):
        reset_game()
        st.rerun()




# --------------------------------------------------------------------------------------
# Panel de administración
# --------------------------------------------------------------------------------------

def _record_date(record: dict) -> date:
    try:
        return datetime.fromisoformat(str(record.get("created_at", ""))).date()
    except (TypeError, ValueError):
        return date.today()


def _leave_admin() -> None:
    st.session_state.admin_ok = False
    st.session_state.admin_last_seen = 0.0
    st.session_state.admin_attempts = 0
    st.session_state.admin_locked_until = 0.0
    st.query_params.clear()
    st.rerun()


def _brand_header(area: str) -> str:
    uri = logo_data_uri()
    logo = (
        f'<img class="brand-logo" src="{uri}" alt="Hospital General de la Plaza de la Salud">'
        if uri else ""
    )
    return (
        f'<div class="brand">{logo}'
        '<div class="brand-text">'
        '<span class="brand-name">Hospital General de la Plaza de la Salud</span>'
        f'<span class="brand-area">{html.escape(area)}</span>'
        "</div></div>"
    )




def _render_admin_summary(summary: dict, records: list[dict], mode: str) -> None:
    minutes, seconds = divmod(int(round(summary["avg_elapsed"])), 60)
    st.markdown('<div class="kicker">▸ Resumen general</div>', unsafe_allow_html=True)
    st.caption(
        "Precisión global ponderada = aciertos totales / preguntas respondidas. "
        "El resumen refleja el filtro de modo seleccionado."
    )
    st.markdown(
        f"""
        <div class="card">
          <div class="metrics">
            <div class="metric"><div class="v">{summary['count']}</div><div class="l">Participantes</div></div>
            <div class="metric"><div class="v">{summary['weighted_accuracy'] * 100:.0f}%</div><div class="l">Precisión ponderada</div></div>
            <div class="metric"><div class="v">{fmt_num(int(round(summary['avg_score'])))}</div><div class="l">Puntuación promedio</div></div>
            <div class="metric"><div class="v">{summary['avg_streak']:.1f}</div><div class="l">Racha promedio</div></div>
            <div class="metric"><div class="v">{minutes:02d}:{seconds:02d}</div><div class="l">Tiempo promedio</div></div>
            <div class="metric"><div class="v">{summary['pct_90'] * 100:.0f}%</div><div class="l">Con 90% o más</div></div>
          </div>
          <div class="src">
            {summary['evaluations']} evaluación(es) · {summary['practice']} práctica(s) ·
            {summary['total_correct']} aciertos de {summary['total_questions']} preguntas ·
            {summary['pct_70'] * 100:.0f}% alcanzó 70% o más.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    module_rows = [
        {
            "Módulo": module["name"],
            "Aciertos": f"{module['correct']}/{module['answered']}" if module["answered"] else "—",
            "Precisión": round(module["accuracy"] * 100, 1),
        }
        for module in summary["modules"]
    ]
    rank_rows = [
        {
            "Rango": rank["title"],
            "Participantes": rank["count"],
            "%": f"{rank['pct'] * 100:.0f}%",
        }
        for rank in summary["ranks"]
    ]

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="kicker">▸ Precisión por módulo</div>', unsafe_allow_html=True)
        st.dataframe(
            module_rows,
            hide_index=True,
            width="stretch",
            height=470,
            column_config={
                "Precisión": st.column_config.ProgressColumn(
                    "Precisión", min_value=0, max_value=100, format="%.0f%%"
                )
            },
        )
    with right:
        st.markdown('<div class="kicker">▸ Distribución por rango</div>', unsafe_allow_html=True)
        st.dataframe(rank_rows, hide_index=True, width="stretch")

    if summary["weak_modules"]:
        names = ", ".join(html.escape(module["name"]) for module in summary["weak_modules"][:4])
        st.caption(f"Módulos por debajo del 70 %: {names}.")
    else:
        st.caption("Todos los módulos con respuestas están en 70 % o más.")

    today = date.today()
    pdf = executive_report_bytes(summary, records, mode, today)
    st.download_button(
        "⬇  DESCARGAR INFORME EJECUTIVO (PDF · 4 PÁGINAS)",
        data=pdf,
        file_name=f"informe_ejecutivo_HGPS_{today:%Y%m%d}.pdf",
        mime="application/pdf",
        key="admin_executive_pdf",
        **WIDTH_KW,
    )
    st.caption(
        "Incluye resumen ejecutivo, discurso para la reunión, indicadores, módulos, "
        "distribución por rango, arquitectura, controles de seguridad y notas."
    )


def render_admin() -> None:
    st.markdown(_brand_header("Panel de administración"), unsafe_allow_html=True)
    st.markdown(
        '<h1 class="hero-title" style="font-size:clamp(1.7rem,4vw,2.6rem);">Panel de seguimiento</h1>'
        '<p class="hero-sub">Resultados de la evaluación de la charla, por participante.</p>',
        unsafe_allow_html=True,
    )

    password = admin_password()
    if not password:
        st.warning(
            "Falta configurar la clave de administración. Agrega `admin_password` en "
            "`.streamlit/secrets.toml` (o en los secrets de Streamlit Cloud)."
        )
        st.code(
            """admin_password = "una-clave-larga"
results_webhook = "https://script.google.com/macros/s/.../exec"
results_token = "el-mismo-token-del-script""",
            language="toml",
        )
        if st.button("Volver al inicio", type="tertiary"):
            _leave_admin()
        return

    now = time.time()
    if st.session_state.get("admin_ok"):
        last_seen = float(st.session_state.get("admin_last_seen", 0) or 0)
        if last_seen and now - last_seen > ADMIN_SESSION_SECONDS:
            st.session_state.admin_ok = False
            st.session_state.admin_last_seen = 0.0
            st.warning("La sesión de administración expiró. Vuelve a ingresar la clave.")
        else:
            st.session_state.admin_last_seen = now

    if not st.session_state.get("admin_ok"):
        locked_until = float(st.session_state.get("admin_locked_until", 0) or 0)
        if locked_until > now:
            st.error(f"Demasiados intentos. Espera {int(locked_until - now) + 1} segundos.")
            if st.button("Volver al inicio", type="tertiary"):
                _leave_admin()
            return

        with st.container(border=True, key="adminlogin"):
            st.markdown('<div class="kicker">▸ Acceso restringido</div>', unsafe_allow_html=True)
            with st.form("admin_login"):
                pwd = st.text_input("Clave de administración", type="password")
                submitted = st.form_submit_button("Entrar", type="primary")
            if submitted:
                if hmac.compare_digest(pwd, password):
                    st.session_state.admin_ok = True
                    st.session_state.admin_attempts = 0
                    st.session_state.admin_locked_until = 0.0
                    st.session_state.admin_last_seen = time.time()
                    st.rerun()
                attempts = int(st.session_state.get("admin_attempts", 0) or 0) + 1
                st.session_state.admin_attempts = attempts
                if attempts >= ADMIN_MAX_ATTEMPTS:
                    st.session_state.admin_attempts = 0
                    st.session_state.admin_locked_until = time.time() + ADMIN_LOCK_SECONDS
                    st.error(f"Demasiados intentos. Espera {ADMIN_LOCK_SECONDS} segundos.")
                else:
                    st.error(f"Clave incorrecta. Intento {attempts} de {ADMIN_MAX_ATTEMPTS}.")
        if st.button("Volver al inicio", type="tertiary"):
            _leave_admin()
        return

    records, error = load_results()
    top_left, top_refresh, top_preview = st.columns([3, 1, 1])
    with top_left:
        st.caption(
            f"Origen de datos: {backend_name()} · "
            f"{len(records)} participante(s) registrados."
        )
    with top_refresh:
        if st.button("↻  Actualizar", type="secondary", **WIDTH_KW):
            st.rerun()
    with top_preview:
        if st.button("👁  Ver ejemplo", type="secondary", **WIDTH_KW):
            st.query_params["ejemplo"] = "1"
            st.rerun()

    if error:
        st.error(error)
    if not records:
        st.info("Todavía no hay resultados. Los participantes aparecerán aquí al completar la evaluación.")
    else:
        mode = st.selectbox("Filtrar por modo", ["Todos", "Evaluación", "Práctica"], key="admin_mode")
        filtered = [
            r for r in records
            if mode == "Todos"
            or (mode == "Práctica" and r.get("training"))
            or (mode == "Evaluación" and not r.get("training"))
        ]
        filtered.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)

        if not filtered:
            st.info("No hay participantes en este filtro.")
        else:
            _render_admin_summary(summarize_records(filtered, LEVELS), filtered, mode)
            st.markdown('<div class="kicker">▸ Participantes</div>', unsafe_allow_html=True)
            table = []
            for r in filtered:
                total = int(r.get("total", TOTAL_QUESTIONS) or TOTAL_QUESTIONS)
                correct = int(r.get("correct", 0) or 0)
                accuracy = float(r.get("accuracy", correct / total if total else 0) or 0)
                table.append(
                    {
                        "Participante": r.get("name", "—"),
                        "Fecha": _record_date(r).strftime("%d/%m/%Y"),
                        "Modo": "Práctica" if r.get("training") else "Evaluación",
                        "Puntos": r.get("score", 0),
                        "Aciertos": f"{correct}/{total}",
                        "Precisión": f"{accuracy * 100:.0f}%",
                        "Mejor racha": r.get("best_streak", 0),
                        "Rango": r.get("rank", "—"),
                    }
                )
            st.dataframe(table, hide_index=True, width="stretch")

            labels = [
                f"{r.get('name', '—')} · {_record_date(r).strftime('%d/%m/%Y')} · "
                f"{r.get('score', 0)} pts"
                for r in filtered
            ]
            choice = st.selectbox(
                "Ver detalle de un participante",
                range(len(filtered)),
                format_func=lambda i: labels[i],
                key="admin_participant",
            )
            record = filtered[int(choice)]

            answers = record.get("answers") or []
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except ValueError:
                    answers = []

            total = int(record.get("total", TOTAL_QUESTIONS) or TOTAL_QUESTIONS)
            correct = int(record.get("correct", 0) or 0)
            accuracy = float(record.get("accuracy", correct / total if total else 0) or 0)
            score = int(record.get("score", 0) or 0)
            streak = int(record.get("best_streak", 0) or 0)
            elapsed = int(record.get("elapsed", 0) or 0)
            rank = str(record.get("rank", "") or rank_for(accuracy)[0])
            name = str(record.get("name", "—"))
            when = _record_date(record)
            minutes, seconds = divmod(max(elapsed, 0), 60)

            st.markdown(
                f"""
                <div class="card" style="margin-top:1rem;">
                  <div class="kicker">▸ Detalle del participante</div>
                  <p class="qtext" style="margin-bottom:.4rem;">{html.escape(name)}</p>
                  <div class="answer-line"><span class="k">Rango:</span> {html.escape(rank)}</div>
                  <div class="metrics">
                    <div class="metric"><div class="v">{fmt_num(score)}</div><div class="l">Puntos</div></div>
                    <div class="metric"><div class="v">{correct}/{total}</div><div class="l">Aciertos</div></div>
                    <div class="metric"><div class="v">{accuracy * 100:.0f}%</div><div class="l">Precisión</div></div>
                    <div class="metric"><div class="v">×{streak}</div><div class="l">Mejor racha</div></div>
                    <div class="metric"><div class="v">{minutes:02d}:{seconds:02d}</div><div class="l">Tiempo</div></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            cert = build_certificate(
                name=name,
                score=score,
                accuracy=accuracy,
                correct=correct,
                total=total,
                rank_title=rank,
                streak=streak,
                when=when,
            )
            report = build_followup_report(
                name=name,
                score=score,
                accuracy=accuracy,
                correct=correct,
                total=total,
                rank_title=rank,
                streak=streak,
                elapsed=elapsed,
                answers=answers,
                levels=LEVELS,
                training=bool(record.get("training")),
                when=when,
            )
            pdf = build_report_pdf(cert, report)

            cert_tab, follow_tab = st.tabs(["🎓  Certificado", "📈  Seguimiento"])
            with cert_tab:
                st.image(cert, width="stretch")
                st.download_button(
                    "⬇  DESCARGAR CERTIFICADO (PNG)",
                    data=cert,
                    file_name=f"certificado_{safe_filename(name)}.png",
                    mime="image/png",
                    key=f"admin_cert_{record.get('id', '0')}",
                    **WIDTH_KW,
                )
            with follow_tab:
                st.image(report, width="stretch")
                st.download_button(
                    "⬇  DESCARGAR INFORME COMPLETO (PDF · 2 PÁGINAS)",
                    data=pdf,
                    file_name=f"informe_{safe_filename(name)}.pdf",
                    mime="application/pdf",
                    key=f"admin_pdf_{record.get('id', '0')}",
                    **WIDTH_KW,
                )

            with st.expander("🔍  Respuestas del participante"):
                if not answers:
                    st.info("Este registro no tiene respuestas guardadas.")
                for a in answers:
                    ok = bool(a.get("ok"))
                    mark = "✔" if ok else "✘"
                    st.markdown(
                        f"""
                        <div class="rev {'ok' if ok else 'ko'}">
                          <div class="q">{mark} {html.escape(str(a.get('q', '')))}</div>
                          <div class="a">Elegida: <b class="{'g' if ok else ''}">{html.escape(str(a.get('options', [''])[a.get('chosen', 0)]))}</b></div>
                          {"" if ok else f'<div class="a">Correcta: <b class="g">{html.escape(str(a.get("options", [""])[a.get("answer", 0)]))}</b></div>'}
                          <div class="w">{html.escape(str(a.get('why', '')))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    if st.button("Salir del panel", type="tertiary"):
        _leave_admin()
    st.caption(
        "Los datos se guardan en el destino configurado (Google Sheets o archivo local). "
        "Comparte la hoja solo con el equipo administrativo."
    )




# --------------------------------------------------------------------------------------
# Vista previa del certificado (sin completar la evaluación)
# --------------------------------------------------------------------------------------

_PREVIEW_CASES = [
    ("3 estrellas · 97 % · Excelencia", 35),
    ("2 estrellas · 81 % · Especialista", 29),
    ("1 estrella · 61 % · Aprendiz", 22),
    ("Sin estrellas · 42 % · Aprendiz", 15),
]


def _sample_answers(correct_count: int) -> list[dict]:
    answers = []
    index = 0
    for level in LEVELS:
        for question in level["questions"]:
            ok = index < correct_count
            chosen = question["answer"] if ok else (question["answer"] + 1) % len(question["options"])
            answers.append(
                {
                    "level": level["id"],
                    "level_name": level["name"],
                    "icon": level["icon"],
                    "q": question["q"],
                    "options": question["options"],
                    "chosen": chosen,
                    "answer": question["answer"],
                    "ok": ok,
                    "why": question["why"],
                    "source": question["source"],
                }
            )
            index += 1
    return answers


def render_preview() -> None:
    st.markdown(_brand_header("Vista de ejemplo"), unsafe_allow_html=True)
    st.markdown(
        '<h1 class="hero-title" style="font-size:clamp(1.7rem,4vw,2.6rem);">Ejemplo de certificado</h1>'
        '<p class="hero-sub">Así se verá el certificado de un participante, sin tener que completar '
        "la evaluación. Elige el nivel para ver las estrellas y el rango.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">
          <div class="kicker">▸ Escala de estrellas del certificado</div>
          <ul class="brief" style="margin:.3rem 0 .7rem; padding-left:1.1rem;">
            <li><b>3 estrellas</b> — 90 % o más de precisión.</li>
            <li><b>2 estrellas</b> — entre 70 % y 89,9 %.</li>
            <li><b>1 estrella</b> — entre 50 % y 69,9 %.</li>
            <li><b>Sin estrellas</b> — menos de 50 %.</li>
          </ul>
          <div class="tip"><b>Rangos:</b> 95 % o más, Excelencia en Dispensación · 85–94,9 %,
          Guardián de la Seguridad · 70–84,9 %, Especialista en Formación · menos de 70 %,
          Aprendiz Comprometido.</div>
          <div class="src">Las estrellas del mapa son por módulo: 3 = 100 %, 2 = 50–99 %, 1 = menos de 50 %.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    case = st.selectbox("Nivel de ejemplo", [label for label, _ in _PREVIEW_CASES], key="preview_case")
    correct_count = dict(_PREVIEW_CASES)[case]
    accuracy = correct_count / TOTAL_QUESTIONS
    rank = rank_for(accuracy)[0]
    name = "Participante de ejemplo"
    answers = _sample_answers(correct_count)

    cert = certificate_bytes(
        name=name,
        score=correct_count * 100,
        accuracy=accuracy,
        correct=correct_count,
        total=TOTAL_QUESTIONS,
        rank=rank,
        streak=5,
    )
    report = report_bytes(
        name=name,
        score=correct_count * 100,
        accuracy=accuracy,
        correct=correct_count,
        total=TOTAL_QUESTIONS,
        rank=rank,
        streak=5,
        elapsed=600,
        training=False,
        answers=answers,
    )
    pdf = full_report_pdf(cert, report)

    cert_tab, follow_tab = st.tabs(["🎓  Certificado", "📈  Seguimiento"])
    with cert_tab:
        st.image(cert, width="stretch")
    with follow_tab:
        st.image(report, width="stretch")

    st.download_button(
        "⬇  DESCARGAR EJEMPLO DE CERTIFICADO (PNG)",
        data=cert,
        file_name=f"ejemplo_certificado_{correct_count}de{TOTAL_QUESTIONS}.png",
        mime="image/png",
        key="preview_cert_png",
        **WIDTH_KW,
    )
    st.download_button(
        "⬇  DESCARGAR EJEMPLO DE INFORME (PDF · 2 PÁGINAS)",
        data=pdf,
        file_name=f"ejemplo_informe_{correct_count}de{TOTAL_QUESTIONS}.pdf",
        mime="application/pdf",
        key="preview_report_pdf",
        **WIDTH_KW,
    )
    st.caption("Vista de ejemplo: no se guarda en el panel de administración.")

    back_to_admin = bool(st.session_state.get("admin_ok")) and st.query_params.get("admin") == "1"
    if st.button("Volver al panel" if back_to_admin else "Volver al inicio", type="tertiary"):
        if back_to_admin:
            st.query_params.pop("ejemplo", None)
        else:
            st.query_params.clear()
        st.rerun()


# --------------------------------------------------------------------------------------
# Arranque
# --------------------------------------------------------------------------------------

def scroll_to_top() -> None:
    """Sube al inicio de la página al cambiar de pantalla (clave en móvil)."""
    snippet = """
        <script>
          const doc = window.parent.document;
          const main = doc.querySelector('[data-testid="stMain"]');
          if (main) main.scrollTo(0, 0);
          window.parent.scrollTo(0, 0);
        </script>
    """
    if hasattr(st, "iframe"):
        st.iframe(snippet, height=1, tab_index=-1)
    else:  # compatibilidad con versiones anteriores de Streamlit
        components.html(snippet, height=0)


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()

    if st.query_params.get("ejemplo") == "1":
        render_preview()
        return

    if st.query_params.get("admin") == "1":
        render_admin()
        return

    phase = st.session_state.phase
    if st.session_state.get("_scroll_phase") != phase:
        scroll_to_top()
        st.session_state["_scroll_phase"] = phase

    if phase == "start":
        render_start()
    elif phase == "briefing":
        render_briefing()
    elif phase == "question":
        render_question()
    elif phase == "feedback":
        render_feedback()
    elif phase == "final":
        render_final()
    elif phase == "gameover":
        render_gameover()
    else:  # estado desconocido: vuelve al inicio
        reset_game()
        st.rerun()


main()
