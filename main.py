import sys
sys.path.append("")
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import random
import struct
from machine import Pin
from max6675 import MAX6675

dev = True

#OTA
if not dev:
    from ota import OTAUpdater
    from WIFI_CONFIG import SSID, PASSWORD
    firmware_url = "https://raw.githubusercontent.com/Eastmanlg/hotbox-pico/"
    ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")
    ota_updater.download_and_install_update_if_available()


# org.bluetooth.service.environmental_sensing
_ENV_SENSE_UUID = bluetooth.UUID(0x181A)
# org.bluetooth.characteristic.temperature
_ENV_SENSE_TEMP1_UUID = bluetooth.UUID(0x2A6E) # generic temperature
_ENV_SENSE_TEMP2_UUID = bluetooth.UUID(0x2A6E) # generic temperature
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


# Thermocouple SPI Configuration
sck = Pin(22, Pin.OUT)  # Clock pin
cs0 = Pin(21, Pin.OUT)  # Chip 0 Select pin
so0 = Pin(19, Pin.IN)  # Data 0 pin
cs1 = Pin(20, Pin.OUT)  # Chip Select 1 pin
so1 = Pin(18, Pin.IN)  # Data 1 pin

# Create sensor instances
sensor0 = MAX6675(sck, cs0, so0)
sensor1 = MAX6675(sck, cs1, so1)


# Helper to encode the temperature characteristic encoding (sint16, hundredths of a degree).
def _encode_temperature(temp_deg_f):
    return struct.pack("<h", int(temp_deg_f * 100))


# This would be periodically polling a hardware sensor.
async def sensor_task():
    while True:
        temp1 = sensor0.read()
        temp2 = sensor1.read()
        
        temp1_characteristic.write(_encode_temperature(temp1))
        temp2_characteristic.write(_encode_temperature(temp2))
        
        if dev:
            print(f"Temperature 1: {temp1:.2f} F")
            print(f"Temperature 2: {temp2:.2f} F")
            print()

        await asyncio.sleep_ms(1000)

async def notify_gatt_client(connection):
    if connection is None: return
    temp1_characteristic.notify(connection)
    temp2_characteristic.notify(connection)


# Serially wait for connections. Don't advertise while a central is
# connected.
async def peripheral_task():
    while True:
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


# Run both tasks.
async def main():
    t1 = asyncio.create_task(sensor_task())
    t2 = asyncio.create_task(peripheral_task())
    await asyncio.gather(t1, t2)


asyncio.run(main())