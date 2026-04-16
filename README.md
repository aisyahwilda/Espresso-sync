# Simulasi Interaktif Model Komunikasi dalam Sistem Terdistribusi

Proyek ini merupakan simulasi pemesanan kopi untuk memahami dampak model komunikasi yang berbeda pada aliran data sistem terdistribusi.

## 1) Tujuan

Menunjukkan secara praktis bagaimana model komunikasi memengaruhi:

- cara pesan dikirim dan diproses,
- urutan komunikasi antar komponen,
- metrik performa (latency dan throughput).

## 2) Model Komunikasi yang Dipilih

Proyek ini mengimplementasikan **3 model komunikasi** (minimal tugas adalah 2):

1. **Request-Response**
   - Client mengirim request ke server.
   - Server memproses lalu mengirim response balik secara sinkron.

2. **Publish-Subscribe**
   - Client mem-publish event order.
   - Subscriber (barista/service) menerima event secara asinkron.

3. **RPC (Remote Procedure Call)**
   - Order Service memanggil service lain seolah fungsi lokal, tetapi sebenarnya komunikasi antarlayanan.

## 3) Komponen Sistem

- **Client**: pengguna mengisi form order pada UI.
- **API Gateway**: menerima request dari client.
- **Order Service**: pusat logika pemrosesan order.
- **Barista/Worker**: pihak yang mengeksekusi order.
- **Logger & Metrics**: pencatatan urutan event dan metrik perbandingan.

## 4) Implementasi Logika Interaksi

Logika ada di `app.py`:

- Endpoint `POST /send` memproses order berdasarkan mode komunikasi.
- Endpoint `GET /log` menampilkan urutan event komunikasi.
- Endpoint `GET /stats` menampilkan metrik perbandingan.
- Endpoint `GET /messages` menampilkan feed publish-subscribe.
- Endpoint `POST /reset` mengosongkan state simulasi.

## 5) Representasi Visual & Interaksi Pengguna

UI ada di `templates/index.html` dengan fitur:

- pemilihan mode komunikasi,
- form input order (nama, minuman, jumlah, metode pickup/dinein/delivery),
- animasi alur paket data antar node,
- playback simulasi langkah komunikasi (mainkan, jeda, step manual, kecepatan),
- panel metrik,
- grafik latency dan throughput,
- feed publish-subscribe,
- timeline log komunikasi.

## 6) Mekanisme Perbandingan

Metrik yang ditampilkan:

- `total_transactions`
- `request_count`, `publish_count`, `rpc_count`
- `last_latency_ms`, `avg_latency_ms`
- `throughput_per_minute`

Dengan metrik ini, pengguna dapat membandingkan perilaku model sinkron vs asinkron dan dampaknya pada performa.

## 7) Cara Menjalankan

1. Install dependency:

```bash
pip install -r requirements.txt
```

2. Jalankan aplikasi:

```bash
python app.py
```

3. Buka browser:

- `http://127.0.0.1:5000`

## 8) Contoh Analisis Hasil

- **Request-Response**: alur paling mudah dipahami, response langsung, cocok untuk operasi sederhana.
- **Publish-Subscribe**: event-driven dan longgar keterikatannya, cocok untuk notifikasi/penyiaran event.
- **RPC**: terlihat seperti pemanggilan fungsi, cocok untuk orkestrasi antar service, namun tetap bergantung jaringan.

## 11) Struktur Proyek

- `app.py`
- `templates/index.html`
- `README.md`
- `requirements.txt`
