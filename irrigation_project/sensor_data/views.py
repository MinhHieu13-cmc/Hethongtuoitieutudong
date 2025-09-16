from django.shortcuts import render
import paho.mqtt.client as mqtt
from django.utils import timezone
from .models import SensorData, Irrigation
import json
import numpy as np
from joblib import load  # Thay đổi từ pickle sang joblib

# Load model when server starts
model = load('C:\Hethongtuoitieutudong\irrigation_project\pump_decision_model.joblib')  # Sử dụng joblib
print(type(model))


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))
    client.subscribe("sensor/data")


def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print(f"Raw message received: {message}")  # Đầu ra kiểm tra

    try:
        # Kiểm tra xem thông điệp có phải là JSON hợp lệ không
        parsed_data = json.loads(message)

        # Lấy các giá trị từ cảm biến
        soil_moisture = parsed_data.get("soil_moisture")
        if soil_moisture is None:
            # Hỗ trợ cả khóa 'moisture' (trường hợp nguồn khác publish)
            soil_moisture = parsed_data.get("moisture")
        humidity = parsed_data.get("humidity")
        temperature = parsed_data.get("temperature")

        if soil_moisture is not None and humidity is not None and temperature is not None:
            # Lưu dữ liệu cảm biến vào cơ sở dữ liệu
            sensor_data = SensorData(
                temperature=float(temperature),
                humidity=float(humidity),
                soil_moisture=float(soil_moisture),
                timestamp=timezone.now()  # Ghi lại thời gian hiện tại
            )
            sensor_data.save()
            print("Dữ liệu đã được lưu vào cơ sở dữ liệu.")

            # Đảm bảo mô hình được gọi đúng cách
            if hasattr(model, 'predict'):
                print(f"Chuẩn bị dự đoán: T={temperature}, H={humidity}, SM={soil_moisture}")
                predict_and_control_pump(float(temperature), float(humidity), float(soil_moisture))
            else:
                print("Mô hình đã tải không có phương thức 'predict'.")
        else:
            print("Thiếu một hoặc nhiều trường dữ liệu cần thiết.")
    except json.JSONDecodeError as e:
        print(f"Lỗi phân tích JSON: {e}")
    except Exception as e:
        print(f"Lỗi xử lý thông điệp: {e}")


# Function to predict and control the pump
def predict_and_control_pump(temperature, humidity, soil_moisture):
    try:
        input_data = np.array([[temperature, humidity, soil_moisture]])  # Chuyển đổi thành mảng 2 chiều
        prediction = model.predict(input_data)  # Gọi phương thức predict trên mô hình
        print(f"Kết quả dự đoán thô: {prediction}")
        pump_status = True if prediction[0] == 1 else False

        # Publish pump status tới thiết bị: dùng chuỗi "true"/"false" để tương thích code trên thiết bị
        pump_status_str = "true" if pump_status else "false"
        client.publish("pump/control", json.dumps({"pump_status": pump_status_str}))
        print(f"Pump status set to: {'ON' if pump_status else 'OFF'}")
    except Exception as e:
        print(f"Lỗi trong quá trình dự đoán và điều khiển bơm: {e}")


# MQTT client initialization
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)
client.loop_start()


def sensor_data_view(request):
    data = SensorData.objects.all().order_by('-timestamp')[:10]
    return render(request, 'data.html', {'data': data})


def home_view(request):
    return render(request, 'home.html')


def data_visualization_view(request):
    data = SensorData.objects.all().order_by('-timestamp')[:10]
    if not data:
        print("Không có dữ liệu cảm biến.")
    else:
        print(f"Dữ liệu truy vấn: {[item.timestamp for item in data]}")

    context = {
        'timestamps': json.dumps([item.timestamp.strftime("%Y-%m-%d %H:%M:%S") for item in data]),
        'temperatures': json.dumps([item.temperature for item in data]),
        'humidities': json.dumps([item.humidity for item in data]),
        'soil_moistures': json.dumps([item.soil_moisture for item in data]),
    }

    return render(request, 'data_visualization.html', context)


def check_and_start_irrigation():
    latest_sensor_data = SensorData.objects.last()
    if not latest_sensor_data:
        print("No sensor data available.")
        return None

    if latest_sensor_data.temperature and latest_sensor_data.humidity:  # Điều kiện giả định
        irrigation = Irrigation.objects.create(
            sensor_data=latest_sensor_data,
            start_time=timezone.now()
        )
        return irrigation
    return None


def end_irrigation(irrigation_id, water_used):
    try:
        irrigation = Irrigation.objects.get(id=irrigation_id)
        irrigation.end_time = timezone.now()
        irrigation.water_used = water_used
        irrigation.save()
    except Irrigation.DoesNotExist:
        print("Irrigation record does not exist.")


def irrigation_view(request):
    # Truy vấn tất cả các phiên tưới tiêu để hiển thị
    irrigation_data = Irrigation.objects.all()

    # Bắt đầu phiên tưới tiêu mới nếu có dữ liệu hợp lệ
    irrigation = check_and_start_irrigation()
    if irrigation:
        irrigation_data = Irrigation.objects.all()  # Cập nhật lại danh sách nếu có phiên mới

    # Truyền danh sách phiên tưới tiêu vào template
    return render(request, 'irrigation.html', {'irrigation_data': irrigation_data})