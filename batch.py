import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import json

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Harian Keuangan", page_icon="💰", layout="centered")

# =========================================================================
# ⚠️ ISI KEDUA KONFIGURASI DI BAWAH INI DENGAN BENAR
# =========================================================================
# 1. Masukkan SPREADSHEET ID Anda (Ambil dari baris URL Google Sheets Anda)
# Contoh URL: https://docs.google.com/spreadsheets/d/1A2B3C4D5E6Fxxxxxxxxx/edit
# Ambil bagian kode acak di antara '/d/' dan '/edit'
SPREADSHEET_ID = "19WepkG5jBNasCwIqH3ii4Yg1Cskyf_zB41M7G_MAlo0"

# 2. Tautan Web App dari Apps Script Anda untuk menyimpan data
API_URL = "https://script.google.com/macros/s/AKfycbynIv_fv7E4lvAuVirI28ADe6uW8kRzUFr_f2xidjGg-77KIwZRdUd_xR8KKmEMFTlJSA/exec"
# =========================================================================

# Fungsi Pintar untuk Membaca Google Sheets Menggunakan Pandas (Bebas Error 400)
def baca_dari_gsheet(nama_tab):
    if SPREADSHEET_ID == "PASTE_ID_SPREADSHEET_ANDA_DISINI":
        st.error("SPREADSHEET_ID belum diisi di dalam kode!")
        return None
    try:
        # Menembak langsung ke fitur export CSV Google Sheets berdasarkan nama tab (sheet)
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nama_tab}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Gagal membaca tab '{nama_tab}'. Pastikan SPREADSHEET_ID benar. Detail: {e}")
        return None

# Fungsi Menyimpan Data via Google Apps Script
def simpan_ke_gsheet(nama_tab, data_baris):
    if API_URL == "PASTE_URL_WEB_APP_ANDA_DISINI" or not API_URL:
        st.error("Gagal mengirim data: API_URL Web App Apps Script belum dikonfigurasi!")
        return False
    try:
        payload = {
            "sheetName": nama_tab,
            "rowData": data_baris
        }
        response = requests.post(API_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        st.error(f"Gagal menghubungi Apps Script: {e}")
        return False

# Inisialisasi Session State Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- HALAMAN BELUM LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Akses Sistem Keuangan")
    tab_login, tab_reg = st.tabs(["🔑 Login", "📝 Daftar Akun Baru"])
    
    with tab_login:
        st.subheader("Silakan Login")
        user_input = st.text_input("Username", key="login_user").strip().lower()
        pass_input = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Masuk", type="primary"):
            if user_input and pass_input:
                # Membaca data secara aman tanpa st-gsheets-connection
                df_users = baca_dari_gsheet("Users")
                user_found = False
                
                if df_users is not None and not df_users.empty:
                    # Normalisasi nama kolom menjadi huruf kecil semua agar tidak sensitif
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
                            st.error("Gagal menyimpan ke Google Sheets. Periksa URL Apps Script Anda.")
            else:
                st.warning("Semua kolom wajib diisi!")

# --- HALAMAN SETELAH BERHASIL LOGIN ---
else:
    st.sidebar.title(f"👤 Akun: {st.session_state.username.capitalize()}")
    if st.sidebar.button("🚪 Logout/Keluar"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.title(f"💰 Harian Keuangan: {st.session_state.username.capitalize()}")
    st.write("Catat pengeluaran pribadi Anda langsung ke cloud.")
    st.markdown("---")
    
    nama_barang = st.text_input("Nama Barang / Kebutuhan", placeholder="Contoh: Bensin, Makan Siang")
    harga = st.number_input("Harga (Rp)", min_value=0, step=1000, value=0)
    
    if st.button("Simpan Pengeluaran", type="primary"):
        if nama_barang == "":
            st.error("Nama barang tidak boleh kosong!")
        elif harga <= 0:
            st.error("Harga harus lebih dari 0!")
        else:
            sekarang = datetime.now()
            hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            hari = hari_indo[sekarang.weekday()]
            tanggal = sekarang.strftime("%Y-%m-%d")
            bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            bulan = bulan_indo[sekarang.month - 1]
            
            data_pengeluaran = [str(st.session_state.username), str(hari), str(tanggal), str(bulan), str(nama_barang), int(harga)]
            
            if simpan_ke_gsheet("Pengeluaran", data_pengeluaran):
                st.success(f"Berhasil disimpan: {nama_barang}")
                st.rerun()
            else:
                st.error("Gagal menyimpan data pengeluaran ke cloud.")

    st.markdown("---")
    st.subheader("📊 Riwayat & Kelola Pengeluaran")
    
    df_all = baca_dari_gsheet("Pengeluaran")
    
    if df_all is not None and not df_all.empty:
        df_all.columns = [str(col).strip() for col in df_all.columns]
        kolom_wajib = ["Username", "Hari", "Tanggal", "Bulan", "Nama Barang / Kebutuhan", "Harga (Rp)"]
        
        for k in kolom_wajib:
            if k not in df_all.columns:
                df_all[k] = ""
                
        df_all_lower_user = df_all["Username"].astype(str).str.strip().str.lower()
        df_user = df_all[df_all_lower_user == str(st.session_state.username).lower()]
        
        if not df_user.empty:
            total_user = 0
            for idx, row in df_user.iterrows():
                nama_b = str(row['Nama Barang / Kebutuhan'])
                tgl_b = str(row['Tanggal'])
                
                try:
                    val_harga = str(row['Harga (Rp)']).split('.')[0].split(',')[0]
                    harga_b = int(''.join(filter(str.isdigit, val_harga)))
                except:
                    harga_b = 0
                    
                total_user += harga_b
                st.write(f"📅 **{tgl_b}** | {nama_b} — Rp {harga_b:,.0f}".replace(",", "."))
                        
            st.markdown("---")
            st.metric(label="Total Pengeluaran Anda Saat Ini", value=f"Rp {total_user:,.0f}".replace(",", "."))
        else:
            st.info("Belum ada riwayat pengeluaran pada akun Anda.")
    else:
        st.info("Database pengeluaran di Google Sheets masih kosong.")
