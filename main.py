import sys
sys.path.append("")
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import random
import struct
from machine import Pin
from max31865 import Max31865
from machine import SPI
from max6675 import MAX6675
import time


# Set CS HIGH before anything else
Pin(9, Pin.OUT, value=1)  # Ensures sensor starts deselected (idle high)
max_power = Pin(28, Pin.OUT, value=1)  # Pin to control power to the MAX31865

# Let MAX31865 power up fully
time.sleep(0.1)

dev = True

# OTA
if not dev:
    from ota import OTAUpdater
    from WIFI_CONFIG import SSID, PASSWORD
    firmware_url = "https://raw.githubusercontent.com/Eastmanlg/hotbox-pico/"
    ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
    ota_updater.download_and_install_update_if_available()

# org.bluetooth.service.environmental_sensing
_ENV_SENSE_UUID = bluetooth.UUID(0x181A)
# org.bluetooth.characteristic.temperature
_ENV_SENSE_TEMP1_UUID = bluetooth.UUID(0x2A6E)  # generic temperature
_ENV_SENSE_TEMP2_UUID = bluetooth.UUID(0x2A1C)  # generic temperature
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)
# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000

# Register GATT server.
temp_service = aioble.Service(_ENV_SENSE_UUID)

# Needs characteristics to read and notify temperature.
temp1_characteristic = aioble.Characteristic(
    temp_service, _ENV_SENSE_TEMP1_UUID, read=True, notify=True
)
temp2_characteristic = aioble.Characteristic(
    temp_service, _ENV_SENSE_TEMP2_UUID, read=True, notify=True
)

aioble.register_services(temp_service)

# Thermocouple and RTD SPI Configuration

# MAX6675 (Temp1) on SPI0
sck0 = Pin(2, Pin.OUT)      # SPI0 Clock
cs0 = Pin(3, Pin.OUT)       # MAX6675 Chip Select
so0 = Pin(4, Pin.IN)        # MAX6675 MISO


# Create sensor instance for MAX6675
sensor0 = MAX6675(sck0, cs0, so0)

# Create MAX31865 instance
sensor1 = Max31865(
    bus=1,
    cs=9,
    wires=3,
    misoPin=12,
    mosiPin=11,
    sckPin=10,
    filter_frequency=60,  # Or 50 depending on your mains
    ref_resistor=430.0
)

# Power cycle the MAX31865 to ensure it starts fresh
time.sleep(0.2)   # Allow MAX31865 to stabilize
max_power.off()    # Cut power
time.sleep(0.2)     # Wait
max_power.on()     # Power on sensor
time.sleep(0.2)     # Let it stabilize


# Helper to encode the temperature characteristic encoding (sint16, hundredths of a degree).
def _encode_temperature(temp_deg_f):
    return struct.pack("<i", int(temp_deg_f * 100))

# Custom median function
def median(data):
    data = sorted(data)
    n = len(data)
    mid = n // 2
    if n % 2 == 0:
        return (data[mid - 1] + data[mid]) / 2
    else:
        return data[mid]

# Multi-sample median filter for robustness
def get_filtered_temp(sensor, samples=4, delay=0.2):
    readings = []
    for _ in range(samples):
        t = sensor.read()
        if t is not None and t > 0:
            readings.append(t)
        # time.sleep(delay)  # Delay is fine here since uasyncio is not used inside

    if not readings:
        return 32.0  # fallback to 32°F if sensor fails

    return median(readings)

# This would be periodically polling a hardware sensor.
async def sensor_task():
    while True:
        temp1 = get_filtered_temp(sensor0)
        # temp2 = get_filtered_temp(sensor1)
        temp2C = sensor1.temperature  # Use MAX31865's temperature method
        temp2 = (temp2C * 9 / 5) + 32  # Convert Celsius to Fahrenheit

        faults = sensor1.fault
        if any(faults):
            print(f"MAX31865 Fault detected: {faults}")
            sensor1.clear_faults()



        temp1_characteristic.write(_encode_temperature(temp1))
        temp2_characteristic.write(_encode_temperature(temp2))

        if dev:
            print(f"Grill:\t{temp1:.2f} F")
            print(f"Drum:\t{temp2:.2f} F")
            print()

        await asyncio.sleep(1)

async def notify_gatt_client(connection):
    if connection is None:
        print("No connection to notify.")
        return
    temp1_characteristic.notify(connection)
    temp2_characteristic.notify(connection)
    #print("Notified GATT client with temperature data.")

# Serially wait for connections. Don't advertise while a central is
# connected.
async def peripheral_task():
    print("Starting BLE task...")
    while True:
        print("Waiting for a GATT client to connect...")
        async with await aioble.advertise(
            _ADV_INTERVAL_MS,
            name="mpy-temp",
            services=[_ENV_SENSE_UUID],
            appearance=_ADV_APPEARANCE_GENERIC_THERMOMETER,
        ) as connection:
            print("Connection from", connection.device)

            while connection.is_connected():
                await notify_gatt_client(connection)
                await asyncio.sleep(1)
            print("Disconnected from", connection.device)

# Run both tasks.
async def main():
    t1 = asyncio.create_task(sensor_task())
    t2 = asyncio.create_task(peripheral_task())
    await asyncio.gather(t1, t2)

asyncio.run(main())