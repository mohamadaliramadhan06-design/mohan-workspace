import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import json

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Harian Keuangan", page_icon="💰", layout="centered")

# =========================================================================
# 🎨 KUSTOMISASI LATAR BELAKANG WARNA SOLID (BIRU ELEGAN)
# =========================================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6f0fa;
    }
    [data-testid="stSidebar"] {
        background-color: #f0f4f8;
    }
    div.stButton > button:first-child {
        border-radius: 8px;
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
    st.title("🔐 Akses Sistem Keuangan")
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

    # 2. SIDEBAR
    st.sidebar.title(f"👤 Akun: {st.session_state.username.capitalize()}")
    st.sidebar.markdown("---")
    
    # Tampilkan info ringkas saldo di sidebar agar sinkron dengan tengah
    st.sidebar.metric(label="💰 Sisa Saldo Anda", value=f"Rp {saldo_sekarang:,.0f}".replace(",", "."))
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout/Keluar Akun"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    # 3. HALAMAN UTAMA
    st.title(f"💰 Harian Keuangan: {st.session_state.username.capitalize()}")
    st.write("Catat keuangan pribadi Anda langsung ke cloud.")
    st.markdown("---")
    
    # Dashboard Utama yang Selalu Sinkron dan Akurat
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="📈 Total Uang Masuk (Pemasukan)", value=f"Rp {total_pemasukan:,.0f}".replace(",", "."))
    with col_m2:
        st.metric(label="📉 Total Uang Keluar (Pengeluaran)", value=f"Rp {total_pengeluaran:,.0f}".replace(",", "."))
        
    st.markdown("---")
    
    # --- FORM INPUT TRANSAKSI BARU ---
    st.subheader("📝 Tambah Catatan Baru")
    
    jenis_transaksi = st.radio("Jenis Transaksi", ["📉 Pengeluaran", "📈 Pemasukan"], horizontal=True)
    jenis_clean = "Pemasukan" if "Pemasukan" in jenis_transaksi else "Pengeluaran"
    
    # Definisi alternatif jika ada bagian kode lama di bawah yang mencari variabel 'jenis'
    jenis = jenis_clean
    
    tanggal_pilihan = st.date_input("Pilih Tanggal Transaksi", value=datetime.now().date())
    
    if jenis_clean == "Pemasukan":
        nama_barang = st.text_input("Sumber Pemasukan / Dana", placeholder="Contoh: Gaji Bulanan, Uang Saku, Pembagian Hasil")
    else:
        nama_barang = st.text_input("Nama Barang / Kebutuhan", placeholder="Contoh: Bensin, Makan Siang")
        
    harga = st.number_input("Nominal / Harga (Rp)", min_value=0, step=1000, value=0)
    
    if st.button("Simpan Transaksi", type="primary"):
        if nama_barang == "":
            st.error("Kolom keterangan/nama barang tidak boleh kosong!")
        elif harga <= 0:
            st.error("Nominal harus lebih dari 0!")
        elif jenis_clean == "Pengeluaran" and harga > saldo_sekarang:
            st.error(f"❌ Saldo tidak cukup! Sisa saldo Anda saat ini adalah Rp {saldo_sekarang:,.0f}".replace(",", "."))
        else:
            hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            hari = hari_indo[tanggal_pilihan.weekday()]
            tanggal_str = tanggal_pilihan.strftime("%Y-%m-%d")
            
            bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            bulan = bulan_indo[tanggal_pilihan.month - 1]
            
            data_transaksi = [str(st.session_state.username), str(hari), str(tanggal_str), str(bulan), str(nama_barang), int(harga), str(jenis_clean)]
            
            if simpan_ke_gsheet("Pengeluaran", data_transaksi):
                st.success(f"Berhasil disimpan sebagai {jenis_clean}: {nama_barang}")
                st.rerun()
            else:
                st.error("Gagal menyimpan data ke cloud.")

    # --- RIWAYAT & DAFTAR DATA ---
    st.markdown("---")
    st.subheader("📊 Riwayat & Kelola Transaksi")
    
    if df_all is not None and not df_all.empty and not df_user.empty:
        for idx, row in df_user.iterrows():
            nama_b = str(row['Nama Barang / Kebutuhan'])
            tgl_b = str(row['Tanggal'])
            baris_target = row['baris_gsheet']
            j_tx = str(row['Jenis'])
            
            try:
                val_harga = str(row['Harga (Rp)']).split('.')[0].split(',')[0]
                harga_b = int(''.join(filter(str.isdigit, val_harga)))
            except:
                harga_b = 0
                
            simbol = "🟢 [Masuk]" if j_tx == "Pemasukan" else "🔴 [Keluar]"
                
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.write(f"📅 **{tgl_b}** | {simbol} {nama_b} — Rp {harga_b:,.0f}".replace(",", "."))
            with col_del:
                if st.button("🗑️ Hapus", key=f"del_{baris_target}"):
                    if hapus_dari_gsheet("Pengeluaran", baris_target):
                        st.success("Terhapus!")
                        st.rerun()
                    else:
                        st.error("Gagal!")
        st.markdown("---")
    else:
        if df_all is None or df_all.empty:
            st.info("Database transaksi di Google Sheets masih kosong.")
        else:
            st.info("Belum ada riwayat transaksi pada akun Anda.")
