import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io
import os

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Data Quality Gate",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "http://127.0.0.1:8000"


def _log_orchestration(layer: str, status: str, message: str = ""):
    """Fire-and-forget call to the orchestration log endpoint. Never raises."""
    try:
        requests.post(
            f"{API}/orchestration/log",
            params={"layer": layer, "status": status, "message": message},
            timeout=3,
        )
    except Exception:
        pass

# =========================
# SESSION STATE
# =========================
defaults = {
    "logged_in": False,
    "page": "landing",
    "ingestion_done": False,
    "profiling_done": False,
    "quality_done": False,
    "security_done": False,
    "dwh_done": False,
    "powerbi_done": False,
    "orchestration_done": False,
    "ingestion_data": None,
    "profiling_data": None,
    "quality_data": None,
    "security_data": None,
    "sql_modal_open": False,
    "sql_connected": False,
    "sql_conn_info": {},
    "sql_databases": [],
    "sql_selected_db": "",
    "sql_tables": [],
    "sql_selected_tables": [],
    "sql_previews": {},
    "sql_step": 1,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# SWIRL SVG
# =========================
SWIRL_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 700' preserveAspectRatio='xMidYMid slice'
     style='position:absolute;top:0;right:0;width:55%;height:100%;z-index:0;pointer-events:none;'>
  <defs>
    <linearGradient id='g1' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#FF6B35;stop-opacity:1'/>
      <stop offset='100%' style='stop-color:#FF3D00;stop-opacity:1'/>
    </linearGradient>
    <linearGradient id='g2' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#FF9800;stop-opacity:1'/>
      <stop offset='100%' style='stop-color:#FF6B35;stop-opacity:1'/>
    </linearGradient>
    <linearGradient id='g3' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#E040FB;stop-opacity:1'/>
      <stop offset='100%' style='stop-color:#7B1FA2;stop-opacity:1'/>
    </linearGradient>
    <linearGradient id='g4' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#00BCD4;stop-opacity:1'/>
      <stop offset='100%' style='stop-color:#0097A7;stop-opacity:1'/>
    </linearGradient>
    <linearGradient id='g5' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#4CAF50;stop-opacity:1'/>
      <stop offset='100%' style='stop-color:#2E7D32;stop-opacity:1'/>
    </linearGradient>
    <linearGradient id='g6' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#FFEB3B;stop-opacity:1'/>
      <stop offset='100%' style='stop-color:#F9A825;stop-opacity:1'/>
    </linearGradient>
  </defs>
  <path d='M 600 0 C 500 100 300 150 200 350 C 100 550 150 650 0 700 L 0 600 C 120 560 80 460 180 280 C 280 100 450 60 600 100 Z'
        fill='url(#g1)' opacity='0.92'/>
  <path d='M 600 50 C 480 130 320 180 230 370 C 140 560 180 650 50 700 L 0 700 L 0 620 C 140 580 100 470 200 300 C 300 130 460 80 600 130 Z'
        fill='url(#g2)' opacity='0.85'/>
  <path d='M 600 120 C 520 180 400 200 330 380 C 260 560 300 640 120 700 L 60 700 C 240 640 210 560 280 390 C 350 220 470 180 600 200 Z'
        fill='url(#g3)' opacity='0.80'/>
  <path d='M 600 200 C 550 240 460 260 400 420 C 340 580 370 650 200 700 L 140 700 C 310 650 290 580 350 430 C 410 280 500 240 600 280 Z'
        fill='url(#g4)' opacity='0.75'/>
  <path d='M 600 290 C 570 320 510 340 460 470 C 410 600 430 660 290 700 L 230 700 C 380 660 360 600 410 480 C 460 360 520 320 600 360 Z'
        fill='url(#g5)' opacity='0.70'/>
  <path d='M 600 380 C 580 400 550 420 510 530 C 470 640 490 680 380 700 L 330 700 C 450 680 430 640 470 540 C 510 440 540 400 600 440 Z'
        fill='url(#g6)' opacity='0.65'/>
</svg>
"""

MINI_SWIRL = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 400'
     style='position:fixed;bottom:0;right:0;width:220px;height:300px;z-index:0;pointer-events:none;opacity:0.18;'>
  <defs>
    <linearGradient id='mg1' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#FF6B35'/>
      <stop offset='100%' style='stop-color:#FF3D00'/>
    </linearGradient>
    <linearGradient id='mg2' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#E040FB'/>
      <stop offset='100%' style='stop-color:#7B1FA2'/>
    </linearGradient>
    <linearGradient id='mg3' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#00BCD4'/>
      <stop offset='100%' style='stop-color:#0097A7'/>
    </linearGradient>
  </defs>
  <path d='M300 0 C200 80 100 120 50 250 C0 380 30 400 0 400 L 0 350 C20 340 0 300 50 200 C100 100 200 60 300 80 Z' fill='url(#mg1)'/>
  <path d='M300 60 C220 120 140 160 100 280 C60 400 80 400 20 400 L 0 400 C60 390 40 350 80 240 C120 130 210 80 300 130 Z' fill='url(#mg2)'/>
  <path d='M300 130 C240 175 180 200 150 310 C120 420 140 400 60 400 L 30 400 C110 390 90 360 120 260 C150 160 220 120 300 190 Z' fill='url(#mg3)'/>
</svg>
"""

# =========================
# GLOBAL STYLES
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

.stApp { background-color: #f7f7f7 !important; color: #1a1a1a !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

.page-header {
    background: #ffffff;
    border-bottom: 2px solid #FF6B35;
    padding: 22px 40px;
    display: flex; align-items: center; justify-content: space-between;
}
.page-layer-badge {
    font-size: 11px; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; color: #FF6B35; margin-bottom: 4px;
}
.page-layer-title { font-size: 22px; font-weight: 800; color: #1a1a1a; }
.page-layer-sub { font-size: 13px; color: #888; }

.info-card {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 8px; padding: 20px 24px; margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.info-card-title {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #FF6B35; margin-bottom: 12px;
}

.stButton > button {
    background: #E23400 !important; color: #fff !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 700 !important; font-size: 15px !important;
    padding: 11px 24px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #c42e00 !important;
    box-shadow: 0 4px 16px rgba(226,52,0,0.25) !important;
}

.stTextInput input {
    background: #f5f5f5 !important;
    border: 1.5px solid #e0e0e0 !important;
    color: #1a1a1a !important;
    border-radius: 6px !important;
    font-size: 15px !important;
}
.stTextInput input:focus {
    border-color: #FF6B35 !important;
    background: #fff !important;
    box-shadow: 0 0 0 3px rgba(255,107,53,0.12) !important;
}
.stTextInput label { color: #444 !important; font-size: 13px !important; font-weight: 600 !important; }

section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 2px solid #FF6B35 !important;
    min-width: 240px !important;
    transform: none !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    margin-left: 0px !important;
    transform: none !important;
}
button[kind="header"] { display: none !important; }
section[data-testid="stSidebar"] .stMarkdown { color: #1a1a1a; }

[data-testid="stFileUploader"] {
    background: #fff !important;
    border: 2px dashed #FF6B35 !important;
    border-radius: 8px !important;
}

.step-dot { width: 9px; height: 9px; border-radius: 50%; background: #e0e0e0; flex-shrink: 0; display:inline-block; }
.step-dot.done { background: #22c55e; }
.step-dot.active { background: #FF6B35; box-shadow: 0 0 8px rgba(255,107,53,0.4); }
.step-name { font-size: 13px; color: #888; font-weight: 500; }
.step-name.active { color: #1a1a1a; font-weight: 700; }
.step-name.done { color: #22c55e; }

.stSpinner > div { border-top-color: #FF6B35 !important; }
.stCheckbox label span { color: #444 !important; }
.stDataFrame { background: #fff !important; border-radius: 8px !important; border: 1px solid #e8e8e8 !important; }

[data-testid="stMetric"] { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px 16px; }
[data-testid="stMetricLabel"] { color: #888 !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #E23400 !important; font-weight: 800 !important; font-size: 26px !important; }

.stSuccess { background: rgba(34,197,94,0.08) !important; border-color: #22c55e !important; color: #166534 !important; border-radius: 8px !important; }
.stWarning { background: rgba(245,158,11,0.08) !important; border-color: #f59e0b !important; border-radius: 8px !important; }
.stError   { background: rgba(239,68,68,0.08) !important; border-color: #ef4444 !important; border-radius: 8px !important; }
.stInfo    { background: rgba(255,107,53,0.06) !important; border-color: #FF6B35 !important; border-radius: 8px !important; }

[data-testid="stExpander"] { background: #fff !important; border: 1px solid #e8e8e8 !important; border-radius: 8px !important; }
[data-testid="stExpander"] summary { color: #1a1a1a !important; font-weight: 600 !important; font-size: 15px !important; }

[data-testid="stTabs"] button { color: #888 !important; font-weight: 600 !important; font-size: 13px !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #E23400 !important; border-bottom-color: #E23400 !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #f7f7f7; }
::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }

hr { border-color: #e8e8e8 !important; }
</style>
""", unsafe_allow_html=True)


# =========================
# LOGIN PAGE
# =========================
def login_page():
    st.markdown("""
    <style>
    .stApp { background: #ffffff !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    [data-testid="stHorizontalBlock"] { gap: 0 !important; align-items: stretch !important; }
    [data-testid="stColumn"] { padding: 0 !important; min-height: 100vh; }

    [data-testid="stColumn"]:first-child {
        background: #ffffff;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        border-right: 1px solid #ececec;
    }
    [data-testid="stColumn"]:first-child > div:first-child {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 100vh;
        padding: 0 72px;
    }

    [data-testid="stColumn"]:last-child {
        background-color: #111827 !important;
        background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNzAwIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCBzbGljZSI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImcxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGNkIzNSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGRjNEMDAiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImcyIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGOTgwMCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGRjZCMzUiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImczIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0UwNDBGQiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiM3QjFGQTIiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc0IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzAwQkNENCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMwMDk3QTciLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc1IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzRDQUY1MCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMyRTdEMzIiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc2IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGRUIzQiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGOUE4MjUiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI2MDAiIGhlaWdodD0iNzAwIiBmaWxsPSIjMTExODI3Ii8+CiAgPHBhdGggZD0iTSA2MDAgMCBDIDUwMCAxMDAgMzAwIDE1MCAyMDAgMzUwIEMgMTAwIDU1MCAxNTAgNjUwIDAgNzAwIEwgMCA2MDAgQyAxMjAgNTYwIDgwIDQ2MCAxODAgMjgwIEMgMjgwIDEwMCA0NTAgNjAgNjAwIDEwMCBaIiBmaWxsPSJ1cmwoI2cxKSIgb3BhY2l0eT0iMC45MiIvPgogIDxwYXRoIGQ9Ik0gNjAwIDUwIEMgNDgwIDEzMCAzMjAgMTgwIDIzMCAzNzAgQyAxNDAgNTYwIDE4MCA2NTAgNTAgNzAwIEwgMCA3MDAgTCAwIDYyMCBDIDE0MCA1ODAgMTAwIDQ3MCAyMDAgMzAwIEMgMzAwIDEzMCA0NjAgODAgNjAwIDEzMCBaIiBmaWxsPSJ1cmwoI2cyKSIgb3BhY2l0eT0iMC44NSIvPgogIDxwYXRoIGQ9Ik0gNjAwIDEyMCBDIDUyMCAxODAgNDAwIDIwMCAzMzAgMzgwIEMgMjYwIDU2MCAzMDAgNjQwIDEyMCA3MDAgTCA2MCA3MDAgQyAyNDAgNjQwIDIxMCA1NjAgMjgwIDM5MCBDIDM1MCAyMjAgNDcwIDE4MCA2MDAgMjAwIFoiIGZpbGw9InVybCgjZzMpIiBvcGFjaXR5PSIwLjgwIi8+CiAgPHBhdGggZD0iTSA2MDAgMjAwIEMgNTUwIDI0MCA0NjAgMjYwIDQwMCA0MjAgQyAzNDAgNTgwIDM3MCA2NTAgMjAwIDcwMCBMIDE0MCA3MDAgQyAzMTAgNjUwIDI5MCA1ODAgMzUwIDQzMCBDIDQxMCAyODAgNTAwIDI0MCA2MDAgMjgwIFoiIGZpbGw9InVybCgjZzQpIiBvcGFjaXR5PSIwLjc1Ii8+CiAgPHBhdGggZD0iTSA2MDAgMjkwIEMgNTcwIDMyMCA1MTAgMzQwIDQ2MCA0NzAgQyA0MTAgNjAwIDQzMCA2NjAgMjkwIDcwMCBMIDIzMCA3MDAgQyAzODAgNjYwIDM2MCA2MDAgNDEwIDQ4MCBDIDQ2MCAzNjAgNTIwIDMyMCA2MDAgMzYwIFoiIGZpbGw9InVybCgjZzUpIiBvcGFjaXR5PSIwLjcwIi8+CiAgPHBhdGggZD0iTSA2MDAgMzgwIEMgNTgwIDQwMCA1NTAgNDIwIDUxMCA1MzAgQyA0NzAgNjQwIDQ5MCA2ODAgMzgwIDcwMCBMIDMzMCA3MDAgQyA0NTAgNjgwIDQzMCA2NDAgNDcwIDU0MCBDIDUxMCA0NDAgNTQwIDQwMCA2MDAgNDQwIFoiIGZpbGw9InVybCgjZzYpIiBvcGFjaXR5PSIwLjY1Ii8+Cjwvc3ZnPg==") !important;
        background-size: cover !important;
        background-position: right center !important;
        background-repeat: no-repeat !important;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stColumn"]:last-child > div:first-child {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 0 64px;
    }
    .lp-logo-row { display:flex;align-items:center;gap:12px;margin-bottom:8px; }
    .lp-logo-hex {
        width:36px;height:36px;flex-shrink:0;
        background:linear-gradient(135deg,#FF6B35,#E23400);
        clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    }
    .lp-logo-name { font-size:19px;font-weight:700;color:#1a1a1a; }
    .lp-tagline { font-size:13px;color:#999;margin-bottom:32px; }
    .lp-heading { font-size:34px;font-weight:800;color:#1a1a1a;letter-spacing:-1px;margin-bottom:6px; }
    .lp-subheading { font-size:15px;color:#666;margin-bottom:28px;line-height:1.5; }
    .lp-footer { font-size:11px;color:#bbb;margin-top:18px;line-height:1.6; }
    .lp-footer a { color:#FF6B35;text-decoration:none; }

    [data-testid="stColumn"]:first-child .stTextInput input {
        background: #f5f5f5 !important;
        border: 1.5px solid #e0e0e0 !important;
        color: #1a1a1a !important;
        border-radius: 6px !important;
        font-size: 15px !important;
        padding: 12px 14px !important;
    }
    [data-testid="stColumn"]:first-child .stTextInput input:focus {
        border-color: #FF6B35 !important;
        background: #fff !important;
        box-shadow: 0 0 0 3px rgba(255,107,53,0.12) !important;
    }
    [data-testid="stColumn"]:first-child .stTextInput label {
        color: #444 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
    }
    [data-testid="stColumn"]:first-child .stButton > button {
        background: #E23400 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 14px !important;
        width: 100% !important;
        margin-top: 6px !important;
        letter-spacing: 0.3px !important;
    }
    [data-testid="stColumn"]:first-child .stButton > button:hover {
        background: #c42e00 !important;
    }

    .lp-right-inner { position:relative;z-index:2;padding: 0 8px; }
    .lp-badge {
        font-size:11px;font-weight:700;letter-spacing:3px;
        text-transform:uppercase;color:#FF6B35;margin-bottom:20px;
    }
    .lp-headline {
        font-size:52px;font-weight:800;color:#fff;
        line-height:1.1;letter-spacing:-2px;margin-bottom:20px;
    }
    .lp-headline span { color:#FF6B35; }
    .lp-desc {
        font-size:16px;color:#9ca3af;line-height:1.75;
        max-width:420px;margin-bottom:36px;
    }
    .lp-stats { display:flex;gap:44px; }
    .lp-stat-num { font-size:36px;font-weight:800;color:#FF6B35;line-height:1; }
    .lp-stat-lbl { font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:1.5px;margin-top:4px; }

    [data-testid="stColumn"]:last-child .stButton > button {
        background: transparent !important;
        color: #FF6B35 !important;
        border: 2px solid #FF6B35 !important;
        border-radius: 4px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        padding: 14px 32px !important;
        width: auto !important;
        position: relative;
        z-index: 2;
    }
    [data-testid="stColumn"]:last-child .stButton > button:hover {
        background: #FF6B35 !important;
        color: #fff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([9, 11])

    with col_left:
        st.markdown("""
        <div class="lp-logo-row">
            <div class="lp-logo-hex"></div>
            <span class="lp-logo-name">Data Quality Gate</span>
        </div>
        <div class="lp-tagline">One login for all things Data Quality</div>
        <div class="lp-heading">Sign in</div>
        <div class="lp-subheading">Welcome back — access your data pipeline</div>
        """, unsafe_allow_html=True)

        user = st.text_input("Email / Username", placeholder="you@example.com", key="login_user")
        pwd  = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pwd")

        if st.button("Login", key="login_btn", use_container_width=True):
            if user and pwd:
                st.session_state.logged_in = True
                st.session_state.page = "ingestion"
                st.rerun()
            else:
                st.error("Please enter both fields.")

        st.markdown("""
        <div class="lp-footer">
            Data Quality Gate will use data provided here in accordance with our
            <a href="#">privacy policy</a>.
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div class="lp-right-inner">
            <div class="lp-badge">Data Intelligence Platform</div>
            <div class="lp-headline">Get expert help<br>with <span>data quality</span></div>
            <div class="lp-desc">
                Sign in to access your enterprise data pipeline — ingest,
                profile, validate, and secure your data with automated,
                audit-ready workflows built for healthcare and beyond.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("GET STARTED →", key="get_started_btn"):
            st.session_state.page = "register"
            st.rerun()

        st.markdown("""
        <div class="lp-right-inner">
            <div class="lp-stats" style="margin-top:28px;">
                <div><div class="lp-stat-num">4</div><div class="lp-stat-lbl">Pipeline Layers</div></div>
                <div><div class="lp-stat-num">10+</div><div class="lp-stat-lbl">DQ Checks</div></div>
                <div><div class="lp-stat-num">AES</div><div class="lp-stat-lbl">Encryption</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =========================
# SIDEBAR
# =========================
def sidebar():
    steps = [
        ("ingestion", "01  Ingestion Layer",  "ingestion_done"),
        ("profiling",  "02  Profiling Layer",  "profiling_done"),
        ("quality",    "03  Data Quality",     "quality_done"),
        ("security",   "04  Security Layer",   "security_done"),
        ("DWH",        "05  Data Warehouse",   "dwh_done"),
        ("Dashboard",  "06  Power BI Layer",   "powerbi_done"),
        ("Orchestration", "07  Orchestration", None),
    ]
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:24px 8px 0 8px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <div style="width:26px;height:26px;background:linear-gradient(135deg,#FF6B35,#FF3D00);
                     clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);flex-shrink:0;"></div>
                <span style="font-size:14px;font-weight:700;color:#ffffff;">DQ Gate</span>
            </div>
            <div style="font-size:11px;color:#6b7280;margin-bottom:28px;letter-spacing:0.3px;">
                Pipeline Navigator
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        for page_key, label, done_key in steps:
            is_active = st.session_state.page == page_key
            is_done   = st.session_state.get(done_key, False) if done_key else False
            dot_cls   = "done" if is_done else ("active" if is_active else "")
            name_cls  = "done" if is_done else ("active" if is_active else "")
            icon      = "✓ " if is_done else ("▶ " if is_active else "  ")

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:10px 8px;
                 border-bottom:1px solid #1e2128;">
                <span class="step-dot {dot_cls}"></span>
                <span class="step-name {name_cls}">{icon}{label}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("⬅ Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown("""
        <div style="margin-top:auto;padding-top:40px;opacity:0.15;overflow:hidden;height:120px;">
            <svg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg' width='200'>
              <path d='M200 0 C140 40 80 60 40 140 C0 220 20 200 0 200 L0 160 C10 150 0 120 40 70 C80 20 140 10 200 40Z' fill='#FF6B35'/>
              <path d='M200 40 C150 70 100 90 70 160 C40 230 60 200 20 200 L0 200 C30 190 20 160 50 100 C80 40 150 20 200 80Z' fill='#E040FB'/>
            </svg>
        </div>
        """, unsafe_allow_html=True)


# =========================
# PAGE HEADER HELPER
# =========================
LAYER_META = {
    "01": {"icon": "", "color": "#FF6B35"},  # Ingestion
    "02": {"icon": "", "color": "#2563eb"},  # Profiling
    "03": {"icon": "",     "color": "#16a34a"},  # Data Quality
    "04": {"icon": "", "color": "#7c3aed"},  # Security
    "05": {"icon": "", "color": "#d97706"},  # Data Warehouse
    "06": {"icon": "", "color": "#dc2626"},  # Power BI
    "07": {"icon": "", "color": "#0d9488"},  # Orchestration
}


def page_header(layer_num, title, subtitle):
    st.markdown(MINI_SWIRL, unsafe_allow_html=True)
    meta = LAYER_META.get(layer_num, {"icon": "", "color": "#FF6B35"})
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:46px;height:46px;border-radius:50%;background:{meta['color']};
                 display:flex;align-items:center;justify-content:center;
                 font-size:21px;flex-shrink:0;">{meta['icon']}</div>
            <div>
                <div class="page-layer-badge" style="color:{meta['color']};">Layer {layer_num}</div>
                <div class="page-layer-title">{title}</div>
            </div>
        </div>
        <div class="page-layer-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# =========================
# SQL SERVER CONNECTOR
# =========================
def sql_connector_panel():
    import importlib
    pyodbc_available = importlib.util.find_spec("pyodbc") is not None

    with st.expander("Connect to SQL Server", expanded=st.session_state.sql_modal_open):
        st.markdown("""
        <div style="padding:4px 0 16px 0;">
            <div style="font-size:13px;font-weight:700;color:#FF6B35;letter-spacing:1.5px;
                 text-transform:uppercase;margin-bottom:4px;">SQL Server Data Source</div>
            <div style="font-size:12px;color:#6b7280;">
                Connect to your SQL Server, browse databases, select tables, and load them directly into the pipeline.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not pyodbc_available:
            st.error(" `pyodbc` is not installed. Run: `pip install pyodbc` then restart.")
            st.code("pip install pyodbc", language="bash")
            return

        step = st.session_state.sql_step

        steps_html = ""
        for i, label in enumerate(["Connection", "Database", "Tables", "Preview"], 1):
            active = "color:#FF6B35;font-weight:700;" if i == step else \
                     "color:#22c55e;" if i < step else "color:#6b7280;"
            dot = "●" if i == step else ("✓" if i < step else "○")
            steps_html += f'<span style="{active}font-size:12px;margin-right:20px;">{dot} {label}</span>'

        st.markdown(f'<div style="margin-bottom:20px;">{steps_html}</div>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color:#1e2128;margin-bottom:20px;">', unsafe_allow_html=True)

        if step == 1:
            st.markdown("**Server Connection**")
            c1, c2 = st.columns(2)
            server = c1.text_input("Server", placeholder="localhost\\SQLEXPRESS  or  192.168.1.1",
                                    value=st.session_state.sql_conn_info.get("server", ""),
                                    key="sql_server_input")
            port   = c2.text_input("Port (optional)", placeholder="1433",
                                    value=st.session_state.sql_conn_info.get("port", "1433"),
                                    key="sql_port_input")

            st.markdown("**Authentication**")
            auth_mode = st.radio("Authentication Mode",
                                  ["SQL Server Authentication", "Windows Authentication"],
                                  horizontal=True, key="sql_auth_mode")

            sql_user = sql_pwd = ""
            if auth_mode == "SQL Server Authentication":
                c3, c4 = st.columns(2)
                sql_user = c3.text_input("Username", placeholder="sa",
                                          value=st.session_state.sql_conn_info.get("user", ""),
                                          key="sql_user_input")
                sql_pwd  = c4.text_input("Password", type="password", key="sql_pwd_input")

            st.markdown("<br>", unsafe_allow_html=True)
            cb1, cb2, _ = st.columns([1, 1, 3])

            with cb1:
                if st.button("Connect", key="sql_connect_btn", use_container_width=True):
                    if not server:
                        st.error("Server name is required.")
                    else:
                        with st.spinner("Connecting to SQL Server..."):
                            try:
                                import pyodbc
                                srv = f"{server},{port}" if port and port != "1433" else server
                                if auth_mode == "Windows Authentication":
                                    conn_str = (f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                                                f"SERVER={srv};Trusted_Connection=yes;")
                                else:
                                    conn_str = (f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                                                f"SERVER={srv};UID={sql_user};PWD={sql_pwd};")

                                conn = pyodbc.connect(conn_str, timeout=10)
                                cursor = conn.cursor()
                                cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN "
                                               "('master','tempdb','model','msdb') ORDER BY name")
                                dbs = [row[0] for row in cursor.fetchall()]
                                conn.close()

                                st.session_state.sql_conn_info = {
                                    "server": server, "port": port,
                                    "user": sql_user, "pwd": sql_pwd,
                                    "auth": auth_mode, "conn_str_base": conn_str
                                }
                                st.session_state.sql_databases = dbs
                                st.session_state.sql_connected = True
                                st.session_state.sql_step = 2
                                st.success(f"✓ Connected! Found {len(dbs)} database(s).")
                                st.rerun()
                            except Exception as e:
                                err = str(e)
                                if "08001" in err or "Login timeout" in err:
                                    st.error("❌ Cannot reach server. Check server name/IP and firewall.")
                                elif "28000" in err or "Login failed" in err:
                                    st.error("❌ Login failed. Check username and password.")
                                elif "IM002" in err or "Data source name not found" in err:
                                    st.error("❌ ODBC Driver not found. Install 'ODBC Driver 17 for SQL Server'.")
                                    st.markdown("[Download ODBC Driver 17](https://aka.ms/downloadmsodbcsql)")
                                else:
                                    st.error(f"❌ Connection error: {err}")
            with cb2:
                if st.button("Cancel", key="sql_cancel1", use_container_width=True):
                    st.session_state.sql_modal_open = False
                    st.rerun()

        elif step == 2:
            st.markdown(f"**Connected to:** `{st.session_state.sql_conn_info.get('server', '')}`")
            st.markdown("**Select a Database**")

            dbs = st.session_state.sql_databases
            if not dbs:
                st.warning("No user databases found on this server.")
            else:
                selected_db = st.selectbox("Database", dbs,
                                            index=dbs.index(st.session_state.sql_selected_db)
                                            if st.session_state.sql_selected_db in dbs else 0,
                                            key="sql_db_select")

                cb1, cb2, cb3, _ = st.columns([1, 1, 1, 3])
                with cb1:
                    if st.button("Next →", key="sql_next_db", use_container_width=True):
                        with st.spinner(f"Loading tables from {selected_db}..."):
                            try:
                                import pyodbc
                                ci = st.session_state.sql_conn_info
                                base = ci["conn_str_base"]
                                conn_str = base + f"DATABASE={selected_db};"
                                conn = pyodbc.connect(conn_str, timeout=10)
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE "
                                    "FROM INFORMATION_SCHEMA.TABLES "
                                    "ORDER BY TABLE_SCHEMA, TABLE_NAME"
                                )
                                tables = [{"schema": r[0], "name": r[1], "type": r[2]}
                                          for r in cursor.fetchall()]
                                conn.close()
                                st.session_state.sql_selected_db = selected_db
                                st.session_state.sql_tables = tables
                                st.session_state.sql_step = 3
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error loading tables: {e}")
                with cb2:
                    if st.button("← Back", key="sql_back_db", use_container_width=True):
                        st.session_state.sql_step = 1; st.rerun()
                with cb3:
                    if st.button("Cancel", key="sql_cancel2", use_container_width=True):
                        st.session_state.sql_modal_open = False; st.rerun()

        elif step == 3:
            tables = st.session_state.sql_tables
            db_name = st.session_state.sql_selected_db

            st.markdown(f"**Database:** `{db_name}` — {len(tables)} object(s) found")
            search = st.text_input("Search tables", placeholder="Filter by table name...",
                                    key="sql_table_search")

            filtered = [t for t in tables
                        if search.lower() in t["name"].lower()] if search else tables

            schemas = {}
            for t in filtered:
                schemas.setdefault(t["schema"], []).append(t)

            selected_full = []
            st.markdown("<div style='max-height:300px;overflow-y:auto;'>", unsafe_allow_html=True)

            for schema, tbls in schemas.items():
                st.markdown(f"<div style='font-size:11px;color:#FF6B35;font-weight:700;"
                            f"letter-spacing:1px;text-transform:uppercase;"
                            f"margin:12px 0 6px 0;'>{schema}</div>", unsafe_allow_html=True)
                for t in tbls:
                    full_name = f"{schema}.{t['name']}"
                    icon = "" if t["type"] == "BASE TABLE" else ""
                    checked = st.checkbox(
                        f"{icon} {t['name']}",
                        value=full_name in st.session_state.sql_selected_tables,
                        key=f"sql_tbl_{schema}_{t['name']}"
                    )
                    if checked:
                        selected_full.append(full_name)

            st.markdown("</div>", unsafe_allow_html=True)

            if selected_full:
                st.info(f"✓ {len(selected_full)} table(s) selected")

            cb1, cb2, cb3, _ = st.columns([1, 1, 1, 2])
            with cb1:
                if st.button("Preview & Load →", key="sql_load_btn", use_container_width=True):
                    if not selected_full:
                        st.warning("Select at least one table.")
                    else:
                        st.session_state.sql_selected_tables = selected_full
                        with st.spinner("Loading previews..."):
                            try:
                                import pyodbc
                                ci = st.session_state.sql_conn_info
                                conn_str = ci["conn_str_base"] + f"DATABASE={db_name};"
                                conn = pyodbc.connect(conn_str, timeout=10)
                                previews = {}
                                for full in selected_full:
                                    schema_n, tbl_n = full.split(".", 1)
                                    try:
                                        df_prev = pd.read_sql(
                                            f"SELECT TOP 10 * FROM [{schema_n}].[{tbl_n}]", conn)
                                        previews[full] = df_prev
                                    except Exception as te:
                                        previews[full] = str(te)
                                conn.close()
                                st.session_state.sql_previews = {
                                    k: v.to_dict() if isinstance(v, pd.DataFrame) else v
                                    for k, v in previews.items()
                                }
                                st.session_state.sql_step = 4
                                st.rerun()
                            except Exception as e:
                                st.error(f" {e}")
            with cb2:
                if st.button("← Back", key="sql_back_tbl", use_container_width=True):
                    st.session_state.sql_step = 2; st.rerun()
            with cb3:
                if st.button("Cancel", key="sql_cancel3", use_container_width=True):
                    st.session_state.sql_modal_open = False; st.rerun()

        elif step == 4:
            db_name  = st.session_state.sql_selected_db
            selected = st.session_state.sql_selected_tables
            previews = st.session_state.sql_previews

            st.markdown(f"**{len(selected)} table(s) ready to load from `{db_name}`**")

            for full_name in selected:
                schema_n, tbl_n = full_name.split(".", 1)
                with st.expander(f" {full_name}", expanded=True):
                    pdata = previews.get(full_name)
                    if isinstance(pdata, dict):
                        try:
                            df_show = pd.DataFrame(pdata)
                            st.markdown(f"<span style='font-size:11px;color:#6b7280;'>"
                                        f"Preview — top 10 rows × {len(df_show.columns)} columns</span>",
                                        unsafe_allow_html=True)
                            st.dataframe(df_show, use_container_width=True)
                        except Exception:
                            st.warning("Could not render preview.")
                    else:
                        st.error(f"Error: {pdata}")

            st.markdown("<br>", unsafe_allow_html=True)
            cb1, cb2, cb3, _ = st.columns([2, 1, 1, 2])

            with cb1:
                if st.button("Load into Pipeline", key="sql_confirm_load", use_container_width=True):
                    with st.spinner("Exporting tables to CSV and loading into pipeline..."):
                        try:
                            import pyodbc
                            ci = st.session_state.sql_conn_info
                            conn_str = ci["conn_str_base"] + f"DATABASE={db_name};"
                            conn = pyodbc.connect(conn_str, timeout=30)

                            os.makedirs("StorageLayer/LoadedData", exist_ok=True)
                            saved = []

                            for full_name in selected:
                                schema_n, tbl_n = full_name.split(".", 1)
                                try:
                                    df_full = pd.read_sql(
                                        f"SELECT * FROM [{schema_n}].[{tbl_n}]", conn)
                                    safe_name = tbl_n.replace(" ", "_")
                                    csv_path = f"StorageLayer/LoadedData/{safe_name}.csv"
                                    df_full.to_csv(csv_path, index=False)
                                    saved.append({"table": full_name,
                                                  "rows": len(df_full),
                                                  "cols": len(df_full.columns),
                                                  "path": csv_path})
                                except Exception as te:
                                    st.warning(f"Could not export {full_name}: {te}")
                            conn.close()

                            if saved:
                                details = {}
                                for s in saved:
                                    df_s = pd.read_csv(s["path"])
                                    mv = {c: int(df_s[c].isnull().sum()) for c in df_s.columns}
                                    details[s["table"].split(".")[-1]] = {
                                        "rows": s["rows"],
                                        "columns": list(df_s.columns),
                                        "missing_values": mv,
                                        "stats": {},
                                        "sample": df_s.head(5).to_dict(orient="records")
                                    }
                                st.session_state.ingestion_data = {
                                    "status": "success",
                                    "tables_loaded": [s["table"] for s in saved],
                                    "details": details
                                }
                                st.session_state.ingestion_done = True
                                st.session_state.sql_modal_open = False
                                st.success(f"✓ {len(saved)} table(s) loaded into pipeline!")
                                st.rerun()
                        except Exception as e:
                            st.error(f" Export failed: {e}")

            with cb2:
                if st.button("← Back", key="sql_back_prev", use_container_width=True):
                    st.session_state.sql_step = 3; st.rerun()
            with cb3:
                if st.button("Cancel", key="sql_cancel4", use_container_width=True):
                    st.session_state.sql_modal_open = False; st.rerun()


# =========================
# INGESTION PAGE
# =========================
def ingestion_page():
    page_header("01", "Ingestion Layer", "Upload → Validate → Store → Inspect")

    st.markdown("""
    <div class="info-card">
        <div class="info-card-title">About This Layer</div>
        <p style="color:#9ca3af;font-size:14px;line-height:1.75;margin:0;">
            The Ingestion Layer is the entry point of your data pipeline. Upload CSV datasets here —
            the engine validates, stores, and inspects each file using Apache Spark,
            returning rich metadata: row counts, column types, null distributions, and data samples.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .source-option-title {
        text-align:center; font-size:14px; font-weight:700; color:#1a1a1a;
        margin-bottom:14px; display:flex; align-items:center; justify-content:center; gap:8px;
    }
    .source-divider {
        display:flex; flex-direction:column; align-items:center; justify-content:center;
        height:100%; color:#c7c7c7; font-size:12px; font-weight:700;
        letter-spacing:1px; padding-top:70px;
    }
    .source-divider .line { width:1px; flex:1; background:#e5e5e5; margin:8px 0; min-height:30px; }
    </style>
    """, unsafe_allow_html=True)

    outer_l, outer_mid, outer_r = st.columns([1, 6, 1])
    with outer_mid:
        col_up, col_div, col_sql = st.columns([2, 0.5, 2])
        with col_up:
            st.markdown('<div class="source-option-title">📥 Upload CSV Files</div>', unsafe_allow_html=True)
            files = st.file_uploader(
                "Drop CSV files here", type="csv", accept_multiple_files=True,
                label_visibility="collapsed",
            )
        with col_div:
            st.markdown(
                '<div class="source-divider"><div class="line"></div>OR<div class="line"></div></div>',
                unsafe_allow_html=True,
            )
        with col_sql:
            st.markdown('<div class="source-option-title"> Connect to SQL Server</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            if st.button("Get Data from SQL Server", use_container_width=True, key="open_sql"):
                st.session_state.sql_modal_open = True
                st.session_state.sql_step = 1
                st.rerun()

    if st.session_state.sql_modal_open or st.session_state.sql_connected:
        st.markdown("<br>", unsafe_allow_html=True)
        sql_connector_panel()

    if st.session_state.ingestion_done and st.session_state.ingestion_data:
        st.success("✓ Ingestion completed")
        _render_ingestion_results(st.session_state.ingestion_data)
        st.markdown("---")
        if st.button("Next Layer → Profiling ▶"):
            st.session_state.page = "profiling"
            st.rerun()
        return

    if files:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("▶ Run Ingestion"):
            payload = [("files", (f.name, f.getvalue(), "text/csv")) for f in files]
            with st.spinner("Processing with Apache Spark..."):
                try:
                    res = requests.post(f"{API}/ingestion/ingest", files=payload, timeout=300)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.ingestion_data = data
                        st.session_state.ingestion_done = True
                        _log_orchestration("ingestion", "success", "Files ingested via upload.")
                        st.success("✓ Ingestion complete!")
                        st.rerun()
                    else:
                        try:
                            detail = res.json().get("detail", res.text)
                        except Exception:
                            detail = res.text
                        st.error(f" API Error {res.status_code}: {detail}")
                        _log_orchestration("ingestion", "failed", f"API Error {res.status_code}: {detail}")
                except requests.exceptions.ConnectionError:
                    st.error(" Cannot connect to backend. Is uvicorn running on port 8000?")
                    _log_orchestration("ingestion", "failed", "Backend unreachable.")
                except requests.exceptions.Timeout:
                    st.error(" Request timed out. Spark may still be processing — wait and refresh.")
                    _log_orchestration("ingestion", "failed", "Request timed out.")
                except Exception as e:
                    st.error(f" Unexpected error: {str(e)}")
                    _log_orchestration("ingestion", "failed", f"Unexpected error: {e}")


def _render_ingestion_results(data):
    details = data.get("details", {})
    st.markdown('<div class="info-card"><div class="info-card-title">Metadata Catalog</div></div>',
                unsafe_allow_html=True)
    for table_name, info in details.items():
        with st.expander(f"{table_name}", expanded=True):
            c = st.columns(4)
            c[0].metric("Rows", f"{info.get('rows', 0):,}")
            c[1].metric("Columns", len(info.get('columns', [])))
            c[2].metric("Cols with Nulls", sum(v > 0 for v in info.get('missing_values', {}).values()))
            c[3].metric("Status", "✓ Loaded")

            t1, t2, t3 = st.tabs(["Sample Data", "Missing Values", "Stats"])
            with t1:
                sample = info.get("sample", [])
                if sample:
                    st.dataframe(pd.DataFrame(sample), use_container_width=True)
            with t2:
                mv = info.get("missing_values", {})
                mv_df = pd.DataFrame(list(mv.items()), columns=["Column", "Null Count"])
                mv_df = mv_df[mv_df["Null Count"] > 0]
                if not mv_df.empty:
                    fig = px.bar(mv_df, x="Column", y="Null Count",
                                 color_discrete_sequence=["#FF6B35"], template="plotly_dark")
                    fig.update_layout(paper_bgcolor="#111317", plot_bgcolor="#0d0d0d",
                                      font_color="#9ca3af", margin=dict(t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True, key=f"ing_mv_{table_name}")
                else:
                    st.success("No missing values!")
            with t3:
                stats = info.get("stats", {})
                if stats:
                    st.json(stats)
                else:
                    st.info("No numeric columns.")


# =========================
# PROFILING PAGE
# =========================
def profiling_page():
    page_header("02", "Profiling Layer", "Analyze → Report → Visualize → Export")

    if not st.session_state.ingestion_done:
        st.warning(" Complete Ingestion Layer first.")
        return

    st.markdown("""
    <div class="info-card">
        <div class="info-card-title">About This Layer</div>
        <p style="color:#9ca3af;font-size:14px;line-height:1.75;margin:0;">
            Deep statistical analysis on ingested datasets — per-column distributions,
            null rates, and descriptive statistics. Reports are packaged into a
            downloadable ZIP archive for offline review.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.profiling_done:
        if st.button("▶ Run Profiling"):
            with st.spinner("Generating profiling reports..."):
                try:
                    res = requests.post(f"{API}/profiling/profiling", timeout=600)
                    if res.status_code == 200:
                        st.session_state.profiling_data = res.json()
                        st.session_state.profiling_done = True
                        _log_orchestration("profiling", "success", "Profiling reports generated.")
                        st.success("✓ Profiling complete!")
                        st.rerun()
                    else:
                        try:
                            detail = res.json().get("detail", res.text)
                        except Exception:
                            detail = res.text
                        st.error(f" API Error {res.status_code}: {detail}")
                        _log_orchestration("profiling", "failed", f"API Error {res.status_code}: {detail}")
                except requests.exceptions.ConnectionError:
                    st.error(" Cannot connect to backend.")
                    _log_orchestration("profiling", "failed", "Backend unreachable.")
                except requests.exceptions.Timeout:
                    st.error(" Profiling timed out — reports may still be generating.")
                    _log_orchestration("profiling", "failed", "Request timed out.")
                except Exception as e:
                    st.error(f" Unexpected error: {str(e)}")
                    _log_orchestration("profiling", "failed", f"Unexpected error: {e}")
        return

    st.success("✓ Profiling completed")
    st.markdown("<br>", unsafe_allow_html=True)

    details = (st.session_state.ingestion_data or {}).get("details", {})
    if details:
        st.markdown('<div class="info-card"><div class="info-card-title">Profile Reports</div></div>',
                    unsafe_allow_html=True)
        for table_name, info in details.items():
            with st.expander(f" {table_name}", expanded=True):
                st.markdown(f"**`{table_name}`** — {info.get('rows', 0):,} rows × {len(info.get('columns', []))} columns")
                mv = info.get("missing_values", {})
                c1, c2 = st.columns(2)
                with c1:
                    if mv:
                        fig = px.bar(x=list(mv.keys()), y=list(mv.values()),
                                     title="Null Distribution",
                                     labels={"x": "Column", "y": "Null Count"},
                                     color_discrete_sequence=["#FF6B35"], template="plotly_dark")
                        fig.update_layout(paper_bgcolor="#111317", plot_bgcolor="#0d0d0d",
                                          font_color="#9ca3af", margin=dict(t=40, b=20))
                        st.plotly_chart(fig, use_container_width=True, key=f"prof_bar_{table_name}")
                with c2:
                    if mv:
                        null_c = sum(v > 0 for v in mv.values())
                        fig2 = px.pie(values=[len(mv) - null_c, null_c],
                                      names=["Complete", "Has Nulls"],
                                      title="Column Completeness",
                                      color_discrete_sequence=["#22c55e", "#FF6B35"],
                                      template="plotly_dark")
                        fig2.update_layout(paper_bgcolor="#111317", font_color="#9ca3af",
                                           margin=dict(t=40, b=20))
                        st.plotly_chart(fig2, use_container_width=True, key=f"prof_pie_{table_name}")
                sample = info.get("sample", [])
                if sample:
                    st.dataframe(pd.DataFrame(sample), use_container_width=True)

    st.markdown("---")
    folder = "StorageLayer/reports"
    zip_buffer = io.BytesIO()
    has_files = False
    if os.path.exists(folder):
        rfiles = [f for f in os.listdir(folder)]
        if rfiles:
            has_files = True
            with zipfile.ZipFile(zip_buffer, "w") as z:
                for f in rfiles:
                    z.write(os.path.join(folder, f), arcname=f)

    c1, c2 = st.columns([1, 4])
    with c1:
        if has_files:
            st.download_button("⬇ Download Reports (ZIP)",
                               data=zip_buffer.getvalue(),
                               file_name="Profiling_Reports.zip",
                               mime="application/zip",
                               use_container_width=True)
    with c2:
        if st.button("Next Layer → Data Quality ▶"):
            st.session_state.page = "quality"
            st.rerun()


# =========================
# QUALITY PAGE
# =========================
def quality_page():
    page_header("03", "Data Quality Engine", "Completeness · Uniqueness · Referential Integrity")

    if not st.session_state.profiling_done:
        st.warning(" Complete Profiling Layer first.")
        return

    st.markdown("""
    <div class="info-card">
        <div class="info-card-title">About This Layer</div>
        <p style="color:#9ca3af;font-size:14px;line-height:1.75;margin:0;">
            Rule-based checks across all ingested tables — completeness, uniqueness,
            and foreign key integrity. Results are scored, visualized across 10+ charts,
            and saved to <code>StorageLayer/DataQualityReports</code>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.quality_done:
        if st.button("▶ Run Data Quality Checks"):
            with st.spinner(" Running DQ Engine with Apache Spark... (this takes 2–5 min)"):
                try:
                    res = requests.get(f"{API}/quality/run-quality?token=admin123", timeout=600)
                    if res.status_code == 200:
                        try:
                            rep = requests.get(f"{API}/quality/get-quality-report?token=admin123", timeout=60)
                            if rep.status_code == 200:
                                rdata = rep.json()
                                if isinstance(rdata, list):
                                    st.session_state.quality_data = rdata
                                else:
                                    st.warning(f"Report issue: {rdata.get('error', 'Unknown')}")
                            else:
                                st.warning(f"Report fetch returned {rep.status_code}")
                        except Exception as rep_e:
                            st.warning(f"Could not fetch report: {rep_e}")
                        st.session_state.quality_done = True
                        _log_orchestration("quality", "success", "Data quality checks completed.")
                        st.success("✓ DQ Checks complete!")
                        st.rerun()
                    elif res.status_code == 401:
                        st.error(" Unauthorized — check token.")
                        _log_orchestration("quality", "failed", "Unauthorized — token issue.")
                    else:
                        try:
                            detail = res.json().get("detail", res.text)
                        except Exception:
                            detail = res.text
                        first_line = detail.split("\n")[0] if "\n" in detail else detail[:300]
                        with st.expander(" DQ Engine Error — click to see details"):
                            st.code(detail, language="text")
                        st.error(f"Root cause: {first_line}")
                        _log_orchestration("quality", "failed", f"Root cause: {first_line}")
                except requests.exceptions.ConnectionError:
                    st.error(" Cannot connect to backend.")
                    _log_orchestration("quality", "failed", "Backend unreachable.")
                except requests.exceptions.Timeout:
                    st.error(" DQ Engine timed out — it may still be running in the background.")
                    _log_orchestration("quality", "failed", "Request timed out.")
                except Exception as e:
                    st.error(f" Unexpected error: {str(e)}")
                    _log_orchestration("quality", "failed", f"Unexpected error: {e}")
        return

    st.success("✓ Data Quality checks completed")
    st.markdown("<br>", unsafe_allow_html=True)

    qdata = st.session_state.quality_data
    if qdata and isinstance(qdata, list) and len(qdata) > 0:
        df = pd.DataFrame(qdata)
        _render_quality_visuals(df)
    else:
        st.warning("No quality report data available. Check if DQ engine ran successfully.")

    st.markdown("---")
    c1, c2 = st.columns([1, 4])
    with c1:
        if qdata and isinstance(qdata, list):
            csv_bytes = pd.DataFrame(qdata).to_csv(index=False).encode()
            st.download_button("⬇ Download DQ Report", data=csv_bytes,
                               file_name="DQ_Report.csv", mime="text/csv",
                               use_container_width=True)
    with c2:
        if st.button("Next Layer → Security ▶"):
            st.session_state.page = "security"
            st.rerun()


def _render_quality_visuals(df):
    total   = len(df)
    passed  = len(df[df["Status"] == "PASS"])    if "Status" in df.columns else 0
    failed  = len(df[df["Status"] == "FAIL"])    if "Status" in df.columns else 0
    skipped = len(df[df["Status"] == "SKIPPED"]) if "Status" in df.columns else 0
    pass_rate = round((passed / total) * 100, 1) if total > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Checks", total)
    c2.metric("✓ Passed", passed)
    c3.metric("✗ Failed", failed)
    c4.metric("⊘ Skipped", skipped)
    c5.metric("Pass Rate", f"{pass_rate}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="info-card"><div class="info-card-title">Quality Visualizations (10 Charts)</div></div>',
                unsafe_allow_html=True)

    dark = dict(paper_bgcolor="#111317", plot_bgcolor="#0d0d0d",
                font_color="#9ca3af", margin=dict(t=40, b=20, l=10, r=10))
    cs = {"PASS": "#22c55e", "FAIL": "#ef4444", "SKIPPED": "#6b7280"}

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        if "Status" in df.columns:
            sc = df["Status"].value_counts().reset_index()
            fig = px.pie(sc, values="count", names="Status", title="Overall Status",
                         color="Status", color_discrete_map=cs, hole=0.5, template="plotly_dark")
            fig.update_layout(**dark)
            st.plotly_chart(fig, use_container_width=True, key="dq_c1")

    with r1c2:
        if "Table" in df.columns and "Status" in df.columns:
            tbl = df.groupby(["Table", "Status"]).size().reset_index(name="Count")
            fig2 = px.bar(tbl, x="Table", y="Count", color="Status",
                          title="Status by Table", color_discrete_map=cs,
                          barmode="stack", template="plotly_dark")
            fig2.update_layout(**dark); fig2.update_xaxes(tickangle=30)
            st.plotly_chart(fig2, use_container_width=True, key="dq_c2")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        if "Error_Rate" in df.columns and "Table" in df.columns:
            er = df.groupby("Table")["Error_Rate"].mean().reset_index()
            fig3 = px.bar(er, x="Table", y="Error_Rate", title="Avg Error Rate by Table",
                          color="Error_Rate",
                          color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
                          template="plotly_dark")
            fig3.update_layout(**dark); fig3.update_xaxes(tickangle=30)
            st.plotly_chart(fig3, use_container_width=True, key="dq_c3")

    with r2c2:
        if "Metric" in df.columns and "Error_Rate" in df.columns:
            mr = df.groupby("Metric")["Error_Rate"].mean().reset_index()
            fig4 = px.bar(mr, x="Metric", y="Error_Rate", title="Avg Error Rate by Check",
                          color_discrete_sequence=["#FF6B35"], template="plotly_dark")
            fig4.update_layout(**dark)
            st.plotly_chart(fig4, use_container_width=True, key="dq_c4")

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        if "Total" in df.columns and "Error_Count" in df.columns:
            fig5 = px.scatter(df, x="Total", y="Error_Count", color="Status",
                              color_discrete_map=cs,
                              hover_data=["Table", "Metric"] if "Table" in df.columns else None,
                              title="Records vs Errors", template="plotly_dark")
            fig5.update_layout(**dark)
            st.plotly_chart(fig5, use_container_width=True, key="dq_c5")

    with r3c2:
        if "Table" in df.columns and "Metric" in df.columns and "Error_Rate" in df.columns:
            try:
                pivot = df.pivot_table(index="Table", columns="Metric",
                                       values="Error_Rate", aggfunc="mean").fillna(0)
                fig6 = px.imshow(pivot, title="Error Rate Heatmap",
                                 color_continuous_scale=["#0d0d0d", "#FF6B35", "#ef4444"],
                                 template="plotly_dark")
                fig6.update_layout(**dark)
                st.plotly_chart(fig6, use_container_width=True, key="dq_c6")
            except Exception:
                pass

    r4c1, r4c2 = st.columns(2)
    with r4c1:
        if "Table" in df.columns and "Error_Count" in df.columns:
            ec = df.groupby("Table")["Error_Count"].sum().reset_index().sort_values("Error_Count")
            fig7 = px.bar(ec, x="Error_Count", y="Table", orientation="h",
                          title="Total Errors by Table",
                          color_discrete_sequence=["#ef4444"], template="plotly_dark")
            fig7.update_layout(**dark)
            st.plotly_chart(fig7, use_container_width=True, key="dq_c7")

    with r4c2:
        if "Metric" in df.columns:
            mc = df["Metric"].value_counts().reset_index()
            fig8 = px.pie(mc, values="count", names="Metric", title="Check Type Distribution",
                          color_discrete_sequence=px.colors.qualitative.Set2,
                          template="plotly_dark")
            fig8.update_layout(**dark)
            st.plotly_chart(fig8, use_container_width=True, key="dq_c8")

    r5c1, r5c2 = st.columns(2)
    with r5c1:
        if "Metric" in df.columns and "Error_Rate" in df.columns:
            fig9 = px.box(df, x="Metric", y="Error_Rate", color="Metric",
                          title="Error Rate Distribution", template="plotly_dark")
            fig9.update_layout(**dark)
            st.plotly_chart(fig9, use_container_width=True, key="dq_c9")

    with r5c2:
        fig10 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pass_rate,
            title={"text": "Overall Pass Rate %", "font": {"color": "#9ca3af"}},
            delta={"reference": 90, "increasing": {"color": "#22c55e"},
                   "decreasing": {"color": "#ef4444"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#6b7280"},
                "bar": {"color": "#FF6B35"},
                "steps": [
                    {"range": [0, 60],  "color": "#1a0a00"},
                    {"range": [60, 85], "color": "#1a1200"},
                    {"range": [85, 100], "color": "#001a0a"},
                ],
                "threshold": {"line": {"color": "#22c55e", "width": 2},
                               "thickness": 0.75, "value": 90}
            }
        ))
        fig10.update_layout(paper_bgcolor="#111317", font_color="#9ca3af",
                            margin=dict(t=60, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig10, use_container_width=True, key="dq_c10")

    st.markdown('<div class="info-card"><div class="info-card-title">Full Quality Report</div></div>',
                unsafe_allow_html=True)

    def highlight(row):
        s = row.get("Status", "")
        if s == "PASS":  return ["background-color:rgba(34,197,94,0.08)"] * len(row)
        if s == "FAIL":  return ["background-color:rgba(239,68,68,0.08)"] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)


# =========================
# SECURITY PAGE
# =========================
def security_page():
    page_header("04", "Security Layer", "Masking · Hashing · AES Encryption · Audit Trail")

    if not st.session_state.quality_done:
        st.warning(" Complete Data Quality Layer first.")
        return

    st.markdown("""
    <div class="info-card">
        <div class="info-card-title">About This Layer</div>
        <p style="color:#9ca3af;font-size:14px;line-height:1.75;margin:0;">
            Enforces data protection with field-level masking and AES-256 encryption via Fernet.
            Original data from <code>StorageLayer/LoadedData</code> is transformed and written
            to <code>StorageLayer/SecuredData</code>. Keys stored in <code>StorageLayer/Keys</code>.
            All actions are logged via the Audit Service.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="info-card"><div class="info-card-title">Security Options</div></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    apply_mask = c1.checkbox("Apply Masking", value=True,
                              help="Masks PII fields: names, phone, address, salary → first 2 chars + ****")
    apply_enc  = c2.checkbox("Apply AES Encryption", value=True,
                              help="Encrypts sensitive fields: national_id, diagnosis, insurance_number → Fernet base64")

    st.markdown("<br>", unsafe_allow_html=True)

    details = (st.session_state.ingestion_data or {}).get("details", {})
    if details:
        first_table = list(details.keys())[0]
        sample_before = details[first_table].get("sample", [])
        if sample_before:
            st.markdown("""
            <div class="info-card">
                <div class="info-card-title">📄 Data Sample — BEFORE Security (Raw)</div>
            </div>""", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(sample_before), use_container_width=True)

    if not st.session_state.security_done:
        if not (apply_mask or apply_enc):
            st.info("Select at least one security option to continue.")
            return

        if st.button("▶ Run Security Layer", use_container_width=False):
            with st.spinner("Applying masking & encryption with pandas + Fernet..."):
                try:
                    res = requests.post(f"{API}/security/run", timeout=300)
                    if res.status_code == 200:
                        st.session_state.security_data = res.json()
                        st.session_state.security_done = True
                        _log_orchestration("security", "success", "Masking & encryption applied.")
                        st.success("✓ Security applied!")
                        st.rerun()
                    else:
                        try:
                            detail = res.json().get("detail", res.text)
                        except Exception:
                            detail = res.text
                        with st.expander(" Security Error — click for details"):
                            st.code(detail, language="text")
                        st.error(f"Root cause: {detail[:300]}")
                        _log_orchestration("security", "failed", f"Root cause: {detail[:300]}")
                except requests.exceptions.ConnectionError:
                    st.error(" Cannot connect to backend. Is uvicorn running?")
                    _log_orchestration("security", "failed", "Backend unreachable.")
                except Exception as e:
                    st.error(f" Unexpected error: {str(e)}")
                    _log_orchestration("security", "failed", f"Unexpected error: {e}")
        return

    st.success("✓ Security transformations applied successfully")
    st.markdown("<br>", unsafe_allow_html=True)

    sec_data = st.session_state.security_data or {}
    if "files_processed" in sec_data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Files Secured", sec_data.get("files_processed", 0))
        c2.metric("Encryption", "AES-256 Fernet")
        c3.metric("Audit Log", "✓ Written")

    st.markdown("<br>", unsafe_allow_html=True)

    secured_path = "StorageLayer/SecuredData"
    shown = 0
    if os.path.exists(secured_path):
        csv_files = [f for f in os.listdir(secured_path) if f.endswith(".csv")]
        for fname in csv_files[:2]:
            fpath = os.path.join(secured_path, fname)
            try:
                sdf = pd.read_csv(fpath, nrows=5)
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-card-title"> AFTER Security — {fname}</div>
                </div>""", unsafe_allow_html=True)
                st.dataframe(sdf, use_container_width=True)
                shown += 1
            except Exception as e:
                st.warning(f"Could not read {fname}: {e}")

    if shown == 0:
        st.info("Secured files not found in StorageLayer/SecuredData — check if run completed.")

    st.markdown("""
    <div class="info-card" style="border-color:#FF6B35;margin-top:16px;">
        <div class="info-card-title"> What Changed</div>
        <div style="color:#9ca3af;font-size:14px;line-height:2;">
            <b style="color:#1a1a1a;">Masked fields:</b>
            first_name, last_name, phone, street, city, state, salary, notes
            → <code style="color:#FF6B35;">Jo****</code><br>
            <b style="color:#FF6B35;">Encrypted fields:</b>
            national_id, diagnosis, insurance_number, hypertension, diabetes
            → <code style="color:#FF6B35;">gAAAAAB...base64ciphertext</code><br>
            <b style="color:#22c55e;">Key location:</b>
            <code>StorageLayer/Keys/encryption_key.txt</code><br>
            <b style="color:#9ca3af;">Audit log:</b>
            <code>StorageLayer/audit_log.txt</code> — timestamp · user · action
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Next Layer → Data Warehouse ▶"):
        st.session_state.page = "DWH"
        st.rerun()


# =========================
# DWH PAGE
# =========================
def DWH_page():
    page_header("05", "Data Warehouse Layer", "Load to Staging & DWH")

    st.markdown("""
    <div class="info-card" style="padding:24px 32px;margin-bottom:24px;">
        <div style="font-size:13px;font-weight:700;color:#6b7280;
                    letter-spacing:.1em;margin-bottom:16px;">PIPELINE FLOW</div>
        <div style="display:flex;align-items:center;gap:0;flex-wrap:wrap;">
            <div style="background:#f5f5f5;border:1px solid #e0e0e0;
                        border-radius:8px;padding:10px 18px;text-align:center;">
                <div style="font-size:18px;"></div>
                <div style="font-size:11px;color:#888;margin-top:4px;">OLTP</div>
                <div style="font-size:10px;color:#aaa;">DEPI</div>
            </div>
            <div style="color:#aaa;font-size:20px;padding:0 8px;">→</div>
            <div style="background:#f5f5f5;border:1px solid #2563eb;
                        border-radius:8px;padding:10px 18px;text-align:center;">
                <div style="font-size:18px;"></div>
                <div style="font-size:11px;color:#2563eb;margin-top:4px;">Staging</div>
                <div style="font-size:10px;color:#aaa;">DEPI_STG</div>
            </div>
            <div style="color:#aaa;font-size:20px;padding:0 8px;">→</div>
            <div style="background:#f5f5f5;border:1px solid #7c3aed;
                        border-radius:8px;padding:10px 18px;text-align:center;">
                <div style="font-size:18px;"></div>
                <div style="font-size:11px;color:#7c3aed;margin-top:4px;">DWH</div>
                <div style="font-size:10px;color:#aaa;">DEPI_DWH</div>
            </div>
            <div style="color:#aaa;font-size:20px;padding:0 8px;">→</div>
            <div style="background:#f5f5f5;border:1px solid #d97706;
                        border-radius:8px;padding:10px 18px;text-align:center;">
                <div style="font-size:18px;"></div>
                <div style="font-size:11px;color:#d97706;margin-top:4px;">Power BI</div>
                <div style="font-size:10px;color:#aaa;">Next step</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title"> Load-to-STG.dtsx</div>
            <div style="font-size:12px;color:#888;line-height:1.9;">
                ✔ Container Admission<br>
                ✔ Container Appointment<br>
                ✔ Container Beds<br>
                ✔ Container Departments<br>
                ✔ Container Doctors<br>
                ✔ Container Equipment<br>
                ✔ Container Medical History<br>
                ✔ Container Notifications<br>
                ✔ Container Nurses<br>
                ✔ Container Patients<br>
                ✔ Container Rooms
            </div>
            <div style="margin-top:12px;font-size:11px;color:#aaa;">
                Source → DEPI &nbsp;|&nbsp; Target → DEPI_STG
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title"> Load-to-DWH.dtsx</div>
            <div style="font-size:12px;color:#888;line-height:1.9;">
                ✔ Build Dim_Date<br>
                ✔ Load Dim_Healthcare<br>
                ✔ Load Dim_Location<br>
                ✔ Load Dim_Patient<br>
                ✔ Load Fact_Admission<br>
                ✔ Load Fact_Appointment<br>
                <br>
                <span style="color:#aaa;font-style:italic;">
                    SCD Type 2 · Slowly Changing Dimensions
                </span>
            </div>
            <div style="margin-top:12px;font-size:11px;color:#aaa;">
                Source → DEPI_STG &nbsp;|&nbsp; Target → DEPI_DWH
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(" Check Connection & Packages"):
        with st.spinner("Checking..."):
            try:
                r = requests.get(f"{API}/dwh/status", timeout=5)
                info = r.json()
                dtexec_ok = info.get("dtexec_found", False)

                if dtexec_ok:
                    st.success(f" DTExec found: `{info.get('dtexec_path')}`")
                else:
                    st.error(" DTExec not found — install SQL Server Integration Services")

                for pkg, detail in info.get("packages", {}).items():
                    icon = "" if detail["exists"] else ""
                    st.markdown(f"{icon} **{pkg}** → `{detail['path']}`")

            except Exception as e:
                st.error(f"API unreachable: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:13px;font-weight:700;color:#888;
                letter-spacing:.1em;margin-bottom:16px;text-transform:uppercase;">
        Run Packages
    </div>
    """, unsafe_allow_html=True)

    btn1, btn2, btn3 = st.columns(3)

    def _show_result(res: dict, label: str):
        status  = res.get("status", "unknown")
        color   = "#22c55e" if status == "success" else "#ef4444"
        icon    = "" if status == "success" else ""
        elapsed = res.get("elapsed_seconds", "—")
        msg     = res.get("message", "")
        stdout  = res.get("stdout", "")
        st.markdown(f"""
        <div class="info-card" style="border-left:3px solid {color};margin-top:12px;">
            <div style="font-size:14px;font-weight:700;color:{color};">
                {icon} {label} — {status.upper()}
            </div>
            <div style="font-size:12px;color:#888;margin-top:6px;">
                ⏱ Elapsed: {elapsed}s
                {f'<br>{msg}' if msg else ''}
            </div>
            {f'<pre style="font-size:10px;color:#aaa;margin-top:8px;max-height:120px;overflow:auto;">{stdout[-800:]}</pre>' if stdout else ''}
        </div>
        """, unsafe_allow_html=True)

    with btn1:
        if st.button("▶ Run STG Only", use_container_width=True):
            with st.spinner("Running Load-to-STG.dtsx …"):
                try:
                    r = requests.post(f"{API}/dwh/run-stg", timeout=620)
                    res = r.json()
                    _show_result(res, "Load-to-STG")
                    _log_orchestration(
                        "stg_to_dwh_dag", res.get("status", "failed"),
                        "Load-to-STG.dtsx run.", 
                    )
                except Exception as e:
                    st.error(str(e))
                    _log_orchestration("stg_to_dwh_dag", "failed", f"STG run error: {e}")

    with btn2:
        if st.button("▶ Run DWH Only", use_container_width=True):
            with st.spinner("Running Load-to-DWH.dtsx …"):
                try:
                    r = requests.post(f"{API}/dwh/run-dwh", timeout=620)
                    res = r.json()
                    _show_result(res, "Load-to-DWH")
                    _log_orchestration(
                        "stg_to_dwh_dag", res.get("status", "failed"),
                        "Load-to-DWH.dtsx run.",
                    )
                except Exception as e:
                    st.error(str(e))
                    _log_orchestration("stg_to_dwh_dag", "failed", f"DWH run error: {e}")

    with btn3:
        if st.button(" Run Full Pipeline", use_container_width=True):
            with st.spinner("Running STG → DWH …"):
                try:
                    r = requests.post(f"{API}/dwh/run-all", timeout=1260)
                    data = r.json()
                    overall = data.get("status", "unknown")
                    if overall == "success":
                        st.success(" Full pipeline completed successfully!")
                    else:
                        st.warning(f" Pipeline ended with status: **{overall}**")
                    if data.get("stg"):
                        _show_result(data["stg"], "Load-to-STG")
                    if data.get("dwh"):
                        _show_result(data["dwh"], "Load-to-DWH")
                    _log_orchestration(
                        "stg_to_dwh_dag",
                        "success" if overall == "success" else "failed",
                        "Full pipeline (STG → DWH) run.",
                    )
                except Exception as e:
                    st.error(str(e))
                    _log_orchestration("stg_to_dwh_dag", "failed", f"Full pipeline error: {e}")

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("⬅ Back to Security"):
            st.session_state.page = "security"
            st.rerun()
    with c2:
        if st.button("Next → Power BI ▶"):
            st.session_state.dwh_done = True
            st.session_state.page = "Dashboard"
            st.rerun()


# =========================
# POWER BI PAGE
# =========================
def Dashboard_page():
    page_header("06", "Power BI Layer", "Live Dashboard")

    DASHBOARD_URL = "https://app.powerbi.com/links/sVc9YDh19Z?ctid=a2c31985-cc3b-4e19-8fa2-59fa488f0c27&pbi_source=linkShare"
    try:
        res = requests.get(f"{API}/powerbi/dashboard", timeout=10)
        if res.status_code == 200:
            fetched_url = res.json().get("dashboard_url", "")
            if fetched_url:
                DASHBOARD_URL = fetched_url
        _log_orchestration("powerbi_refresh_dag", "success", "Dashboard link served to UI.")
    except Exception:
        # Backend unreachable or endpoint not registered — silently fall back, never crash the page.
        _log_orchestration("powerbi_refresh_dag", "failed", "Backend unreachable while loading dashboard.")

    st.markdown("""
    <div class="info-card" style="text-align:center;padding:48px 40px;margin-bottom:24px;">
        <div style="font-size:52px;margin-bottom:16px;"></div>
        <div style="font-size:24px;font-weight:800;color:#1a1a1a;margin-bottom:10px;">
            Hospital Analytics Dashboard
        </div>
        <div style="font-size:14px;color:#888;max-width:480px;margin:0 auto 32px auto;line-height:1.7;">
            Your Data Warehouse is ready. View the live Power BI dashboard
            connected directly to <code>DEPI_DWH</code> — star schema,
            fact &amp; dimension tables, fully loaded.
        </div>
        <a href="{url}" target="_blank"
           style="display:inline-block;padding:16px 48px;
                  background:#E23400;color:#fff;
                  font-size:15px;font-weight:700;letter-spacing:0.5px;
                  border-radius:6px;text-decoration:none;">
            🔗 Open Power BI Dashboard
        </a>
    </div>
    """.format(url=DASHBOARD_URL), unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <div class="info-card-title">Dashboard URL</div>
    </div>
    """, unsafe_allow_html=True)
    st.code(DASHBOARD_URL, language="text")

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown("""
    <div class="info-card" style="text-align:center;">
        <div style="font-size:32px;"></div>
        <div style="font-size:12px;font-weight:700;color:#FF6B35;margin-top:8px;
                    letter-spacing:1px;text-transform:uppercase;">Source</div>
        <div style="font-size:13px;color:#888;margin-top:6px;">DEPI_DWH<br>(OLAP)</div>
    </div>
    """, unsafe_allow_html=True)
    c2.markdown("""
    <div class="info-card" style="text-align:center;">
        <div style="font-size:32px;">⭐</div>
        <div style="font-size:12px;font-weight:700;color:#FF6B35;margin-top:8px;
                    letter-spacing:1px;text-transform:uppercase;">Schema</div>
        <div style="font-size:13px;color:#888;margin-top:6px;">Star Schema<br>Fact + Dims</div>
    </div>
    """, unsafe_allow_html=True)
    c3.markdown("""
    <div class="info-card" style="text-align:center;">
        <div style="font-size:32px;"></div>
        <div style="font-size:12px;font-weight:700;color:#FF6B35;margin-top:8px;
                    letter-spacing:1px;text-transform:uppercase;">Access</div>
        <div style="font-size:13px;color:#888;margin-top:6px;">ShareLink<br>Authenticated</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("⬅ Back to Data Warehouse"):
            st.session_state.page = "DWH"
            st.rerun()
    with c2:
        if st.button("Next → Orchestration ▶"):
            st.session_state.powerbi_done = True
            st.session_state.page = "Orchestration"
            st.rerun()


# =========================
# ORCHESTRATION PAGE (Apache Airflow style)
# =========================
def orchestration_page():
    page_header("07", "Orchestration Layer", "Powered by Apache Airflow")

    AIRFLOW_URL = "http://localhost:8080"
    AIRFLOW_DAG_ID = "data_catalog_pipeline"
    AIRFLOW_USER = "admin"
    AIRFLOW_PASS = "admin"

    def _trigger_airflow_dag():
        """
        Triggers a new run of the real Airflow DAG via its REST API.
        NOTE: targets Airflow's /api/v2 surface (Airflow 3.x). If your
        instance expects a different path/auth, this fails gracefully
        with an error message instead of crashing the page — check
        http://localhost:8080/api/v2/openapi.json for the exact contract.
        """
        import uuid
        try:
            resp = requests.post(
                f"{AIRFLOW_URL}/api/v2/dags/{AIRFLOW_DAG_ID}/dagRuns",
                json={"dag_run_id": f"manual__{uuid.uuid4().hex[:8]}", "conf": {}},
                auth=(AIRFLOW_USER, AIRFLOW_PASS),
                timeout=10,
            )
            if resp.status_code in (200, 201):
                return True, "Triggered successfully."
            return False, f"Airflow returned {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            return False, str(e)

    st.markdown("""
    <div class="info-card" style="text-align:center;padding:48px 40px;margin-bottom:24px;">
        <div style="font-size:52px;margin-bottom:16px;">🪁</div>
        <div style="font-size:24px;font-weight:800;color:#1a1a1a;margin-bottom:10px;">
            Orchestration runs on Apache Airflow
        </div>
        <div style="font-size:14px;color:#888;max-width:520px;margin:0 auto 8px auto;line-height:1.7;">
            Every layer above — Profiling, Data Quality, Security, DWH, Power BI —
            is wired into a single Airflow DAG (<code>data_catalog_pipeline</code>)
            that runs them in order. Manage and monitor runs directly in Airflow.
        </div>
    </div>
    """, unsafe_allow_html=True)

    af_c1, af_c2 = st.columns(2)
    with af_c1:
        st.link_button("Open Airflow UI ↗", AIRFLOW_URL, use_container_width=True)
    with af_c2:
        if st.button("▶ Trigger Pipeline Now", use_container_width=True, key="af_trigger_btn"):
            ok, msg = _trigger_airflow_dag()
            if ok:
                st.success(f"DAG '{AIRFLOW_DAG_ID}' triggered — track progress in the Airflow UI above.")
            else:
                st.error(f"Could not trigger DAG: {msg}")

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("⬅ Back to Power BI"):
            st.session_state.page = "Dashboard"
            st.rerun()
    with c2:
        if st.button("Finish ✓", use_container_width=False):
            st.session_state.orchestration_done = True
            st.session_state.page = "Goodbye"
            st.rerun()


def register_page():
    st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 60px 10% !important; max-width: 700px !important; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:60px 0 40px 0;">
        <div style="width:56px;height:56px;background:linear-gradient(135deg,#FF6B35,#E23400);
             clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
             margin:0 auto 20px auto;"></div>
        <div style="font-size:13px;font-weight:700;letter-spacing:3px;text-transform:uppercase;
             color:#FF6B35;margin-bottom:12px;">Data Quality Gate</div>
        <div style="font-size:36px;font-weight:800;color:#1a1a1a;letter-spacing:-1px;margin-bottom:16px;">
            Thank you for choosing Data Quality Gate
        </div>
        <div style="font-size:16px;color:#666;max-width:480px;margin:0 auto 36px auto;line-height:1.75;">
            We're glad to have you with us. If you need an account or would like to
            talk to us about the platform, send us an email and we'll get back to you shortly.
        </div>
        <a href="mailto:Shimaaelzadey@gmail.com?subject=Data%20Quality%20Gate%20-%20Inquiry"
           style="display:inline-block;padding:14px 36px;
                  background:#E23400;color:#fff;
                  font-size:14px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
                  border-radius:6px;text-decoration:none;margin-bottom:36px;">
            Get in Touch
        </a>
        <div style="background:#fff8f5;border:1.5px solid #FF6B35;border-radius:8px;
             padding:24px 32px;max-width:480px;margin:0 auto 36px auto;text-align:left;">
            <div style="font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
                 color:#FF6B35;margin-bottom:12px;">Contact Information</div>
            <div style="font-size:14px;color:#444;line-height:2;">
                Platform: <b>Data Quality Gate v1.0</b><br>
                Email: <b>Shimaaelzadey@gmail.com</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Back to Sign In", use_container_width=False):
        st.session_state.page = "login"
        st.rerun()


# =========================
# LANDING / WELCOME PAGE  (shown before login)
# =========================
_HERO_STYLE = """<style>
    .stApp { background-color: #ffffff !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* ── Top utility bar ── */
    .land-topbar {
        background:#f7f7f7; border-bottom:1px solid #eee;
        padding:8px 40px; display:flex; justify-content:flex-end; gap:24px;
        font-size:12px; color:#666;
    }

    /* ── Navbar ── */
    .land-navbar {
        display:flex; align-items:center; justify-content:space-between;
        padding:18px 40px; border-bottom:1px solid #eee; background:#fff;
    }
    .land-nav-logo { display:flex; align-items:center; gap:10px; }
    .land-nav-hex {
        width:30px;height:30px;flex-shrink:0;
        background:linear-gradient(135deg,#FF6B35,#E23400);
        clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    }
    .land-nav-name { font-size:17px; font-weight:700; color:#1a1a1a; }
    .land-nav-links { display:flex; gap:32px; font-size:14px; color:#333; font-weight:500; }

    /* ── Breadcrumb bar ── */
    .land-breadcrumb {
        padding:14px 40px; border-bottom:1px solid #eee;
        font-size:12px; font-weight:700; letter-spacing:1px;
        color:#666; text-transform:uppercase;
    }

    /* ── Dark hero banner with REAL Informatica-style swirl image as background ── */
    .land-hero {
        background-color: #0d1117;
        background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNzAwIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCBzbGljZSI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImcxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGNkIzNSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGRjNEMDAiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImcyIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGOTgwMCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGRjZCMzUiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImczIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0UwNDBGQiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiM3QjFGQTIiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc0IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzAwQkNENCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMwMDk3QTciLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc1IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzRDQUY1MCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMyRTdEMzIiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc2IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGRUIzQiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGOUE4MjUiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI2MDAiIGhlaWdodD0iNzAwIiBmaWxsPSIjMTExODI3Ii8+CiAgPHBhdGggZD0iTSA2MDAgMCBDIDUwMCAxMDAgMzAwIDE1MCAyMDAgMzUwIEMgMTAwIDU1MCAxNTAgNjUwIDAgNzAwIEwgMCA2MDAgQyAxMjAgNTYwIDgwIDQ2MCAxODAgMjgwIEMgMjgwIDEwMCA0NTAgNjAgNjAwIDEwMCBaIiBmaWxsPSJ1cmwoI2cxKSIgb3BhY2l0eT0iMC45MiIvPgogIDxwYXRoIGQ9Ik0gNjAwIDUwIEMgNDgwIDEzMCAzMjAgMTgwIDIzMCAzNzAgQyAxNDAgNTYwIDE4MCA2NTAgNTAgNzAwIEwgMCA3MDAgTCAwIDYyMCBDIDE0MCA1ODAgMTAwIDQ3MCAyMDAgMzAwIEMgMzAwIDEzMCA0NjAgODAgNjAwIDEzMCBaIiBmaWxsPSJ1cmwoI2cyKSIgb3BhY2l0eT0iMC44NSIvPgogIDxwYXRoIGQ9Ik0gNjAwIDEyMCBDIDUyMCAxODAgNDAwIDIwMCAzMzAgMzgwIEMgMjYwIDU2MCAzMDAgNjQwIDEyMCA3MDAgTCA2MCA3MDAgQyAyNDAgNjQwIDIxMCA1NjAgMjgwIDM5MCBDIDM1MCAyMjAgNDcwIDE4MCA2MDAgMjAwIFoiIGZpbGw9InVybCgjZzMpIiBvcGFjaXR5PSIwLjgwIi8+CiAgPHBhdGggZD0iTSA2MDAgMjAwIEMgNTUwIDI0MCA0NjAgMjYwIDQwMCA0MjAgQyAzNDAgNTgwIDM3MCA2NTAgMjAwIDcwMCBMIDE0MCA3MDAgQyAzMTAgNjUwIDI5MCA1ODAgMzUwIDQzMCBDIDQxMCAyODAgNTAwIDI0MCA2MDAgMjgwIFoiIGZpbGw9InVybCgjZzQpIiBvcGFjaXR5PSIwLjc1Ii8+CiAgPHBhdGggZD0iTSA2MDAgMjkwIEMgNTcwIDMyMCA1MTAgMzQwIDQ2MCA0NzAgQyA0MTAgNjAwIDQzMCA2NjAgMjkwIDcwMCBMIDIzMCA3MDAgQyAzODAgNjYwIDM2MCA2MDAgNDEwIDQ4MCBDIDQ2MCAzNjAgNTIwIDMyMCA2MDAgMzYwIFoiIGZpbGw9InVybCgjZzUpIiBvcGFjaXR5PSIwLjcwIi8+CiAgPHBhdGggZD0iTSA2MDAgMzgwIEMgNTgwIDQwMCA1NTAgNDIwIDUxMCA1MzAgQyA0NzAgNjQwIDQ5MCA2ODAgMzgwIDcwMCBMIDMzMCA3MDAgQyA0NTAgNjgwIDQzMCA2NDAgNDcwIDU0MCBDIDUxMCA0NDAgNTQwIDQwMCA2MDAgNDQwIFoiIGZpbGw9InVybCgjZzYpIiBvcGFjaXR5PSIwLjY1Ii8+Cjwvc3ZnPg==");
        background-size: cover;
        background-position: right center;
        background-repeat: no-repeat;
        position: relative; overflow:hidden;
        padding: 90px 40px 70px 40px;
        text-align:center;
    }
    .land-hero::before {
        content:''; position:absolute; inset:0;
        background: linear-gradient(90deg, rgba(13,17,23,0.92) 0%, rgba(13,17,23,0.72) 32%, rgba(13,17,23,0.15) 62%, rgba(13,17,23,0.0) 100%);
        z-index:1;
    }
    .land-hero-inner { position:relative; z-index:2; max-width:780px; margin:0 auto; }
    .land-hero-title {
        font-size:54px; font-weight:800; color:#fff; line-height:1.15;
        letter-spacing:-1px; margin-bottom:22px;
    }
    .land-hero-sub {
        font-size:17px; color:#d1d5db; line-height:1.75; margin-bottom:0;
        max-width:680px; margin-left:auto; margin-right:auto;
    }

    /* ── CTA row under hero, centered ── */
    .land-cta-row { padding:44px 40px 24px 40px; text-align:center; background:#fff; }

    /* ── Layer cards section ── */
    .land-layers-heading {
        text-align:center; padding: 8px 40px 0 40px;
    }
    .land-layers-heading .badge {
        font-size:11px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase;
        color:#FF6B35; margin-bottom:10px; display:block;
    }
    .land-layers-heading .title {
        font-size:30px; font-weight:800; color:#1a1a1a; letter-spacing:-0.5px; margin-bottom:6px;
    }
    .land-layers-heading .sub {
        font-size:14px; color:#888; margin-bottom:32px;
    }
    </style>"""


def landing_page():
    st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* ── Top utility bar ── */
    .land-topbar {
        background:#f7f7f7; border-bottom:1px solid #eee;
        padding:8px 40px; display:flex; justify-content:flex-end; gap:24px;
        font-size:12px; color:#666;
    }

    /* ── Navbar ── */
    .land-navbar {
        display:flex; align-items:center; justify-content:space-between;
        padding:18px 40px; border-bottom:1px solid #eee; background:#fff;
    }
    .land-nav-logo { display:flex; align-items:center; gap:10px; }
    .land-nav-hex {
        width:30px;height:30px;flex-shrink:0;
        background:linear-gradient(135deg,#FF6B35,#E23400);
        clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    }
    .land-nav-name { font-size:17px; font-weight:700; color:#1a1a1a; }
    .land-nav-links { display:flex; gap:32px; font-size:14px; color:#333; font-weight:500; }

    /* ── Breadcrumb bar ── */
    .land-breadcrumb {
        padding:14px 40px; border-bottom:1px solid #eee;
        font-size:12px; font-weight:700; letter-spacing:1px;
        color:#666; text-transform:uppercase;
    }

    /* ── Dark hero banner with REAL Informatica-style swirl image as background ── */
    .land-hero {
        background-color: #0d1117;
        background-image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MDAgNzAwIiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCBzbGljZSI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImcxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGNkIzNSIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGRjNEMDAiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImcyIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGOTgwMCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGRjZCMzUiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImczIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0UwNDBGQiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiM3QjFGQTIiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc0IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzAwQkNENCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMwMDk3QTciLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc1IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzRDQUY1MCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiMyRTdEMzIiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9Imc2IiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iI0ZGRUIzQiIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNGOUE4MjUiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI2MDAiIGhlaWdodD0iNzAwIiBmaWxsPSIjMTExODI3Ii8+CiAgPHBhdGggZD0iTSA2MDAgMCBDIDUwMCAxMDAgMzAwIDE1MCAyMDAgMzUwIEMgMTAwIDU1MCAxNTAgNjUwIDAgNzAwIEwgMCA2MDAgQyAxMjAgNTYwIDgwIDQ2MCAxODAgMjgwIEMgMjgwIDEwMCA0NTAgNjAgNjAwIDEwMCBaIiBmaWxsPSJ1cmwoI2cxKSIgb3BhY2l0eT0iMC45MiIvPgogIDxwYXRoIGQ9Ik0gNjAwIDUwIEMgNDgwIDEzMCAzMjAgMTgwIDIzMCAzNzAgQyAxNDAgNTYwIDE4MCA2NTAgNTAgNzAwIEwgMCA3MDAgTCAwIDYyMCBDIDE0MCA1ODAgMTAwIDQ3MCAyMDAgMzAwIEMgMzAwIDEzMCA0NjAgODAgNjAwIDEzMCBaIiBmaWxsPSJ1cmwoI2cyKSIgb3BhY2l0eT0iMC44NSIvPgogIDxwYXRoIGQ9Ik0gNjAwIDEyMCBDIDUyMCAxODAgNDAwIDIwMCAzMzAgMzgwIEMgMjYwIDU2MCAzMDAgNjQwIDEyMCA3MDAgTCA2MCA3MDAgQyAyNDAgNjQwIDIxMCA1NjAgMjgwIDM5MCBDIDM1MCAyMjAgNDcwIDE4MCA2MDAgMjAwIFoiIGZpbGw9InVybCgjZzMpIiBvcGFjaXR5PSIwLjgwIi8+CiAgPHBhdGggZD0iTSA2MDAgMjAwIEMgNTUwIDI0MCA0NjAgMjYwIDQwMCA0MjAgQyAzNDAgNTgwIDM3MCA2NTAgMjAwIDcwMCBMIDE0MCA3MDAgQyAzMTAgNjUwIDI5MCA1ODAgMzUwIDQzMCBDIDQxMCAyODAgNTAwIDI0MCA2MDAgMjgwIFoiIGZpbGw9InVybCgjZzQpIiBvcGFjaXR5PSIwLjc1Ii8+CiAgPHBhdGggZD0iTSA2MDAgMjkwIEMgNTcwIDMyMCA1MTAgMzQwIDQ2MCA0NzAgQyA0MTAgNjAwIDQzMCA2NjAgMjkwIDcwMCBMIDIzMCA3MDAgQyAzODAgNjYwIDM2MCA2MDAgNDEwIDQ4MCBDIDQ2MCAzNjAgNTIwIDMyMCA2MDAgMzYwIFoiIGZpbGw9InVybCgjZzUpIiBvcGFjaXR5PSIwLjcwIi8+CiAgPHBhdGggZD0iTSA2MDAgMzgwIEMgNTgwIDQwMCA1NTAgNDIwIDUxMCA1MzAgQyA0NzAgNjQwIDQ5MCA2ODAgMzgwIDcwMCBMIDMzMCA3MDAgQyA0NTAgNjgwIDQzMCA2NDAgNDcwIDU0MCBDIDUxMCA0NDAgNTQwIDQwMCA2MDAgNDQwIFoiIGZpbGw9InVybCgjZzYpIiBvcGFjaXR5PSIwLjY1Ii8+Cjwvc3ZnPg==");
        background-size: cover;
        background-position: right center;
        background-repeat: no-repeat;
        position: relative; overflow:hidden;
        padding: 90px 40px 70px 40px;
        text-align:center;
    }
    .land-hero::before {
        content:''; position:absolute; inset:0;
        background: linear-gradient(90deg, rgba(13,17,23,0.92) 0%, rgba(13,17,23,0.72) 32%, rgba(13,17,23,0.15) 62%, rgba(13,17,23,0.0) 100%);
        z-index:1;
    }
    .land-hero-inner { position:relative; z-index:2; max-width:780px; margin:0 auto; }
    .land-hero-title {
        font-size:54px; font-weight:800; color:#fff; line-height:1.15;
        letter-spacing:-1px; margin-bottom:22px;
    }
    .land-hero-sub {
        font-size:17px; color:#d1d5db; line-height:1.75; margin-bottom:0;
        max-width:680px; margin-left:auto; margin-right:auto;
    }

    /* ── CTA row under hero, centered ── */
    .land-cta-row { padding:44px 40px 24px 40px; text-align:center; background:#fff; }

    /* ── Layer cards section ── */
    .land-layers-heading {
        text-align:center; padding: 8px 40px 0 40px;
    }
    .land-layers-heading .badge {
        font-size:11px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase;
        color:#FF6B35; margin-bottom:10px; display:block;
    }
    .land-layers-heading .title {
        font-size:30px; font-weight:800; color:#1a1a1a; letter-spacing:-0.5px; margin-bottom:6px;
    }
    .land-layers-heading .sub {
        font-size:14px; color:#888; margin-bottom:32px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="land-topbar">
        <span>Support</span><span>Pricing</span><span>Contact Us</span>
    </div>
    <div class="land-navbar">
        <div class="land-nav-logo">
            <div class="land-nav-hex"></div>
            <span class="land-nav-name">Data Quality Gate</span>
        </div>
        <div class="land-nav-links">
            <span>Why DQ Gate</span><span>Layers</span><span>Resources</span><span>Partners</span>
        </div>
    </div>
    <div class="land-breadcrumb">PIPELINE PLATFORM &nbsp;&rsaquo;&nbsp; ORCHESTRATION SUITE</div>

    <div class="land-hero">
        <div class="land-hero-inner">
            <div class="land-hero-title">Data Quality and Orchestration</div>
            <div class="land-hero-sub">
                A complete platform for managing the full healthcare data lifecycle —
                from ingestion to interactive dashboards, covering profiling, quality
                checks, security, warehouse loading, and end-to-end orchestration.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA buttons, centered ──
    st.markdown('<div class="land-cta-row">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([2, 1, 0.3, 1, 2])
    with c2:
        if st.button("Get Started", use_container_width=True, key="land_get_started"):
            st.session_state.page = "login"
            st.rerun()
    with c4:
        if st.button("Get in Touch", use_container_width=True, key="land_get_touch"):
            st.session_state.page = "register"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Layer cards heading ──
    st.markdown("""
    <div class="land-layers-heading">
        <span class="badge">Platform Capabilities</span>
        <div class="title">Six Layers, One Pipeline</div>
        <div class="sub">Six layers, one pipeline — here's what each one does.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .land-layers-wrap { max-width: 1080px; margin: 0 auto; padding: 0 40px 56px 40px; }
    </style>
    """, unsafe_allow_html=True)

    layers_cards = [
        {"num": "01", "icon": "", "color": "#FF6B35",
         "title": "Ingestion",
         "desc": "Imports raw data from CSV files or SQL Server. Apache Spark reads, validates, and stores each table, capturing row counts, column types, and null distributions."},
        {"num": "02", "icon": "", "color": "#2563eb",
         "title": "Profiling",
         "desc": "Runs deep statistical analysis on every ingested table — per-column distributions, null rates, and descriptive stats — packaged as a downloadable report."},
        {"num": "03", "icon": "", "color": "#16a34a",
         "title": "Data Quality",
         "desc": "Rule-based checks across all tables: completeness, uniqueness, and referential integrity, scored against configurable thresholds."},
        {"num": "04", "icon": "", "color": "#7c3aed",
         "title": "Security",
         "desc": "Protects sensitive fields with masking and AES-256 (Fernet) encryption before data leaves the platform, with every action written to an audit log."},
        {"num": "05", "icon": "", "color": "#d97706",
         "title": "Data Warehouse",
         "desc": "SSIS packages load data into Staging, then transform and load it into the warehouse using a star schema (fact + dimension tables)."},
        {"num": "06", "icon": "", "color": "#dc2626",
         "title": "Power BI",
         "desc": "Surfaces the warehouse data as a live, interactive dashboard, connected directly to the DWH and refreshed on a daily schedule."},
    ]

    st.markdown("""
    <style>
    .layer-card-grid {
        display:grid; grid-template-columns:repeat(3, 1fr); gap:20px;
        max-width:1080px; margin:0 auto;
    }
    @media (max-width: 900px) { .layer-card-grid { grid-template-columns:repeat(2, 1fr); } }
    .layer-card {
        background:#fff; border:1px solid #e8e8e8; border-radius:12px;
        padding:26px 22px; box-shadow:0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .layer-card:hover { transform: translateY(-3px); box-shadow:0 8px 22px rgba(0,0,0,0.09); }
    .layer-card-icon {
        width:64px; height:64px; border-radius:50%; display:flex;
        align-items:center; justify-content:center; font-size:30px;
        margin-bottom:16px; color:#fff;
    }
    .layer-card-num {
        font-size:11px; font-weight:800; letter-spacing:1.5px; color:#aaa; margin-bottom:4px;
    }
    .layer-card-title { font-size:18px; font-weight:800; color:#1a1a1a; margin-bottom:10px; }
    .layer-card-desc { font-size:13px; color:#666; line-height:1.7; }
    </style>
    """, unsafe_allow_html=True)

    # NOTE: every fragment below is built with ZERO leading whitespace before
    # each tag. Streamlit's markdown renderer treats lines indented by 4+
    # spaces as a code block, which breaks HTML rendering for anything
    # after the first card if we indent nicely here. Keep it flat/compact.
    card_parts = []
    for c in layers_cards:
        card_parts.append(
            '<div class="layer-card">'
            f'<div class="layer-card-icon" style="background:{c["color"]};">{c["icon"]}</div>'
            f'<div class="layer-card-num">LAYER {c["num"]}</div>'
            f'<div class="layer-card-title" style="color:{c["color"]};">{c["title"]}</div>'
            f'<div class="layer-card-desc">{c["desc"]}</div>'
            '</div>'
        )
    cards_html = '<div class="land-layers-wrap"><div class="layer-card-grid">' + "".join(card_parts) + '</div></div>'

    st.markdown(cards_html, unsafe_allow_html=True)







def goodbye_page():
    st.markdown(_HERO_STYLE, unsafe_allow_html=True)

    st.markdown("""
    <div class="land-topbar">
        <span>Support</span><span>Pricing</span><span>Contact Us</span>
    </div>
    <div class="land-navbar">
        <div class="land-nav-logo">
            <div class="land-nav-hex"></div>
            <span class="land-nav-name">Data Quality Gate</span>
        </div>
        <div class="land-nav-links">
            <span>Why DQ Gate</span><span>Layers</span><span>Resources</span><span>Partners</span>
        </div>
    </div>
    <div class="land-breadcrumb">PIPELINE PLATFORM &nbsp;&rsaquo;&nbsp; RUN COMPLETE</div>

    <div class="land-hero">
        <div class="land-hero-inner">
            <div class="land-hero-title">Thanks for exploring the platform 🎉</div>
            <div class="land-hero-sub">
                Every layer ran end-to-end — ingestion, profiling, quality, security,
                warehouse, dashboard, and orchestration. Your pipeline is live and
                being tracked in Airflow.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="land-cta-row">', unsafe_allow_html=True)
    g1, g2, g3, g4, g5 = st.columns([2, 1, 0.3, 1, 2])
    with g2:
        if st.button("⬅ Back to Orchestration", use_container_width=True, key="goodbye_back"):
            st.session_state.page = "Orchestration"
            st.rerun()
    with g4:
        if st.button("Logout", use_container_width=True, key="goodbye_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# ROUTER
# =========================
if not st.session_state.logged_in:
    current_pre_auth_page = st.session_state.get("page", "landing")
    if current_pre_auth_page == "register":
        register_page()
    elif current_pre_auth_page == "login":
        login_page()
    else:
        landing_page()
elif st.session_state.get("page") == "Goodbye":
    goodbye_page()
else:
    sidebar()
    page = st.session_state.get("page", "ingestion")

    PAGES = {
        "ingestion": ingestion_page,
        "profiling": profiling_page,
        "quality":   quality_page,
        "security":  security_page,
        "DWH":       DWH_page,
        "Dashboard": Dashboard_page,
        "Orchestration": orchestration_page,
    }

    render_fn = PAGES.get(page)
    if render_fn is not None:
        render_fn()
    else:
        st.warning(f"Unknown page state: '{page}'. Resetting to last known step.")
        ingestion_page()