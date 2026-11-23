import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import date

# ==========================================
# KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Kalkulator APILL PKJI",
    page_icon="🚦",
    layout="wide"
)

# Inisialisasi Session State
if "identitas_tersimpan" not in st.session_state:
    st.session_state.identitas_tersimpan = False

if "data_identitas" not in st.session_state:
    st.session_state.data_identitas = {
        "nama_simpang": "",
        "ruas_jalan": "",
        "kota": "",
        "tanggal": date.today(),
        "jam_survei": "07.00 - 08.00 WIB",
        "cuaca": "Cerah",
        "surveyor": ""
    }

if "hasil_pertama_df" not in st.session_state:
    st.session_state.hasil_pertama_df = None

if "hasil_pertama_detail" not in st.session_state:
    st.session_state.hasil_pertama_detail = None

if "rumus_terpilih" not in st.session_state:
    st.session_state.rumus_terpilih = "Derajat Kejenuhan (DJ)"


# ==========================================
# FUNGSI BANTUAN PERHITUNGAN PKJI
# ==========================================
def get_emp_pkji(tipe_pendekat):
    """Mengembalikan nilai eMP standar PKJI berdasarkan tipe pendekat ('P' atau 'O')."""
    if tipe_pendekat == "P":
        return {"MP": 1.0, "KB": 1.3, "SM": 0.2, "KTB": 0.0}
    else:  # 'O' (Terlawan)
        return {"MP": 1.0, "KB": 1.3, "SM": 0.4, "KTB": 0.0}


def hitung_konversi_smp(data_input, custom_emp_map):
    """Mode 1: Hanya mengonversi data mentah lapangan ke satuan smp."""
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
    """Menghitung seluruh parameter kinerja simpang APILL hingga LOS."""
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

        # Jumlah antrian (NQ1 & NQ2) dan Panjang Antrian (PA)
        if DJ > 0.5 and C > 0:
            NQ1 = 0.25 * C * ((DJ - 1.0) + np.sqrt((DJ - 1.0) ** 2 + (8.0 * (DJ - 0.5) / C)))
        else:
            NQ1 = 0.0

        penyebut_antrian = max(0.05, 1.0 - min(0.95, DJ * rasio_hijau))
        NQ2 = ((1.0 - rasio_hijau) / penyebut_antrian) * (Q_smp / 3600.0) * max(0.0, (c_s - w_H))
        NQ_total = NQ1 + NQ2
        PA = (NQ_total * 20.0) / L_E if L_E > 0 else 0.0

        # Rasio Kendaraan Henti (RKH) & Tundaan (T_LL, T_G, T_total)
        RKH = min(1.0, 0.9 * ((1.0 - rasio_hijau) / penyebut_antrian))
        T_LL = ((0.5 * c_s * ((1.0 - rasio_hijau) ** 2)) / penyebut_antrian) + ((NQ1 * 3600.0 / C) if C > 0 else 0.0)
        T_G = (1.0 - RKH) * 4.0 + RKH * 6.0
        T_total = T_LL + T_G

        # Penentuan LOS
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


def tampilkan_detail_rumus(nama_rumus, det):
    """Menampilkan Rumus -> Masukkan Angka -> Hasil Akhir untuk rumus yang dipilih."""
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


# ==========================================
# HALAMAN AWAL: IDENTITAS SURVEI & SIMPANG
# ==========================================
if not st.session_state.identitas_tersimpan:
    st.title("🚦 Kalkulator Kinerja Simpang APILL (PKJI)")
    st.caption("Silakan lengkapi data identitas survei terlebih dahulu sebelum membuka menu kalkulasi.")
    st.divider()

    st.subheader("📋 Data Identitas Simpang & Survei")
    with st.form("form_identitas_awal"):
        col1, col2 = st.columns(2)
        with col1:
            nama_simpang = st.text_input(
                "Nama Simpang *",
                value=st.session_state.data_identitas["nama_simpang"],
                placeholder="Contoh: Simpang Empat Kebonpolo"
            )
            ruas_jalan = st.text_input(
                "Ruas Jalan yang Bertemu *",
                value=st.session_state.data_identitas["ruas_jalan"],
                placeholder="Contoh: Jl. Ahmad Yani - Jl. Tentara Pelajar"
            )
            kota = st.text_input(
                "Kota / Kabupaten",
                value=st.session_state.data_identitas["kota"],
                placeholder="Contoh: Kota Magelang"
            )
        with col2:
            tanggal = st.date_input(
                "Tanggal Survei",
                value=st.session_state.data_identitas["tanggal"]
            )
            jam_survei = st.text_input(
                "Jam Survei / Periode Waktu",
                value=st.session_state.data_identitas["jam_survei"],
                placeholder="Contoh: 07.00 - 08.00 WIB"
            )
            cuaca = st.selectbox(
                "Kondisi Cuaca",
                ["Cerah", "Berawan", "Hujan Ringan", "Hujan Lebat"],
                index=["Cerah", "Berawan", "Hujan Ringan", "Hujan Lebat"].index(
                    st.session_state.data_identitas["cuaca"]
                )
            )

        surveyor = st.text_input(
            "Nama Surveyor / Instansi / Kelompok",
            value=st.session_state.data_identitas["surveyor"],
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
                    "tanggal": tanggal,
                    "jam_survei": jam_survei.strip() if jam_survei.strip() else "-",
                    "cuaca": cuaca,
                    "surveyor": surveyor.strip() if surveyor.strip() else "-"
                }
                st.session_state.identitas_tersimpan = True
                st.rerun()

