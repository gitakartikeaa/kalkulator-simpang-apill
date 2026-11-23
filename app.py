import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import os
import json
import html as html_lib
from datetime import date, datetime

# ==========================================
# KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Kalkulator APILL PKJI",
    page_icon="🚦",
    layout="wide"
)

HISTORY_FILE = ".pkji_history.json"
PENDEKAT_LIST = ["Utara", "Selatan", "Timur", "Barat"]

DEFAULT_IDENTITAS = {
    "nama_simpang": "",
    "ruas_jalan": "",
    "kota": "",
    "tanggal": date.today().isoformat(),
    "jam_survei": "07.00 - 08.00 WIB",
    "cuaca": "Cerah",
    "surveyor": ""
}

DEFAULT_INPUT = {
    "Utara": {"tipe": "P", "L": 7.0, "L_BKiJT": 0.0, "w_H": 25.0, "MP": 700, "KB": 50, "SM": 1800, "KTB": 0},
    "Selatan": {"tipe": "P", "L": 7.0, "L_BKiJT": 0.0, "w_H": 25.0, "MP": 700, "KB": 50, "SM": 1800, "KTB": 0},
    "Timur": {"tipe": "P", "L": 6.0, "L_BKiJT": 0.0, "w_H": 25.0, "MP": 500, "KB": 30, "SM": 1400, "KTB": 0},
    "Barat": {"tipe": "P", "L": 6.0, "L_BKiJT": 0.0, "w_H": 25.0, "MP": 500, "KB": 30, "SM": 1400, "KTB": 0},
}


def muat_riwayat_disk():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []


