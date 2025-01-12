import asyncio
import logging
import struct

import bleak

logger = logging.getLogger(__name__)

# org.bluetooth.service.environmental_sensing
_ENV_SENSE_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x181A)
# org.bluetooth.characteristic.temperature
_ENV_SENSE_TEMP_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2A6E)


def _decode_temperature(data):
    return struct.unpack("<h", data)[0] / 100


def _callback(sender: bleak.BleakGATTCharacteristic, data: bytearray):
    data = None if not data else _decode_temperature(data)
    print(f"{sender}: {data}")


async def find_temp_sensor():
    name = 'mpy-temp'
    return await bleak.BleakScanner.find_device_by_name(name)


async def do_connect():
    logger.info("Start scanning for temperature sensor device")
    device = await find_temp_sensor()
    if not device:
        logger.error("Temperature sensor not found")
        return

    async with bleak.BleakClient(device) as client:
        # Get the service:
        service = client.services.get_service(_ENV_SENSE_UUID)
        if service is None:
            logger.error("Temperature service not found")
            return

        characteristic = service.get_characteristic(_ENV_SENSE_TEMP_UUID)
        if characteristic is None:
            logger.error("Temperature characteristic not found")
            return

        await client.start_notify(characteristic, _callback)
        while client.is_connected:
            await asyncio.sleep(5)


async def main():
    while True:
        await do_connect()

asyncio.run(main())
