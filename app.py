import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import io

# 1. KONFIGURASI HALAMAN WEB & TEMA DARK NAVY BLUE
st.set_page_config(
    page_title="Kalkulator Simpang APILL PKJI 2023",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Dark Navy Theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0B132B !important;
        color: #FFFFFF !important;
    }
    h1, h2, h3, h4, h5, h6, label, p, span {
        color: #E0E6ED !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1 {
        color: #64DFDF !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #1C2541 !important;
        border-right: 1px solid #3A506B;
    }
    div[data-testid="stRadio"] label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        color: #64DFDF !important;
        font-weight: bold !important;
    }
    .stAlert {
        background-color: #1C2541 !important;
        border: 1px solid #3A506B !important;
        border-left: 5px solid #64DFDF !important;
    }
    .stAlert p {
        color: #FFFFFF !important;
    }
    .stButton>button {
        background-color: #3A506B !important;
        color: #64DFDF !important;
        border: 1px solid #64DFDF !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #64DFDF !important;
        color: #0B132B !important;
        box-shadow: 0 4px 12px rgba(100, 223, 223, 0.3);
    }
    div[data-testid="stMetricValue"] {
        color: #64DFDF !important;
        font-weight: bold;
    }
    div[data-testid="stMetricLabel"] {
        color: #A3CEF1 !important;
        font-weight: 600;
    }
    div[data-testid="stDataEditor"] {
        background-color: #1C2541 !important;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. INISIALISASI SESSION STATE UNTUK INTEGRASI DATA OTOMATIS
data_awal_default = {
    "Pendekat": ["Utara", "Selatan", "Timur", "Barat"],
    "Tipe": ["P", "P", "P", "P"],
    "Lebar Efektif L_E (m)": [3.5, 3.5, 3.0, 3.0],
    "Jumlah Lajur (N)": [1, 1, 1, 1],
    "MP - LRS": [400, 450, 300, 250],
    "MP - BKi": [100, 120, 80, 90],
    "MP - BKa": [150, 130, 110, 100],
    "KB - LRS": [30, 25, 20, 15],
    "KB - BKi": [5, 10, 5, 5],
    "KB - BKa": [10, 8, 5, 5],
    "SM - LRS": [1200, 1100, 800, 900],
    "SM - BKi": [300, 250, 200, 220],
    "SM - BKa": [400, 350, 250, 280]
}

if 'df_global_input' not in st.session_state:
    st.session_state.df_global_input = pd.DataFrame(data_awal_default)

# 3. FUNGSI PERHITUNGAN CORE PKJI 2023
def hitung_pkji_simpang_lengkap(df_in, w_k, w_ms, fase, map_fase):
    hasil_pendekat = []
    hasil_konversi = []
    
    for idx, row in df_in.iterrows():
        pend = row["Pendekat"]
        tipe = row["Tipe"]
        le = float(row["Lebar Efektif L_E (m)"])
        n_lajur = int(row["Jumlah Lajur (N)"])
        fase_pend = map_fase[pend]
        
        emp_mp = 1.0
        emp_kb = 1.3
        emp_sm = 0.2 if tipe == "P" else 0.4
        
        tot_mp_kend = row["MP - LRS"] + row["MP - BKi"] + row["MP - BKa"]
        tot_kb_kend = row["KB - LRS"] + row["KB - BKi"] + row["KB - BKa"]
        tot_sm_kend = row["SM - LRS"] + row["SM - BKi"] + row["SM - BKa"]
        
        q_mp_smp = tot_mp_kend * emp_mp
        q_kb_smp = tot_kb_kend * emp_kb
        q_sm_smp = tot_sm_kend * emp_sm
        q_total_smp = q_mp_smp + q_kb_smp + q_sm_smp
        
        hasil_konversi.append({
            "Pendekat": pend,
            "Tipe": tipe,
            "EMP (MP/KB/SM)": f"{emp_mp} / {emp_kb} / {emp_sm}",
            "Total Kendaraan (kend/jam)": tot_mp_kend + tot_kb_kend + tot_sm_kend,
            "MP (smp/jam)": q_mp_smp,
            "KB (smp/jam)": q_kb_smp,
            "SM (smp/jam)": q_sm_smp,
            "Total Arus q (smp/jam)": q_total_smp
        })
        
        j0 = 600 * le if tipe == "P" else 500 * le
        j_adj = j0
        fr = q_total_smp / j_adj if j_adj > 0 else 0
        
        hasil_pendekat.append({
            "Pendekat": pend,
            "Fase": fase_pend,
            "Tipe": tipe,
            "L_E (m)": le,
            "N Lajur": n_lajur,
            "q MP (smp/jam)": q_mp_smp,
            "q KB (smp/jam)": q_kb_smp,
            "q SM (smp/jam)": q_sm_smp,
            "q Total (smp/jam)": q_total_smp,
            "J0 Dasar (smp/jam)": j0,
            "J Adj (smp/jam)": j_adj,
            "FR (Rasio Arus)": fr
        })
        
    df_res = pd.DataFrame(hasil_pendekat)
    df_konv = pd.DataFrame(hasil_konversi)
    w_hh = (w_k + w_ms) * fase
    
    fr_kritis_per_fase = {}
    for f in range(1, fase + 1):
        df_fase = df_res[df_res["Fase"] == f]
        fr_max = df_fase["FR (Rasio Arus)"].max() if not df_fase.empty else 0
        fr_kritis_per_fase[f] = fr_max
        
    ras = sum(fr_kritis_per_fase.values())
    
    if ras < 0.95 and ras > 0:
        s_opt = (1.5 * w_hh + 5) / (1 - ras)
    else:
        s_opt = 120.0
        
    s_opt = float(np.clip(s_opt, 30.0, 180.0))
    w_he_total = s_opt - w_hh
    
    list_c, list_dj, list_nq, list_pa = [], [], [], []
    list_tll, list_tg, list_t, list_los, list_w_h, list_rkh = [], [], [], [], [], []
    
    for idx, row in df_res.iterrows():
        f_i = row["Fase"]
        fr_kritis = fr_kritis_per_fase.get(f_i, 0.001)
        
        if ras > 0:
            w_h = (row["FR (Rasio Arus)"] / ras) * w_he_total if fr_kritis == 0 else (fr_kritis / ras) * w_he_total
        else:
            w_h = w_he_total / fase
            
        w_h = max(round(w_h, 1), 10.0)
        list_w_h.append(w_h)
        
        rh = w_h / s_opt
        c = row["J Adj (smp/jam)"] * rh
        list_c.append(round(c, 1))
        
        dj = row["q Total (smp/jam)"] / c if c > 0 else 0
        list_dj.append(round(dj, 3))
        
        rkh = 0.9 * ((1 - rh) / (1 - rh * min(dj, 0.99)))
        list_rkh.append(round(rkh, 3))
        
        if dj <= 0.5:
            nq1 = 0
        else:
            nq1 = 0.25 * s_opt * ((dj - 1) + np.sqrt((dj - 1)**2 + (8 * (dj - 0.5) / s_opt)))
            
        denom = 1 - (rh * dj)
        nq2 = s_opt * ((1 - rh) / denom) * (row["q Total (smp/jam)"] / 3600) if denom > 0 else 0
        
        nq_total = nq1 + nq2
        pa = (nq_total * 20) / row["N Lajur"]
        
        list_nq.append(round(nq_total, 2))
        list_pa.append(round(pa, 1))
        
        t_ll = s_opt * (0.5 * (1 - rh)**2 / max(1 - rh * dj, 0.01)) + (nq1 * 3600 / max(c, 1))
        t_g = (1 - rkh) * 4.0 + rkh * 6.0
        t_total = t_ll + t_g
        
        list_tll.append(round(t_ll, 1))
        list_tg.append(round(t_g, 1))
        list_t.append(round(t_total, 1))
        
        if t_total <= 10:
            los = "A"
        elif t_total <= 20:
            los = "B"
        elif t_total <= 35:
            los = "C"
        elif t_total <= 55:
            los = "D"
        elif t_total <= 80:
            los = "E"
        else:
            los = "F"
        list_los.append(los)
        
    df_res["Waktu Hijau w_h (det)"] = list_w_h
    df_res["Kapasitas C (smp/jam)"] = list_c
    df_res["Derajat Kejenuhan (DJ)"] = list_dj
    df_res["Rasio Kend Henti (RKH)"] = list_rkh
    df_res["Jumlah Antrian NQ (smp)"] = list_nq
    df_res["Panjang Antrian PA (m)"] = list_pa
    df_res["Tundaan LL (det/smp)"] = list_tll
    df_res["Tundaan Geometri (det/smp)"] = list_tg
    df_res["Tundaan Total T (det/smp)"] = list_t
    df_res["LOS"] = list_los
    
    return df_res, df_konv, s_opt, w_hh, ras

# 4. FUNGSI GENERATE SIMULASI ANIMASI 2D PYTHON
def generate_simulasi_simpang_html(s_opt, df_res):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('#1C2541')
    ax.set_facecolor('#1C2541')
    
    ax.plot([-10, -2], [2, 2], color='#FFFFFF', lw=2)
    ax.plot([-10, -2], [-2, -2], color='#FFFFFF', lw=2)
    ax.plot([2, 10], [2, 2], color='#FFFFFF', lw=2)
    ax.plot([2, 10], [-2, -2], color='#FFFFFF', lw=2)
    ax.plot([-2, -2], [2, 10], color='#FFFFFF', lw=2)
    ax.plot([2, 2], [2, 10], color='#FFFFFF', lw=2)
    ax.plot([-2, -2], [-10, -2], color='#FFFFFF', lw=2)
    ax.plot([2, 2], [-10, -2], color='#FFFFFF', lw=2)
    
    car_u, = ax.plot([], [], 'ro', ms=10)
    car_s, = ax.plot([], [], 'ro', ms=10)
    car_t, = ax.plot([], [], 'ro', ms=10)
    car_b, = ax.plot([], [], 'ro', ms=10)
    
    light_u = ax.scatter([0], [3], c='red', s=100)
    light_s = ax.scatter([0], [-3], c='red', s=100)
    light_t = ax.scatter([3], [0], c='green', s=100)
    light_b = ax.scatter([-3], [0], c='green', s=100)
    
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.axis('off')
    ax.set_title("🎬 Animasi Pergerakan Lalu Lintas Simpang (2D)", color="#64DFDF")
    
    frames = 40
    def animate(i):
        if i % 20 < 10:
            light_u.set_color('green')
            light_s.set_color('green')
            light_t.set_color('red')
            light_b.set_color('red')
            
            y_pos = 10 - (i % 20) * 1.8
            car_u.set_data([0], [y_pos])
            car_s.set_data([0], [-y_pos])
            car_t.set_data([5], [0])
            car_b.set_data([-5], [0])
        else:
            light_u.set_color('red')
            light_s.set_color('red')
            light_t.set_color('green')
            light_b.set_color('green')
            
            x_pos = 10 - (i % 20 - 10) * 1.8
            car_u.set_data([0], [5])
            car_s.set_data([0], [-5])
            car_t.set_data([x_pos], [0])
            car_b.set_data([-x_pos], [0])
            
        return car_u, car_s, car_t, car_b, light_u, light_s, light_t, light_b

    ani = animation.FuncAnimation(fig, animate, frames=frames, interval=150, blit=True)
    html_out = ani.to_jshtml()
    plt.close()
    return html_out

# 5. HEADER & NAVIGASI 4 MODE
st.markdown("<h1 style='text-align: center;'>🌐 Kalkulator & Evaluasi Simpang APILL (PKJI 2023)</h1>", unsafe_allow_html=True)

mode = st.radio(
    "📌 Pilih Mode Fitur Aplikasi:",
    [
        "Mode 1: Konversi Kendaraan ke Satuan Mobil Penumpang (SMP)",
        "Mode 2: Analisis Kinerja Lengkap & Evaluasi Solusi",
        "Mode 3: Alternatif Simulasi Perbandingan (Before vs After)",
        "Mode 4: Kumpulan Rumus & Landasan Teori PKJI 2023"
    ],
    horizontal=True
)

st.divider()

# 6. SIDEBAR CONFIG
st.sidebar.header("⚙️ Sinyal & Geometri Simpang")
fase = st.sidebar.number_input("Jumlah Fase Sinyal", min_value=2, max_value=4, value=2)
w_k = st.sidebar.number_input("Waktu Kuning per Fase (detik)", min_value=1, value=3)
w_ms = st.sidebar.number_input("Waktu Merah Semua per Fase (detik)", min_value=1, value=2)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 Alokasi Fase Pendekat")
fase_utara = st.sidebar.selectbox("Fase Pendekat Utara", options=[1, 2, 3, 4], index=0)
fase_selatan = st.sidebar.selectbox("Fase Pendekat Selatan", options=[1, 2, 3, 4], index=0)
fase_timur = st.sidebar.selectbox("Fase Pendekat Timur", options=[1, 2, 3, 4], index=1 if fase >= 2 else 0)
fase_barat = st.sidebar.selectbox("Fase Pendekat Barat", options=[1, 2, 3, 4], index=1 if fase >= 2 else 0)

map_fase = {"Utara": fase_utara, "Selatan": fase_selatan, "Timur": fase_timur, "Barat": fase_barat}

# ==============================================================================
# MODE 1: KONVERSI KENDARAAN KE SMP
# ==============================================================================
if mode == "Mode 1: Konversi Kendaraan ke Satuan Mobil Penumpang (SMP)":
    st.subheader("🚙 Fitur Konversi Arus Kendaraan Real ke Satuan Mobil Penumpang (SMP/jam)")
    st.info("💡 **Catatan**: Data tersimpan otomatis ke Mode 2 & Mode 3 (Before):")
    
    df_edited_m1 = st.data_editor(st.session_state.df_global_input, num_rows="fixed", use_container_width=True, key="m1_editor")
    st.session_state.df_global_input = df_edited_m1.copy()
    
    if st.button("🔄 Proses Konversi ke SMP/jam", type="primary", use_container_width=True):
        df_res, df_konv, s_opt, w_hh, ras = hitung_pkji_simpang_lengkap(st.session_state.df_global_input, w_k, w_ms, fase, map_fase)
        
        st.divider()
        st.subheader("📊 Tabel Hasil Konversi Arus Lalu Lintas (Form SA-II PKJI 2023)")
        st.dataframe(df_konv, use_container_width=True)
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('#1C2541')
        ax.set_facecolor('#1C2541')
        
        p1 = ax.bar(df_konv["Pendekat"], df_konv["MP (smp/jam)"], label='Mobil Penumpang (MP)', color='#457B9D')
        p2 = ax.bar(df_konv["Pendekat"], df_konv["KB (smp/jam)"], bottom=df_konv["MP (smp/jam)"], label='Kendaraan Berat (KB)', color='#E07A5F')
        p3 = ax.bar(df_konv["Pendekat"], df_konv["SM (smp/jam)"], bottom=df_konv["MP (smp/jam)"]+df_konv["KB (smp/jam)"], label='Sepeda Motor (SM)', color='#64DFDF')
        
        ax.set_ylabel("Volume (smp/jam)", color="#FFFFFF")
        ax.set_title("Kontribusi Jenis Kendaraan terhadap Arus Total (smp/jam)", color="#64DFDF")
        ax.legend()
        ax.grid(axis='y', linestyle=':', alpha=0.3)
        st.pyplot(fig)

# ==============================================================================
# MODE 2: ANALISIS KINERJA LENGKAP & EVALUASI SOLUSI
# ==============================================================================
elif mode == "Mode 2: Analisis Kinerja Lengkap & Evaluasi Solusi":
    st.subheader("📋 Input Geometri & Volume Lalu Lintas (Tersambung dari Mode 1)")
    
    df_edited_m2 = st.data_editor(st.session_state.df_global_input, num_rows="fixed", use_container_width=True, key="m2_editor")
    st.session_state.df_global_input = df_edited_m2.copy()
    
    if st.button("🚀 Hitung & Evaluasi Kinerja Simpang Lengkap", type="primary", use_container_width=True):
        df_res, df_konv, s_opt, w_hh, ras = hitung_pkji_simpang_lengkap(st.session_state.df_global_input, w_k, w_ms, fase, map_fase)
        
        st.divider()
        st.subheader("📊 Ringkasan Indikator Sinyal & Kinerja Simpang")
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Waktu Siklus (s)", f"{s_opt:.1f} detik")
        m2.metric("Waktu Hilang (W_HH)", f"{w_hh} detik")
        m3.metric("Rasio Arus Simpang (RAS)", f"{ras:.3f}")
        
        q_total_simpang = df_res["q Total (smp/jam)"].sum()
        m4.metric("Arus Total Simpang", f"{q_total_simpang:.1f} smp/jam")
        
        dj_max = df_res["Derajat Kejenuhan (DJ)"].max()
        pendekat_kritis = df_res.loc[df_res["Derajat Kejenuhan (DJ)"].idxmax(), "Pendekat"]
        los_worst = df_res.loc[df_res["Derajat Kejenuhan (DJ)"].idxmax(), "LOS"]
        m5.metric("DJ Max & LOS Simpang", f"{dj_max:.3f} (LOS {los_worst})")
        
        st.subheader("📑 Rekapitulasi Perhitungan Kinerja Simpang (Form SA-I s.d SA-V)")
        st.dataframe(df_res, use_container_width=True)
        
        st.divider()
        col_anim1, col_anim2 = st.columns([1, 1])
        
        with col_anim1:
            st.subheader("📈 Grafik Kinerja Simpang")
            plt.style.use('dark_background')
            fig, axes = plt.subplots(3, 1, figsize=(6, 8))
            fig.patch.set_facecolor('#1C2541')
            for ax in axes:
                ax.set_facecolor('#1C2541')
                
            colors_dj = ['#64DFDF' if x <= 0.85 else '#E07A5F' for x in df_res["Derajat Kejenuhan (DJ)"]]
            axes[0].bar(df_res["Pendekat"], df_res["Derajat Kejenuhan (DJ)"], color=colors_dj)
            axes[0].axhline(0.85, color='#E07A5F', linestyle='--')
            axes[0].set_title("Derajat Kejenuhan (DJ)", color="#64DFDF")
            
            axes[1].bar(df_res["Pendekat"], df_res["Panjang Antrian PA (m)"], color='#457B9D')
            axes[1].set_title("Panjang Antrian PA (m)", color="#64DFDF")
            
            axes[2].bar(df_res["Pendekat"], df_res["Tundaan Total T (det/smp)"], color='#A3CEF1')
            axes[2].set_title("Tundaan Total T (det/smp)", color="#64DFDF")
            st.pyplot(fig)

        with col_anim2:
            st.subheader("🎬 Simulasi Visual Pergerakan Sinyal")
            html_sim = generate_simulasi_simpang_html(s_opt, df_res)
            st.components.v1.html(html_sim, height=500)

        st.divider()
        st.subheader("🧐 Evaluasi Kelayakan & Rekomendasi Solusi Rekayasa")
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            st.markdown("### 🚦 Kelayakan Penggunaan APILL")
            if q_total_simpang < 500:
                st.error("❌ **TIDAK COCOK DIGUNAKAN APILL**")
                st.write(f"• Total arus simpang terlalu rendah ({q_total_simpang:.1f} smp/jam < 500 smp/jam).")
                st.write("• **Saran**: Cukup gunakan **Simpang Tak Ber-APILL** (Prioritas/Stop) atau buat Bundaran.")
            elif ras >= 0.90 or dj_max > 0.85:
                st.warning("⚠️ **APILL KURANG EFEKTIF (KONDISI OVERCAPACITY)**")
                st.write(f"• Rasio Arus Simpang (RAS = {ras:.3f}) mendekati/melebihi batas jenuh (0.85).")
                st.write("• Diperlukan perbaikan geometri/manajemen lalu lintas tambahan.")
            else:
                st.success("✅ **SANGAT COCOK DIGUNAKAN APILL**")
                st.write(f"• Total arus memadai ({q_total_simpang:.1f} smp/jam) dan Rasio Arus aman (RAS = {ras:.3f} < 0.85).")

        with col_e2:
            st.markdown("### 💡 Rekomendasi Solusi Rekayasa")
            if dj_max <= 0.85 and los_worst in ["A", "B", "C"]:
                st.success("🎉 **Kinerja Simpang Sangat Baik** (Tidak perlu perubahan mayor).")
            else:
                st.error(f"🚨 **Kinerja Simpang BURUK (LOS {los_worst} / DJ Max = {dj_max:.3f})**")
                st.write("1. **Optimasi Waktu Hijau**: Alokasikan waktu hijau lebih lama pada pendekat kritis.")
                st.write("2. **Pelebaran Geometri**: Perlebar lajur pada pendekat dengan DJ tinggi.")
                st.write("3. **Belok Kiri Jalan Terus (LTOR)**: Terapkan aturan LTOR untuk kurangi antrean.")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_edited_m2.to_excel(writer, sheet_name='Input Data', index=False)
            df_res.to_excel(writer, sheet_name='Hasil Kinerja PKJI 2023', index=False)
            
        st.download_button(
            label="📥 Unduh Laporan Excel PKJI 2023 (.xlsx)",
            data=buffer.getvalue(),
            file_name="Laporan_Kinerja_Simpang_PKJI2023.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ==============================================================================
# MODE 3: ALTERNATIF SIMULASI PERBANDINGAN (BEFORE VS AFTER)
# ==============================================================================
elif mode == "Mode 3: Alternatif Simulasi Perbandingan (Before vs After)":
    st.subheader("📋 1. Input Data Eksisting (Kondisi Before - Tersambung dari Mode 1)")
    df_edited_before = st.data_editor(st.session_state.df_global_input, num_rows="fixed", use_container_width=True, key="m3_before")
    st.session_state.df_global_input = df_edited_before.copy()
    
    st.subheader("🛠️ 2. Input Skenario Usulan Rekayasa (Kondisi After)")
    df_edited_after = st.data_editor(df_edited_before.copy(), num_rows="fixed", use_container_width=True, key="m3_after")
    
    if st.button("🚀 Jalankan Perhitungan & Simulasi Before-After", type="primary", use_container_width=True):
        df_res_b, df_k_b, s_opt_b, w_hh_b, ras_b = hitung_pkji_simpang_lengkap(df_edited_before, w_k, w_ms, fase, map_fase)
        df_res_a, df_k_a, s_opt_a, w_hh_a, ras_a = hitung_pkji_simpang_lengkap(df_edited_after, w_k, w_ms, fase, map_fase)
        
        st.divider()
        st.subheader("📊 Tabel Komparasi Parameter Kinerja Lengkap per Pendekat")
        
        dj_b = df_res_b["Derajat Kejenuhan (DJ)"].max()
        dj_a = df_res_a["Derajat Kejenuhan (DJ)"].max()
        los_b = df_res_b.loc[df_res_b["Derajat Kejenuhan (DJ)"].idxmax(), "LOS"]
        los_a = df_res_a.loc[df_res_a["Derajat Kejenuhan (DJ)"].idxmax(), "LOS"]
        t_b_avg = df_res_b["Tundaan Total T (det/smp)"].mean()
        t_a_avg = df_res_a["Tundaan Total T (det/smp)"].mean()
        
        df_comp = pd.DataFrame({
            "Pendekat": df_res_b["Pendekat"],
            "Arus q (smp/jam)": df_res_b["q Total (smp/jam)"],
            "C (Before)": df_res_b["Kapasitas C (smp/jam)"],
            "C (After)": df_res_a["Kapasitas C (smp/jam)"],
            "DJ (Before)": df_res_b["Derajat Kejenuhan (DJ)"],
            "DJ (After)": df_res_a["Derajat Kejenuhan (DJ)"],
            "PA Before (m)": df_res_b["Panjang Antrian PA (m)"],
            "PA After (m)": df_res_a["Panjang Antrian PA (m)"],
            "Tundaan Before": df_res_b["Tundaan Total T (det/smp)"],
            "Tundaan After": df_res_a["Tundaan Total T (det/smp)"],
            "LOS (Before)": df_res_b["LOS"],
            "LOS (After)": df_res_a["LOS"]
        })
        
        st.dataframe(df_comp, use_container_width=True)
        
        plt.style.use('dark_background')
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor('#1C2541')
        for ax in axes:
            ax.set_facecolor('#1C2541')
            
        x = np.arange(len(df_res_b["Pendekat"]))
        width = 0.35
        
        axes[0].bar(x - width/2, df_res_b["Derajat Kejenuhan (DJ)"], width, label='Before (Eksisting)', color='#E07A5F')
        axes[0].bar(x + width/2, df_res_a["Derajat Kejenuhan (DJ)"], width, label='After (Rekayasa)', color='#64DFDF')
        axes[0].axhline(0.85, color='#E07A5F', linestyle='--', label='Batas Kritis (DJ = 0.85)')
        axes[0].set_title("Perbandingan Derajat Kejenuhan (DJ)", color="#64DFDF")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(df_res_b["Pendekat"])
        axes[0].legend()
        axes[0].grid(axis='y', linestyle=':', alpha=0.3)
        
        axes[1].bar(x - width/2, df_res_b["Tundaan Total T (det/smp)"], width, label='Before (Eksisting)', color='#457B9D')
        axes[1].bar(x + width/2, df_res_a["Tundaan Total T (det/smp)"], width, label='After (Rekayasa)', color='#A3CEF1')
        axes[1].set_title("Perbandingan Tundaan Total (det/smp)", color="#64DFDF")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(df_res_b["Pendekat"])
        axes[1].legend()
        axes[1].grid(axis='y', linestyle=':', alpha=0.3)
        
        st.pyplot(fig)

        st.divider()
        st.subheader("⚖️ Pertimbangan & Keputusan Skenario Terbaik")
        
        eval_col1, eval_col2 = st.columns(2)
        
        with eval_col1:
            st.markdown("### 📌 Penilaian Kelayakan Skenario")
            if dj_a <= 0.85 and (los_a in ["A", "B", "C", "D"]):
                st.success("✅ **SKENARIO REKAYASA (AFTER) SANGAT DIREKOMENDASIKAN**")
                st.write(f"• Usulan berhasil menurunkan derajat kejenuhan di bawah kriteria kritis PKJI ($DJ = {dj_a:.3f} \\le 0.85$).")
                st.write(f"• Tingkat pelayanan simpang membaik menjadi **LOS {los_a}**.")
            elif dj_a < dj_b:
                st.warning("⚠️ **SKENARIO REKAYASA MEMBAIK TAPI BELUM OPTIMAL**")
                st.write(f"• Terdapat perbaikan kinerja ($DJ$ turun menjadi {dj_a:.3f}), namun masih melampaui batas kritis 0.85.")
            else:
                st.error("❌ **SKENARIO REKAYASA TIDAK EFEKTIF**")
                st.write("• Perubahan yang dilakukan tidak memberikan efisiensi penurunan kemacetan.")

        with eval_col2:
            st.markdown("### 🎯 Ringkasan Keputusan Analisis")
            st.write(f"1. **Pilihan Utama:** Skenario **{'After (Rekayasa Usulan)' if dj_a < dj_b else 'Before (Eksisting)'}** lebih unggul.")
            st.write(f"2. **Efisiensi Tundaan:** Penghematan waktu tundaan rata-rata kendaraan mencapai **{max(0, t_b_avg - t_a_avg):.1f} detik/kendaraan**.")
            st.write(f"3. **Perubahan Tingkat Pelayanan:** Transisi Grade dari **LOS {los_b}** $\\rightarrow$ **LOS {los_a}**.")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_comp.to_excel(writer, sheet_name='Komparasi Parameter Lengkap', index=False)
            df_res_b.to_excel(writer, sheet_name='Kondisi Before', index=False)
            df_res_a.to_excel(writer, sheet_name='Kondisi After', index=False)
            
        st.download_button(
            label="📥 Unduh Laporan Perbandingan Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="Laporan_Simulasi_BeforeAfter_PKJI2023.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ==============================================================================
# MODE 4: KUMPULAN RUMUS & LANDASAN TEORI PKJI 2023 (FITUR BARU)
# ==============================================================================
else:
    st.subheader("📚 Kumpulan Rumus & Landasan Teori Analisis Simpang APILL (PKJI 2023)")
    st.info("Klik pada tombol ekspander di bawah untuk melihat rincian rumus matematis, variabel, dan penjelasan teknisnya:")
    
    # 1. Konversi Arus Kendaraan
    with st.expander("🔍 1. Konversi Arus Kendaraan ke Satuan Mobil Penumpang (smp/jam)"):
        st.latex(r"q = (Q_{MP} \times EMP_{MP}) + (Q_{KB} \times EMP_{KB}) + (Q_{SM} \times EMP_{SM})")
        st.markdown("""
        **Penjelasan Variabel:**
        * $q$ = Arus lalu lintas total dalam Satuan Mobil Penumpang per jam ($smp/jam$).
        * $Q_{MP}, Q_{KB}, Q_{SM}$ = Volume kendaraan nyata per jenis (Mobil Penumpang, Kendaraan Berat, Sepeda Motor) dalam $kendaraan/jam$.
        * $EMP$ = Ekivalen Mobil Penumpang sesuai PKJI 2023:
          * MP = $1,0$
          * KB = $1,3$
          * SM = $0,2$ (Tipe Pendekat Terlindung) / $0,4$ (Tipe Pendekat Terlawan).
        """)

    # 2. Arus Jenuh Dasar & Tersesuaikan
    with st.expander("🔍 2. Arus Jenuh Dasar (J0) & Tersesuaikan (J)"):
        st.latex(r"J_0 = 600 \times L_E \quad \text{(Tipe Protected / Terlindung)}")
        st.latex(r"J_0 = 500 \times L_E \quad \text{(Tipe Opposed / Terlawan)}")
        st.latex(r"J = J_0 \times F_{HS} \times F_{UK} \times F_{G} \times F_{P}")
        st.markdown("""
        **Penjelasan Variabel:**
        * $J_0$ = Arus jenuh dasar ($smp/jam$ hijau).
        * $L_E$ = Lebar efektif pendekat ($meter$).
        * $J$ = Arus jenuh tersesuaikan hasil perkalian faktor koreksi hambatan samping ($F_{HS}$), ukuran kota ($F_{UK}$), kelandaian ($F_{G}$), dan parkir ($F_{P}$).
        """)

    # 3. Waktu Siklus Webster
    with st.expander("🔍 3. Waktu Hilang Total (W_HH) & Waktu Siklus Optimum Webster (s)"):
        st.latex(r"W_{HH} = \sum (w_k + w_{ms})")
        st.latex(r"s_{opt} = \frac{1,5 \times W_{HH} + 5}{1 - RAS}")
        st.markdown("""
        **Penjelasan Variabel:**
        * $W_{HH}$ = Waktu hilang total dalam satu siklus ($detik$).
        * $w_k, w_{ms}$ = Waktu kuning dan waktu merah semua per fase ($detik$).
        * $RAS$ = Rasio Arus Simpang, yaitu jumlah Rasio Arus Kritis ($FR_{kritis}$) seluruh fase ($\sum FR_{kritis}$).
        * $s_{opt}$ = Waktu siklus optimum metode Webster ($detik$), dibatasi antara $30$ s.d. $180$ detik sesuai PKJI.
        """)

    # 4. Waktu Hijau & Kapasitas
    with st.expander("🔍 4. Waktu Hijau Efektif (w_h) & Kapasitas (C)"):
        st.latex(r"w_{h} = \frac{FR_{kritis}}{RAS} \times (s - W_{HH})")
        st.latex(r"C = J \times \frac{w_h}{s}")
        st.markdown("""
        **Penjelasan Variabel:**
        * $w_h$ = Waktu hijau efektif untuk suatu pendekat ($detik$).
        * $C$ = Kapasitas pendekat simpang ($smp/jam$).
        * $s$ = Waktu siklus yang ditetapkan ($detik$).
        """)

    # 5. Derajat Kejenuhan & Antrian
    with st.expander("🔍 5. Derajat Kejenuhan (DJ) & Panjang Antrian (PA)"):
        st.latex(r"DJ = \frac{q}{C}")
        st.latex(r"NQ_1 = 0,25 \times s \times \left( (DJ - 1) + \sqrt{(DJ - 1)^2 + \frac{8 \times (DJ - 0,5)}{s}} \right)")
        st.latex(r"PA = \frac{NQ_{total} \times 20}{N_{lajur}}")
        st.markdown("""
        **Penjelasan Variabel:**
        * $DJ$ = Derajat Kejenuhan. Nilai kritis menurut PKJI 2023 adalah $DJ > 0,85$.
        * $NQ_1$ = Jumlah antrian $smp$ sisa dari siklus sebelumnya.
        * $PA$ = Panjang Antrian ($meter$), mengasumsikan ruang rata-rata per $smp$ adalah $20\,m^2/N_{lajur}$.
        """)

    # 6. Tundaan & Tingkat Pelayanan (LOS)
    with st.expander("🔍 6. Tundaan Total (T) & Determination Level of Service (LOS)"):
        st.latex(r"T = T_{LL} + T_G")
        st.markdown("""
        **Kriteria Standar LOS Simpang APILL (PKJI 2023):**
        | Level of Service (LOS) | Tundaan Total T (detik/smp) | Keterangan Kondisi Operasional |
        | :---: | :---: | :--- |
        | **A** | $T \le 10$ | Sangat Baik, bebas dari hambatan. |
        | **B** | $10 < T \le 20$ | Baik, arus stabil dan waktu tunggu pendek. |
        | **C** | $20 < T \le 35$ | Sedang, hambatan mulai terasa. |
        | **D** | $35 < T \le 55$ | Kurang Baik, antrian mulai memanjang. |
        | **E** | $55 < T \le 80$ | Buruk, mendekati kapasitas maksimum. |
        | **F** | $T > 80$ | Sangat Buruk, kemacetan parah / *overcapacity*. |
        """)