import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd
import hashlib

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Aplikasi Keuangan Bersama", page_icon="💰", layout="centered")

# Inisialisasi Koneksi ke Google Sheets via TOML Secrets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Gagal menyambungkan ke Google Sheets. Pastikan link di Secrets sudah benar.")

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
                    df_users = conn.read(worksheet="Users", ttl=0)
                    user_found = False
                    
                    if not df_users.empty and "username" in df_users.columns:
                        # Cari kecocokan data
                        match = df_users[(df_users["username"] == user_input) & (df_users["password"] == hash_password(pass_input))]
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
                    st.error("Gagal membaca data akun di Google Sheets.")
            else:
                st.warning("Semua kolom harus diisi!")

    with tab_reg:
        st.subheader("Buat Akun Baru")
        new_user = st.text_input("Buat Username", key="reg_user").strip().lower()
        new_pass = st.text_input("Buat Password", type="password", key="reg_pass")
        confirm_pass = st.text_input("Konfirmasi Password", type="password", key="reg_pass_conf")
        
        if st.button("Daftar Sekarang"):
            if new_user and new_pass and confirm_pass:
                if new_pass != confirm_pass:
                    st.error("Konfirmasi password tidak cocok!")
                else:
                    try:
                        df_users = conn.read(worksheet="Users", ttl=0)
                        
                        username_exists = False
                        if not df_users.empty and "username" in df_users.columns:
                            if new_user in df_users["username"].values:
                                username_exists = True
                        
                        if username_exists:
                            st.error("Username sudah terpakai! Silakan gunakan nama lain.")
                        else:
                            # Tambah user baru ke dataframe dan update Google Sheets
                            new_row = pd.DataFrame([{"username": new_user, "password": hash_password(new_pass)}])
                            df_updated = pd.concat([df_users, new_row], ignore_index=True)
                            conn.update(worksheet="Users", data=df_updated)
                            st.success("Akun berhasil didaftarkan di Google Sheets! Silakan Login.")
                    except Exception as e:
                        st.error("Gagal mendaftarkan akun ke server.")
            else:
                st.warning("Semua kolom wajib diisi!")

# --- HALAMAN SETELAH BERHASIL LOGIN ---
else:
    st.sidebar.title(f"👤 Akun: {st.session_state.username.capitalize()}")
    if st.sidebar.button("🚪 Logout/Keluar"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.title(f"💰 Dompet Digital: {st.session_state.username.capitalize()}")
    st.write("Catat pengeluaran pribadi Anda langsung ke database cloud.")
    st.markdown("---")
    
    # Form Input Data
    nama_barang = st.text_input("Nama Barang / Kebutuhan", placeholder="Contoh: Beli Buku, Makan Siang")
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
            
            try:
                # Ambil data pengeluaran yang sudah ada di Google Sheets
                df_pengeluaran = conn.read(worksheet="Pengeluaran", ttl=0)
                
                # Masukkan data baru
                new_data = pd.DataFrame([{
                    "Username": st.session_state.username,
                    "Hari": hari,
                    "Tanggal": tanggal,
                    "Bulan": bulan,
                    "Nama Barang / Kebutuhan": nama_barang,
                    "Harga (Rp)": harga
                }])
                
                df_updated = pd.concat([df_pengeluaran, new_data], ignore_index=True)
                # Kirim balik ke Google Sheets
                conn.update(worksheet="Pengeluaran", data=df_updated)
                
                st.success(f"Berhasil disimpan ke Google Sheets: {nama_barang}")
                st.rerun()
            except Exception as e:
                st.error("Gagal menyimpan data ke Google Sheets.")

    st.markdown("---")
    st.subheader("📊 Riwayat & Kelola Pengeluaran Cloud")
    
    try:
        df_all = conn.read(worksheet="Pengeluaran", ttl=0)
        
        if not df_all.empty and "Username" in df_all.columns:
            # Filter data milik user aktif beserta penanda indeks barisnya
            df_all['index_asli'] = df_all.index
            df_user = df_all[df_all["Username"] == st.session_state.username]
            
            if not df_user.empty:
                total_user = 0
                for idx, row in df_user.iterrows():
                    index_target = row['index_asli']
                    nama_b = row['Nama Barang / Kebutuhan']
                    tgl_b = row['Tanggal']
                    harga_b = row['Harga (Rp)']
                    total_user += harga_b
                    
                    col_text, col_btn = st.columns([5, 1])
                    with col_text:
                        st.write(f"📅 **{tgl_b}** | {nama_b} — Rp {harga_b:,.0f}".replace(",", "."))
                    with col_btn:
                        if st.button("🗑️ Hapus", key=f"del_{index_target}"):
                            # Hapus data berdasarkan indeks baris, lalu perbarui Google Sheets
                            df_all_updated = df_all.drop(index_target).drop(columns=['index_asli'])
                            conn.update(worksheet="Pengeluaran", data=df_all_updated)
                            st.success("Data berhasil dihapus dari Google Sheets!")
                            st.rerun()
                            
                st.markdown("---")
                st.metric(label="Total Pengeluaran Anda Saat Ini", value=f"Rp {total_user:,.0f}".replace(",", "."))
            else:
                st.info("Belum ada riwayat pengeluaran pada akun Anda.")
        else:
            st.info("Database pengeluaran di Google Sheets masih kosong.")
    except Exception as e:
        st.error("Sedang menyinkronkan data dengan Google Sheets...")
