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
    page_title="Kalkulator APILL PKJI 2023",
    page_icon="🚦",
    layout="wide"
)

# Inisialisasi Session State untuk menyimpan data identitas & status halaman
if "identitas_tersimpan" not in st.session_state:
    st.session_state.identitas_tersimpan = False

if "data_identitas" not in st.session_state:
    st.session_state.data_identitas = {
        "nama_simpang": "",
        "ruas_jalan": "",
        "kota": "",
        "tanggal": date.today(),
        "periode_jam": "Pagi (07.00 - 08.00 WIB)",
        "cuaca": "Cerah",
        "surveyor": ""
    }

# ==========================================
# HALAMAN 1: FORM IDENTITAS SURVEI & LOKASI
# ==========================================
if not st.session_state.identitas_tersimpan:
    st.title("🚦 Kalkulator Kinerja Simpang APILL (PKJI 2023)")
    st.markdown(
        "Selamat datang! Silakan lengkapi **Data Identitas Lokasi & Survei Lalu Lintas** di bawah ini "
        "sebelum memulai perhitungan kinerja simpang bersinyal."
    )
    st.divider()

    with st.form("form_identitas_simpang"):
        st.subheader("📋 Data Identitas Simpang & Survei")
        
        col1, col2 = st.columns(2)
        with col1:
            nama_simpang = st.text_input(
                "Nama Simpang *",
                value=st.session_state.data_identitas["nama_simpang"],
                placeholder="Contoh: Simpang Empat Tugu / Simpang Artos"
            )
            ruas_jalan = st.text_input(
                "Nama Ruas Jalan yang Bertemu *",
                value=st.session_state.data_identitas["ruas_jalan"],
                placeholder="Contoh: Jl. Sudirman - Jl. Ahmad Yani"
            )
            kota = st.text_input(
                "Kota / Kabupaten",
                value=st.session_state.data_identitas["kota"],
                placeholder="Contoh: Kota Magelang, Jawa Tengah"
            )

        with col2:
            tanggal = st.date_input(
                "Tanggal Pelaksanaan Survei",
                value=st.session_state.data_identitas["tanggal"]
            )
            periode_jam = st.selectbox(
                "Periode Jam Survei / Jam Puncak",
                [
                    "Pagi (06.00 - 09.00 WIB)",
                    "Siang (11.00 - 14.00 WIB)",
                    "Sore (16.00 - 19.00 WIB)",
                    "Lainnya / Kustom"
                ],
                index=0
            )
            cuaca = st.selectbox(
                "Kondisi Cuaca Saat Survei",
                ["Cerah", "Berawan", "Hujan Ringan", "Hujan Lebat"],
                index=0
            )

        surveyor = st.text_input(
            "Nama Surveyor / Instansi / Kelompok",
            value=st.session_state.data_identitas["surveyor"],
            placeholder="Contoh: Tim Survei Teknik Sipil"
        )

        st.markdown("")
        submit_btn = st.form_submit_button(
            "Mulai Hitung Kinerja Simpang ➡️",
            type="primary",
            use_container_width=True
        )

        if submit_btn:
            if not nama_simpang.strip() or not ruas_jalan.strip():
                st.error("⚠️ Harap isi minimal **Nama Simpang** dan **Nama Ruas Jalan** terlebih dahulu.")
            else:
                st.session_state.data_identitas = {
                    "nama_simpang": nama_simpang.strip(),
                    "ruas_jalan": ruas_jalan.strip(),
                    "kota": kota.strip() if kota.strip() else "-",
                    "tanggal": tanggal,
                    "periode_jam": periode_jam,
                    "cuaca": cuaca,
                    "surveyor": surveyor.strip() if surveyor.strip() else "-"
                }
                st.session_state.identitas_tersimpan = True
                st.rerun()

