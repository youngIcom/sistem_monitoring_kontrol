# Kontrol Robot Line Follower via WiFi dengan ESP32

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Proyek ini adalah implementasi untuk program robot line follower sederhana, dimana fungsi program digunakan sebagai remote yang dapat dikontrol dengan laptop via jaringan wifi

---


## ✨ Fitur Utama

- **Kontrol Gerak Penuh:** Menggerakkan robot **maju, mundur, belok kiri,**, **belok kanan**, dan **diam**.
- **Kecepatan Dinamis:** Mengatur kecepatan motor dari 0 hingga 255.
- **Kontrol Servo:** Menggerakkan servo ke sudut tertentu (0-180 derajat).
- **Pembacaan Sensor Real-time:** Menerima data dari 5 sensor garis secara langsung.
- **Konfigurasi WiFi Mudah:** Menggunakan **WiFiManager** untuk setup koneksi WiFi awal tanpa perlu mengubah kode.
- **Komunikasi TCP:** Menggunakan protokol TCP yang andal untuk pengiriman perintah.

---

## 🛠️ Tumpukan Teknologi & Hardware

### Hardware
- Mikrokontroler: **ESP32 Dev Module** 
- Driver Motor: **L298N**
- Sensor: **5x TCRT5000 Line Follower Sensor Module**
- Servo: **SG90 Micro Servo**
- Chassis Robot & Roda

### Firmware & Software
- Bahasa: **C++ (Arduino Framework)**
- Library:
  - `WiFiManager.h` oleh tzapu
  - `ESP32Servo.h`
- Protokol Komunikasi: **TCP/IP**

---


## 🚀 Instalasi & Persiapan

Untuk menjalankan proyek ini di ESP32 Anda, ikuti langkah-langkah berikut:

1.  **Clone Repositori**
    ```bash
    git clone [https://github.com/NAMA_USER_ANDA/NAMA_REPO_ANDA.git](https://github.com/NAMA_USER_ANDA/NAMA_REPO_ANDA.git)
    ```

2.  **Buka di Arduino IDE**
    - Buka file `.ino` menggunakan Arduino IDE.

3.  **Instal Library**
    - Buka **Tools > Manage Libraries...**
    - Cari dan instal library berikut:
      - `WiFiManager` oleh tzapu
      - `ESP32Servo`

4.  **Konfigurasi Board**
    - Di Arduino IDE, buka **Tools > Board**.
    - Pilih **"ESP32 Dev Module"** atau board ESP32 lain yang sesuai.

5.  **Upload Kode**
    - Hubungkan ESP32 Anda ke komputer.
    - Klik tombol **Upload** di Arduino IDE.

---

## 🎮 Cara Penggunaan

### 1. Konfigurasi WiFi
- Saat pertama kali dinyalakan, ESP32 akan membuat sebuah Access Point (AP) dengan nama **"AutoConnectAP"** dan kata sandi **"password"**.
- Hubungkan ponsel atau laptop Anda ke AP tersebut.
- Sebuah halaman konfigurasi akan muncul secara otomatis. Pilih jaringan WiFi rumah Anda, masukkan kata sandinya, dan simpan.
- ESP32 akan me-restart dan terhubung ke jaringan Anda. Alamat IP-nya akan muncul di Serial Monitor.

### 2. Kirim Perintah
Hubungkan aplikasi TCP client Anda ke **alamat IP ESP32** pada **port 8080**. Kirim perintah dalam format teks berikut:

- **Menggerakkan Motor:** `M:KECEPATAN:AKSI`
  - `M:200:F` - Maju dengan kecepatan 200.
  - `M:150:B` - Mundur dengan kecepatan 150.
  - `M:255:L` - Belok kiri.
  - `M:255:R` - Belok kanan.
  - `M:0:S` - Berhenti.

- **Menggerakkan Servo:** `S:SUDUT`
  - `S:90` - Menggerakkan servo ke posisi 90 derajat.
  - `S:0` - Menggerakkan servo ke posisi 0 derajat.
  - `S:180` - Menggerakkan servo ke posisi 180 derajat.

- **Mendapatkan Data Sensor:** `GETSENSOR`
  - Mengirim perintah ini akan membuat ESP32 merespons dengan data sensor, contoh: `SENSORS:1,1,0,1,1`

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **Lisensi GPL 3.0**. Lihat file `LICENSE` untuk detailnya.
