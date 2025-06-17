#include <WiFi.h>
#include <WiFiManager.h> // https://github.com/tzapu/WiFiManager
#include <ESP32Servo.h>

// --- Pin untuk Motor Driver L298N ---
#define ENA 19 // Kiri (Motor A) - Harus pin yang mendukung PWM
#define IN1 18
#define IN2 5

#define ENB 4  // Kanan (Motor B) - Harus pin yang mendukung PWM
#define IN3 17
#define IN4 16

// --- Pin untuk Sensor Garis ---
#define S1 35
#define S2 32
#define S3 33 // Pin ini bisa membaca nilai analog
#define S4 25
#define S5 26

// --- Pin untuk Servo ---
#define SERVO_PIN 13 // Pin yang aman untuk digunakan

// --- Objek Servo ---
Servo myServo;

// --- Server WiFi ---
WiFiServer server(8080); // Server akan listen di port 8080
WiFiClient client;       // Merepresentasikan client yang terhubung

// --- Variabel Global ---
String buff; 
const char delimiter[] = ":";
int motor_speed_val, servo_angle_val; 
int sensor1, sensor2, sensor4, sensor5;
int sensor3; // Disimpan sebagai integer untuk nilai analog

void setup() {
  Serial.begin(115200); // Mulai komunikasi serial untuk debugging

  // Set pin motor sebagai OUTPUT
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Set pin sensor sebagai INPUT
  pinMode(S1, INPUT);
  pinMode(S2, INPUT);
  pinMode(S3, INPUT); // Mode input untuk pin analog
  pinMode(S4, INPUT);
  pinMode(S5, INPUT);

  // Inisialisasi posisi awal
  stopMotors(); 
  myServo.attach(SERVO_PIN);
  myServo.write(0); // Posisi awal servo

  // =================================================================
  // BLOK PEMANASAN WIFI (WORKAROUND UNTUK HARDWARE ERROR)
  // Menginisialisasi WiFi secara manual sebelum memanggil WiFiManager.
  // =================================================================
  Serial.println("Melakukan inisialisasi WiFi manual (Workaround)...");
  WiFi.mode(WIFI_STA);    // Secara eksplisit atur mode ke Station (client)
  WiFi.disconnect();      // Putuskan koneksi lama untuk memulai dari awal
  delay(100);             // Beri jeda singkat agar sistem memproses
  Serial.println("Inisialisasi manual selesai.");
  // =================================================================

  // Sekarang, kita serahkan ke WiFiManager
  Serial.println("Menyerahkan kontrol ke WiFiManager...");
  WiFiManager wm;
  
  // wm.resetSettings(); // Hapus komentar ini untuk memaksa konfigurasi ulang

  bool res;
  res = wm.autoConnect("AutoConnectAP", "password"); // Membuat AP jika koneksi gagal

  if (!res) {
    Serial.println("WiFiManager gagal terhubung. Silakan restart board.");
  } else {
    // Jika sampai sini, WORKAROUND BERHASIL!
    Serial.println("BERHASIL! WiFi terhubung via WiFiManager.");
    Serial.print("Alamat IP: ");
    Serial.println(WiFi.localIP());
    
    // Mulai server TCP setelah WiFi terhubung
    server.begin(); 
    Serial.println("Server TCP dimulai di port 8080. Menunggu client...");
  }
}

