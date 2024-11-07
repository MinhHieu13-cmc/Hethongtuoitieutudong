from django.urls import path
from .views import sensor_data_view,home_view,data_visualization_view,irrigation_view,predict_and_control_pump


urlpatterns = [
    path('data/', sensor_data_view, name='sensor_data_view'),
    path('', home_view, name='home'),
    path('data/visualization/', data_visualization_view, name='data_visualization'),
    path('irrigation/', irrigation_view, name='irrigation_view'),
]

            