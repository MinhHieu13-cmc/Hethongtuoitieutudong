from django.apps import AppConfig

class SensorDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sensor_data'

    def ready(self):
        # Import trực tiếp từ views.py để khởi động MQTT client khi ứng dụng bắt đầu
        from .views import client

        # Bắt đầu vòng lặp cho MQTT client
        client.loop_start()
