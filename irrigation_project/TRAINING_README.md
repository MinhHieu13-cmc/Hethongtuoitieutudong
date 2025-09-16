Pump Decision Model Training Guide

This document explains how to train the K-Means clustering model (pump_decision_model.joblib) from the existing SQLite database.

Prerequisites
- Python environment with scikit-learn and joblib installed.
- The SQLite database irrigation_project\db.sqlite3 containing table sensor_data_sensordata.

Steps
1) Activate your virtual environment (optional).
2) Install dependencies if needed:
   pip install scikit-learn joblib numpy
3) Run the training script from the irrigation_project folder:
   python train_pump_model.py

What the script does
- Reads features [temperature, humidity, soil_moisture] from sensor_data_sensordata.
- Uses K-Means (n_clusters=2) to cluster data into two groups without needing ON/OFF labels.
- Automatically maps the cluster with lower average soil_moisture to ON (1), the other to OFF (0).
- Saves a wrapper model to irrigation_project\pump_decision_model.joblib which exposes predict() returning 0/1 and is used by the Django app in sensor_data\views.py.

Notes
- If the database has very few rows, the clustering may be unstable; the script will still run.
- Missing values (if any) are imputed with median before clustering.
