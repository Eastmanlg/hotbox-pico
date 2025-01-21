import time
from machine import Pin, SPI
from max6675 import MAX6675

# SPI Configuration
# sck = Pin(22, Pin.OUT)  # Clock pin
# cs = Pin(21, Pin.OUT)  # Chip Select pin
# so = Pin(19, Pin.IN)  # Data pin

# SPI Configuration
sck = Pin(22, Pin.OUT)  # Clock pin
cs = Pin(20, Pin.OUT)  # Chip Select pin
so = Pin(18, Pin.IN)  # Data pin

# Create MAX6675 sensor instance
sensor = MAX6675(sck, cs, so)

# Function to read temperature
def read_temperature():
    try:
        temp_c = sensor.read()
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        print(f"Temperature: {temp_f:.2f} F")
    except Exception as e:
        print(f"Error reading temperature: {e}")

# Polling loop
while True:
    read_temperature()
    time.sleep(0.2)  # Poll every 2 seconds