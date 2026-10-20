# IF3170_G29_TheSeekers

## Deskripsi Repository

Repository Tugas Besar 1 IF3170 Inteligensi Artifisial oleh Kelompok 29, The Seekers. Program mencari konfigurasi pemuatan paket ke dalam truk yang memaksimalkan fungsi objektif menggunakan algoritma Hill Climbing, Simulated Annealing, dan Genetic Algorithm. Hasil pencarian dapat dilihat melalui antarmuka web dengan visualisasi 3D dan grafik eksperimen.

Struktur folder repository:

```text
.
|-- docs/                    Laporan dan dokumentasi pendukung
|-- output/                  Hasil test case dan tangkapan layar eksperimen
|-- src/                     Source code program
|   |-- backend/             Algoritma Python, model persoalan, dan API Flask
|   |   `-- requirements.txt Dependensi backend
|   `-- frontend/            Antarmuka React dan visualisasi 3D
`-- README.md
```

## Cara Setup dan Run

### Prasyarat

- Python 3.10 atau lebih baru, dengan modul `venv` dan `pip`.
- Node.js 20 (minimal 20.19) atau versi 22.12 ke atas, beserta npm.

Semua perintah berikut dijalankan dari direktori root repository.

### Setup Backend

Buat dan aktifkan virtual environment, lalu pasang dependensi backend:

```bash
python3 -m venv src/backend/.venv
source src/backend/.venv/bin/activate
python -m pip install -r src/backend/requirements.txt
```

Untuk Windows PowerShell, gunakan `python` sebagai pengganti `python3` saat membuat virtual environment, lalu aktifkan dengan:

```powershell
.\src\backend\.venv\Scripts\Activate.ps1
```

Setelah aktif, jalankan perintah pemasangan dependensi yang sama.

### Setup Frontend

Pasang dependensi dan buat build frontend:

```bash
npm --prefix src/frontend ci
npm --prefix src/frontend run build
```

### Menjalankan Program Web

Dengan virtual environment backend aktif, jalankan:

```bash
python -m src.backend.server
```

Buka [http://127.0.0.1:8000](http://127.0.0.1:8000) di browser. Backend juga menyajikan hasil build frontend, sehingga cukup menjalankan satu server untuk menggunakan program web.

Melalui antarmuka web, pengguna dapat memilih algoritma, mengatur parameter eksperimen, serta melihat state awal, state akhir, grafik, dan metrik hasil pencarian. Hasil eksperimen yang disimpan melalui program tersimpan di `output/results.pkl`.

### Mode Pengembangan Frontend

Tetap jalankan backend pada port `8000`. Di terminal lain, jalankan:

```bash
npm --prefix src/frontend run dev
```

Buka [http://localhost:5173](http://localhost:5173). Server pengembangan frontend meneruskan permintaan `/api` ke backend pada port `8000`.

### Menjalankan Program Terminal

Sebagai alternatif antarmuka web, jalankan aplikasi terminal dengan virtual environment backend aktif:

```bash
python -m src.backend.main
```

Ikuti menu interaktif untuk memilih algoritma dan parameter eksperimen. Gunakan `Ctrl+C` untuk menghentikan program atau server.

## Hasil Test Case

Hasil eksekusi test case disimpan di `output/results.pkl`. Untuk melihatnya pada website, cukup jalankan program web seperti biasa sesuai langkah di atas. Backend otomatis memuat file tersebut saat mulai dijalankan, lalu menampilkan hasil yang tersimpan pada daftar eksperimen. Pengguna tidak perlu mengimpor file atau menjalankan ulang test case, pilih eksperimen untuk melihat detail hasilnya.

Jika ingin menjalankan program tanpa hasil test case yang tersimpan:

1. Hentikan backend dengan `Ctrl+C` jika masih berjalan.
2. Pindahkan, ubah nama, atau hapus `output/results.pkl`. Untuk tetap menyimpan hasil lama, ubah namanya menjadi `output/results-backup.pkl`.
3. Jalankan kembali backend dengan `python -m src.backend.server`, lalu buka atau muat ulang website.

Jika `output/results.pkl` tidak ada, program dimulai dengan daftar eksperimen kosong. File tersebut akan dibuat kembali ketika pengguna menyimpan hasil eksperimen baru. Menghapus file saat backend masih berjalan tidak mengosongkan hasil yang sudah dimuat ke memori, backend perlu dihentikan terlebih dahulu.

## Pembagian Tugas

| Nama (NIM) | Tugas |
| --- | --- |
| Audric (13524010) | Algoritma Hill Climb<br>Bonus Hill Climb<br>Visualisasi<br>Eksperimen dan Analisis |
| Mahatma (13524015) | Algoritma Genetic Algorithm<br>Bonus Objective Function |
| Ishak (13524022) | Algoritma Simulated Annealing<br>Bonus Multitruck<br>Visualisasi |
