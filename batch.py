import streamlit as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os
from datetime import datetime

EXCEL_FILE = "Laporan_Bulanan.xlsx"

def inisialisasi_excel():
    """Membuat file Excel beserta headernya jika belum ada"""
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Data Pengeluaran"
        ws.views.sheetView[0].showGridLines = True
        
        headers = ["Hari", "Tanggal", "Bulan", "Nama Barang / Kebutuhan", "Harga (Rp)"]
        ws.append(headers)
        
        # Gaya Desain Header
        dark_emerald = "1B4D3E"
        font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color=dark_emerald, end_color=dark_emerald, fill_type="solid")
        
        for col in range(1, 6):
            cell = ws.cell(row=1, column=col)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center")
            
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 30
        ws.column_dimensions['E'].width = 20
        wb.save(EXCEL_FILE)

# Jalankan inisialisasi awal
inisialisasi_excel()

# --- TAMPILAN WEB (STREAMLIT) ---
st.set_page_config(page_title="Catat Pengeluaran", page_icon="💰", layout="centered")

st.title("💰 Pencatatan Pengeluaran Harian")
st.write("Hari, Tanggal, dan Bulan akan dicatat secara otomatis oleh sistem.")
st.markdown("---")

# Form Input Web
nama_barang = st.text_input("Nama Barang / Kebutuhan", placeholder="Contoh: Nasi Padang, Bensin")
harga = st.number_input("Harga (Rp)", min_value=0, step=1000, value=0)

# Tombol Simpan
if st.button("Simpan ke Excel", type="primary"):
    if nama_barang == "":
        st.error("Nama barang tidak boleh kosong!")
    elif harga <= 0:
        st.error("Harga harus lebih dari 0!")
    else:
        # Ambil waktu otomatis saat tombol diklik
        sekarang = datetime.now()
        
        hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        hari = hari_indo[sekarang.weekday()]
        tanggal = sekarang.strftime("%Y-%m-%d")
        
        bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                      "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan = bulan_indo[sekarang.month - 1]
        
        # Proses tulis ke Excel
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active
        
        ws.append([hari, tanggal, bulan, nama_barang, harga])
        
        # Merapikan baris baru di Excel
        row_terakhir = ws.max_row
        price_cell = ws.cell(row=row_terakhir, column=5)
        price_cell.number_format = '#,##0'
        price_cell.alignment = Alignment(horizontal="right")
        
        thin_border = Border(left=Side(style='thin', color='D3D3D3'),
                             right=Side(style='thin', color='D3D3D3'),
                             top=Side(style='thin', color='D3D3D3'),
                             bottom=Side(style='thin', color='D3D3D3'))
        
        for col in range(1, 6):
            c = ws.cell(row=row_terakhir, column=col)
            c.font = Font(name="Segoe UI", size=11)
            c.border = thin_border
            if col in [1, 2, 3]:
                c.alignment = Alignment(horizontal="center")
                
        wb.save(EXCEL_FILE)
        
        # Tampilkan notifikasi sukses di web
        st.success(f"Berhasil menyimpan: {nama_barang} - Rp {harga:,}")

st.markdown("---")
st.subheader("📂 Download File Data Anda")

# --- FITUR BARU: TOMBOL DOWNLOAD BIAR MUNCUL DI WEB ---
if os.path.exists(EXCEL_FILE):
    with open(EXCEL_FILE, "rb") as file:
        btn = st.download_button(
            label="📥 Download File Excel Keuangan",
            data=file,
            file_name="Aplikasi_Keuangan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Belum ada data yang tersimpan. Silakan isi form di atas terlebih dahulu.")