# ==========================================
# HALAMAN 2: 4 MODE DI BAGIAN ATAS
# ==========================================
else:
    identitas = st.session_state.data_identitas

    c_h1, c_h2 = st.columns([5, 1])
    with c_h1:
        st.title("🚦 Kalkulator Kinerja Simpang APILL (PKJI)")
    with c_h2:
        st.markdown("")
        if st.button("✏️ Ubah Identitas", use_container_width=True):
            st.session_state.identitas_tersimpan = False
            st.rerun()

    st.caption(
        f"**Simpang:** {identitas['nama_simpang']} | "
        f"**Ruas Jalan:** {identitas['ruas_jalan']} | "
        f"**Kota:** {identitas['kota']} | "
        f"**Tanggal:** {identitas['tanggal'].strftime('%d-%m-%Y')} | "
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
    # SIDEBAR - INPUT DATA MENTAH & PARAMETER
    # ==========================================
    st.sidebar.header("⚙️ Parameter Input Simpang")

    st.sidebar.subheader("1. Informasi Sinyal & Kota")
    fase = st.sidebar.number_input("Jumlah Fase", min_value=2, max_value=6, value=4)
    w_MS = st.sidebar.number_input("Waktu Merah Semua / Fase (detik)", min_value=1.0, value=3.0, step=0.5)
    w_K = st.sidebar.number_input("Waktu Kuning / Fase (detik)", min_value=1.0, value=3.0, step=0.5)
    ukuran_kota = st.sidebar.selectbox(
        "Ukuran Kota (Juta Jiwa)",
        ["> 3.0", "1.0 - 3.0", "0.5 - 1.0", "0.1 - 0.5", "< 0.1"],
        index=1
    )

    f_uk_map = {"> 3.0": 1.05, "1.0 - 3.0": 1.00, "0.5 - 1.0": 0.94, "0.1 - 0.5": 0.88, "< 0.1": 0.82}
    F_UK = f_uk_map[ukuran_kota]

    st.sidebar.subheader("2. Data Pendekat & Arus Mentah")
    pendekat_list = ["Utara", "Selatan", "Timur", "Barat"]
    data_input = {}

    for p in pendekat_list:
        with st.sidebar.expander(f"Pendekat {p}", expanded=False):
            tipe = st.selectbox(f"Tipe Pendekat {p}", ["P", "O"], key=f"tipe_{p}", help="P = Terlindung, O = Terlawan")
            L = st.number_input(f"Lebar Pendekat L (m) [{p}]", min_value=2.0, value=7.0 if p in ["Utara", "Selatan"] else 6.0, key=f"L_{p}")
            L_BKiJT = st.number_input(f"Lebar BKiJT (m) [{p}]", min_value=0.0, value=0.0, key=f"bk_{p}")
            w_H = st.number_input(f"Waktu Hijau w_H (detik) [{p}]", min_value=5.0, value=25.0, key=f"wH_{p}")

            st.write("**Arus Lalu Lintas Mentah (kend/jam):**")
            mp = st.number_input(f"Mobil Penumpang (MP) [{p}]", min_value=0, value=700 if p in ["Utara", "Selatan"] else 500, key=f"mp_{p}")
            kb = st.number_input(f"Kendaraan Berat (KB) [{p}]", min_value=0, value=50 if p in ["Utara", "Selatan"] else 30, key=f"kb_{p}")
            sm = st.number_input(f"Sepeda Motor (SM) [{p}]", min_value=0, value=1800 if p in ["Utara", "Selatan"] else 1400, key=f"sm_{p}")
            ktb = st.number_input(f"Kendaraan Tak Bermotor (KTB) [{p}]", min_value=0, value=0, key=f"ktb_{p}")

            data_input[p] = {
                "tipe": tipe, "L": L, "L_BKiJT": L_BKiJT, "w_H": w_H,
                "MP": mp, "KB": kb, "SM": sm, "KTB": ktb
            }

    st.sidebar.subheader("3. Pengaturan Nilai eMP")
    gunakan_emp_custom = st.sidebar.checkbox("Ubah nilai eMP secara mandiri (Custom)", value=False)
    custom_emp_map = {}

    for p in pendekat_list:
        default_emp = get_emp_pkji(data_input[p]["tipe"])
        if gunakan_emp_custom:
            with st.sidebar.expander(f"eMP Custom — {p}", expanded=False):
                e_mp = st.number_input(f"eMP [{p}]", min_value=0.0, value=float(default_emp["MP"]), step=0.05, key=f"emp_mp_{p}")
                e_kb = st.number_input(f"eKB [{p}]", min_value=0.0, value=float(default_emp["KB"]), step=0.05, key=f"emp_kb_{p}")
                e_sm = st.number_input(f"eSM [{p}]", min_value=0.0, value=float(default_emp["SM"]), step=0.05, key=f"emp_sm_{p}")
                e_ktb = st.number_input(f"eKTB [{p}]", min_value=0.0, value=float(default_emp["KTB"]), step=0.05, key=f"emp_ktb_{p}")
                custom_emp_map[p] = {"MP": e_mp, "KB": e_kb, "SM": e_sm, "KTB": e_ktb}
        else:
            custom_emp_map[p] = default_emp

    df_awal, c_s_awal, w_hh_awal, detail_awal = hitung_kinerja_lengkap(
        data_input, custom_emp_map, fase, w_MS, w_K, F_UK
    )
    if st.session_state.hasil_pertama_df is None:
        st.session_state.hasil_pertama_df = df_awal.copy()
        st.session_state.hasil_pertama_detail = detail_awal

    # ==========================================================
    # MODE 1: KONVERSI DATA MENTAH KE SATUAN SMP SAJA
    # ==========================================================
    if mode_pilihan == "Mode 1: Konversi ke SMP":
        st.subheader("🔄 Mode 1 — Konversi Arus Lalu Lintas Mentah ke Satuan SMP")
        if not gunakan_emp_custom:
            st.info("Menggunakan nilai **eMP standar PKJI** (MP = 1,00; KB = 1,30; SM = 0,20 untuk tipe **P** dan 0,40 untuk tipe **O**). Centang **Ubah nilai eMP secara mandiri (Custom)** di sidebar bila ingin mengubah eMP sendiri.")
        else:
            st.warning("Mode **eMP Custom** aktif: nilai eMP disesuaikan dengan input mandiri Anda di sidebar.")

        df_konversi = hitung_konversi_smp(data_input, custom_emp_map)
        st.dataframe(df_konversi, use_container_width=True, hide_index=True)

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
        styled_df = df_awal.style.format({
            "L_E (m)": "{:.2f}",
            "w_H (s)": "{:.1f}",
            "c_s (s)": "{:.1f}",
            "Q (smp/jam)": "{:.1f}",
            "J_0 (smp/jam)": "{:.1f}",
            "J (smp/jam)": "{:.1f}",
            "C (smp/jam)": "{:.1f}",
            "DJ": "{:.3f}",
            "NQ_total (smp)": "{:.2f}",
            "PA (m)": "{:.1f}",
            "RKH": "{:.3f}",
            "Tundaan (s/smp)": "{:.2f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.markdown("### 📐 Cek Detail Rumus per Perhitungan (Klik Tombol Rumus)")
        pendekat_aktif = st.selectbox("Pilih Pendekat untuk Melihat Substitusi Angka:", pendekat_list)

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
        colors = ["#e74c3c" if x > 0.85 else "#2b6cb0" for x in df_awal["DJ"]]
        ax1.bar(df_awal["Pendekat"], df_awal["DJ"], color=colors)
        ax1.axhline(0.85, color="red", linestyle="--", label="Batas Kritis DJ = 0,85")
        ax1.set_title("Derajat Kejenuhan (DJ) per Pendekat")
        ax1.set_ylabel("DJ")
        ax1.set_ylim(0, max(1.0, df_awal["DJ"].max() * 1.2))
        ax1.legend()

        ax2.bar(df_awal["Pendekat"], df_awal["PA (m)"], color="#2f855a")
        ax2.set_title("Panjang Antrian (PA) per Pendekat")
        ax2.set_ylabel("Panjang Antrian (meter)")

        plt.tight_layout()
        st.pyplot(fig)

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

        st.markdown("### 📥 Unduh Laporan Excel")
        df_identitas_excel = pd.DataFrame({
            "Parameter": [
                "Nama Simpang", "Ruas Jalan", "Kota / Kabupaten", "Tanggal Survei",
                "Jam Survei", "Kondisi Cuaca", "Surveyor", "Ukuran Kota",
                "Jumlah Fase", "Waktu Siklus Estimasi (s)"
            ],
            "Keterangan": [
                identitas["nama_simpang"], identitas["ruas_jalan"], identitas["kota"],
                identitas["tanggal"].strftime("%d-%m-%Y"), identitas["jam_survei"],
                identitas["cuaca"], identitas["surveyor"], ukuran_kota,
                fase, round(c_s_awal, 1)
            ]
        })

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_identitas_excel.to_excel(writer, sheet_name="Identitas Survei", index=False)
            df_awal.to_excel(writer, sheet_name="Kinerja Simpang", index=False)

        st.download_button(
            label="Download Hasil Perhitungan (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Kinerja_{identitas['nama_simpang'].replace(' ', '_') or 'Simpang'}_PKJI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ==========================================================
    # MODE 3: PERBANDINGAN TABEL HASIL PERTAMA & TABEL EVALUASI
    # ==========================================================
    elif mode_pilihan == "Mode 3: Perbandingan & Evaluasi":
        st.subheader("⚖️ Mode 3 — Perbandingan Hasil Hitungan Pertama & Evaluasi")

        st.markdown("#### 1. Pengaturan Parameter Evaluasi")
        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
            tambah_wh = st.slider("Penyesuaian Waktu Hijau Semua Pendekat (detik)", min_value=-15.0, max_value=20.0, value=0.0, step=1.0)
        with col_ev2:
            tambah_lebar = st.slider("Penyesuaian Lebar Pendekat L Semua Lengan (m)", min_value=-2.0, max_value=4.0, value=0.0, step=0.5)

        override_wH = {p: max(5.0, data_input[p]["w_H"] + tambah_wh) for p in pendekat_list}
        override_L = {p: max(2.0, data_input[p]["L"] + tambah_lebar) for p in pendekat_list}

        df_evaluasi, c_s_eval, _, _ = hitung_kinerja_lengkap(
            data_input, custom_emp_map, fase, w_MS, w_K, F_UK,
            override_wH=override_wH, override_L=override_L
        )

        df_pertama = st.session_state.hasil_pertama_df.copy()

        st.markdown("#### 2. Tabel Hasil Hitungan Pertama (Baseline)")
        st.dataframe(df_pertama, use_container_width=True, hide_index=True)

        st.markdown(f"#### 3. Tabel Hasil Evaluasi (Waktu Siklus Evaluasi: {c_s_eval:.1f} detik)")
        st.dataframe(df_evaluasi, use_container_width=True, hide_index=True)

        st.markdown("#### 4. Tabel Perbandingan (Evaluasi vs Hitungan Pertama)")
        df_banding = pd.DataFrame({
            "Pendekat": df_pertama["Pendekat"],
            "DJ Awal": df_pertama["DJ"],
            "DJ Evaluasi": df_evaluasi["DJ"],
            "Selisih DJ (ΔDJ)": (df_evaluasi["DJ"] - df_pertama["DJ"]).round(3),
            "PA Awal (m)": df_pertama["PA (m)"],
            "PA Evaluasi (m)": df_evaluasi["PA (m)"],
            "Selisih PA (Δm)": (df_evaluasi["PA (m)"] - df_pertama["PA (m)"]).round(1),
            "Tundaan Awal (s/smp)": df_pertama["Tundaan (s/smp)"],
            "Tundaan Evaluasi (s/smp)": df_evaluasi["Tundaan (s/smp)"],
            "LOS Awal": df_pertama["LOS"],
            "LOS Evaluasi": df_evaluasi["LOS"]
        })
        st.dataframe(df_banding, use_container_width=True, hide_index=True)

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
        st.dataframe(df_los_ref, use_container_width=True, hide_index=True)
