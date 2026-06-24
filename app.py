import streamlit as st
import pandas as pd
import cv2
import numpy as np
import os
from datetime import datetime
from PIL import Image

# 1. Pengaturan Tampilan Awal Website
st.set_page_config(page_title="Presensi QR RT & Ekskul", page_icon="📱", layout="centered")

# --- KODE CSS UNTUK MEMPERBESAR TAMPILAN ELEMENT DI HP ---
st.markdown("""
    <style>
    /* Memperbesar teks input nama */
    .stTextInput input {
        font-size: 20px !important;
        height: 50px !important;
    }
    /* Memperbesar tombol kirim kehadiran agar ramah jempol */
    .stButton button {
        font-size: 20px !important;
        height: 50px !important;
        width: 100% !important;
        background-color: #FF4B4B !important;
        color: white !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Web Presensi QR Code")
st.write("Gunakan kamera HP Anda untuk memfoto QR Code Kegiatan, lalu upload di bawah ini.")

# Membuat folder penyimpanan data secara lokal jika belum ada
if not os.path.exists("laporan_web"):
    os.makedirs("laporan_web")

# 2. FITUR UPLOAD FOTO / JEPRET KAMERA ASLI HP (Solusi Bebas Blokir HTTP)
file_gambar = st.file_uploader("Silakan foto QR Code lalu upload di sini:", type=["jpg", "jpeg", "png"])

# Tempat menampung teks hasil pembacaan QR
data_qr = None

# 3. Proses Membaca QR Code dari Gambar yang Di-upload
if file_gambar is not None:
    try:
        # Mengubah file gambar agar bisa dibaca oleh library OpenCV
        img_pil = Image.open(file_gambar)
        img_np = np.array(img_pil)
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Proses pendeteksian QR Code
        detector = cv2.QRCodeDetector()
        data_qr, bbox, _ = detector.detectAndDecode(gray_img)
        
        if data_qr:
            st.success(f"✅ QR Code Terdeteksi! Kegiatan: **{data_qr}**")
        else:
            st.error("❌ QR Code tidak terbaca atau kurang jelas. Pastikan gambar QR Code terlihat utuh, lalu upload ulang.")
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")

# 4. Jika QR Code Sukses Terbaca -> Tampilkan Form Isian Nama Warga/Siswa
if data_qr:
    st.markdown("---")
    with st.form(key='form_absen'):
        st.markdown("### 📝 Isi Kehadiran")
        nama_peserta = st.text_input("Masukkan Nama Lengkap Anda:").strip()
        submit_button = st.form_submit_button(label='Kirim Kehadiran')
        
        if submit_button:
            if nama_peserta:
                waktu_sekarang = datetime.now()
                tanggal = waktu_sekarang.strftime("%Y-%m-%d")
                jam = waktu_sekarang.strftime("%H:%M:%S")
                
                # Menentukan lokasi file Excel (.csv) di laptopmu
                nama_file_csv = f"laporan_web/Presensi_{data_qr}.csv"
                file_baru = not os.path.exists(nama_file_csv)
                
                # Simpan data kehadiran dengan format pemisah titik koma (;) agar rapi di Excel
                with open(nama_file_csv, "a", encoding="utf-8") as f:
                    if file_baru:
                        f.write("sep=;\n")  # Trik agar Excel otomatis membagi kolom
                        f.write("Tanggal;Jam;Nama Peserta\n")
                    f.write(f"{tanggal};{jam};{nama_peserta}\n")
                
                st.balloons() # Efek animasi sukses
                st.success(f"Terima kasih {nama_peserta}, Anda berhasil absen untuk kegiatan '{data_qr}' pada jam {jam}!")
            else:
                st.error("Nama tidak boleh kosong! Silakan ketik nama Anda.")

# 5. Menampilkan Tabel Hasil Rekap Absen Hari Ini secara Real-Time di Web
st.markdown("---")
st.subheader("📊 Cek Data Kehadiran")
if data_qr:
    file_target = f"laporan_web/Presensi_{data_qr}.csv"
    if os.path.exists(file_target):
        try:
            # FIX: skiprows=1 untuk melompati 'sep=;', dan on_bad_lines='skip' untuk mencegah eror pembacaan
            df = pd.read_csv(file_target, sep=";", skiprows=1, header=0, on_bad_lines="skip")
            st.dataframe(df, use_container_width=True)
        except Exception as err:
            st.warning("Sedang menyelaraskan data baru...")
    else:
        st.info("Belum ada warga/siswa yang mengisi absen untuk kegiatan ini.")
else:
    st.info("Upload foto QR Code kegiatan di atas terlebih dahulu untuk memunculkan tabel kehadiran.")