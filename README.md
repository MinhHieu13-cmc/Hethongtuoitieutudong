
---

# 🌱 Hệ Thống Tưới Tiêu Tự Động

> **Sử dụng Raspberry Pi Pico W, MQTT và cảm biến DHT22 + độ ẩm đất**

---

## 🛠️ Thành phần phần cứng

* Raspberry Pi Pico W
* Cảm biến DHT22 (nhiệt độ & độ ẩm không khí)
* Cảm biến độ ẩm đất (Soil Moisture Sensor)
* Relay module (điều khiển máy bơm)
* Máy bơm mini
* Kết nối WiFi

---

## 🧠 Chức năng chính

* Đọc cảm biến nhiệt độ, độ ẩm, độ ẩm đất
* Gửi dữ liệu lên máy chủ thông qua MQTT
* Nhận lệnh điều khiển từ xa để bật/tắt bơm
* Gửi dữ liệu định kỳ mỗi 10 giây

---

## 📂 Cấu trúc thư mục

```
/Hethongtuoitieutudong
├── main.py       # Mã nguồn chính cho Raspberry Pi Pico W
└── README.md     # Tài liệu hướng dẫn
```

---

## 🔄 Cấu hình MQTT

* Broker: `broker.hivemq.com`
* Gửi dữ liệu: `sensor/data`
* Nhận điều khiển: `pump/control`

---

## ▶️ Cách chạy

1. Kết nối phần cứng đúng sơ đồ chân (GPIO)
2. Mở Thonny IDE, nạp `main.py` vào Pico W
3. Đảm bảo đổi đúng WiFi:

   ```python
   connect_wifi("Samsung", "khongcho")
   ```
4. Xem dữ liệu trên MQTT client hoặc website

---

## 📜 Mã nguồn `main.py`

```python
import network
import time
from umqtt.simple import MQTTClient
import dht
import machine
import json

# Initialize DHT22 and soil moisture sensor
dht_sensor = dht.DHT22(machine.Pin(0))  # DHT22 on GPIO 0
soil_moisture_sensor = machine.ADC(28)  # Soil moisture on GPIO 28

# Setup relay for pump
relay = machine.Pin(26, machine.Pin.OUT)  # Relay on GPIO 26
relay.off()  # Initially turn off pump

# Connect to WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    print('Network config:', wlan.ifconfig())

# Callback to receive control commands
def on_message(topic, msg):
    try:
        command = json.loads(msg)
        pump_status = command.get("pump_status")
        if pump_status == "true":
            relay.on()
            print("Pump turned ON by server command.")
        elif pump_status == "false":
            relay.off()
            print("Pump turned OFF by server command.")
        else:
            print("Invalid command:", msg)
    except json.JSONDecodeError:
        print("JSON decode error:", msg)

# MQTT connection
def connect_mqtt():
    try:
        client = MQTTClient("pico", "broker.hivemq.com", port=1883)
        client.set_callback(on_message)
        client.connect()
        client.subscribe(b"pump/control")
        print("Connected to MQTT broker and subscribed to control channel")
        return client
    except Exception as e:
        print("Error connecting to MQTT:", e)
        return None

# Get formatted time string
def get_time():
    rtc = machine.RTC()
    current_time = rtc.datetime()
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(*current_time)

# Main loop
def main():
    connect_wifi("Samsung", "khongcho")
    client = connect_mqtt()
    if not client:
        print("Cannot connect to MQTT. Check connection.")
        return

    while True:
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            soil_moisture = soil_moisture_sensor.read_u16()
            timestamp = get_time()

            message = {
                "timestamp": timestamp,
                "temperature": temp,
                "humidity": humidity,
                "soil_moisture": soil_moisture
            }
            json_message = json.dumps(message)
            client.publish(b"sensor/data", json_message)
            print("Data sent:", json_message)
            client.check_msg()

        except OSError as e:
            print("Sensor error:", e)
        except Exception as e:
            print("Error:", e)

        time.sleep(10)

# Run
main()
```

---

## 📬 Gửi lệnh điều khiển từ xa

* Bật bơm:

```json
{"pump_status": "true"}
```

* Tắt bơm:

```json
{"pump_status": "false"}
```

---

