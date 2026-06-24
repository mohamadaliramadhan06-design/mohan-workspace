import streamlit as st
import pandas as pd
import cv2
import numpy as np
import os
import base64
import io
from datetime import datetime
import pytz
from PIL import Image

# 1. Pengaturan Tampilan Awal Website
st.set_page_config(page_title="Presensi QR RT & Ekskul", page_icon="📱", layout="centered")

# --- KODE CSS UNTUK MEMPERBESAR TAMPILAN ELEMENT DI HP ---
st.markdown("""
    <style>
    .stTextInput input {
        font-size: 20px !important;
        height: 50px !important;
    }
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

st.title("📱 Web Presensi QR Code + Bukti Foto")
st.write("Gunakan kamera HP Anda untuk memfoto QR Code Kegiatan, lalu upload di bawah ini.")

# Membuat folder penyimpanan data secara lokal jika belum ada
if not os.path.exists("laporan_web"):
    os.makedirs("laporan_web")

# Fungsi untuk mengubah gambar bukti menjadi teks Base64 agar bisa masuk Excel
def konversi_gambar_ke_base64(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        # Kompres gambar ke ukuran kecil agar file Excel tidak terlalu berat
        img.thumbnail((300, 300)) 
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except:
        return "Gagal memproses gambar"

# 2. FITUR UPLOAD FOTO QR CODE KEGIATAN
file_gambar = st.file_uploader("1. Silakan foto QR Code lalu upload di sini:", type=["jpg", "jpeg", "png"], key="qr_code")

data_qr = None

# 3. Proses Membaca QR Code dari Gambar yang Di-upload
if file_gambar is not None:
    try:
        img_pil = Image.open(file_gambar)
        img_np = np.array(img_pil)
        gray_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        detector = cv2.QRCodeDetector()
        data_qr, bbox, _ = detector.detectAndDecode(gray_img)
        
        if data_qr:
            st.success(f"✅ QR Code Terdeteksi! Kegiatan: **{data_qr}**")
        else:
            st.error("❌ QR Code tidak terbaca atau kurang jelas. Pastikan gambar QR Code terlihat utuh, lalu upload ulang.")
    except Exception as e:
        st.error(f"Gagal memproses gambar QR: {e}")

# 4. Jika QR Code Sukses Terbaca -> Tampilkan Form Isian Nama & Upload Bukti Foto
if data_qr:
    st.markdown("---")
    st.markdown("### 📝 Isi Kehadiran")
    
    nama_peserta = st.text_input("Masukkan Nama Lengkap Anda:").strip()
    
    # Tambahan fitur upload/jepret foto bukti di tempat
    file_bukti = st.file_uploader("2. Foto Bukti di Tempat (Selfie / Suasana Kegiatan):", type=["jpg", "jpeg", "png"], key="bukti_foto")
    
    if file_bukti:
        st.image(file_bukti, caption="Pratinjau Bukti Foto Anda", width=200)

    submit_button = st.button(label='Kirim Kehadiran')
    
    if submit_button:
        if not nama_peserta:
            st.error("Nama tidak boleh kosong! Silakan ketik nama Anda.")
        elif not file_bukti:
            st.error("Wajib mengunggah bukti foto di tempat sebelum mengirim!")
        else:
            # Mengunci waktu ke Waktu Indonesia Barat (WIB / GMT+7)
            tz_jakarta = pytz.timezone('Asia/Jakarta')
            waktu_sekarang = datetime.now(tz_jakarta)
            tanggal = waktu_sekarang.strftime("%Y-%m-%d")
            jam = waktu_sekarang.strftime("%H:%M:%S")
            
            # Proses gambar bukti menjadi string teks
            string_foto_bukti = konversi_gambar_ke_base64(file_bukti)
            
            nama_file_csv = f"laporan_web/Presensi_{data_qr}.csv"
            file_baru = not os.path.exists(nama_file_csv)
            
            with open(nama_file_csv, "a", encoding="utf-8") as f:
                if file_baru:
                    f.write("sep=;\n")  
                    f.write("Tanggal;Jam;Nama Peserta;Bukti Foto\n")
                f.write(f"{tanggal};{jam};{nama_peserta};{string_foto_bukti}\n")
            
            st.balloons() 
            st.success(f"Terima kasih {nama_peserta}, Anda berhasil absen!")

# 5. MENAMPILKAN TABEL DAN FOTO BUKTI SECARA LANGSUNG
st.markdown("---")
st.subheader("📊 Cek Data Kehadiran")
if data_qr:
    file_target = f"laporan_web/Presensi_{data_qr}.csv"
    if os.path.exists(file_target):
        try:
            df = pd.read_csv(file_target, sep=";", skiprows=1, header=0, on_bad_lines="skip")
            
            # SULAP: Mengubah teks kode Base64 menjadi kolom gambar asli di tabel web kamu!
            st.dataframe(
                df,
                column_config={
                    "Bukti Foto": st.column_config.ImageColumn(
                        "Foto Bukti", help="Foto bukti di lokasi kegiatan"
                    )
                },
                use_container_width=True
            )
            
            # TOMBOL UNDUH FILE ASLI
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Rekap Absen (Excel .csv)",
                data=csv_data,
                file_name=f"Rekap_Presensi_{data_qr}.csv",
                mime="text/csv",
            )
        except Exception as err:
            st.warning("Sedang menyelaraskan data baru...")
    else:
        st.info("Belum ada yang mengisi absen untuk kegiatan ini.")
else:
    st.info("Upload foto QR Code kegiatan di atas terlebih dahulu untuk memunculkan data.")