void loop() {
  // Selalu baca data sensor di setiap loop
  bacaSensor(); 

  // Cek jika ada client baru yang ingin terhubung
  if (server.hasClient()) {
    // Jika sudah ada client yang terhubung, putuskan koneksi lama
    if (client && client.connected()) {
        Serial.println("Client baru mencoba terhubung, memutuskan client lama.");
        client.stop();
    }
    client = server.available(); 
    if (client) {
        Serial.println("Client baru terhubung!");
        client.flush(); // Bersihkan buffer client baru
    }
  }

  // Jika client terhubung, proses datanya
  if (client && client.connected()) {
    if (client.available() > 0) {
      buff = client.readStringUntil('\n'); 
      buff.trim(); // Hapus spasi atau karakter tak terlihat
      Serial.print("Diterima dari client: "); 
      Serial.println(buff);

      // Pastikan buffer tidak kosong sebelum diproses
      if (buff.length() > 0) {
        // --- Parsing Perintah Motor (Format: "M:SPEED:AKSI") ---
        if (buff[0] == 'M') {
          char buff_array[buff.length() + 1]; 
          buff.toCharArray(buff_array, sizeof(buff_array));
          
          char *token = strtok(buff_array, delimiter); // Skip "M"
          if (token != NULL) {
            token = strtok(NULL, delimiter); // Ambil nilai kecepatan
            if (token != NULL) {
              motor_speed_val = atoi(token); 
            } else { motor_speed_val = 0; }
          } else { motor_speed_val = 0; }

          char *action_token = strtok(NULL, delimiter); // Ambil karakter aksi
          if (action_token != NULL && strlen(action_token) > 0) {
            char action = action_token[0];
            if (action == 'F')      { forward(motor_speed_val); }
            else if (action == 'B') { backward(motor_speed_val); }
            else if (action == 'L') { turnLeft(motor_speed_val); }
            else if (action == 'R') { turnRight(motor_speed_val); }
            else if (action == 'S') { stopMotors(); }
            else { Serial.println("Aksi motor tidak dikenal."); stopMotors(); }
          } else { Serial.println("Aksi motor tidak ada, memberhentikan motor."); stopMotors(); }
        } 
        // --- Parsing Perintah Servo (Format: "S:SUDUT") ---
        else if (buff[0] == 'S') {
          char buff_array[buff.length() + 1];
          buff.toCharArray(buff_array, sizeof(buff_array));
          
          char *token = strtok(buff_array, delimiter); // Skip "S"
          if (token != NULL) {
            token = strtok(NULL, delimiter); // Ambil nilai sudut
            if (token != NULL) {
              servo_angle_val = atoi(token); 
              myServo.write(servo_angle_val);
              Serial.print("Servo diatur ke: "); Serial.println(servo_angle_val);
            }
          }
        } 
        // --- Perintah untuk meminta data sensor ---
        else if (buff.startsWith("GETSENSOR")) {
          String sensorData = "SENSORS:";
          sensorData += String(sensor1) + ",";
          sensorData += String(sensor2) + ",";
          sensorData += String(sensor3) + ","; // Nilai analog
          sensorData += String(sensor4) + ",";
          sensorData += String(sensor5);
          client.println(sensorData); // Kirim data ke client
          Serial.print("Dikirim ke client: "); 
          Serial.println(sensorData);
        } 
        else {
            Serial.print("Perintah tidak dikenal: ");
            Serial.println(buff);
        }
      }
    }
  } 
}

void bacaSensor() {
  sensor1 = digitalRead(S1);
  sensor2 = digitalRead(S2);
  sensor3 = analogRead(S3); // Baca sebagai nilai analog
  sensor4 = digitalRead(S4);
  sensor5 = digitalRead(S5);
}

// Fungsi kontrol motor menggunakan analogWrite
void forward(int speed_val) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, speed_val); // Menggunakan analogWrite
  analogWrite(ENB, speed_val); // Menggunakan analogWrite
  Serial.print("Motor: Maju, Kecepatan: "); Serial.println(speed_val);
}

void backward(int speed_val) {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, speed_val); // Menggunakan analogWrite
  analogWrite(ENB, speed_val); // Menggunakan analogWrite
  Serial.print("Motor: Mundur, Kecepatan: "); Serial.println(speed_val);
}

void turnRight(int speed_val) {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, speed_val);
  analogWrite(ENB, speed_val);
  Serial.print("Motor: Belok Kanan (pivot), Kecepatan: "); Serial.println
(speed_val);
}

void turnLeft(int speed_val) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENA, speed_val);
  analogWrite(ENB, speed_val);
  Serial.print("Motor: Belok Kiri (pivot), Kecepatan: "); Serial.println
(speed_val);
}

void stopMotors() {
  analogWrite(ENA, 0); // Menggunakan analogWrite
  analogWrite(ENB, 0); // Menggunakan analogWrite
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  Serial.println("Motor: Berhenti");
}