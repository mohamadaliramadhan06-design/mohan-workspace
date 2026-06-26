import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd
import requests
import json

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Harian Keuangan", page_icon="💰", layout="centered")

# =========================================================================
# ⚠️ PENTING: Ganti teks di bawah ini dengan tautan Web App dari Apps Script Anda!
# Contoh: "https://script.google.com/macros/s/XXXXX/exec"
API_URL = "https://script.google.com/macros/s/AKfycbypT6phRMzXpRux-ieLG8FsMK6DJvKE9R4gKFBGHvT1x0iVa_akeMhAVSIwyoSZFOQQMA/exec"
# =========================================================================

# Inisialisasi Koneksi Membaca (Read) via Streamlit
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Gagal menyambungkan ke Google Sheets. Detail: {e}")

# Fungsi Menyimpan Data via Google Apps Script
def simpan_ke_gsheet(nama_tab, data_baris):
    if API_URL == "PASTE_URL_WEB_APP_ANDA_DISINI" or not API_URL:
        st.error("Gagal mengirim data: API_URL Web App Apps Script belum dikonfigurasi di dalam kode Anda!")
        return False
    try:
        payload = {
            "sheetName": nama_tab,
            "rowData": data_baris
        }
        # Mengirimkan data dalam bentuk JSON POST ke Apps Script
        response = requests.post(API_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            try:
                res_data = response.json()
                if res_data.get("status") == "success":
                    st.cache_data.clear() # Bersihkan cache agar data terbaru langsung tampil
                    return True
                else:
                    st.error(f"Apps Script menolak penyimpanan. Detail: {res_data.get('message')}")
            except Exception:
                # Jika Apps Script sukses merespon tapi tidak mengirim JSON (biasanya karena salah setup deployment)
                st.warning("Data dikirim, namun respon dari Apps Script tidak berformat JSON standar.")
                st.cache_data.clear()
                return True
        else:
            st.error(f"Gagal menyimpan! Web App Apps Script merespon dengan Status Code: {response.status_code}")
        return False
    except Exception as e:
        st.error(f"Gagal menghubungi API Web App Apps Script. Masalah Teknis: {e}")
        return False

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
                try:
                    df_users = conn.read(worksheet="Users")
                    user_found = False
                    
                    if df_users is not None and not df_users.empty:
                        df_users.columns = df_users.columns.str.strip().str.lower()
                        
                        if "username" in df_users.columns and "password" in df_users.columns:
                            df_users["username"] = df_users["username"].astype(str).str.strip().str.lower()
                            df_users["password"] = df_users["password"].astype(str).str.strip()
                            
                            match = df_users[(df_users["username"] == user_input) & (df_users["password"] == pass_input)]
                            if not match.empty:
                                user_found = True
                    
                    if user_found:
                        st.session_state.logged_in = True
                        st.session_state.username = user_input
                        st.success(f"Selamat datang kembali, {user_input.capitalize()}!")
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")
                except Exception as e:
                    st.error(f"Gagal membaca database 'Users'. Masalah Teknis: {e}")
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
                    try:
                        try:
                            df_users = conn.read(worksheet="Users")
                            df_users.columns = df_users.columns.str.strip().str.lower()
                            username_exists = new_user in df_users["username"].astype(str).values
                        except Exception:
                            username_exists = False
                        
                        if username_exists:
                            st.error("Username sudah terpakai! Silakan gunakan nama lain.")
                        else:
                            # Mengirim data pendaftaran akun baru ke tab 'Users'
                            if simpan_ke_gsheet("Users", [str(new_user), str(new_pass)]):
                                st.success("Akun berhasil didaftarkan! Silakan kembali ke tab 'Login' di atas.")
                                st.balloons()
                            else:
                                st.error("Sistem gagal menulis ke Google Sheets melalui Apps Script.")
                                
                    except Exception as e:
                        st.error(f"Terjadi kendala sistem pendaftaran: {e}")
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
    
    try:
        df_all = conn.read(worksheet="Pengeluaran")
        
        if df_all is not None and not df_all.empty:
            df_all.columns = df_all.columns.str.strip()
            kolom_wajib = ["Username", "Hari", "Tanggal", "Bulan", "Nama Barang / Kebutuhan", "Harga (Rp)"]
            
            for k in kolom_wajib:
                if k not in df_all.columns:
                    df_all[k] = ""
                    
            df_all['index_asli'] = df_all.index
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
    except Exception as e:
        st.error(f"Gagal memuat riwayat pengeluaran: {e}")
