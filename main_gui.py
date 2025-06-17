import tkinter as tk
from tkinter import ttk, messagebox
import socket # Untuk komunikasi TCP
import threading
import time

class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Monitor (TCP/IP)")
        # Sedikit menambah tinggi window untuk input IP
        self.root.geometry("900x700") 
        self.root.configure(bg="#E8EEF5") # Atur warna background window utama

        self.judul = ["Motor Speed", "Servo Angle"]
        self.entries = [] # List untuk menampung widget Entry untuk kecepatan motor dan sudut servo
        self.sensor_labels = [] # List untuk menampung label nilai sensor
        self.sensor_bars = [] # List untuk menampung progress bar nilai sensor

        # Label Status Navigasi
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Disconnected") # Status awal
        self.status_label = tk.Label(self.root, textvariable=self.status_var,
                                     font=("Times New Roman", 12, "bold"), fg="#CC2F13", bg="#E8EEF5")
        self.status_label.pack(pady=(5, 5)) # Sesuaikan padding

        # Variabel untuk melacak pergerakan lingkaran di canvas
        self.moving_direction = None    # None, "up", "down", "left", "right"
        self.move_speed_factor = 0.1    # Faktor untuk skala kecepatan pergerakan dari PWM (misal PWM 200 -> 20 pixel)
        self.move_interval = 100        # ms, interval update pergerakan
        self.move_job = None            # Untuk menyimpan job 'after' untuk pergerakan kontinu

        # Buat style untuk 5 progress bar sensor
        self.pb_styles = []
        for i in range(5):
            style = ttk.Style()
            style_name = f"SensorPB{i}.Horizontal.TProgressbar"
            style.theme_use('default')
            # Konfigurasi warna trough dan background default
            style.configure(style_name, troughcolor="#D3D3D3", background="#D3D3D3")
            self.pb_styles.append(style_name)

        # Koneksi TCP
        self.sock = None
        self.is_connected = False
        self.server_ip_var = tk.StringVar(value="192.168.160.64") # IP default, ubah sesuai kebutuhan
        self.server_port_var = tk.StringVar(value="8080") # Port default

        # Frame Koneksi
        conn_frame = tk.Frame(self.root, bg="#E8EEF5")
        conn_frame.pack(pady=(0,10))
        tk.Label(conn_frame, text="ESP32 IP:", font=("Times New Roman", 11), bg="#E8EEF5").pack(side=tk.LEFT, padx=5)
        self.ip_entry = tk.Entry(conn_frame, textvariable=self.server_ip_var, font=("Times New Roman", 11), width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(conn_frame, text="Port:", font=("Times New Roman", 11), bg="#E8EEF5").pack(side=tk.LEFT, padx=5)
        self.port_entry = tk.Entry(conn_frame, textvariable=self.server_port_var, font=("Times New Roman", 11), width=7)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.connect_button = tk.Button(conn_frame, text="Connect", font=("Times New Roman", 10, "bold"), 
                                        bg="#CC2F13", fg="white", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        # Judul Utama GUI
        tk.Label(self.root, text="SISTEM MONITOR", font=("Times New Roman", 18, "bold"),
                 fg="#CC2F13", bg="#E8EEF5").pack(pady=10) # Sesuaikan padding

        # Buat frame utama untuk bagian kiri dan kanan
        main_frame = tk.Frame(self.root, bg="#E8EEF5")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        # Konfigurasi kolom agar bisa expand secara merata
        main_frame.columnconfigure(0, weight=1, uniform='a')
        main_frame.columnconfigure(1, weight=1, uniform='a')
        main_frame.rowconfigure(0, weight=1)

        # Frame Kiri dan Kanan
        self.left_frame = tk.Frame(main_frame, bg="#E8EEF5")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0,15))
        self.right_frame = tk.Frame(main_frame, bg="#E8EEF5")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(15,0))

        # Separator antara frame kiri dan kanan
        separator = ttk.Separator(main_frame, orient='vertical')
        separator.place(relx=0.5, rely=0, relheight=1)

        # Panggil fungsi untuk membuat elemen GUI sisi kiri dan kanan
        self.create_left_side()
        self.create_right_side()

        # Thread untuk membaca data dari koneksi TCP
        self.data_thread = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) # Tangani event penutupan window

    def on_closing(self):
        """Menangani event penutupan window."""
        if self.is_connected and self.sock:
            try:
                # Kirim perintah stop motor sebelum menutup jika diinginkan
                # self.send_command_to_esp("M:0:S") 
                print("Closing TCP socket...")
                self.sock.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
        self.is_connected = False # Pastikan thread berhenti
        if self.data_thread and self.data_thread.is_alive():
             print("Data thread is alive, attempting to join...")
             self.data_thread.join(timeout=1.0) # Beri waktu thread untuk selesai
             if self.data_thread.is_alive():
                 print("Data thread did not terminate gracefully.")
        print("Exiting application.")
        self.root.destroy()

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()

    def connect_to_server(self):
        ip = self.server_ip_var.get()
        port_str = self.server_port_var.get()
        if not ip or not port_str:
            messagebox.showerror("Error", "Alamat IP dan Port tidak boleh kosong.")
            return
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Error", "Port harus berupa angka.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5) # Timeout 5 detik untuk koneksi
            print(f"Mencoba menghubungkan ke {ip}:{port}...")
            self.sock.connect((ip, port))
            self.sock.settimeout(1) # Timeout 1 detik untuk operasi selanjutnya
            self.is_connected = True
            self.status_var.set(f"Status: Terhubung ke {ip}:{port}")
            self.connect_button.config(text="Disconnect", bg="red")
            print(f"Terhubung ke ESP32 di {ip}:{port}")

            # Mulai loop pembacaan data di thread terpisah
            if self.data_thread is None or not self.data_thread.is_alive():
                self.data_thread = threading.Thread(target=self.read_data_loop, daemon=True)
                self.data_thread.start()

        except socket.timeout:
            messagebox.showerror("Kesalahan Koneksi", f"Koneksi ke {ip}:{port} timeout.")
            self.is_connected = False
            if self.sock: self.sock.close()
            self.sock = None
        except ConnectionRefusedError:
            messagebox.showerror("Kesalahan Koneksi", f"Koneksi ke {ip}:{port} ditolak. Pastikan server ESP32 berjalan.")
            self.is_connected = False
            if self.sock: self.sock.close()
            self.sock = None
        except Exception as e:
            messagebox.showerror("Error", f"Tidak dapat terhubung ke {ip}:{port}.\n{e}")
            self.is_connected = False
            if self.sock: self.sock.close()
            self.sock = None
            print(f"Error saat menghubungkan: {e}")

    def disconnect_from_server(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                print(f"Error saat menutup socket: {e}")
        self.sock = None
        self.is_connected = False # Ini akan menghentikan loop di data_thread
        self.status_var.set("Status: Disconnected")
        self.connect_button.config(text="Connect", bg="#CC2F13")
        print("Terputus dari ESP32.")
        # Reset tampilan sensor
        for i in range(5):
            self.update_sensor_value(i, "-") # Atau 0
            if i < len(self.sensor_bars): # Pastikan sensor_bars sudah diinisialisasi
                 self.sensor_bars[i]["value"] = 0
                 style = ttk.Style()
                 style.configure(self.pb_styles[i], background="#D3D3D3")


    def create_left_side(self):
        # Frame Input Manual Motor dan Servo
        input_frame = tk.LabelFrame(self.left_frame, text="Kontrol Motor & Servo",
                                    font=("Times New Roman", 14, "bold"), fg="#CC2F13", bg="#E8EEF5", padx=15, pady=15)
        input_frame.pack(fill="x")

        for i, label_text in enumerate(self.judul):
            lbl = tk.Label(input_frame, text=f"{label_text}", font=("Times New Roman", 13), bg="#E8EEF5")
            lbl.grid(row=i, column=0, sticky="w", pady=8, padx=(0,10))

            entry = tk.Entry(input_frame, font=("Times New Roman", 12), width=12, relief="groove", bd=2)
            entry.grid(row=i, column=1, pady=8, padx=(0,10))
            self.entries.append(entry)

            # Tombol OK untuk mengirim nilai
            btn = tk.Button(input_frame, text="OK", font=("Times New Roman", 11, "bold"),
                            bg="#CC2F13", fg="white", width=5,
                            command=lambda e=entry, l=label_text: self.submit_manual_value(e, l))
            btn.grid(row=i, column=2, pady=8)

        # Frame Kontrol Arah Robot (Tombol panah dan STOP)
        control_frame = tk.LabelFrame(self.left_frame, text="Kontrol Arah",
                                      font=("Times New Roman", 14, "bold"), fg="#CC2F13", bg="#E8EEF5", padx=15, pady=15)
        control_frame.pack(pady=20, fill="both", expand=True)

        btn_opts = {"width": 5, "height": 2, "bg": "#CC2F13", "fg": "white", "font": ("Times New Roman", 14, "bold"), "relief": "raised"}

        btn_frame = tk.Frame(control_frame, bg="#E8EEF5")
        btn_frame.pack()

        # Tombol arah
        tk.Button(btn_frame, text="↑", command=self.move_forward, **btn_opts).grid(row=0, column=1, padx=10, pady=5)
        tk.Button(btn_frame, text="←", command=self.turn_left, **btn_opts).grid(row=1, column=0, padx=10, pady=5)
        tk.Button(btn_frame, text="↓", command=self.move_backward, **btn_opts).grid(row=1, column=1, padx=10, pady=5)
        tk.Button(btn_frame, text="→", command=self.turn_right, **btn_opts).grid(row=1, column=2, padx=10, pady=5)
        tk.Button(btn_frame, text="STOP", command=self.stop_motor, **btn_opts).grid(row=2, column=1, pady=10)

    def create_right_side(self):
        # Frame Sensor Garis (dengan 5 progress bar)
        sensor_frame = tk.LabelFrame(self.right_frame, text="Sensor Garis",
                                     font=("Times New Roman", 14, "bold"), fg="#CC2F13", bg="#E8EEF5", padx=20, pady=15)
        sensor_frame.pack(fill="both", expand=True, pady=10)

        for i in range(5):
            row_frame = tk.Frame(sensor_frame, bg="#E8EEF5")
            row_frame.pack(fill="x", pady=6, padx=10)

            sensor_label = tk.Label(row_frame, text=f"Sensor {i+1}: -",
                                    font=("Times New Roman", 13), fg="#333", bg="#E8EEF5", anchor="w", width=15)
            sensor_label.pack(side="left")
            self.sensor_labels.append(sensor_label)

            # Progress bar untuk setiap sensor
            # Atur maximum untuk S3 ke 4095 (resolusi analog ESP32)
            max_val = 4095 if i == 2 else 1 # S3 (index 2) analog, lainnya digital
            bar = ttk.Progressbar(row_frame, orient="horizontal", length=120, mode="determinate", maximum=max_val, style=self.pb_styles[i])
            bar.pack(side="left", padx=10)
            bar["value"] = 0 # Nilai awal
            self.sensor_bars.append(bar)

        # Frame Canvas Tracking
        tracking_frame = tk.LabelFrame(self.right_frame, text="Tracking Navigasi",
                                       font=("Times New Roman", 14, "bold"), fg="#CC2F13", bg="#E8EEF5", padx=20, pady=15)
        tracking_frame.pack(fill="both", expand=True, pady=10)

        self.tracking_canvas = tk.Canvas(tracking_frame, width=200, height=200, bg="#fff", highlightthickness=1, highlightbackground="#CC2F13")
        self.tracking_canvas.pack(pady=10)

        # Posisi awal lingkaran di tengah
        self.circle_radius = 10 #jari jari lingkaran
        self.circle_x = 100 #
        self.circle_y = 100
        self.tracking_circle = self.tracking_canvas.create_oval(
            self.circle_x - self.circle_radius, self.circle_y - self.circle_radius,
            self.circle_x + self.circle_radius, self.circle_y + self.circle_radius,
            fill="#CC2F13", outline="#1354CC"
        )

    def move_tracking_circle(self, dx, dy):
        # Hitung posisi baru
        new_x = self.circle_x + dx #posisi baru di x= posisi lama + perubahan posisi
        new_y = self.circle_y + dy #posisi baru di y= posisi lama + perubahan posisi

        # Batas canvas / batas aman
        min_pos = self.circle_radius #batas minimum = jari jari lingkaran
        max_pos_x = self.tracking_canvas.winfo_width() - 10 #self.circle_radius # batas maksimum x = lebar canvas - jari jari lingkaran
        max_pos_y = self.tracking_canvas.winfo_height() - 10 #self.circle_radius # batas maksimum y = tinggi canvas - jari jari lingkaran
        
        if max_pos_x < min_pos : max_pos_x = 200 - self.circle_radius # Fallback jika winfo_width belum siap untuk memastikan bahwa ukuran kanvas sesuai dengan yang sudah ditentukan
        if max_pos_y < min_pos : max_pos_y = 200 - self.circle_radius # sama

        # Pastikan lingkaran tetap dalam batas canvas
        #menggunakan clamping method
        self.circle_x = max(min_pos, min(new_x, max_pos_x))
        self.circle_y = max(min_pos, min(new_y, max_pos_y))

        # Update koordinat lingkaran
        self.tracking_canvas.coords(
            self.tracking_circle,
            self.circle_x - self.circle_radius, self.circle_y - self.circle_radius, #
            self.circle_x + self.circle_radius, self.circle_y + self.circle_radius  #
        )

    def move_tracking_circle_continuous(self):
        """
        Secara kontinu menggerakkan lingkaran tracking berdasarkan arah dan kecepatan saat ini.
        """
        current_move_speed = self.update_move_speed_for_tracking() # Dapatkan kecepatan berdasarkan PWM
        
        if self.moving_direction == "up":
            self.move_tracking_circle(0, -current_move_speed)
        elif self.moving_direction == "down":
            self.move_tracking_circle(0, current_move_speed)
        elif self.moving_direction == "left":
            self.move_tracking_circle(-current_move_speed, 0)
        elif self.moving_direction == "right":
            self.move_tracking_circle(current_move_speed, 0)
        
        # Lanjutkan pergerakan jika masih dalam state bergerak
        if self.moving_direction:
            self.move_job = self.root.after(self.move_interval, self.move_tracking_circle_continuous)
        else:
            self.move_job = None


    def get_pwm_value_from_entry(self):
        """
        Mengambil nilai PWM dari entry "Motor Speed".
        Default ke 150 jika entry kosong atau tidak valid.

        Returns:
            int: Nilai PWM yang tervalidasi.
        """
        try:
            val = int(self.entries[0].get()) # Asumsi entry[0] adalah untuk Motor Speed
            if 0 <= val <= 255:
                return val
        except (ValueError, IndexError): # Tangani jika entry kosong, tidak ada, atau bukan angka
            pass
        return 150  # Nilai PWM default

    def update_move_speed_for_tracking(self):
        """
        Memperbarui `move_speed` untuk lingkaran tracking berdasarkan nilai PWM saat ini.
        Mengembalikan kecepatan yang diskalakan.
        """
        pwm = self.get_pwm_value_from_entry()
        # Skala kecepatan: minimum 2, maksimum sekitar 25 (pwm 255 * 0.1)
        # Sesuaikan self.move_speed_factor jika perlu skala yang berbeda
        scaled_speed = max(2, int(pwm * self.move_speed_factor)) 
        return scaled_speed


    def update_sensor_value(self, index, value_str):
 
        if not (0 <= index < len(self.sensor_labels) and index < len(self.sensor_bars)):
            print(f"Index sensor tidak valid: {index}")
            return

        self.sensor_labels[index].config(text=f"Sensor {index+1}: {value_str}")
        try:
            v = int(value_str)
            style = ttk.Style() # Dapatkan style lagi untuk modifikasi
            
            # Untuk S3 (index 2), nilai analog (0-4095)
            if index == 2: 
                self.sensor_bars[index]["value"] = v
                # Ubah warna berdasarkan nilai analog untuk S3 (misalnya, jika di atas ambang batas tertentu)
                if v > 2000: # Contoh ambang batas, sesuaikan jika perlu
                    style.configure(self.pb_styles[index], background="#4CAF50", troughcolor="#D3D3D3") # Hijau untuk "terdeteksi"
                else:
                    style.configure(self.pb_styles[index], background="#D3D3D3", troughcolor="#D3D3D3") # Default
            else: # Untuk sensor digital (S1, S2, S4, S5), nilai 0 atau 1
                self.sensor_bars[index]["value"] = v
                if v == 1: # Asumsi 1 berarti garis terdeteksi (atau sebaliknya tergantung sensor)
                    style.configure(self.pb_styles[index], background="#4CAF50", troughcolor="#D3D3D3") # Hijau untuk terdeteksi
                else:
                    style.configure(self.pb_styles[index], background="#D3D3D3", troughcolor="#D3D3D3") # Default untuk tidak terdeteksi
        except ValueError:
            # Jika nilai tidak bisa di-cast ke int, mungkin "-" atau error
            self.sensor_bars[index]["value"] = 0 # Reset ke 0 jika nilai tidak valid
            style = ttk.Style()
            style.configure(self.pb_styles[index], background="#D3D3D3") # Warna default
        except Exception as e:
            print(f"Error saat update sensor UI ({index}): {e}")
            self.sensor_bars[index]["value"] = 0 
            style = ttk.Style()
            style.configure(self.pb_styles[index], background="#D3D3D3")


    def read_data_loop(self):
        """
        Secara kontinu membaca data dari koneksi TCP dan memperbarui GUI.
        Fungsi ini berjalan di thread terpisah.
        """
        buffer = ""
        while self.is_connected and self.sock:
            try:
                # Minta data sensor dari ESP32
                self.send_command_to_esp("GETSENSOR") # \n akan ditambahkan oleh send_command_to_esp
                
                # Baca respons jika tersedia
                # Loop untuk membaca data hingga newline
                while self.is_connected and self.sock: # Periksa koneksi lagi di dalam loop
                    try:
                        chunk = self.sock.recv(1024).decode('utf-8', errors='ignore')
                        if not chunk: # Koneksi ditutup oleh server
                            print("Koneksi ditutup oleh server.")
                            self.root.after(0, self.disconnect_from_server)
                            return
                        buffer += chunk
                        if '\n' in buffer:
                            data, buffer = buffer.split('\n', 1)
                            data = data.strip()
                            if data.startswith("SENSORS:"):
                                parts_str = data.replace("SENSORS:", "")
                                if parts_str: # Pastikan tidak kosong setelah replace
                                    parts = parts_str.split(",")
                                    if len(parts) == 5: # Pastikan ada 5 nilai sensor
                                        # Update elemen GUI di main thread menggunakan after()
                                        self.root.after(0, lambda p=list(parts): [self.update_sensor_value(i, val) for i, val in enumerate(p)])
                                    else:
                                        print(f"Data sensor tidak lengkap diterima: {data}")
                                else:
                                    print(f"Data sensor kosong diterima: {data}")

                            elif data: # Jika ada data lain dari ESP32 (misal debug)
                                print("ESP32:", data)
                            break # Keluar dari loop baca chunk, tunggu GETSENSOR berikutnya
                    except socket.timeout:
                        # Timeout pada recv() adalah normal jika ESP32 tidak mengirim apa-apa
                        # Kita akan coba kirim GETSENSOR lagi di iterasi berikutnya
                        break 
                    except UnicodeDecodeError as ude:
                        print(f"Unicode decode error: {ude}. Buffer: {buffer}")
                        buffer = "" # Reset buffer jika ada error decode
                        break
                    except Exception as e_recv:
                        if self.is_connected: # Hanya tampilkan error jika masih menganggap terhubung
                            print(f"Error saat menerima data: {e_recv}")
                        self.root.after(0, self.disconnect_from_server) # Asumsikan koneksi bermasalah
                        return


            except (socket.error, BrokenPipeError, ConnectionResetError) as e_sock:
                if self.is_connected: # Hanya jika kita masih mengira terhubung
                    print(f"Kesalahan socket: {e_sock}. Mencoba memutuskan koneksi.")
                    messagebox.showerror("Kesalahan Koneksi", f"Koneksi ke ESP32 terputus: {e_sock}")
                self.root.after(0, self.disconnect_from_server) # Panggil disconnect di main thread
                return # Keluar dari loop read_data_loop
            except Exception as e_outer:
                if self.is_connected:
                    print(f"Error di loop baca data: {e_outer}")
                # Mungkin tidak perlu disconnect untuk semua error, tergantung jenisnya
                # self.root.after(0, self.disconnect_from_server) 
                # return
            
            if self.is_connected: # Hanya sleep jika masih terhubung
                 time.sleep(0.2) # Baca setiap 200ms
            else:
                break # Keluar dari while self.is_connected

        print("Loop baca data dihentikan.")


    def send_command_to_esp(self, command_str):
        """
        Mengirim perintah ke ESP32 melalui koneksi TCP.

        Args:
            command_str (str): String perintah yang akan dikirim (tanpa newline).
        """
        if self.is_connected and self.sock:
            try:
                full_command = command_str + "\n"
                self.sock.sendall(full_command.encode('utf-8'))
                print(f"Terkirim ke ESP32: {command_str}")
            except (socket.error, BrokenPipeError) as e:
                messagebox.showerror("Error", f"Gagal mengirim data ke ESP32: {e}")
                print(f"Socket error saat mengirim: {e}")
                self.disconnect_from_server() # Putuskan koneksi jika ada error kirim
            except Exception as e_send:
                messagebox.showerror("Error", f"Terjadi kesalahan saat mengirim: {e_send}")
                print(f"Error umum saat mengirim: {e_send}")
        else:
            messagebox.showwarning("Peringatan", "Tidak terhubung ke ESP32.")
            print("Gagal mengirim: Tidak terhubung.")


    # Fungsi arah motor
    def stop_motor(self):
        """
        Mengirim perintah STOP ke motor dan memperbarui status GUI.
        """
        pwm = self.get_pwm_value_from_entry() # Meskipun speed 0, ESP32 mungkin mengharapkannya
        self.send_command_to_esp(f"M:{pwm}:S") # Atau M:0:S
        self.status_var.set("Status: Diam")
        self.moving_direction = None    # Hentikan pergerakan lingkaran
        if self.move_job:
            self.root.after_cancel(self.move_job) # Batalkan job pergerakan yang tertunda
            self.move_job = None
        # Reset lingkaran ke tengah saat berhenti
        self.circle_x = self.tracking_canvas.winfo_width() / 2 if self.tracking_canvas.winfo_width() > 0 else 100
        self.circle_y = self.tracking_canvas.winfo_height() / 2 if self.tracking_canvas.winfo_height() > 0 else 100
        self.tracking_canvas.coords(
            self.tracking_circle,
            self.circle_x - self.circle_radius, self.circle_y - self.circle_radius,
            self.circle_x + self.circle_radius, self.circle_y + self.circle_radius
        )

    def move_forward(self):
        """
        Mengirim perintah FORWARD ke motor dan memperbarui status serta tracking GUI.
        """
        pwm = self.get_pwm_value_from_entry()
        self.send_command_to_esp(f"M:{pwm}:F")
        self.status_var.set(f"Status: Maju (PWM: {pwm})")
        self.moving_direction = "up"
        if self.move_job:
            self.root.after_cancel(self.move_job) # Batalkan job pergerakan sebelumnya
        self.move_tracking_circle_continuous() # Mulai pergerakan kontinu baru

    def move_backward(self):
        """
        Mengirim perintah BACKWARD ke motor dan memperbarui status serta tracking GUI.
        """
        pwm = self.get_pwm_value_from_entry()
        self.send_command_to_esp(f"M:{pwm}:B")
        self.status_var.set(f"Status: Mundur (PWM: {pwm})")
        self.moving_direction = "down"
        if self.move_job:
            self.root.after_cancel(self.move_job)
        self.move_tracking_circle_continuous()

    def turn_left(self):
        pwm = self.get_pwm_value_from_entry()
        self.send_command_to_esp(f"M:{pwm}:L")
        self.status_var.set(f"Status: Kiri (PWM: {pwm})")
        self.moving_direction = "left"
        if self.move_job:
            self.root.after_cancel(self.move_job)
        self.move_tracking_circle_continuous()

    def turn_right(self):
        pwm = self.get_pwm_value_from_entry()
        self.send_command_to_esp(f"M:{pwm}:R")
        self.status_var.set(f"Status: Kanan (PWM: {pwm})")
        self.moving_direction = "right"
        if self.move_job:
            self.root.after_cancel(self.move_job)
        self.move_tracking_circle_continuous()

    def submit_manual_value(self, entry_widget, label_text):
        val_str = entry_widget.get()
        try:
            val_int = int(val_str)
            if label_text == "Motor Speed":
                if 0 <= val_int <= 255:
                    # Untuk kecepatan motor manual, asumsikan arah maju atau gunakan status saat ini
                    # Di sini kita kirim dengan arah 'F' (Forward) sebagai default jika hanya speed diset
                    self.send_command_to_esp(f"M:{val_int}:F") 
                    messagebox.showinfo("Sukses", f"Perintah kecepatan motor {val_int} terkirim!")
                else:
                    messagebox.showwarning("Input Error", "Input Kecepatan Motor harus angka antara 0 sampai 255.")
            elif label_text == "Servo Angle":
                if 0 <= val_int <= 180:
                    self.send_command_to_esp(f"S:{val_int}")
                    messagebox.showinfo("Sukses", f"Perintah sudut servo {val_int} terkirim!")
                else:
                    messagebox.showwarning("Input Error", "Input Sudut Servo harus angka antara 0 sampai 180.")
        except ValueError:
            messagebox.showwarning("Input Error", "Input harus berupa angka.")
        

# Blok eksekusi utama
if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorApp(root)
    root.mainloop()