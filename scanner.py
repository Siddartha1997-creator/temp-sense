import asyncio
from bleak import BleakScanner

def detection_callback(device, advertisement_data):
    # Print out everything discovered to find your tag's unique macOS ID
    name = device.name or "Unknown Device"
    
    # We look for "Holyiot", "Holy", or common beacon keywords
    if "holy" in name.lower() or advertisement_data.service_data:
        print(f"Device Found: {name}")
        print(f" -> macOS Identifier String: {device.address}")
        print(f" -> RSSI Signal Strength  : {advertisement_data.rssi} dBm")
        print("-" * 50)

async def main():
    print("Scanning for all local beacons... look for 'Holyiot' in the output.")
    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    await asyncio.sleep(15)  # Scan for 15 seconds
    await scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())