def simpan_riwayat_disk(riwayat_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(riwayat_list[-25:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# Inisialisasi Session State
if "tema_gelap" not in st.session_state:
    st.session_state.tema_gelap = False

if "riwayat_penggunaan" not in st.session_state:
    st.session_state.riwayat_penggunaan = muat_riwayat_disk()

last_snap = st.session_state.riwayat_penggunaan[-1] if st.session_state.riwayat_penggunaan else None

if "identitas_tersimpan" not in st.session_state:
    st.session_state.identitas_tersimpan = bool(
        last_snap and last_snap.get("identitas", {}).get("nama_simpang")
    )

if "data_identitas" not in st.session_state:
    if last_snap and "identitas" in last_snap:
        id_raw = dict(DEFAULT_IDENTITAS)
        id_raw.update(last_snap["identitas"])
        st.session_state.data_identitas = id_raw
    else:
        st.session_state.data_identitas = dict(DEFAULT_IDENTITAS)

if "sinyal_tersimpan" not in st.session_state:
    st.session_state.sinyal_tersimpan = (
        last_snap.get("sinyal", {"fase": 4, "w_MS": 3.0, "w_K": 3.0, "ukuran_kota": "1.0 - 3.0"})
        if last_snap else {"fase": 4, "w_MS": 3.0, "w_K": 3.0, "ukuran_kota": "1.0 - 3.0"}
    )

if "pendekat_tersimpan" not in st.session_state:
    if last_snap and "pendekat" in last_snap:
        p_init = {}
        for p in PENDEKAT_LIST:
            base_p = dict(DEFAULT_INPUT[p])
            base_p.update(last_snap["pendekat"].get(p, {}))
            p_init[p] = base_p
        st.session_state.pendekat_tersimpan = p_init
    else:
        st.session_state.pendekat_tersimpan = {p: dict(DEFAULT_INPUT[p]) for p in PENDEKAT_LIST}

if "emp_custom_tersimpan" not in st.session_state:
    st.session_state.emp_custom_tersimpan = (
        last_snap.get("emp_custom", {}) if last_snap else {}
    )

if "hasil_pertama_df" not in st.session_state:
    st.session_state.hasil_pertama_df = None

if "hasil_pertama_detail" not in st.session_state:
    st.session_state.hasil_pertama_detail = None

if "rumus_terpilih" not in st.session_state:
    st.session_state.rumus_terpilih = "Derajat Kejenuhan (DJ)"


# ==========================================
# TEMA WARNA
# Terang: Merino (#F5EEDD), Rock Blue (#84B3CE), Venice Blue (#16587B)
# Gelap: Navy
# ==========================================
def terapkan_tema(is_dark: bool):
    if is_dark:
        palet = {
            "bg_main": "#081024",
            "bg_secondary": "#0E1A38",
            "bg_card": "#13234A",
            "bg_input": "#0B1633",
            "border": "#3B62A8",
            "primary": "#84B3CE",
            "primary_hover": "#679BB8",
            "primary_text": "#061026",
            "text_main": "#F5EEDD",
            "text_muted": "#D8E6F3",
            "placeholder": "#8FA7C7",
            "alert_bg": "#152B59",
            "alert_text": "#F5EEDD",
            "alert_border": "#84B3CE",
            "table_head_bg": "#16587B",
            "table_head_text": "#F5EEDD",
            "table_row_even": "#0E1C3D",
            "table_row_odd": "#14254E",
            "table_hover": "#1D356B",
            "chart_bg": "#0E1A38",
            "chart_text": "#F5EEDD",
            "chart_grid": "#2A4785"
        }
    else:
        palet = {
            "bg_main": "#F5EEDD",
            "bg_secondary": "#84B3CE",
            "bg_card": "#FFFFFF",
            "bg_input": "#FFFFFF",
            "border": "#16587B",
            "primary": "#16587B",
            "primary_hover": "#0F405A",
            "primary_text": "#F5EEDD",
            "text_main": "#0E3950",
            "text_muted": "#16587B",
            "placeholder": "#5C7E91",
            "alert_bg": "#DCECF5",
            "alert_text": "#0E3950",
            "alert_border": "#16587B",
            "table_head_bg": "#16587B",
            "table_head_text": "#F5EEDD",
            "table_row_even": "#FFFFFF",
            "table_row_odd": "#EBF4F9",
            "table_hover": "#CFE4F0",
            "chart_bg": "#FFFFFF",
            "chart_text": "#0E3950",
            "chart_grid": "#9BBFD4"
        }

    st.markdown(
        f"""
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: {palet['bg_main']} !important;
            color: {palet['text_main']} !important;
        }}

        [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
            background-color: {palet['bg_secondary']} !important;
            border-right: 2px solid {palet['border']} !important;
        }}

        /* Seluruh teks utama & label (kecuali badge & delta metric agar tidak tertimpa) */
        .stApp p, .stApp label, .stApp li,
        [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
        [data-testid="stCaptionContainer"], .stCheckbox label p, .stRadio label p,
        [data-testid="stSlider"] label p, [data-testid="stSlider"] div,
        [data-testid="stExpander"] summary span, [data-testid="stExpander"] summary p {{
            color: {palet['text_main']} !important;
        }}
        .stApp span:not(.badge):not([data-testid="stMetricDelta"] span) {{
            color: {palet['text_main']} !important;
        }}

        /* Pil Delta pada st.metric agar kontras & jelas di mode terang maupun gelap */
        [data-testid="stMetricDelta"] {{
            background-color: #E2E8F0 !important;
            border-radius: 999px !important;
            padding: 2px 10px !important;
            width: fit-content !important;
        }}
        [data-testid="stMetricDelta"] span, [data-testid="stMetricDelta"] svg {{
            color: #0F172A !important;
            fill: #0F172A !important;
            font-weight: 800 !important;
        }}

        /* Placeholder input */
        input::placeholder, textarea::placeholder {{
            color: {palet['placeholder']} !important;
            opacity: 1 !important;
        }}

        /* Semua kolom input: text_input, number_input, date_input, selectbox */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stDateInput"] > div > div,
        [data-baseweb="input"], [data-baseweb="input"] > div,
        [data-baseweb="select"], [data-baseweb="select"] > div,
        [data-baseweb="select"] > div > div {{
            background-color: {palet['bg_input']} !important;
            color: {palet['text_main']} !important;
            border-color: {palet['border']} !important;
        }}
        [data-baseweb="select"] span, [data-baseweb="select"] div,
        [data-testid="stDateInput"] input {{
            color: {palet['text_main']} !important;
            -webkit-text-fill-color: {palet['text_main']} !important;
        }}
        [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [role="listbox"] li {{
            background-color: {palet['bg_card']} !important;
            color: {palet['text_main']} !important;
        }}
        [data-testid="stNumberInput"] button {{
            background-color: {palet['bg_card']} !important;
            color: {palet['text_main']} !important;
            border-color: {palet['border']} !important;
        }}

        /* Kotak Info / Warning / Success / Error */
        [data-testid="stAlert"], [data-testid="stAlert"] > div,
        [data-testid="stNotification"], [data-testid="stNotification"] > div {{
            background-color: {palet['alert_bg']} !important;
            color: {palet['alert_text']} !important;
            border: 1px solid {palet['alert_border']} !important;
            border-radius: 10px !important;
        }}
        [data-testid="stAlert"] p, [data-testid="stAlert"] span, [data-testid="stAlert"] div {{
            color: {palet['alert_text']} !important;
        }}

        /* Expander */
        [data-testid="stExpander"] {{
            background-color: {palet['bg_card']} !important;
            border: 1px solid {palet['border']} !important;
            border-radius: 10px !important;
        }}

        /* Kartu KPI */
        [data-testid="stMetric"] {{
            background-color: {palet['bg_card']} !important;
            border: 1px solid {palet['border']} !important;
            border-left: 5px solid {palet['primary']} !important;
            border-radius: 12px;
            padding: 14px 18px;
        }}
        [data-testid="stMetricLabel"] p, [data-testid="stMetricLabel"] div {{
            color: {palet['text_muted']} !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMetricValue"] div {{
            color: {palet['text_main']} !important;
            font-weight: 800 !important;
        }}

        /* Form */
        [data-testid="stForm"] {{
            background-color: {palet['bg_card']} !important;
            border: 1px solid {palet['border']} !important;
            border-radius: 14px;
            padding: 24px;
        }}

        /* Tombol */
        .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
            border-radius: 10px;
            border: 1px solid {palet['border']} !important;
            background-color: {palet['bg_card']} !important;
            color: {palet['text_main']} !important;
            font-weight: 700;
            transition: all 0.2s ease;
        }}
        .stButton > button p, .stFormSubmitButton > button p, .stDownloadButton > button p {{
            color: {palet['text_main']} !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {{
            border-color: {palet['primary']} !important;
            background-color: {palet['primary']} !important;
            color: {palet['primary_text']} !important;
        }}
        .stButton > button:hover p, .stFormSubmitButton > button:hover p, .stDownloadButton > button:hover p {{
            color: {palet['primary_text']} !important;
        }}
        button[kind="primary"], button[kind="primary"] p {{
            background-color: {palet['primary']} !important;
            color: {palet['primary_text']} !important;
            border: 1px solid {palet['border']} !important;
        }}
        button[kind="primary"]:hover, button[kind="primary"]:hover p {{
            background-color: {palet['primary_hover']} !important;
            color: {palet['primary_text']} !important;
        }}

        /* Radio Navigasi */
        div[role="radiogroup"] {{
            background-color: {palet['bg_card']} !important;
            border: 1px solid {palet['border']} !important;
            border-radius: 12px;
            padding: 8px 14px;
        }}

        /* Tabs */
        button[data-baseweb="tab"] p {{
            color: {palet['text_muted']} !important;
            font-weight: 700 !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] p {{
            color: {palet['primary']} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            border-bottom-color: {palet['primary']} !important;
        }}

        /* Tabel Kustom */
        .pkji-table-wrap {{
            width: 100%;
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid {palet['border']};
            margin: 10px 0 18px 0;
        }}
        table.pkji-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.90rem;
            font-variant-numeric: tabular-nums;
        }}
        table.pkji-table thead th {{
            background-color: {palet['table_head_bg']} !important;
            color: {palet['table_head_text']} !important;
            font-weight: 700;
            text-align: center;
            padding: 12px 10px;
            border-bottom: 2px solid {palet['border']};
            white-space: nowrap;
        }}
        table.pkji-table tbody tr:nth-child(even) {{
            background-color: {palet['table_row_even']};
        }}
        table.pkji-table tbody tr:nth-child(odd) {{
            background-color: {palet['table_row_odd']};
        }}
        table.pkji-table tbody tr:hover {{
            background-color: {palet['table_hover']};
        }}
        table.pkji-table tbody td {{
            color: {palet['text_main']} !important;
            padding: 10px 10px;
            border-bottom: 1px solid {palet['border']};
            text-align: center;
            white-space: nowrap;
        }}
        table.pkji-table tbody td:first-child {{
            font-weight: 700;
            text-align: left;
            padding-left: 14px;
        }}

        /* Badge Status & LOS */
        span.badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-weight: 800 !important;
            font-size: 0.80rem;
        }}
        span.badge-ok {{ background-color: #DCFCE7 !important; color: #14532D !important; border: 1px solid #86EFAC; }}
        span.badge-warn {{ background-color: #FEF3C7 !important; color: #78350F !important; border: 1px solid #FCD34D; }}
        span.badge-bad {{ background-color: #FEE2E2 !important; color: #7F1D1D !important; border: 1px solid #FCA5A5; }}
        span.badge-info {{ background-color: #DCECF5 !important; color: #0E3950 !important; border: 1px solid #84B3CE; }}
        </style>
        """,
        unsafe_allow_html=True
    )
    return palet


def render_tabel_cantik(df: pd.DataFrame, format_cols: dict = None):
    format_cols = format_cols or {}
    headers_html = "".join(f"<th>{html_lib.escape(str(col))}</th>" for col in df.columns)

    rows_html = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            col_str = str(col)

            if col_str in ("LOS", "LOS Awal", "LOS Evaluasi") and str(val) in ("A", "B", "C", "D", "E", "F"):
                huruf = str(val)
                cls = "badge-ok" if huruf in ("A", "B") else ("badge-warn" if huruf in ("C", "D") else "badge-bad")
                cell_content = f'<span class="badge {cls}">{huruf}</span>'
            elif col_str in ("DJ", "DJ Awal", "DJ Eval", "DJ Evaluasi") and isinstance(val, (int, float)):
                cls = "badge-bad" if val > 0.85 else ("badge-warn" if val > 0.75 else "badge-ok")
                cell_content = f'<span class="badge {cls}">{val:.3f}</span>'
            elif col_str == "Status DJ":
                cls = "badge-bad" if "Kritis" in str(val) else "badge-ok"
                cell_content = f'<span class="badge {cls}">{html_lib.escape(str(val))}</span>'
            elif col_str in ("ΔDJ", "ΔPA (m)", "ΔTundaan") and isinstance(val, (int, float)):
                fmt = format_cols.get(col_str, "{:+.3f}" if col_str == "ΔDJ" else "{:+.2f}")
                teks = fmt.format(val)
                cls = "badge-ok" if val < 0 else ("badge-bad" if val > 0 else "badge-info")
                cell_content = f'<span class="badge {cls}">{teks}</span>'
            elif col_str in format_cols and isinstance(val, (int, float)):
                cell_content = html_lib.escape(format_cols[col_str].format(val))
            else:
                cell_content = html_lib.escape(str(val))

            cells.append(f"<td>{cell_content}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    tabel_html = f"""
    <div class="pkji-table-wrap">
        <table class="pkji-table">
            <thead><tr>{headers_html}</tr></thead>
            <tbody>{''.join(rows_html)}</tbody>
        </table>
    </div>
    """
    st.markdown(tabel_html, unsafe_allow_html=True)


# ==========================================
# FUNGSI BANTUAN PERHITUNGAN PKJI
# ==========================================
def get_emp_pkji(tipe_pendekat):
    if tipe_pendekat == "P":
        return {"MP": 1.0, "KB": 1.3, "SM": 0.2, "KTB": 0.0}
    else:
        return {"MP": 1.0, "KB": 1.3, "SM": 0.4, "KTB": 0.0}


def hitung_konversi_smp(data_input, custom_emp_map):
    rows = []
    for p, d in data_input.items():
        emp = custom_emp_map[p]
        q_mp = d["MP"] * emp["MP"]
        q_kb = d["KB"] * emp["KB"]
        q_sm = d["SM"] * emp["SM"]
        q_ktb = d["KTB"] * emp["KTB"]
        q_total = q_mp + q_kb + q_sm + q_ktb

        rows.append({
            "Pendekat": p,
            "Tipe": d["tipe"],
            "eMP (MP/KB/SM/KTB)": f"{emp['MP']:.2f} / {emp['KB']:.2f} / {emp['SM']:.2f} / {emp['KTB']:.2f}",
            "MP (smp/jam)": round(q_mp, 2),
            "KB (smp/jam)": round(q_kb, 2),
            "SM (smp/jam)": round(q_sm, 2),
            "KTB (smp/jam)": round(q_ktb, 2),
            "Total Arus Q (smp/jam)": round(q_total, 2),
        })
    return pd.DataFrame(rows)


def hitung_kinerja_lengkap(
    data_input,
    custom_emp_map,
    fase,
    w_MS,
    w_K,
    F_UK,
    override_wH=None,
    override_L=None,
    override_FUK=None,
):
    f_uk_aktif = override_FUK if override_FUK is not None else F_UK

    w_h_map = {}
    l_map = {}
    for p, d in data_input.items():
        w_h_map[p] = override_wH.get(p, d["w_H"]) if override_wH else d["w_H"]
        l_map[p] = override_L.get(p, d["L"]) if override_L else d["L"]

    W_HH = fase * (w_MS + w_K)
    total_wH = max(w_h_map.values()) * (fase / 2.0)
    c_s = total_wH + W_HH

    tabel_rows = []
    detail_per_pendekat = {}

    for p, d in data_input.items():
        tipe = d["tipe"]
        emp = custom_emp_map[p]
        w_H = w_h_map[p]
        L = l_map[p]
        L_BKiJT = d["L_BKiJT"]

        mp_smp = d["MP"] * emp["MP"]
        kb_smp = d["KB"] * emp["KB"]
        sm_smp = d["SM"] * emp["SM"]
        ktb_smp = d["KTB"] * emp["KTB"]
        Q_smp = mp_smp + kb_smp + sm_smp + ktb_smp

        L_E = max(0.5, L - L_BKiJT)
        J_0 = 600.0 * L_E
        J = J_0 * f_uk_aktif

        rasio_hijau = (w_H / c_s) if c_s > 0 else 0.0
        C = J * rasio_hijau if c_s > 0 else 1.0
        DJ = (Q_smp / C) if C > 0 else 0.0

        if DJ > 0.5 and C > 0:
            NQ1 = 0.25 * C * ((DJ - 1.0) + np.sqrt((DJ - 1.0) ** 2 + (8.0 * (DJ - 0.5) / C)))
        else:
            NQ1 = 0.0

        penyebut_antrian = max(0.05, 1.0 - min(0.95, DJ * rasio_hijau))
        NQ2 = ((1.0 - rasio_hijau) / penyebut_antrian) * (Q_smp / 3600.0) * max(0.0, (c_s - w_H))
        NQ_total = NQ1 + NQ2
        PA = (NQ_total * 20.0) / L_E if L_E > 0 else 0.0

        RKH = min(1.0, 0.9 * ((1.0 - rasio_hijau) / penyebut_antrian))
        T_LL = ((0.5 * c_s * ((1.0 - rasio_hijau) ** 2)) / penyebut_antrian) + ((NQ1 * 3600.0 / C) if C > 0 else 0.0)
        T_G = (1.0 - RKH) * 4.0 + RKH * 6.0
        T_total = T_LL + T_G

        if T_total <= 5.0:
            los = "A"
        elif T_total <= 15.0:
            los = "B"
        elif T_total <= 25.0:
            los = "C"
        elif T_total <= 40.0:
            los = "D"
        elif T_total <= 60.0:
            los = "E"
        else:
            los = "F"

        status_dj = "Kritis (DJ > 0,85)" if DJ > 0.85 else "Layak (DJ ≤ 0,85)"

        tabel_rows.append({
            "Pendekat": p,
            "Tipe": tipe,
            "L_E (m)": round(L_E, 2),
            "w_H (s)": round(w_H, 1),
            "c_s (s)": round(c_s, 1),
            "Q (smp/jam)": round(Q_smp, 1),
            "J_0 (smp/jam)": round(J_0, 1),
            "J (smp/jam)": round(J, 1),
            "C (smp/jam)": round(C, 1),
            "DJ": round(DJ, 3),
            "NQ_total (smp)": round(NQ_total, 2),
            "PA (m)": round(PA, 1),
            "RKH": round(RKH, 3),
            "Tundaan (s/smp)": round(T_total, 2),
            "LOS": los,
            "Status DJ": status_dj
        })

        detail_per_pendekat[p] = {
            "tipe": tipe,
            "MP": d["MP"], "KB": d["KB"], "SM": d["SM"], "KTB": d["KTB"],
            "emp_MP": emp["MP"], "emp_KB": emp["KB"], "emp_SM": emp["SM"], "emp_KTB": emp["KTB"],
            "Q_smp": Q_smp,
            "L": L, "L_BKiJT": L_BKiJT, "L_E": L_E,
            "J_0": J_0, "F_UK": f_uk_aktif, "J": J,
            "w_H": w_H, "c_s": c_s, "C": C, "DJ": DJ,
            "NQ1": NQ1, "NQ2": NQ2, "NQ_total": NQ_total, "PA": PA,
            "RKH": RKH, "T_LL": T_LL, "T_G": T_G, "T_total": T_total,
            "los": los
        }

    return pd.DataFrame(tabel_rows), c_s, W_HH, detail_per_pendekat


def hitung_rekomendasi_pkji(detail_awal, target_dj=0.85):
    rekom_rows = []
    for p in PENDEKAT_LIST:
        det = detail_awal[p]
        Q = det["Q_smp"]
        J = det["J"]
        c_s = det["c_s"]
        w_H_awal = det["w_H"]
        L_BK = det["L_BKiJT"]
        L_E_awal = det["L_E"]
        DJ_awal = det["DJ"]

        C_perlu = Q / target_dj if target_dj > 0 else Q
        w_H_perlu = ((C_perlu / J) * c_s) if J > 0 else w_H_awal
        w_H_usulan = max(5.0, round(w_H_perlu, 1))

        rasio_h = (w_H_awal / c_s) if c_s > 0 else 0.0
        penyebut_le = 600.0 * det["F_UK"] * rasio_h
        L_E_perlu = (C_perlu / penyebut_le) if penyebut_le > 0 else L_E_awal
        L_usulan = max(2.0, round(L_E_perlu + L_BK, 2))

        if DJ_awal > target_dj:
            tindakan = f"Perlu perbaikan: naikkan w_H ke ~{w_H_usulan:.1f} s atau L ke ~{L_usulan:.2f} m"
        else:
            tindakan = f"Sudah memenuhi batas DJ ≤ {target_dj:.2f}"

        rekom_rows.append({
            "Pendekat": p,
            "Q (smp/jam)": round(Q, 1),
            "DJ Awal": round(DJ_awal, 3),
            "w_H Awal (s)": round(w_H_awal, 1),
            "w_H Rekomendasi (s)": w_H_usulan,
            "L_E Awal (m)": round(L_E_awal, 2),
            "L Rekomendasi (m)": L_usulan,
            "Evaluasi & Saran PKJI": tindakan
        })
    return pd.DataFrame(rekom_rows)


def tampilkan_detail_rumus(nama_rumus, det):
    p_nama = det.get("pendekat_label", "Pendekat")
    st.markdown(f"#### 🧮 Rincian Perhitungan: **{nama_rumus}** ({p_nama})")

    if nama_rumus == "Arus Lalu Lintas (Q)":
        st.latex(r"Q = (N_{MP} \times e_{MP}) + (N_{KB} \times e_{KB}) + (N_{SM} \times e_{SM}) + (N_{KTB} \times e_{KTB})")
        st.code(
            f"Q = ({det['MP']} × {det['emp_MP']}) + ({det['KB']} × {det['emp_KB']}) + ({det['SM']} × {det['emp_SM']}) + ({det['KTB']} × {det['emp_KTB']})\n"
            f"Hasil Akhir: Q = {det['Q_smp']:.2f} smp/jam",
            language="text"
        )
    elif nama_rumus == "Lebar Efektif Pendekat (L_E)":
        st.latex(r"L_E = L - L_{BKiJT}")
        st.code(
            f"L_E = {det['L']:.2f} - {det['L_BKiJT']:.2f}\n"
            f"Hasil Akhir: L_E = {det['L_E']:.2f} m",
            language="text"
        )
    elif nama_rumus == "Arus Jenuh Dasar (J_0)":
        st.latex(r"J_0 = 600 \times L_E")
        st.code(
            f"J_0 = 600 × {det['L_E']:.2f}\n"
            f"Hasil Akhir: J_0 = {det['J_0']:.2f} smp/jam hijau",
            language="text"
        )
    elif nama_rumus == "Arus Jenuh Tersesuaikan (J)":
        st.latex(r"J = J_0 \times F_{UK}")
        st.code(
            f"J = {det['J_0']:.2f} × {det['F_UK']:.2f}\n"
            f"Hasil Akhir: J = {det['J']:.2f} smp/jam hijau",
            language="text"
        )
    elif nama_rumus == "Kapasitas Pendekat (C)":
        st.latex(r"C = J \times \frac{w_H}{c_s}")
        st.code(
            f"C = {det['J']:.2f} × ({det['w_H']:.1f} / {det['c_s']:.1f})\n"
            f"Hasil Akhir: C = {det['C']:.2f} smp/jam",
            language="text"
        )
    elif nama_rumus == "Derajat Kejenuhan (DJ)":
        st.latex(r"DJ = \frac{Q}{C}")
        st.code(
            f"DJ = {det['Q_smp']:.2f} / {det['C']:.2f}\n"
            f"Hasil Akhir: DJ = {det['DJ']:.3f}",
            language="text"
        )
    elif nama_rumus == "Jumlah Antrian (NQ_total)":
        st.latex(r"NQ_1 = 0{,}25 \times C \left[(DJ - 1) + \sqrt{(DJ - 1)^2 + \frac{8(DJ - 0{,}5)}{C}}\right] \quad (\text{jika } DJ > 0{,}5)")
        st.latex(r"NQ_2 = \frac{1 - (w_H / c_s)}{1 - \min(1;\ DJ \cdot w_H / c_s)} \times \frac{Q}{3600} \times (c_s - w_H)")
        st.latex(r"NQ_{\text{total}} = NQ_1 + NQ_2")
        st.code(
            f"NQ_1 = {det['NQ1']:.3f} smp\n"
            f"NQ_2 = {det['NQ2']:.3f} smp\n"
            f"Hasil Akhir: NQ_total = {det['NQ1']:.3f} + {det['NQ2']:.3f} = {det['NQ_total']:.2f} smp",
            language="text"
        )
    elif nama_rumus == "Panjang Antrian (PA)":
        st.latex(r"PA = \frac{NQ_{\text{total}} \times 20}{L_E}")
        st.code(
            f"PA = ({det['NQ_total']:.2f} × 20) / {det['L_E']:.2f}\n"
            f"Hasil Akhir: PA = {det['PA']:.1f} meter",
            language="text"
        )
    elif nama_rumus == "Rasio Kendaraan Henti (RKH)":
        rasio_h = (det["w_H"] / det["c_s"]) if det["c_s"] > 0 else 0
        penj = max(0.05, 1.0 - min(0.95, det["DJ"] * rasio_h))
        st.latex(r"RKH = 0{,}9 \times \frac{1 - (w_H / c_s)}{1 - \min(1;\ DJ \cdot w_H / c_s)}")
        st.code(
            f"RKH = 0.9 × ((1 - {rasio_h:.3f}) / {penj:.3f})\n"
            f"Hasil Akhir: RKH = {det['RKH']:.3f}",
            language="text"
        )
    elif nama_rumus == "Tundaan Rata-Rata (T_total)":
        st.latex(r"T_{LL} = \frac{0{,}5 \times c_s \times (1 - w_H/c_s)^2}{1 - \min(1;\ DJ \cdot w_H/c_s)} + \frac{NQ_1 \times 3600}{C}")
        st.latex(r"T_G = (1 - RKH) \times 4 + RKH \times 6 \qquad ; \qquad T_{\text{total}} = T_{LL} + T_G")
        st.code(
            f"T_LL = {det['T_LL']:.2f} s/smp\n"
            f"T_G  = {det['T_G']:.2f} s/smp\n"
            f"Hasil Akhir: T_total = {det['T_LL']:.2f} + {det['T_G']:.2f} = {det['T_total']:.2f} s/smp (LOS: {det['los']})",
            language="text"
        )


def catat_history(identitas_dict, sinyal_dict, pendekat_dict, emp_custom_dict):
    label_simpang = identitas_dict.get("nama_simpang") or "Simpang Tanpa Nama"
    label_waktu = datetime.now().strftime("%d/%m %H:%M")
    snapshot = {
        "label": f"{label_simpang} ({label_waktu})",
        "identitas": dict(identitas_dict),
        "sinyal": dict(sinyal_dict),
        "pendekat": {p: dict(d) for p, d in pendekat_dict.items()},
        "emp_custom": {p: dict(e) for p, e in emp_custom_dict.items()}
    }
    st.session_state.riwayat_penggunaan.append(snapshot)
    st.session_state.riwayat_penggunaan = st.session_state.riwayat_penggunaan[-25:]
    simpan_riwayat_disk(st.session_state.riwayat_penggunaan)


def terapkan_snapshot(snap):
    id_new = dict(DEFAULT_IDENTITAS)
    id_new.update(snap.get("identitas", {}))
    st.session_state.data_identitas = id_new
    st.session_state.identitas_tersimpan = bool(id_new.get("nama_simpang"))

    sinyal_new = {"fase": 4, "w_MS": 3.0, "w_K": 3.0, "ukuran_kota": "1.0 - 3.0"}
    sinyal_new.update(snap.get("sinyal", {}))
    st.session_state.sinyal_tersimpan = sinyal_new

    p_new = {}
    for p in PENDEKAT_LIST:
        base = dict(DEFAULT_INPUT[p])
        base.update(snap.get("pendekat", {}).get(p, {}))
        p_new[p] = base
        st.session_state[f"tipe_{p}"] = base["tipe"]
        st.session_state[f"L_{p}"] = float(base["L"])
        st.session_state[f"bk_{p}"] = float(base["L_BKiJT"])
        st.session_state[f"wH_{p}"] = float(base["w_H"])
        st.session_state[f"mp_{p}"] = int(base["MP"])
        st.session_state[f"kb_{p}"] = int(base["KB"])
        st.session_state[f"sm_{p}"] = int(base["SM"])
        st.session_state[f"ktb_{p}"] = int(base["KTB"])

    st.session_state["sb_fase"] = int(sinyal_new["fase"])
    st.session_state["sb_wms"] = float(sinyal_new["w_MS"])
    st.session_state["sb_wk"] = float(sinyal_new["w_K"])
    st.session_state["sb_kota"] = sinyal_new["ukuran_kota"]

    st.session_state.emp_custom_tersimpan = snap.get("emp_custom", {})
    st.session_state.hasil_pertama_df = None
    st.session_state.hasil_pertama_detail = None


# Terapkan Tema Aktif
palet_aktif = terapkan_tema(st.session_state.tema_gelap)


# ==========================================
# HALAMAN AWAL: IDENTITAS SURVEI & SIMPANG
# ==========================================
if not st.session_state.identitas_tersimpan:
    col_top1, col_top2 = st.columns([5, 1.3])
    with col_top1:
        st.title("🚦 Kalkulator Kinerja Simpang APILL (PKJI)")
        st.caption("Silakan lengkapi data identitas survei terlebih dahulu sebelum membuka menu kalkulasi.")
    with col_top2:
        st.markdown("")
        label_tema = "☀️ Mode Terang" if st.session_state.tema_gelap else "🌙 Mode Gelap"
        if st.button(label_tema, key="toggle_tema_awal", use_container_width=True):
            st.session_state.tema_gelap = not st.session_state.tema_gelap
            st.rerun()

    st.divider()

    if st.session_state.riwayat_penggunaan:
        with st.expander(f"🕒 Riwayat Tersimpan ({len(st.session_state.riwayat_penggunaan)} data)", expanded=False):
            pilihan_awal = [item["label"] for item in reversed(st.session_state.riwayat_penggunaan)]
            dipilih_awal = st.selectbox("Pilih data dari riwayat sebelumnya:", pilihan_awal, key="awal_hist_sel")
            if st.button("📂 Muat Data Riwayat Ini", key="awal_hist_btn"):
                cocok = next((x for x in reversed(st.session_state.riwayat_penggunaan) if x["label"] == dipilih_awal), None)
                if cocok:
                    terapkan_snapshot(cocok)
                    st.session_state.identitas_tersimpan = True
                    st.rerun()

    st.subheader("📋 Data Identitas Simpang & Survei")
    id_init = st.session_state.data_identitas
    try:
        tgl_init = date.fromisoformat(str(id_init.get("tanggal", date.today().isoformat())))
    except Exception:
        tgl_init = date.today()

    cuaca_opsi = ["Cerah", "Berawan", "Hujan Ringan", "Hujan Lebat"]
    cuaca_idx = cuaca_opsi.index(id_init.get("cuaca", "Cerah")) if id_init.get("cuaca", "Cerah") in cuaca_opsi else 0

    with st.form("form_identitas_awal"):
        col1, col2 = st.columns(2)
        with col1:
            nama_simpang = st.text_input(
                "Nama Simpang *",
                value=id_init.get("nama_simpang", ""),
                placeholder="Contoh: Simpang Empat Kebonpolo"
            )
            ruas_jalan = st.text_input(
                "Ruas Jalan yang Bertemu *",
                value=id_init.get("ruas_jalan", ""),
                placeholder="Contoh: Jl. Ahmad Yani - Jl. Tentara Pelajar"
            )
            kota = st.text_input(
                "Kota / Kabupaten",
                value=id_init.get("kota", ""),
                placeholder="Contoh: Kota Magelang"
            )
        with col2:
            tanggal = st.date_input(
                "Tanggal Survei",
                value=tgl_init
            )
            jam_survei = st.text_input(
                "Jam Survei / Periode Waktu",
                value=id_init.get("jam_survei", "07.00 - 08.00 WIB"),
                placeholder="Contoh: 07.00 - 08.00 WIB"
            )
            cuaca = st.selectbox(
                "Kondisi Cuaca",
                cuaca_opsi,
                index=cuaca_idx
            )

        surveyor = st.text_input(
            "Nama Surveyor / Instansi / Kelompok",
            value=id_init.get("surveyor", ""),
            placeholder="Opsional"
        )

        lanjut = st.form_submit_button("Masuk ke Halaman Kalkulator ➡️", type="primary", use_container_width=True)
        if lanjut:
            if not nama_simpang.strip() or not ruas_jalan.strip():
                st.error("⚠️ Harap isi **Nama Simpang** dan **Ruas Jalan** terlebih dahulu.")
            else:
                st.session_state.data_identitas = {
                    "nama_simpang": nama_simpang.strip(),
                    "ruas_jalan": ruas_jalan.strip(),
                    "kota": kota.strip() if kota.strip() else "-",
                    "tanggal": tanggal.isoformat(),
                    "jam_survei": jam_survei.strip() if jam_survei.strip() else "-",
                    "cuaca": cuaca,
                    "surveyor": surveyor.strip() if surveyor.strip() else "-"
                }
                st.session_state.identitas_tersimpan = True
                catat_history(
                    st.session_state.data_identitas,
                    st.session_state.sinyal_tersimpan,
                    st.session_state.pendekat_tersimpan,
                    st.session_state.emp_custom_tersimpan
                )
                st.rerun()

# ==========================================
# HALAMAN 2: 4 MODE DI BAGIAN ATAS
# ==========================================
else:
    identitas = st.session_state.data_identitas
    try:
        tgl_tampil = date.fromisoformat(str(identitas.get("tanggal", date.today().isoformat()))).strftime("%d-%m-%Y")
    except Exception:
        tgl_tampil = str(identitas.get("tanggal", "-"))

    c_h1, c_h2, c_h3 = st.columns([4.4, 1.3, 1.1])
    with c_h1:
        st.title("🚦 Kalkulator Kinerja Simpang APILL (PKJI)")
    with c_h2:
        st.markdown("")
        label_tema = "☀️ Mode Terang" if st.session_state.tema_gelap else "🌙 Mode Gelap"
        if st.button(label_tema, key="toggle_tema_utama", use_container_width=True):
            st.session_state.tema_gelap = not st.session_state.tema_gelap
            st.rerun()
    with c_h3:
        st.markdown("")
        if st.button("✏️ Identitas", use_container_width=True):
            st.session_state.identitas_tersimpan = False
            st.rerun()

    st.caption(
        f"**Simpang:** {identitas['nama_simpang']} | "
        f"**Ruas Jalan:** {identitas['ruas_jalan']} | "
        f"**Kota:** {identitas['kota']} | "
        f"**Tanggal:** {tgl_tampil} | "
        f"**Jam Survei:** {identitas['jam_survei']} | "
        f"**Cuaca:** {identitas['cuaca']} | "
        f"**Surveyor:** {identitas['surveyor']}"
    )

    mode_pilihan = st.radio(
        "Pilih Mode Analisis:",
        [
            "Mode 1: Konversi ke SMP",
            "Mode 2: Perhitungan Lengkap & LOS",
            "Mode 3: Perbandingan & Evaluasi",
            "Mode 4: Rumus-Rumus PKJI"
        ],
        horizontal=True
    )
    st.divider()

    # ==========================================
    # SIDEBAR - INPUT PARAMETER SIMPANG
    # ==========================================
    st.sidebar.header("⚙️ Parameter Input Simpang")

    sinyal_init = st.session_state.sinyal_tersimpan
    kota_opsi = ["> 3.0", "1.0 - 3.0", "0.5 - 1.0", "0.1 - 0.5", "< 0.1"]
    kota_idx = kota_opsi.index(sinyal_init.get("ukuran_kota", "1.0 - 3.0")) if sinyal_init.get("ukuran_kota", "1.0 - 3.0") in kota_opsi else 1

    st.sidebar.subheader("1. Informasi Sinyal & Kota")
    fase = st.sidebar.number_input("Jumlah Fase", min_value=2, max_value=6, value=int(sinyal_init.get("fase", 4)), key="sb_fase")
    w_MS = st.sidebar.number_input("Waktu Merah Semua / Fase (detik)", min_value=1.0, value=float(sinyal_init.get("w_MS", 3.0)), step=0.5, key="sb_wms")
    w_K = st.sidebar.number_input("Waktu Kuning / Fase (detik)", min_value=1.0, value=float(sinyal_init.get("w_K", 3.0)), step=0.5, key="sb_wk")
    ukuran_kota = st.sidebar.selectbox("Ukuran Kota (Juta Jiwa)", kota_opsi, index=kota_idx, key="sb_kota")

    st.session_state.sinyal_tersimpan = {
        "fase": fase, "w_MS": w_MS, "w_K": w_K, "ukuran_kota": ukuran_kota
    }

    f_uk_map = {"> 3.0": 1.05, "1.0 - 3.0": 1.00, "0.5 - 1.0": 0.94, "0.1 - 0.5": 0.88, "< 0.1": 0.82}
    F_UK = f_uk_map[ukuran_kota]

    st.sidebar.subheader("2. Data Pendekat & Arus Mentah")
    data_input = {}

    for p in PENDEKAT_LIST:
        p_init = st.session_state.pendekat_tersimpan.get(p, DEFAULT_INPUT[p])
        with st.sidebar.expander(f"Pendekat {p}", expanded=False):
            tipe = st.selectbox(f"Tipe Pendekat {p}", ["P", "O"], index=0 if p_init.get("tipe", "P") == "P" else 1, key=f"tipe_{p}", help="P = Terlindung, O = Terlawan")
            L = st.number_input(f"Lebar Pendekat L (m) [{p}]", min_value=2.0, value=float(p_init.get("L", DEFAULT_INPUT[p]["L"])), key=f"L_{p}")
            L_BKiJT = st.number_input(f"Lebar BKiJT (m) [{p}]", min_value=0.0, value=float(p_init.get("L_BKiJT", 0.0)), key=f"bk_{p}")
            w_H = st.number_input(f"Waktu Hijau w_H (detik) [{p}]", min_value=5.0, value=float(p_init.get("w_H", 25.0)), key=f"wH_{p}")

            st.write("**Arus Lalu Lintas Mentah (kend/jam):**")
            mp = st.number_input(f"Mobil Penumpang (MP) [{p}]", min_value=0, value=int(p_init.get("MP", DEFAULT_INPUT[p]["MP"])), key=f"mp_{p}")
            kb = st.number_input(f"Kendaraan Berat (KB) [{p}]", min_value=0, value=int(p_init.get("KB", DEFAULT_INPUT[p]["KB"])), key=f"kb_{p}")
            sm = st.number_input(f"Sepeda Motor (SM) [{p}]", min_value=0, value=int(p_init.get("SM", DEFAULT_INPUT[p]["SM"])), key=f"sm_{p}")
            ktb = st.number_input(f"Kendaraan Tak Bermotor (KTB) [{p}]", min_value=0, value=int(p_init.get("KTB", 0)), key=f"ktb_{p}")

            data_input[p] = {
                "tipe": tipe, "L": L, "L_BKiJT": L_BKiJT, "w_H": w_H,
                "MP": mp, "KB": kb, "SM": sm, "KTB": ktb
            }
            st.session_state.pendekat_tersimpan[p] = dict(data_input[p])

    st.sidebar.subheader("3. Custom eMP")
    gunakan_emp_custom = st.sidebar.checkbox("Ubah nilai eMP secara mandiri (Custom)", value=bool(st.session_state.emp_custom_tersimpan), key="sb_emp_custom")
    custom_emp_map = {}

    for p in PENDEKAT_LIST:
        default_emp = get_emp_pkji(data_input[p]["tipe"])
        saved_emp = st.session_state.emp_custom_tersimpan.get(p, default_emp)
        if gunakan_emp_custom:
            with st.sidebar.expander(f"eMP Custom — {p}", expanded=False):
                e_mp = st.number_input(f"eMP [{p}]", min_value=0.0, value=float(saved_emp.get("MP", default_emp["MP"])), step=0.05, key=f"emp_mp_{p}")
                e_kb = st.number_input(f"eKB [{p}]", min_value=0.0, value=float(saved_emp.get("KB", default_emp["KB"])), step=0.05, key=f"emp_kb_{p}")
                e_sm = st.number_input(f"eSM [{p}]", min_value=0.0, value=float(saved_emp.get("SM", default_emp["SM"])), step=0.05, key=f"emp_sm_{p}")
                e_ktb = st.number_input(f"eKTB [{p}]", min_value=0.0, value=float(saved_emp.get("KTB", default_emp["KTB"])), step=0.05, key=f"emp_ktb_{p}")
                custom_emp_map[p] = {"MP": e_mp, "KB": e_kb, "SM": e_sm, "KTB": e_ktb}
        else:
            custom_emp_map[p] = default_emp

    if gunakan_emp_custom:
        st.session_state.emp_custom_tersimpan = {p: dict(custom_emp_map[p]) for p in PENDEKAT_LIST}
    else:
        st.session_state.emp_custom_tersimpan = {}

    df_awal, c_s_awal, w_hh_awal, detail_awal = hitung_kinerja_lengkap(
        data_input, custom_emp_map, fase, w_MS, w_K, F_UK
    )
    if st.session_state.hasil_pertama_df is None:
        st.session_state.hasil_pertama_df = df_awal.copy()
        st.session_state.hasil_pertama_detail = detail_awal

    df_konversi_global = hitung_konversi_smp(data_input, custom_emp_map)

    ev_wh_aktif = st.session_state.get("eval_wh_map", {p: float(data_input[p]["w_H"]) for p in PENDEKAT_LIST})
    ev_l_aktif = st.session_state.get("eval_l_map", {p: float(data_input[p]["L"]) for p in PENDEKAT_LIST})
    ev_bk_aktif = st.session_state.get("eval_bk_map", {p: float(data_input[p]["L_BKiJT"]) for p in PENDEKAT_LIST})
    data_eval_global = {}
    for p in PENDEKAT_LIST:
        sal = dict(data_input[p])
        sal["L_BKiJT"] = ev_bk_aktif.get(p, data_input[p]["L_BKiJT"])
        data_eval_global[p] = sal
    df_evaluasi_global, _, _, _ = hitung_kinerja_lengkap(
        data_eval_global, custom_emp_map, fase, w_MS, w_K, F_UK,
        override_wH=ev_wh_aktif, override_L=ev_l_aktif
    )
    df_pertama_global = st.session_state.hasil_pertama_df.copy()
    df_banding_global = pd.DataFrame({
        "Pendekat": df_pertama_global["Pendekat"],
        "DJ Awal": df_pertama_global["DJ"],
        "DJ Eval": df_evaluasi_global["DJ"],
        "ΔDJ": (df_evaluasi_global["DJ"] - df_pertama_global["DJ"]).round(3),
        "PA Awal (m)": df_pertama_global["PA (m)"],
        "PA Eval (m)": df_evaluasi_global["PA (m)"],
        "ΔPA (m)": (df_evaluasi_global["PA (m)"] - df_pertama_global["PA (m)"]).round(1),
        "Tundaan Awal": df_pertama_global["Tundaan (s/smp)"],
        "Tundaan Eval": df_evaluasi_global["Tundaan (s/smp)"],
        "ΔTundaan": (df_evaluasi_global["Tundaan (s/smp)"] - df_pertama_global["Tundaan (s/smp)"]).round(2),
        "LOS Awal": df_pertama_global["LOS"],
        "LOS Evaluasi": df_evaluasi_global["LOS"]
    })

    # ==========================================================
    # SIDEBAR KIRI BAWAH (DI BAWAH CUSTOM EMP): HISTORY & EKSPOR EXCEL
    # ==========================================
    st.sidebar.divider()
    st.sidebar.subheader("🕒 History")
    if st.sidebar.button("💾 Simpan Sesi ke History", key="btn_simpan_history", use_container_width=True):
        catat_history(
            st.session_state.data_identitas,
            st.session_state.sinyal_tersimpan,
            st.session_state.pendekat_tersimpan,
            st.session_state.emp_custom_tersimpan
        )
        st.sidebar.success("Data tersimpan ke history.")

    if st.session_state.riwayat_penggunaan:
        opsi_hist = [item["label"] for item in reversed(st.session_state.riwayat_penggunaan)]
        pilih_hist = st.sidebar.selectbox("Riwayat tersimpan:", opsi_hist, key="sb_hist_select")
        if st.sidebar.button("📂 Muat History Terpilih", key="btn_muat_history", use_container_width=True):
            item_cocok = next((x for x in reversed(st.session_state.riwayat_penggunaan) if x["label"] == pilih_hist), None)
            if item_cocok:
                terapkan_snapshot(item_cocok)
                st.rerun()
    else:
        st.sidebar.caption("Belum ada riwayat tersimpan.")

    st.sidebar.subheader("📥 Ekspor Excel (Mode 1, 2, 3)")
    df_id_sheet = pd.DataFrame({
        "Parameter": [
            "Nama Simpang", "Ruas Jalan", "Kota / Kabupaten", "Tanggal Survei",
            "Jam Survei", "Kondisi Cuaca", "Surveyor", "Ukuran Kota",
            "Jumlah Fase", "Waktu Siklus Estimasi (s)"
        ],
        "Keterangan": [
            identitas["nama_simpang"], identitas["ruas_jalan"], identitas["kota"],
            tgl_tampil, identitas["jam_survei"], identitas["cuaca"],
            identitas["surveyor"], ukuran_kota, fase, round(c_s_awal, 1)
        ]
    })

    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        df_id_sheet.to_excel(writer, sheet_name="Identitas Survei", index=False)
        df_konversi_global.to_excel(writer, sheet_name="Mode 1 - Konversi SMP", index=False)
        df_awal.to_excel(writer, sheet_name="Mode 2 - Kinerja Lengkap", index=False)
        df_banding_global.to_excel(writer, sheet_name="Mode 3 - Evaluasi", index=False)

    st.sidebar.download_button(
        label="📊 Download Excel (.xlsx)",
        data=excel_buf.getvalue(),
        file_name=f"PKJI_{identitas['nama_simpang'].replace(' ', '_') or 'Simpang'}_Mode1_2_3.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    format_tabel_lengkap = {
        "L_E (m)": "{:.2f}",
        "w_H (s)": "{:.1f}",
        "c_s (s)": "{:.1f}",
        "Q (smp/jam)": "{:,.1f}",
        "J_0 (smp/jam)": "{:,.1f}",
        "J (smp/jam)": "{:,.1f}",
        "C (smp/jam)": "{:,.1f}",
        "DJ": "{:.3f}",
        "NQ_total (smp)": "{:.2f}",
        "PA (m)": "{:.1f}",
        "RKH": "{:.3f}",
        "Tundaan (s/smp)": "{:.2f}"
    }

    # ==========================================================
    # MODE 1: INPUT HITUNGAN MENTAH SURVEI -> HASIL SATUAN SMP
    # ==========================================================
    if mode_pilihan == "Mode 1: Konversi ke SMP":
        st.subheader("🔄 Mode 1 — Konversi Hitungan Mentah Survei ke Satuan SMP")
        st.caption("Masukkan angka hitungan mentah per jenis kendaraan dari hasil survei lapangan untuk memperoleh tabel hasil dalam satuan smp/jam.")

        col_m1_opt1, col_m1_opt2 = st.columns([2, 3])
        with col_m1_opt1:
            emp_custom_mode1 = st.checkbox("Ubah nilai eMP sendiri (Custom)", value=False, key="m1_emp_custom")
        with col_m1_opt2:
            if not emp_custom_mode1:
                st.info("Nilai **eMP standar PKJI** aktif otomatis: **MP = 1,00**, **KB = 1,30**, **SM = 0,20** (Tipe **P**) atau **0,40** (Tipe **O**), **KTB = 0,00**.")
            else:
                st.warning("Mode **eMP Custom** aktif: sesuaikan faktor eMP pada tiap pendekat di bawah ini.")

        st.markdown("#### 1. Input Angka Hitungan Mentah Lapangan (kend/jam)")
        data_mentah_m1 = {}
        emp_map_m1 = {}

        cols_m1 = st.columns(4)
        for idx, p in enumerate(PENDEKAT_LIST):
            with cols_m1[idx]:
                st.markdown(f"**Pendekat {p}**")
                tipe_m1 = st.selectbox(f"Tipe [{p}]", ["P", "O"], index=0 if data_input[p]["tipe"] == "P" else 1, key=f"m1_tipe_{p}")
                mp_m1 = st.number_input(f"MP (kend/jam) [{p}]", min_value=0, value=int(data_input[p]["MP"]), step=10, key=f"m1_mp_{p}")
                kb_m1 = st.number_input(f"KB (kend/jam) [{p}]", min_value=0, value=int(data_input[p]["KB"]), step=5, key=f"m1_kb_{p}")
                sm_m1 = st.number_input(f"SM (kend/jam) [{p}]", min_value=0, value=int(data_input[p]["SM"]), step=10, key=f"m1_sm_{p}")
                ktb_m1 = st.number_input(f"KTB (kend/jam) [{p}]", min_value=0, value=int(data_input[p]["KTB"]), step=5, key=f"m1_ktb_{p}")

                data_mentah_m1[p] = {"tipe": tipe_m1, "MP": mp_m1, "KB": kb_m1, "SM": sm_m1, "KTB": ktb_m1}

                emp_bawaan = get_emp_pkji(tipe_m1)
                if emp_custom_mode1:
                    with st.expander(f"Atur eMP [{p}]", expanded=True):
                        e_mp_1 = st.number_input(f"eMP [{p}]", min_value=0.0, value=float(emp_bawaan["MP"]), step=0.05, key=f"m1_emp_mp_{p}")
                        e_kb_1 = st.number_input(f"eKB [{p}]", min_value=0.0, value=float(emp_bawaan["KB"]), step=0.05, key=f"m1_emp_kb_{p}")
                        e_sm_1 = st.number_input(f"eSM [{p}]", min_value=0.0, value=float(emp_bawaan["SM"]), step=0.05, key=f"m1_emp_sm_{p}")
                        e_ktb_1 = st.number_input(f"eKTB [{p}]", min_value=0.0, value=float(emp_bawaan["KTB"]), step=0.05, key=f"m1_emp_ktb_{p}")
                        emp_map_m1[p] = {"MP": e_mp_1, "KB": e_kb_1, "SM": e_sm_1, "KTB": e_ktb_1}
                else:
                    emp_map_m1[p] = emp_bawaan

        st.markdown("#### 2. Tabel Hasil Konversi Satuan SMP (smp/jam)")
        df_konversi = hitung_konversi_smp(data_mentah_m1, emp_map_m1)
        render_tabel_cantik(
            df_konversi,
            format_cols={
                "MP (smp/jam)": "{:,.2f}",
                "KB (smp/jam)": "{:,.2f}",
                "SM (smp/jam)": "{:,.2f}",
                "KTB (smp/jam)": "{:,.2f}",
                "Total Arus Q (smp/jam)": "{:,.2f}"
            }
        )

        total_all_smp = df_konversi["Total Arus Q (smp/jam)"].sum()
        st.metric("Total Arus Lalu Lintas Seluruh Pendekat", f"{total_all_smp:,.2f} smp/jam")

    # ==========================================================
    # MODE 2: PERHITUNGAN LENGKAP HINGGA LOS + RUMUS INTERAKTIF
    # ==========================================================
    elif mode_pilihan == "Mode 2: Perhitungan Lengkap & LOS":
        st.subheader("📊 Mode 2 — Tabel Perhitungan Kinerja Simpang Lengkap (Hingga LOS)")

        _, col_btn2 = st.columns([3, 1])
        with col_btn2:
            if st.button("📌 Jadikan Hitungan Pertama (Mode 3)", use_container_width=True):
                st.session_state.hasil_pertama_df = df_awal.copy()
                st.session_state.hasil_pertama_detail = detail_awal
                st.success("Hasil hitungan pertama berhasil diperbarui untuk Mode 3.")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Rata-rata DJ", f"{df_awal['DJ'].mean():.3f}")
        k2.metric("Max Panjang Antrian", f"{df_awal['PA (m)'].max():.1f} m")
        k3.metric("Rata-rata Tundaan", f"{df_awal['Tundaan (s/smp)'].mean():.2f} s/smp")
        k4.metric("LOS Terburuk", f"{df_awal['LOS'].max()}")

        st.markdown("### 📋 Tabel Rekapitulasi Perhitungan Simpang")
        render_tabel_cantik(df_awal, format_cols=format_tabel_lengkap)

        st.markdown("### 📐 Cek Detail Rumus per Perhitungan (Klik Tombol Rumus)")
        pendekat_aktif = st.selectbox("Pilih Pendekat untuk Melihat Substitusi Angka:", PENDEKAT_LIST)

        daftar_rumus = [
            "Arus Lalu Lintas (Q)",
            "Lebar Efektif Pendekat (L_E)",
            "Arus Jenuh Dasar (J_0)",
            "Arus Jenuh Tersesuaikan (J)",
            "Kapasitas Pendekat (C)",
            "Derajat Kejenuhan (DJ)",
            "Jumlah Antrian (NQ_total)",
            "Panjang Antrian (PA)",
            "Rasio Kendaraan Henti (RKH)",
            "Tundaan Rata-Rata (T_total)"
        ]

        cols_rumus = st.columns(5)
        for idx, nama_r in enumerate(daftar_rumus):
            with cols_rumus[idx % 5]:
                if st.button(nama_r, key=f"btn_rumus_{idx}", use_container_width=True):
                    st.session_state.rumus_terpilih = nama_r

        det_pilihan = dict(detail_awal[pendekat_aktif])
        det_pilihan["pendekat_label"] = f"Pendekat {pendekat_aktif}"
        tampilkan_detail_rumus(st.session_state.rumus_terpilih, det_pilihan)

        st.markdown("### 📈 Grafik Perbandingan Kinerja per Pendekat")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor(palet_aktif["chart_bg"])
        for ax in (ax1, ax2):
            ax.set_facecolor(palet_aktif["chart_bg"])
            ax.tick_params(colors=palet_aktif["chart_text"])
            ax.xaxis.label.set_color(palet_aktif["chart_text"])
            ax.yaxis.label.set_color(palet_aktif["chart_text"])
            ax.title.set_color(palet_aktif["chart_text"])
            ax.grid(axis="y", linestyle=":", alpha=0.45, color=palet_aktif["chart_grid"])
            for spine in ax.spines.values():
                spine.set_color(palet_aktif["chart_grid"])

        colors = ["#EF4444" if x > 0.85 else palet_aktif["primary"] for x in df_awal["DJ"]]
        ax1.bar(df_awal["Pendekat"], df_awal["DJ"], color=colors)
        ax1.axhline(0.85, color="#EF4444", linestyle="--", label="Batas Kritis DJ = 0,85")
        ax1.set_title("Derajat Kejenuhan (DJ) per Pendekat")
        ax1.set_ylabel("DJ")
        ax1.set_ylim(0, max(1.0, df_awal["DJ"].max() * 1.2))
        leg = ax1.legend()
        for text in leg.get_texts():
            text.set_color(palet_aktif["chart_text"])

        ax2.bar(df_awal["Pendekat"], df_awal["PA (m)"], color="#2E8B57")
        ax2.set_title("Panjang Antrian (PA) per Pendekat")
        ax2.set_ylabel("Panjang Antrian (meter)")

        plt.tight_layout()
        st.pyplot(fig)

        st.markdown("#### 🔍 Penjelasan Arti Grafik")
        st.markdown(
            "* **Grafik Kiri — Derajat Kejenuhan (DJ) per Pendekat:** Menunjukkan rasio perbandingan antara arus lalu lintas (`Q`) dengan kapasitas pendekat (`C`). Garis putus-putus merah menandakan **batas kritis DJ = 0,85** sesuai pedoman PKJI. Batang berwarna utama berarti nilai DJ masih di bawah batas kritis, sedangkan batang merah menunjukkan pendekat yang melewati batas kritis (`DJ > 0,85`) sehingga rawan kepadatan dan antrian berlebih.\n"
            "* **Grafik Kanan — Panjang Antrian (PA) per Pendekat:** Menggambarkan perkiraan panjang barisan kendaraan (dalam meter) yang mengantre di tiap lengan pendekat berdasarkan jumlah antrian (`NQ_total`) dan lebar efektif pendekat (`L_E`). Semakin tinggi batang pada grafik ini, semakin panjang antrian kendaraan yang terbentuk sehingga perlu dicermati potensi hambatan hingga ke persimpangan/lengan sebelumnya."
        )

        st.markdown("### 📝 Penjelasan Hasil Perhitungan & Evaluasi Teknis")
        pendekat_kritis = df_awal[df_awal["DJ"] > 0.85]["Pendekat"].tolist()
        rata_dj = df_awal["DJ"].mean()
        rata_tundaan = df_awal["Tundaan (s/smp)"].mean()
        max_pa = df_awal["PA (m)"].max()
        pendekat_max_pa = df_awal.loc[df_awal["PA (m)"].idxmax(), "Pendekat"]

        teks_rekomendasi = (
            "⚠️ Terdapat pendekat dengan nilai **DJ > 0,85** yaitu: **"
            + ", ".join(pendekat_kritis)
            + "**. Evaluasi yang dapat dilakukan antara lain: (1) menyesuaikan alokasi waktu hijau (w_H) proporsional terhadap rasio arus/kapasitas, (2) meninjau pengaturan fase sinyal atau pembatasan BKiJT bila mengganggu antrian, atau (3) mengevaluasi pelebaran lebar efektif pendekat (L_E) bila secara geometrik memungkinkan."
            if pendekat_kritis
            else "✅ Seluruh pendekat memiliki nilai **DJ ≤ 0,85**, sehingga kapasitas pendekat masih mampu melayani arus lalu lintas eksisting. Evaluasi tetap disarankan untuk memantau tundaan dan panjang antrian pada jam puncak serta menguji alternatif pengaturan waktu sinyal pada **Mode 3**."
        )

        st.markdown(
            f"* **Kapasitas & Derajat Kejenuhan (DJ):** Waktu siklus estimasi saat ini adalah **{c_s_awal:.1f} detik** (waktu hilang total **{w_hh_awal:.1f} detik**). Rata-rata derajat kejenuhan simpang sebesar **{rata_dj:.3f}**. Menurut pedoman PKJI, nilai **DJ ≤ 0,85** menunjukkan kondisi operasional yang masih dapat ditoleransi.\n"
            f"* **Panjang Antrian & Tundaan:** Panjang antrian tertinggi terjadi pada **Pendekat {pendekat_max_pa}** sebesar **{max_pa:.1f} m**, dengan rata-rata tundaan simpang **{rata_tundaan:.2f} detik/smp**.\n"
            f"* **Evaluasi & Rekomendasi Perbaikan:** {teks_rekomendasi}"
        )

    # ==========================================================
    # MODE 3: PERBANDINGAN + PERBAIKAN & EVALUASI RUMUS PKJI
    # ==========================================================
    elif mode_pilihan == "Mode 3: Perbandingan & Evaluasi":
        st.subheader("⚖️ Mode 3 — Perbandingan Hasil Hitungan Pertama & Evaluasi")
        st.caption("Atur parameter evaluasi per pendekat dan tinjau perhitungan perbaikan menurut rumus PKJI.")

        df_pertama = st.session_state.hasil_pertama_df.copy()
        df_rekom = hitung_rekomendasi_pkji(detail_awal, target_dj=0.85)

        if "eval_wh_map" not in st.session_state:
            st.session_state.eval_wh_map = {p: float(data_input[p]["w_H"]) for p in PENDEKAT_LIST}
        if "eval_l_map" not in st.session_state:
            st.session_state.eval_l_map = {p: float(data_input[p]["L"]) for p in PENDEKAT_LIST}
        if "eval_bk_map" not in st.session_state:
            st.session_state.eval_bk_map = {p: float(data_input[p]["L_BKiJT"]) for p in PENDEKAT_LIST}

        for p in PENDEKAT_LIST:
            st.session_state.setdefault(f"ev_wh_{p}", float(st.session_state.eval_wh_map[p]))
            st.session_state.setdefault(f"ev_l_{p}", float(st.session_state.eval_l_map[p]))
            st.session_state.setdefault(f"ev_bk_{p}", float(st.session_state.eval_bk_map[p]))

        st.markdown("#### 1. Preset & Pengaturan Parameter Evaluasi")
        p_col1, p_col2, p_col3, p_col4 = st.columns([2, 2, 2, 1])
        pendekat_dj_max = df_pertama.loc[df_pertama["DJ"].idxmax(), "Pendekat"]

        with p_col1:
            if st.button(f"➕ Hijau +5s ({pendekat_dj_max})", key="pre_wh_max", use_container_width=True):
                baru = round(float(st.session_state[f"ev_wh_{pendekat_dj_max}"]) + 5.0, 1)
                st.session_state.eval_wh_map[pendekat_dj_max] = baru
                st.session_state[f"ev_wh_{pendekat_dj_max}"] = baru
                st.rerun()

        with p_col2:
            if st.button(f"📐 Lebar +1,0m ({pendekat_dj_max})", key="pre_l_max", use_container_width=True):
                baru = round(float(st.session_state[f"ev_l_{pendekat_dj_max}"]) + 1.0, 2)
                st.session_state.eval_l_map[pendekat_dj_max] = baru
                st.session_state[f"ev_l_{pendekat_dj_max}"] = baru
                st.rerun()

        with p_col3:
            if st.button("✨ Terapkan Rekomendasi PKJI", key="btn_terapkan_rekom_atas", use_container_width=True):
                for _, r_row in df_rekom.iterrows():
                    p_name = r_row["Pendekat"]
                    wh_rek = float(r_row["w_H Rekomendasi (s)"])
                    l_rek = float(r_row["L Rekomendasi (m)"])
                    st.session_state.eval_wh_map[p_name] = wh_rek
                    st.session_state.eval_l_map[p_name] = l_rek
                    st.session_state[f"ev_wh_{p_name}"] = wh_rek
                    st.session_state[f"ev_l_{p_name}"] = l_rek
                st.rerun()

        with p_col4:
            if st.button("🔄 Reset", key="pre_reset_ev", use_container_width=True):
                for p in PENDEKAT_LIST:
                    wh_0 = float(data_input[p]["w_H"])
                    l_0 = float(data_input[p]["L"])
                    bk_0 = float(data_input[p]["L_BKiJT"])
                    st.session_state.eval_wh_map[p] = wh_0
                    st.session_state.eval_l_map[p] = l_0
                    st.session_state.eval_bk_map[p] = bk_0
                    st.session_state[f"ev_wh_{p}"] = wh_0
                    st.session_state[f"ev_l_{p}"] = l_0
                    st.session_state[f"ev_bk_{p}"] = bk_0
                st.rerun()

        cols_p = st.columns(4)
        for idx, p in enumerate(PENDEKAT_LIST):
            with cols_p[idx]:
                st.markdown(f"**Pendekat {p}**")
                wh_val = st.number_input(
                    f"Waktu Hijau w_H (s) [{p}]",
                    min_value=5.0, max_value=120.0,
                    step=1.0, key=f"ev_wh_{p}"
                )
                l_val = st.number_input(
                    f"Lebar Pendekat L (m) [{p}]",
                    min_value=2.0, max_value=30.0,
                    step=0.5, key=f"ev_l_{p}"
                )
                bk_val = st.number_input(
                    f"Lebar BKiJT (m) [{p}]",
                    min_value=0.0, max_value=15.0,
                    step=0.5, key=f"ev_bk_{p}"
                )
                st.session_state.eval_wh_map[p] = wh_val
                st.session_state.eval_l_map[p] = l_val
                st.session_state.eval_bk_map[p] = bk_val

        data_eval_input = {}
        for p in PENDEKAT_LIST:
            salinan = dict(data_input[p])
            salinan["L_BKiJT"] = st.session_state.eval_bk_map[p]
            data_eval_input[p] = salinan

        df_evaluasi, c_s_eval, _, _ = hitung_kinerja_lengkap(
            data_eval_input,
            custom_emp_map,
            fase,
            w_MS,
            w_K,
            F_UK,
            override_wH=st.session_state.eval_wh_map,
            override_L=st.session_state.eval_l_map,
        )

        tampilkan_semua_kolom = st.checkbox("Tampilkan semua kolom detail (16 kolom)", value=False, key="ev_semua_kolom")

        st.markdown("#### 2. Ringkasan Perubahan Kinerja")
        delta_dj = df_evaluasi["DJ"].mean() - df_pertama["DJ"].mean()
        delta_pa = df_evaluasi["PA (m)"].max() - df_pertama["PA (m)"].max()
        delta_t = df_evaluasi["Tundaan (s/smp)"].mean() - df_pertama["Tundaan (s/smp)"].mean()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rata-rata DJ (Evaluasi)", f"{df_evaluasi['DJ'].mean():.3f}", f"{delta_dj:+.3f}", delta_color="inverse")
        m2.metric("Max PA (Evaluasi)", f"{df_evaluasi['PA (m)'].max():.1f} m", f"{delta_pa:+.1f} m", delta_color="inverse")
        m3.metric("Rata-rata Tundaan", f"{df_evaluasi['Tundaan (s/smp)'].mean():.2f} s/smp", f"{delta_t:+.2f} s/smp", delta_color="inverse")
        m4.metric("LOS (Awal → Evaluasi)", f"{df_pertama['LOS'].max()} → {df_evaluasi['LOS'].max()}")

        st.markdown("#### 3. Tabel Perbandingan")
        tab_selisih, tab_awal, tab_eval = st.tabs([
            "📊 Selisih (Evaluasi vs Awal)",
            "📌 Hitungan Pertama",
            "🛠️ Hasil Evaluasi"
        ])

        df_banding = pd.DataFrame({
            "Pendekat": df_pertama["Pendekat"],
            "DJ Awal": df_pertama["DJ"],
            "DJ Eval": df_evaluasi["DJ"],
            "ΔDJ": (df_evaluasi["DJ"] - df_pertama["DJ"]).round(3),
            "PA Awal (m)": df_pertama["PA (m)"],
            "PA Eval (m)": df_evaluasi["PA (m)"],
            "ΔPA (m)": (df_evaluasi["PA (m)"] - df_pertama["PA (m)"]).round(1),
            "Tundaan Awal": df_pertama["Tundaan (s/smp)"],
            "Tundaan Eval": df_evaluasi["Tundaan (s/smp)"],
            "ΔTundaan": (df_evaluasi["Tundaan (s/smp)"] - df_pertama["Tundaan (s/smp)"]).round(2),
            "LOS Awal": df_pertama["LOS"],
            "LOS Evaluasi": df_evaluasi["LOS"]
        })

        kolom_ringkas = ["Pendekat", "Tipe", "L_E (m)", "w_H (s)", "c_s (s)", "Q (smp/jam)", "C (smp/jam)", "DJ", "PA (m)", "Tundaan (s/smp)", "LOS"]

        with tab_selisih:
            render_tabel_cantik(
                df_banding,
                format_cols={
                    "PA Awal (m)": "{:.1f}",
                    "PA Eval (m)": "{:.1f}",
                    "ΔPA (m)": "{:+.1f}",
                    "Tundaan Awal": "{:.2f}",
                    "Tundaan Eval": "{:.2f}",
                    "ΔTundaan": "{:+.2f}",
                    "ΔDJ": "{:+.3f}"
                }
            )

        with tab_awal:
            render_tabel_cantik(
                df_pertama if tampilkan_semua_kolom else df_pertama[kolom_ringkas],
                format_cols=format_tabel_lengkap
            )

        with tab_eval:
            st.caption(f"Waktu siklus evaluasi: **{c_s_eval:.1f} detik**")
            render_tabel_cantik(
                df_evaluasi if tampilkan_semua_kolom else df_evaluasi[kolom_ringkas],
                format_cols=format_tabel_lengkap
            )

        st.markdown("#### 4. Perbaikan & Evaluasi Menurut Perhitungan PKJI dan Rumus")
        st.caption("Berdasarkan prinsip kapasitas PKJI (C = J × w_H / c_s dan DJ = Q / C ≤ 0,85), berikut perhitungan target perbaikan per pendekat:")

        st.latex(r"C_{\text{target}} = \frac{Q}{0{,}85} \qquad ; \qquad w_{H,\text{target}} = \frac{C_{\text{target}}}{J} \times c_s \qquad ; \qquad L_{E,\text{target}} = \frac{C_{\text{target}}}{600 \times F_{UK} \times (w_H / c_s)}")

        render_tabel_cantik(
            df_rekom,
            format_cols={
                "Q (smp/jam)": "{:,.1f}",
                "DJ Awal": "{:.3f}",
                "w_H Awal (s)": "{:.1f}",
                "w_H Rekomendasi (s)": "{:.1f}",
                "L_E Awal (m)": "{:.2f}",
                "L Rekomendasi (m)": "{:.2f}"
            }
        )

        pendekat_rumus_ev = st.selectbox("Pilih Pendekat untuk Melihat Substitusi Rumus Perbaikan PKJI:", PENDEKAT_LIST, key="ev_rumus_p")
        det_ev = detail_awal[pendekat_rumus_ev]
        c_targ = det_ev["Q_smp"] / 0.85
        wh_targ = ((c_targ / det_ev["J"]) * det_ev["c_s"]) if det_ev["J"] > 0 else det_ev["w_H"]
        ras_h_ev = (det_ev["w_H"] / det_ev["c_s"]) if det_ev["c_s"] > 0 else 0.0
        penj_le_ev = 600.0 * det_ev["F_UK"] * ras_h_ev
        le_targ = (c_targ / penj_le_ev) if penj_le_ev > 0 else det_ev["L_E"]

        st.code(
            f"[{pendekat_rumus_ev}] C_target = {det_ev['Q_smp']:.1f} / 0.85 = {c_targ:.1f} smp/jam\n"
            f"  • w_H_target = ({c_targ:.1f} / {det_ev['J']:.1f}) × {det_ev['c_s']:.1f} = {wh_targ:.1f} detik\n"
            f"  • L_E_target = {c_targ:.1f} / (600 × {det_ev['F_UK']:.2f} × {ras_h_ev:.3f}) = {le_targ:.2f} m",
            language="text"
        )

        st.markdown("#### 5. Penjelasan & Masukan Evaluasi")
        ada_perubahan = any(
            abs(st.session_state.eval_wh_map[p] - data_input[p]["w_H"]) > 1e-9
            or abs(st.session_state.eval_l_map[p] - data_input[p]["L"]) > 1e-9
            or abs(st.session_state.eval_bk_map[p] - data_input[p]["L_BKiJT"]) > 1e-9
            for p in PENDEKAT_LIST
        )

        if not ada_perubahan:
            st.info(
                "Belum ada perubahan parameter evaluasi. Gunakan tombol preset, terapkan rekomendasi PKJI di atas, atau ubah nilai **w_H**, **L**, atau **L_BKiJT** per pendekat."
            )
        else:
            if delta_dj < 0 and delta_pa < 0 and delta_t < 0:
                st.success("Skenario evaluasi **menurunkan rata-rata DJ, panjang antrian maksimum, dan tundaan rata-rata** dibanding hitungan pertama.")
            elif delta_t > 0 or delta_dj > 0:
                st.warning("Ada parameter yang **meningkat** (misalnya karena waktu siklus ikut naik atau hijau pendekat lain berkurang). Cek kolom `ΔDJ`, `ΔPA (m)`, dan `ΔTundaan` per lengan.")
            else:
                st.info("Perubahan berdampak bervariasi antar pendekat; perhatikan selisih tiap baris pada tabel perbandingan.")

        st.markdown(
            "* **Penyesuaian Waktu Hijau (w_H) per Lengan:** Menambah w_H pada pendekat dengan DJ tinggi membantu mengurangi antrian di lengan tersebut, tetapi jika w_H yang ditambahkan melebihi w_H maksimum eksisting maka waktu siklus (c_s) ikut memanjang dan dapat menaikkan tundaan di lengan lain.\n"
            "* **Penyesuaian Lebar Pendekat (L) & L_BKiJT:** Menambah L atau menyesuaikan L_BKiJT menaikkan lebar efektif (L_E) dan kapasitas (C), namun harus tetap mempertimbangkan ketersediaan ruang jalan dan kelayakan teknis di lapangan.\n"
            "* **Evaluasi LOS:** Jika DJ ≤ 0,85 tetapi tingkat pelayanan masih berada di **LOS C atau D**, pertimbangkan penyeimbangan durasi hijau antar fase, pengurangan waktu hilang bila memungkinkan, atau pemisahan pergerakan konflik."
        )

    # ==========================================================
    # MODE 4: RUMUS-RUMUS YANG DIGUNAKAN SESUAI PKJI & MATERI
    # ==========================================================
    elif mode_pilihan == "Mode 4: Rumus-Rumus PKJI":
        st.subheader("📚 Mode 4 — Kumpulan Rumus Perhitungan Simpang APILL (PKJI)")
        st.markdown("Berikut adalah rumusan matematis yang digunakan dalam perhitungan kinerja simpang bersinyal:")

        st.markdown("#### A. Konversi Arus Lalu Lintas ke Satuan SMP")
        st.latex(r"Q = (N_{MP} \times e_{MP}) + (N_{KB} \times e_{KB}) + (N_{SM} \times e_{SM}) + (N_{KTB} \times e_{KTB})")
        st.caption("Keterangan: Q = arus total (smp/jam); N = volume kendaraan per jenis (kend/jam); eMP = ekivalen mobil penumpang sesuai tipe pendekat (P = Terlindung, O = Terlawan).")

        st.markdown("#### B. Lebar Efektif, Arus Jenuh Dasar & Arus Jenuh Tersesuaikan")
        st.latex(r"L_E = L - L_{BKiJT}")
        st.latex(r"J_0 = 600 \times L_E")
        st.latex(r"J = J_0 \times F_{UK}")
        st.caption("Keterangan: L_E = lebar efektif pendekat (m); L = lebar pendekat (m); L_BKiJT = lebar belok kiri jalan terus (m); J_0 = arus jenuh dasar (smp/jam hijau); F_UK = faktor penyesuaian ukuran kota; J = arus jenuh tersesuaikan (smp/jam hijau).")

        st.markdown("#### C. Waktu Siklus, Kapasitas & Derajat Kejenuhan")
        st.latex(r"W_{HH} = \text{Jumlah Fase} \times (w_{MS} + w_K)")
        st.latex(r"c_s = \left(w_{H,\max} \times \frac{\text{Jumlah Fase}}{2}\right) + W_{HH}")
        st.latex(r"C = J \times \frac{w_H}{c_s} \qquad ; \qquad DJ = \frac{Q}{C}")
        st.caption("Keterangan: W_HH = waktu hilang total (detik); w_MS = waktu merah semua (detik); w_K = waktu kuning (detik); c_s = waktu siklus (detik); w_H = waktu hijau pendekat (detik); C = kapasitas (smp/jam); DJ = derajat kejenuhan.")

        st.markdown("#### D. Jumlah Antrian, Panjang Antrian, Rasio Kendaraan Henti & Tundaan")
        st.latex(r"NQ_1 = 0{,}25 \times C \left[(DJ - 1) + \sqrt{(DJ - 1)^2 + \frac{8(DJ - 0{,}5)}{C}}\right] \quad (\text{jika } DJ > 0{,}5)")
        st.latex(r"NQ_2 = \frac{1 - (w_H / c_s)}{1 - \min(1;\ DJ \cdot w_H / c_s)} \times \frac{Q}{3600} \times (c_s - w_H)")
        st.latex(r"NQ_{\text{total}} = NQ_1 + NQ_2 \qquad ; \qquad PA = \frac{NQ_{\text{total}} \times 20}{L_E}")
        st.latex(r"RKH = 0{,}9 \times \frac{1 - (w_H / c_s)}{1 - \min(1;\ DJ \cdot w_H / c_s)}")
        st.latex(r"T_{LL} = \frac{0{,}5 \times c_s \times (1 - w_H/c_s)^2}{1 - \min(1;\ DJ \cdot w_H/c_s)} + \frac{NQ_1 \times 3600}{C}")
        st.latex(r"T_G = (1 - RKH) \times 4 + RKH \times 6 \qquad ; \qquad T_{\text{total}} = T_{LL} + T_G")
        st.caption("Keterangan: NQ_total = jumlah antrian total (smp); PA = panjang antrian (m); RKH = rasio kendaraan henti; T_LL = tundaan lalu lintas (detik/smp); T_G = tundaan geometrik (detik/smp); T_total = tundaan rata-rata (detik/smp).")

        st.markdown("#### E. Kriteria Tingkat Pelayanan (Level of Service / LOS)")
        df_los_ref = pd.DataFrame({
            "LOS": ["A", "B", "C", "D", "E", "F"],
            "Batas Tundaan Rata-Rata (detik/smp)": ["≤ 5,0", "> 5,0 – 15,0", "> 15,0 – 25,0", "> 25,0 – 40,0", "> 40,0 – 60,0", "> 60,0"],
            "Karakteristik Operasional": [
                "Arus bebas, tundaan sangat kecil",
                "Arus stabil, tundaan rendah",
                "Arus stabil, pergerakan mulai dipengaruhi volume",
                "Mendekati arus tidak stabil, tundaan sedang",
                "Arus pada/mendekati kapasitas, tundaan tinggi",
                "Arus terhambat/macet total, tundaan sangat besar"
            ]
        })
        render_tabel_cantik(df_los_ref)
