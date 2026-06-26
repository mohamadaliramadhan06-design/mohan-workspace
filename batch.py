import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import json

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Harian Keuangan", page_icon="💰", layout="centered")

# =========================================================================
# 🎨 KUSTOMISASI DESAIN ANTARMUKA MODERN DENGAN ANIMASI & TRANSISI
# =========================================================================
st.markdown(
    """
    <style>
    /* Mengimpor Font Modern */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Mengubah Latar Belakang Aplikasi & Font Global */
    .stApp {
        background-color: #f3f7fa;
        font-family: 'Poppins', sans-serif;
    }
    
    /* 🎬 ANIMASI TRANSISI HALAMAN (FADE-IN EFFECT) */
    @keyframes pageFadeIn {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Menerapkan transisi masuk ke seluruh blok konten utama */
    [data-testid="stVerticalBlock"] > div {
        animation: pageFadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    /* Mengubah Desain Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Desain Kartu Ringkasan (Card Dashboard) */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        border-left: 5px solid #3b82f6;
        margin-bottom: 15px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    .metric-card.pemasukan { border-left-color: #10b981; }
    .metric-card.pengeluaran { border-left-color: #ef4444; }
    
    .metric-title {
        font-size: 11px;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 5px;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 22px;
        color: #1e293b;
        font-weight: 700;
    }
    
    /* Desain Form Input Kontainer */
    .form-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 25px;
        border: 1px solid #e2e8f0;
    }
    
    /* ⚡ TRANSISI INTERAKTIF PADA ELEMEN INPUT STREAMLIT */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        transition: all 0.25s ease-in-out !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }
    
    /* 🎯 TRANSISI ANIMASI TOMBOL UTAMA (HOVER & ACTIVE EFFECT) */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        padding: 10px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    div.stButton > button:first-child:active {
        transform: translateY(1px);
    }
    
    /* Transisi khusus tombol hapus sampah agar tidak ikut melebar */
    div[data-testid="stHorizontalBlock"] div.stButton > button:first-child {
        width: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================
# ⚙️ CONFIGURATION
# =========================================================================
SPREADSHEET_ID = "19WepkG5jBNasCwIqH3ii4Yg1Cskyf_zB41M7G_MAlo0"
API_URL = "https://script.google.com/macros/s/AKfycbwr7TSnzbrdbK9qKVJUibcaZ4UfWfCbVm5BfExgbi6nqPbVGcrgelhdAa2RyzTN22hMQA/exec"

# Fungsi untuk Membaca Google Sheets
def baca_dari_gsheet(nama_tab):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nama_tab}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Gagal membaca tab '{nama_tab}'. Detail: {e}")
        return None

# Fungsi Menyimpan Data via Google Apps Script
def simpan_ke_gsheet(nama_tab, data_baris):
    try:
        payload = {
            "sheetName": nama_tab,
            "action": "INSERT",
            "rowData": data_baris
        }
        response = requests.post(API_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        return response.status_code == 200
    except Exception:
        return False

# Fungsi Menghapus Data
def hapus_dari_gsheet(nama_tab, nomor_baris_gsheet):
    try:
        payload = {
            "sheetName": nama_tab,
            "action": "DELETE",
            "rowIndex": int(nomor_baris_gsheet)
        }
        response = requests.post(API_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        return response.status_code == 200
    except Exception:
        return False

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- HALAMAN BELUM LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; margin-top: 30px;'>🔐 Akses Sistem Keuangan</h2>", unsafe_allow_html=True)
    tab_login, tab_reg = st.tabs(["🔑 Login", "📝 Daftar Akun Baru"])
    
    with tab_login:
        st.subheader("Silakan Login")
        user_input = st.text_input("Username", key="login_user").strip().lower()
        pass_input = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Masuk", type="primary"):
            if user_input and pass_input:
                df_users = baca_dari_gsheet("Users")
                user_found = False
                
                if df_users is not None and not df_users.empty:
                    df_users.columns = [str(col).strip().lower() for col in df_users.columns]
                    if "username" in df_users.columns and "password" in df_users.columns:
                        df_users["username"] = df_users["username"].astype(str).str.strip().str.lower()
                        df_users["password"] = df_users["password"].astype(str).str.strip()
                        
                        match = df_users[(df_users["username"] == user_input) & (df_users["password"] == str(pass_input))]
                        if not match.empty:
                            user_found = True
                
                if user_found:
                    st.session_state.logged_in = True
                    st.session_state.username = user_input
                    st.success(f"Selamat datang kembali, {user_input.capitalize()}!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
            else:
                st.warning("Semua kolom harus diisi!")

    with tab_reg:
        st.subheader("Buat Akun Baru")
        new_user = st.text_input("Buat Username", key="reg_user").strip().lower()
        new_pass = st.text_input("Buat Password", type="password", key="reg_pass")
        confirm_pass = st.text_input("Konfirmasi Password", type="password", key="reg_pass_conf")
        
        if st.button("Daftar Sekarang"):
            if new_user and new_pass and confirm_pass:
                if " " in new_user:
                    st.error("Username tidak boleh mengandung spasi!")
                elif new_pass != confirm_pass:
                    st.error("Konfirmasi password tidak cocok!")
                else:
                    df_users = baca_dari_gsheet("Users")
                    username_exists = False
                    
                    if df_users is not None and not df_users.empty:
                        df_users.columns = [str(col).strip().lower() for col in df_users.columns]
                        if "username" in df_users.columns:
                            username_exists = new_user in df_users["username"].astype(str).values
                    
                    if username_exists:
                        st.error("Username sudah terpakai! Silakan gunakan nama lain.")
                    else:
                        if simpan_ke_gsheet("Users", [str(new_user), str(new_pass)]):
                            st.success("Akun berhasil didaftarkan! Silakan login melalui tab 'Login'.")
                            st.balloons()
                        else:
                            st.error("Gagal menyimpan ke Google Sheets.")
            else:
                st.warning("Semua kolom wajib diisi!")

# --- HALAMAN SETELAH LOGIN ---
else:
    # 1. AMBIL DATA DAN HITUNG PEMASUKAN & PENGELUARAN SECARA REAL-TIME
    df_all = baca_dari_gsheet("Pengeluaran")
    total_pengeluaran = 0
    total_pemasukan = 0
    df_user = pd.DataFrame()
    
    if df_all is not None and not df_all.empty:
        df_all.columns = [str(col).strip() for col in df_all.columns]
        df_all['baris_gsheet'] = df_all.index + 2
        
        # Pengaman pembacaan kolom agar data lama tidak error
        kolom_wajib = ["Username", "Hari", "Tanggal", "Bulan", "Nama Barang / Kebutuhan", "Harga (Rp)"]
        for k in kolom_wajib:
            if k not in df_all.columns:
                df_all[k] = ""
                
        if "Jenis" not in df_all.columns:
            df_all["Jenis"] = "Pengeluaran"
                
        df_all_lower_user = df_all["Username"].astype(str).str.strip().str.lower()
        df_user = df_all[df_all_lower_user == str(st.session_state.username).lower()]
        
        if not df_user.empty:
            for idx, row in df_user.iterrows():
                try:
                    val_harga = str(row['Harga (Rp)']).split('.')[0].split(',')[0]
                    harga_b = int(''.join(filter(str.isdigit, val_harga)))
                except:
                    harga_b = 0
                
                # Cek jenis transaksi
                jenis_tx = str(row['Jenis']).strip()
                if jenis_tx == "Pemasukan":
                    total_pemasukan += harga_b
                else:
                    total_pengeluaran += harga_b

    # Hitung sisa saldo murni
    saldo_sekarang = total_pemasukan - total_pengeluaran
    saldo_format = f"Rp {saldo_sekarang:,.0f}".replace(",", ".")

    # 2. SIDEBAR DESAIN
    nama_user_cap = str(st.session_state.username).capitalize()
    st.sidebar.markdown(f"<h3 style='text-align: center; color: #1e293b;'>👤 Akun: {nama_user_cap}</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # Tampilkan info ringkas saldo berbentuk Box Elegan di Sidebar
    st.sidebar.markdown(
        f"""
        <div class='metric-card'>
            <div class='metric-title'>💰 SISA SALDO ANDA</div>
            <div class='metric-value'>{saldo_format}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout/Keluar Akun"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    # 3. HALAMAN UTAMA
    st.markdown(f"<h2>💰 Harian Keuangan: {nama_user_cap}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;'>Catat keuangan pribadi Anda langsung ke cloud secara terstruktur.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Dashboard Utama berbentuk Row Kartu Grid
    pemasukan_format = f"Rp {total_pemasukan:,.0f}".replace(",", ".")
    pengeluaran_format = f"Rp {total_pengeluaran:,.0f}".replace(",", ".")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            f"""
            <div class='metric-card pemasukan'>
                <div class='metric-title'>📈 TOTAL UANG MASUK (PEMASUKAN)</div>
                <div class='metric-value' style='color:#10b981;'>{pemasukan_format}</div>
            </div>
            """, unsafe_allow_html=True
        )
    with col_m2:
        st.markdown(
            f"""
            <div class='metric-card pengeluaran'>
                <div class='metric-title'>📉 TOTAL UANG KELUAR (PENGELUARAN)</div>
                <div class='metric-value' style='color:#ef4444;'>{pengeluaran_format}</div>
            </div>
            """, unsafe_allow_html=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- FORM INPUT TRANSAKSI BARU ---
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)
    st.subheader("📝 Tambah Catatan Baru")
    
    jenis_transaksi = st.radio("Jenis Transaksi", ["📉 Pengeluaran", "📈 Pemasukan"], horizontal=True)
    jenis_clean = "Pemasukan" if "Pemasukan" in jenis_transaksi else "Pengeluaran"
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tanggal_pilihan = st.date_input("Pilih Tanggal Transaksi", value=datetime.now().date())
    with col_f2:
        harga = st.number_input("Harga / Nominal (Rp)", min_value=0, step=1000, value=0)
        
    nama_barang = st.text_input("Nama Barang / Kebutuhan / Sumber Dana", placeholder="Contoh: Bensin, Makan Siang, Uang Saku")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Simpan Transaksi", type="primary"):
        if nama_barang == "":
            st.error("Keterangan transaksi tidak boleh kosong!")
        elif harga <= 0:
            st.error("Nominal transaksi harus lebih besar dari Rp 0!")
        elif jenis_clean == "Pengeluaran" and harga > saldo_sekarang:
            st.error(f"❌ Saldo tidak mencukupi! Sisa saldo Anda adalah {saldo_format}")
        else:
            # Hitung hari dan bulan otomatis dalam bahasa Indonesia
            hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            hari = hari_indo[tanggal_pilihan.weekday()]
            tanggal_str = tanggal_pilihan.strftime("%Y-%m-%d")
            
            bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            bulan = bulan_indo[tanggal_pilihan.month - 1]
            
            data_transaksi = [str(st.session_state.username), str(hari), str(tanggal_str), str(bulan), str(nama_barang), int(harga), str(jenis_clean)]
            
            if simpan_ke_gsheet("Pengeluaran", data_transaksi):
                st.success("Data berhasil disimpan ke cloud!")
                st.rerun()
            else:
                st.error("Gagal menyimpan ke Google Sheets.")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- RIWAYAT DATA BERGAYA KARTU ---
    st.markdown("<h3>📊 Riwayat & Kelola Pengeluaran</h3>", unsafe_allow_html=True)
    
    if df_all is not None and not df_all.empty and not df_user.empty:
        # Menampilkan data mulai dari yang paling baru dimasukkan (di-reverse)
        for idx, row in df_user.iloc[::-1].iterrows():
            nama_b = str(row['Nama Barang / Kebutuhan'])
            tgl_b = str(row['Tanggal'])
            baris_target = row['baris_gsheet']
            j_tx = str(row['Jenis'])
            
            try:
                val_harga = str(row['Harga (Rp)']).split('.')[0].split(',')[0]
                harga_b = int(''.join(filter(str.isdigit, val_harga)))
            except:
                harga_b = 0
                
            border_color = "#10b981" if j_tx == "Pemasukan" else "#ef4444"
            bg_badge = "#e6f4ea" if j_tx == "Pemasukan" else "#fce8e6"
            label_badge = "MASUK" if j_tx == "Pemasukan" else "KELUAR"
            tanda_minus = " " if j_tx == "Pemasukan" else "-"
            
            # Format harga ke IDR rupiah (Titik sebagai ribuan)
            harga_format = f"{tanda_minus}Rp {harga_b:,.0f}".replace(",", ".")
            
            col_box, col_action = st.columns([6, 1])
            with col_box:
                st.markdown(
                    f"""
                    <div style='background-color:#ffffff; padding:12px 18px; border-radius:10px; border-left: 4px solid {border_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:11px; background-color:{bg_badge}; color:{border_color}; padding:2px 8px; border-radius:12px; font-weight:700;'>{label_badge}</span>
                            <span style='font-size:12px; color:#64748b; margin-left:8px;'>📅 {tgl_b}</span>
                            <div style='font-weight:600; color:#1e293b; margin-top:4px; font-size:15px;'>{nama_b}</div>
                        </div>
                        <div style='font-size:16px; font-weight:700; color:{border_color};'>
                            {harga_format}
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )
            with col_action:
                st.markdown("<div style='margin-top: 8px;'>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{baris_target}"):
                    if hapus_dari_gsheet("Pengeluaran", baris_target):
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Belum ada riwayat pengeluaran pada akun Anda.")