# ==========================================
# HALAMAN 2: KALKULATOR & DASHBOARD ANALISIS
# ==========================================
else:
    identitas = st.session_state.data_identitas

    # Header Utama + Tombol Kembali Edit Identitas
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.title("🚦 Kalkulator Kinerja Simpang APILL (PKJI 2023)")
        st.caption("Analisis Derajat Kejenuhan (DJ), Panjang Antrian (PA), Tundaan (T), dan Level of Service (LOS).")
    with col_head2:
        st.markdown("")
        if st.button("✏️ Ubah Identitas", use_container_width=True):
            st.session_state.identitas_tersimpan = False
            st.rerun()

    # Kartu Informasi Identitas Survei
    with st.expander("📌 Informasi Identitas Simpang & Survei", expanded=True):
        c_id1, c_id2, c_id3, c_id4 = st.columns(4)
        c_id1.markdown(f"**Nama Simpang:**\n{identitas['nama_simpang']}")
        c_id2.markdown(f"**Ruas Jalan:**\n{identitas['ruas_jalan']}")
        c_id3.markdown(f"**Kota & Tanggal:**\n{identitas['kota']} ({identitas['tanggal'].strftime('%d-%m-%Y')})")
        c_id4.markdown(f"**Jam Survei & Cuaca:**\n{identitas['periode_jam']} | {identitas['cuaca']}")
        if identitas["surveyor"] != "-":
            st.caption(f"Surveyor / Instansi: {identitas['surveyor']}")

    # ==========================================
    # 1. SIDEBAR - INPUT PARAMETER
    # ==========================================
    st.sidebar.header("⚙️ Parameter Input Simpang")

    # Parameter Sinyal Global
    st.sidebar.subheader("1. Informasi Sinyal & Kota")
    fase = st.sidebar.number_input("Jumlah Fase", min_value=2, max_value=6, value=4)
    w_MS = st.sidebar.number_input("Waktu Merah Semua / Fase (detik)", min_value=1.0, value=3.0, step=0.5)
    w_K = st.sidebar.number_input("Waktu Kuning / Fase (detik)", min_value=1.0, value=3.0, step=0.5)
    ukuran_kota = st.sidebar.selectbox(
        "Ukuran Kota (Juta Jiwa)",
        ["> 3.0", "1.0 - 3.0", "0.5 - 1.0", "0.1 - 0.5", "< 0.1"],
        index=1
    )

    # Mapping Faktor Koreksi Ukuran Kota (F_UK)
    f_uk_map = {"> 3.0": 1.05, "1.0 - 3.0": 1.00, "0.5 - 1.0": 0.94, "0.1 - 0.5": 0.88, "< 0.1": 0.82}
    F_UK = f_uk_map[ukuran_kota]

    # Input Per Pendekat
    st.sidebar.subheader("2. Data Pendekat & Arus")
    pendekat_list = ['Utara', 'Selatan', 'Timur', 'Barat']
    data_input = {}

    for p in pendekat_list:
        with st.sidebar.expander(f"Pendekat {p}", expanded=False):
            tipe = st.selectbox(f"Tipe Pendekat {p}", ['P', 'O'], key=f"tipe_{p}", help="P = Terlindung, O = Terlawan")
            L = st.number_input(f"Lebar Pendekat L (m) [{p}]", min_value=2.0, value=7.0 if p in ['Utara', 'Selatan'] else 6.0, key=f"L_{p}")
            L_BKiJT = st.number_input(f"Lebar BKiJT (m) [{p}]", min_value=0.0, value=0.0, key=f"bk_{p}")
            w_H = st.number_input(f"Waktu Hijau w_H (detik) [{p}]", min_value=5.0, value=25.0, key=f"wH_{p}")
            
            st.write("**Arus Lalu Lintas (kend/jam):**")
            mp = st.number_input(f"Mobil Penumpang (MP) [{p}]", min_value=0, value=700 if p in ['Utara', 'Selatan'] else 500, key=f"mp_{p}")
            kb = st.number_input(f"Kendaraan Berat (KB) [{p}]", min_value=0, value=50 if p in ['Utara', 'Selatan'] else 30, key=f"kb_{p}")
            sm = st.number_input(f"Sepeda Motor (SM) [{p}]", min_value=0, value=1800 if p in ['Utara', 'Selatan'] else 1400, key=f"sm_{p}")
            
            data_input[p] = {
                'tipe': tipe, 'L': L, 'L_BKiJT': L_BKiJT, 'w_H': w_H,
                'MP': mp, 'KB': kb, 'SM': sm
            }

    # ==========================================
    # 2. PERHITUNGAN OTOMATIS (PKJI 2023)
    # ==========================================
    W_HH = fase * (w_MS + w_K)
    total_wH = max([data_input[p]['w_H'] for p in data_input]) * (fase / 2)
    c_s = total_wH + W_HH 

    hasil_perhitungan = []

    for p, data in data_input.items():
        tipe = data['tipe']
        emp_mp = 1.0
        emp_kb = 1.3
        emp_sm = 0.2 if tipe == 'P' else 0.4
        
        Q_smp = (data['MP'] * emp_mp) + (data['KB'] * emp_kb) + (data['SM'] * emp_sm)
        L_E = data['L'] - data['L_BKiJT']
        J_0 = 600 * L_E
        J = J_0 * F_UK
        C = J * (data['w_H'] / c_s) if c_s > 0 else 1
        DJ = Q_smp / C if C > 0 else 0
        
        NQ1 = 0.25 * C * ((DJ - 1) + np.sqrt((DJ - 1)**2 + (8 * (DJ - 0.5) / C))) if DJ > 0.5 else 0
        NQ2 = (1 - (data['w_H'] / c_s)) / (1 - min(1.0, DJ * (data['w_H'] / c_s))) * (Q_smp / 3600) * (c_s - data['w_H'])
        NQ_total = NQ1 + NQ2
        PA = (NQ_total * 20) / L_E if L_E > 0 else 0
        
        RKH = 0.9 * (1 - (data['w_H'] / c_s)) / (1 - min(1.0, DJ * (data['w_H'] / c_s)))
        T_LL = (0.5 * c_s * (1 - (data['w_H'] / c_s))**2) / (1 - min(1.0, DJ * (data['w_H'] / c_s))) + (NQ1 * 3600 / C)
        T_G = (1 - RKH) * 4 + RKH * 6
        T_total = T_LL + T_G
        
        if T_total <= 5.0: los = 'A'
        elif T_total <= 15.0: los = 'B'
        elif T_total <= 25.0: los = 'C'
        elif T_total <= 40.0: los = 'D'
        elif T_total <= 60.0: los = 'E'
        else: los = 'F'
        
        hasil_perhitungan.append({
            'Pendekat': p,
            'L_E (m)': round(L_E, 2),
            'Q (smp/jam)': round(Q_smp, 1),
            'J (smp/jam)': round(J, 1),
            'C (smp/jam)': round(C, 1),
            'DJ': round(DJ, 3),
            'PA (m)': round(PA, 1),
            'Tundaan (s/smp)': round(T_total, 2),
            'LOS': los
        })

    df_hasil = pd.DataFrame(hasil_perhitungan)

    # ==========================================
    # 3. DASHBOARD HALAMAN UTAMA
    # ==========================================
    st.subheader("📊 Ringkasan Kinerja Simpang")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rata-rata DJ", f"{df_hasil['DJ'].mean():.3f}")
    col2.metric("Max Panjang Antrian", f"{df_hasil['PA (m)'].max():.1f} m")
    col3.metric("Rata-rata Tundaan", f"{df_hasil['Tundaan (s/smp)'].mean():.1f} s/smp")
    col4.metric("LOS Simpang", f"{df_hasil['LOS'].max()}")

    st.dataframe(df_hasil, use_container_width=True)

    # ==========================================
    # 4. VISUALISASI GRAFIK
    # ==========================================
    st.subheader("📈 Grafik Visualisasi Kinerja")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    colors = ['#ff4b4b' if x > 0.85 else '#1f77b4' for x in df_hasil['DJ']]
    ax1.bar(df_hasil['Pendekat'], df_hasil['DJ'], color=colors)
    ax1.axhline(0.85, color='red', linestyle='--', label='Batas Kritis (0.85)')
    ax1.set_title("Derajat Kejenuhan (DJ) per Pendekat")
    ax1.set_ylabel("DJ")
    ax1.set_ylim(0, max(1.0, df_hasil['DJ'].max() * 1.2))
    ax1.legend()

    ax2.bar(df_hasil['Pendekat'], df_hasil['PA (m)'], color='#2ca02c')
    ax2.set_title("Panjang Antrian (PA) per Pendekat")
    ax2.set_ylabel("Panjang Antrian (meter)")

    plt.tight_layout()
    st.pyplot(fig)

    # ==========================================
    # 5. TOMBOL DOWNLOAD EXCEL
    # ==========================================
    st.subheader("📥 Unduh Laporan Excel")

    df_identitas_excel = pd.DataFrame({
        "Parameter": [
            "Nama Simpang",
            "Ruas Jalan",
            "Kota / Kabupaten",
            "Tanggal Survei",
            "Periode Jam Survei",
            "Kondisi Cuaca",
            "Surveyor / Instansi",
            "Ukuran Kota (Juta Jiwa)",
            "Jumlah Fase",
            "Waktu Siklus Estimasi (detik)"
        ],
        "Keterangan": [
            identitas["nama_simpang"],
            identitas["ruas_jalan"],
            identitas["kota"],
            identitas["tanggal"].strftime("%d-%m-%Y"),
            identitas["periode_jam"],
            identitas["cuaca"],
            identitas["surveyor"],
            ukuran_kota,
            fase,
            round(c_s, 1)
        ]
    })

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_identitas_excel.to_excel(writer, sheet_name='Identitas Survei', index=False)
        df_hasil.to_excel(writer, sheet_name='Kinerja Simpang', index=False)

    nama_file_bersih = identitas["nama_simpang"].replace(" ", "_")
    st.download_button(
        label="Download Hasil Perhitungan (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Kinerja_{nama_file_bersih}_PKJI2023.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
