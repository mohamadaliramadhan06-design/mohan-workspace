import streamlit as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os
from datetime import datetime
import pandas as pd
import hashlib

# Nama file database Excel harian
DB_FILE = "Database_Multiuser.xlsx"

def hash_password(password):
    """Mengubah password menjadi kode unik acak demi keamanan"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def inisialisasi_database():
    """Membuat file Excel database jika belum ada"""
    if not os.path.exists(DB_FILE):
        wb = openpyxl.Workbook()
        
        # Sheet 1: Data Akun User
        ws_users = wb.active
        ws_users.title = "Users"
        ws_users.append(["username", "password"])
        
        # Sheet 2: Data Pengeluaran Semua User
        ws_data = wb.create_sheet(title="Pengeluaran")
        headers = ["Username", "Hari", "Tanggal", "Bulan", "Nama Barang / Kebutuhan", "Harga (Rp)"]
        ws_data.append(headers)
        
        # Styling Header Pengeluaran
        dark_emerald = "1B4D3E"
        font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color=dark_emerald, end_color=dark_emerald, fill_type="solid")
        
        for col in range(1, 7):
            cell = ws_data.cell(row=1, column=col)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center")
            
        wb.save(DB_FILE)

# Jalankan inisialisasi database di awal
inisialisasi_database()

# --- PENGATURAN HALAMAN WEB ---
st.set_page_config(page_title="Aplikasi Keuangan Bersama", page_icon="💰", layout="centered")

# Menggunakan Session State Streamlit untuk melacak apakah user sudah login atau belum
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- HALAMAN BELUM LOGIN (LOGIN / REGISTRASI) ---
if not st.session_state.logged_in:
    st.title("🔐 Akses Sistem Keuangan")
    
    tab_login, tab_reg = st.tabs(["🔑 Login", "📝 Daftar Akun Baru"])
    
    # --- PROSES LOGIN ---
    with tab_login:
        st.subheader("Silakan Login")
        user_input = st.text_input("Username", key="login_user").strip().lower()
        pass_input = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Masuk", type="primary"):
            if user_input and pass_input:
                wb = openpyxl.load_workbook(DB_FILE)
                ws = wb["Users"]
                
                # Cari user di excel
                user_found = False
                for row in range(2, ws.max_row + 1):
                    db_user = ws.cell(row=row, column=1).value
                    db_pass = ws.cell(row=row, column=2).value
                    
                    if db_user == user_input and db_pass == hash_password(pass_input):
                        user_found = True
                        break
                
                if user_found:
                    st.session_state.logged_in = True
                    st.session_state.username = user_input
                    st.success(f"Selamat datang kembali, {user_input.capitalize()}!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
            else:
                st.warning("Semua kolom harus diisi!")

    # --- PROSES REGISTRASI ---
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
                    wb = openpyxl.load_workbook(DB_FILE)
                    ws = wb["Users"]
                    
                    # Cek apakah username sudah terpakai
                    username_exists = False
                    for row in range(2, ws.max_row + 1):
                        if ws.cell(row=row, column=1).value == new_user:
                            username_exists = True
                            break
                    
                    if username_exists:
                        st.error("Username sudah terpakai! Silakan cari nama lain.")
                    else:
                        # Simpan akun baru ke Excel
                        ws.append([new_user, hash_password(new_pass)])
                        wb.save(DB_FILE)
                        st.success("Akun berhasil dibuat! Silakan pindah ke tab Login.")
            else:
                st.warning("Semua kolom wajib diisi!")

# --- HALAMAN SETELAH BERHASIL LOGIN ---
else:
    # Header Aplikasi
    st.sidebar.title(f"👤 Akun: {st.session_state.username.capitalize()}")
    if st.sidebar.button("🚪 Logout/Keluar"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.title(f"💰 Dompet Digital: {st.session_state.username.capitalize()}")
    st.write("Catat pengeluaran pribadi Anda di bawah ini.")
    st.markdown("---")
    
    # Form Input Data
    nama_barang = st.text_input("Nama Barang / Kebutuhan", placeholder="Contoh: Nasi Goreng, Pulsa")
    harga = st.number_input("Harga (Rp)", min_value=0, step=1000, value=0)
    
    if st.button("Simpan Pengeluaran", type="primary"):
        if nama_barang == "":
            st.error("Nama barang tidak boleh kosong!")
        elif harga <= 0:
            st.error("Harga harus lebih dari 0!")
        else:
            # Ambil waktu otomatis
            sekarang = datetime.now()
            hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            hari = hari_indo[sekarang.weekday()]
            tanggal = sekarang.strftime("%Y-%m-%d")
            bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            bulan = bulan_indo[sekarang.month - 1]
            
            # Tulis ke lembar Pengeluaran Excel
            wb = openpyxl.load_workbook(DB_FILE)
            ws = wb["Pengeluaran"]
            
            # Tambahkan baris baru (Ada kolom username di paling depan)
            ws.append([st.session_state.username, hari, tanggal, bulan, nama_barang, harga])
            
            # Atur format uang rupiah di Excel
            row_terakhir = ws.max_row
            ws.cell(row=row_terakhir, column=6).number_format = '#,##0'
            
            wb.save(DB_FILE)
            st.success(f"Berhasil disimpan ke akun Anda: {nama_barang}")
            st.rerun()

    st.markdown("---")
    st.subheader("📊 Riwayat Pengeluaran Pribadi Anda")
    
    # Tampilkan data tabel, TETAPI di-filter hanya milik user yang sedang login
    try:
        df = pd.read_excel(DB_FILE, sheet_name="Pengeluaran")
        
        # Filter data berdasarkan username yang login
        df_user = df[df["Username"] == st.session_state.username]
        
        if not df_user.empty:
            # Hapus kolom username saat ditampilkan di web agar lebih privat
            df_display = df_user.drop(columns=["Username"])
            
            # Format tampilan mata uang rupiah
            df_display["Harga (Rp)"] = df_display["Harga (Rp)"].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
            
            # Tampilkan tabel di web
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Hitung total khusus user tersebut
            total_user = df_user["Harga (Rp)"].sum()
            st.metric(label="Total Pengeluaran Anda", value=f"Rp {total_user:,.0f}".replace(",", "."))
            
            # Tombol unduh data khusus milik user tersebut
            st.markdown("---")
            st.subheader("📂 Download Data Pribadi")
            
            # Ekspor hasil filter ke file excel sementara untuk didownload user
            file_download_name = f"Pengeluaran_{st.session_state.username}.xlsx"
            df_user.to_excel(file_download_name, index=False)
            
            with open(file_download_name, "rb") as file:
                st.download_button(
                    label="📥 Download Excel Pengeluaran Saya",
                    data=file,
                    file_name=file_download_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            # Hapus file sampah lokal setelah dibaca memori
            if os.path.exists(file_download_name):
                os.remove(file_download_name)
        else:
            st.info("Belum ada riwayat pengeluaran pada akun Anda.")
    except Exception as e:
        st.error("Belum ada database pengeluaran yang terbentuk.")
