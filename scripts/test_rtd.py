# Tests connection to MAX31865 sensor and prints temperature data.
from machine import SPI, Pin
from max31865 import MAX31865

# SPI bus configuration
spi = SPI(1, baudrate=5000000, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
cs = Pin(13)
    
sensor = MAX31865(spi, cs)
temp = sensor.temperature
print(temp)
print(sensor.read_rtd())