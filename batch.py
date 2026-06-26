import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import json

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Harian Keuangan", page_icon="💰", layout="centered")

# =========================================================================
# 🎨 KUSTOMISASI DESAIN ANTARMUKA MODERN (CUSTOM CSS)
# =========================================================================
st.markdown(
    """
    <style>
    /* Mengubah Latar Belakang Aplikasi */
    .stApp {
        background-color: #f3f7fa;
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
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border-left: 5px solid #3b82f6;
        margin-bottom: 15px;
    }
    .metric-card.pemasukan { border-left-color: #10b981; }
    .metric-card.pengeluaran { border-left-color: #ef4444; }
    
    .metric-title {
        font-size: 14px;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        color: #1e293b;
        font-weight: 700;
    }
    
    /* Desain Form Input Kontainer */
    .form-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 25px;
        border: 1px solid #e2e8f0;
    }
    
    /* Tombol Utama */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        padding: 10px;
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

    # Hitung sisa saldo murni dari matematika cloud
    saldo_sekarang = total_pemasukan - total_pengeluaran

    # 2. SIDEBAR DESAIN
    st.sidebar.markdown(f"<h3 style='text-align: center; color: #1e293b;'>👤 Akun: {st.session_state.username.capitalize()}</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # Tampilkan info ringkas saldo berbentuk Box Elegan di Sidebar
    st.sidebar.markdown(
        f"""
        <div class='metric-card'>
            <div class='metric-title'>💰 SISA SALDO ANDA</div>
            <div class='metric-value'>Rp {saldo_sekarang:,.0f}</div>
        </div>
        """.replace(",", "."), 
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout/Keluar Akun"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    # 3. HALAMAN UTAMA
    st.markdown(f"<h2>💰 Harian Keuangan: {st.session_state.
