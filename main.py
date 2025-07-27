import sys
sys.path.append("")
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import random
import struct
from machine import Pin
from max31865 import MAX31865
from machine import SPI
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
_ENV_SENSE_TEMP2_UUID = bluetooth.UUID(0x2A1C) # generic temperature
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

# MAX31865 (Temp2) on SPI1
sck1 = Pin(10, Pin.OUT)     # SPI1 Clock
cs2 = Pin(9, Pin.OUT)       # MAX31865 Chip Select
mosi = Pin(11, Pin.OUT)     # MAX31865 MOSI
miso = Pin(12, Pin.IN)      # MAX31865 MISO

# Create sensor instance for MAX6675
sensor0 = MAX6675(sck0, cs0, so0)

# Create SPI1 bus and MAX31865 instance
spi = SPI(1, baudrate=5000000, sck=sck1, mosi=mosi, miso=miso)
sensor1 = MAX31865(spi, cs2)


# Helper to encode the temperature characteristic encoding (sint16, hundredths of a degree).
def _encode_temperature(temp_deg_f):
    return struct.pack("<h", int(temp_deg_f * 100))


# This would be periodically polling a hardware sensor.
async def sensor_task():
    while True:
        temp1 = get_filtered_temp(sensor0)
        # temp2 = get_filtered_temp(sensor1)
        config = 0xD2  # 11010010
        sensor1.configure(config)
        temp2 = sensor1.temperature  # Use MAX31865's temperature method

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