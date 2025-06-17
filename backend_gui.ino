#include <WiFi.h>
#include <WiFiManager.h> // https://github.com/tzapu/WiFiManager
#include <ESP32Servo.h>

// Pin untuk Motor
#define ENA 19 // Kiri (Motor A)
#define IN1 18
#define IN2 5

#define ENB 4  // Kanan (Motor B)
#define IN3 17
#define IN4 16

// Pin untuk Sensor Garis
#define S1 35
#define S2 32
#define S3 33 // Pin analog untuk sensor S3
#define S4 25
#define S5 26

// Pin untuk Servo
#define SERVO_PIN 2

Servo myServo;

// Server WiFi
WiFiServer server(8080); // Server akan listen di port 8080
WiFiClient client;       // Merepresentasikan client yang terhubung

// Variabel untuk menyimpan data
String buff;
const char delimiter[] = ":";
int motor_speed_val, servo_angle_val;
int sensor1, sensor2, sensor3, sensor4, sensor5;

void setup() {
  Serial.begin(115200); // Mulai komunikasi serial untuk debugging

  // Set pin motor sebagai OUTPUT
  pinMode(ENA, OUTPUT); // ENA akan dikontrol dengan analogWrite
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT); // ENB akan dikontrol dengan analogWrite
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Set pin sensor sebagai INPUT
  pinMode(S1, INPUT);
  pinMode(S2, INPUT);
  pinMode(S3, INPUT);
  pinMode(S4, INPUT);
  pinMode(S5, INPUT);

  stopMotors(); // Inisialisasi motor dalam keadaan berhenti
  myServo.attach(SERVO_PIN);
  myServo.write(0); // Posisi awal servo

  // WiFiManager
  WiFiManager wm;
  bool res;
  res = wm.autoConnect("AutoConnectAP","password");

  if (!res) {
    Serial.println("Gagal terhubung ke WiFi");
  } else {
    Serial.println("WiFi terhubung!");
    Serial.print("Alamat IP: ");
    Serial.println(WiFi.localIP());
    server.begin();
    Serial.println("Server TCP dimulai. Menunggu client...");
  }
}

void loop() {
  sensor();

  if (server.hasClient()) {
    if (client && client.connected()) {
        Serial.println("Client baru mencoba terhubung, memutuskan client
lama.");
        client.stop();
    }
    client = server.available();
    if (client) {
        Serial.println("Client baru terhubung!");
        client.flush();
    }
  }

  if (client && client.connected()) {
    if (client.available() > 0) {
      buff = client.readStringUntil('\n');
      buff.trim();
      Serial.print("Diterima dari client: ");
      Serial.println(buff);

      if (buff.length() > 0) {
        if (buff[0] == 'M') {
          char buff_array[buff.length() + 1];
          buff.toCharArray(buff_array, sizeof(buff_array));

          char *token = strtok(buff_array, delimiter);
          if (token != NULL) {
            token = strtok(NULL, delimiter);
            if (token != NULL) {
              motor_speed_val = atoi(token);
            } else {
              motor_speed_val = 0;
            }
          } else {
            motor_speed_val = 0;
          }

          char *action_token = strtok(NULL, delimiter);
          if (action_token != NULL && strlen(action_token) > 0) {
            char action = action_token[0];
            if (action == 'F') {
              forward(motor_speed_val);
            } else if (action == 'B') {
              backward(motor_speed_val);
            } else if (action == 'L') {
              turnLeft(motor_speed_val);
            } else if (action == 'R') {
              turnRight(motor_speed_val);
            } else if (action == 'S') {
              stopMotors();
            } else {
              Serial.println("Aksi motor tidak dikenal.");
              stopMotors();
            }
          } else {
            Serial.println("Aksi motor tidak ada, memberhentikan motor.");
            stopMotors();
          }
        }
        else if (buff[0] == 'S') {
          char buff_array[buff.length() + 1];
          buff.toCharArray(buff_array, sizeof(buff_array));

          char *token = strtok(buff_array, delimiter);
          if (token != NULL) {
            token = strtok(NULL, delimiter);
            if (token != NULL) {
              servo_angle_val = atoi(token);
              myServo.write(servo_angle_val);
              Serial.print("Servo diatur ke: "); Serial.println
(servo_angle_val);
            }
          }
        }
        else if (buff.startsWith("GETSENSOR")) {
          String sensorData = "SENSORS:";
          sensorData += String(sensor1) + ",";
          sensorData += String(sensor2) + ",";
          sensorData += String(sensor3) + ",";
          sensorData += String(sensor4) + ",";
          sensorData += String(sensor5);
          client.println(sensorData);
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

void sensor() {
  sensor1 = digitalRead(S1);
  sensor2 = digitalRead(S2);
  sensor3 = analogRead(S3);
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
