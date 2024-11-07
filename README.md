# Hethongtuoitieutudong
Raspberry pi pico w
main.py 

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

# Initialize MQTT client
def connect_mqtt():
    try:
        client = MQTTClient("pico", "broker.hivemq.com", port=1883)
        client.set_callback(on_message)  # Set callback for control command
        client.connect()
        client.subscribe(b"pump/control")  # Listen for control commands from Django
        print("Connected to MQTT broker and subscribed to control channel")
        return client
    except Exception as e:
        print("Error connecting to MQTT:", e)
        return None

# Callback to receive control commands from server
def on_message(topic, msg):
    try:
        command = json.loads(msg)
        pump_status = command.get("pump_status")
        
        if pump_status == "true":
            relay.on()  # Turn on pump
            print("Pump turned ON by server command.")
        elif pump_status == "false":
            relay.off()  # Turn off pump
            print("Pump turned OFF by server command.")
        else:
            print("Invalid command:", msg)
    except json.JSONDecodeError:
        print("JSON decode error:", msg)

# Function to get current timestamp
def get_time():
    rtc = machine.RTC()
    current_time = rtc.datetime()  # Returns tuple (year, month, day, weekday, hours, minutes, seconds, subseconds)
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(*current_time)

# Main function
def main():
    connect_wifi("Samsung", "khongcho")
    client = connect_mqtt()
    if not client:
        print("Cannot connect to MQTT. Check connection.")
        return

    while True:
        try:
            # Read DHT22 sensor
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            
            # Read soil moisture sensor
            soil_moisture = soil_moisture_sensor.read_u16()  # Value from 0 to 65535
            
            # Get current time
            timestamp = get_time()  # Use function to get time

            # Create JSON message to send sensor data
            message = {
                "timestamp": timestamp,
                "temperature": temp,
                "humidity": humidity,
                "soil_moisture": soil_moisture
            }
            json_message = json.dumps(message)
            
            # Publish data via MQTT
            client.publish(b"sensor/data", json_message)
            print("Data sent:", json_message)
            
            # Listen for commands from server
            client.check_msg()

        except OSError as e:
            print("Sensor error:", e)
        
        except Exception as e:
            print("Error:", e)
        
        # Wait 10 seconds before reading and sending data again
        time.sleep(10)

# Run the program
main()

