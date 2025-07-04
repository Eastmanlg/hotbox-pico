import threading
import struct
import bleak
import time
from queue import Queue

# UUIDs for BLE service and characteristics
_ENV_SENSE_UUID = "0000181A-0000-1000-8000-00805f9b34fb"
_ENV_SENSE_TEMP1_UUID = "00002A6E-0000-1000-8000-00805f9b34fb"
_ENV_SENSE_TEMP2_UUID = "00002A1C-0000-1000-8000-00805f9b34fb"

def _decode_temperature(data):
    return struct.unpack("<h", data)[0] / 100

class BLEClient(threading.Thread):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.running = True
    
    async def find_temp_sensor(self):
        name = 'mpy-temp'
        return await bleak.BleakScanner.find_device_by_name(name)
    
    async def connect_and_listen(self):
        device = await self.find_temp_sensor()
        if not device:
            print("Temperature sensor not found")
            return
        
        async with bleak.BleakClient(device) as client:
            service = client.services.get_service(_ENV_SENSE_UUID)
            if service is None:
                print("Temperature service not found")
                return
            
            temp1_characteristic = service.get_characteristic(_ENV_SENSE_TEMP1_UUID)
            temp2_characteristic = service.get_characteristic(_ENV_SENSE_TEMP2_UUID)
            
            if not temp1_characteristic or not temp2_characteristic:
                print("Temperature characteristics not found")
                return
            
            async def _callback(sender, data):
                temperature = _decode_temperature(data)
                self.data_queue.put((sender.uuid, temperature))
            
            await client.start_notify(temp1_characteristic, _callback)
            await client.start_notify(temp2_characteristic, _callback)
            
            while self.running:
                await asyncio.sleep(1)
    
    def run(self):
        asyncio.run(self.connect_and_listen())
    
    def stop(self):
        self.running = False