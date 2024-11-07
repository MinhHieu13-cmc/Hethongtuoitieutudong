from django.db import models

class SensorData(models.Model):
    temperature = models.FloatField()
    humidity = models.FloatField()
    soil_moisture = models.FloatField(default=0.0)  # Độ ẩm đất
    timestamp = models.DateTimeField(auto_now_add=True)

class Irrigation(models.Model):
    sensor_data = models.ForeignKey(SensorData, on_delete=models.CASCADE, null=True)  # Thêm null=True
    start_time = models.DateTimeField()  # Thời gian bắt đầu tưới
    end_time = models.DateTimeField(null=True, blank=True)  # Thời gian kết thúc tưới
    water_used = models.FloatField(default=0.0)  # Lượng nước sử dụng

    def __str__(self):
        return f"Irrigation from {self.start_time} to {self.end_time}"
