import asyncio
from bleak import BleakScanner

# TARGET HARDWARE MAC ADDRESS FROM YOUR SYSTEM
TARGET_DEVICE_MAC = "A335BDF3-07C3-3FA0-A3B9-F077E8A03763"
TARGET_SERVICE_UUID = "00005242-0000-1000-8000-00805f9b34fb"

# Keep track of global state since variables are split across packets
latest_climate = {
    'Temperature': 'Waiting...',
    'Humidity': 'Waiting...'
}

def decode_environmental_data(data_bytes):
    global latest_climate
    try:
        if len(data_bytes) < 13:
            return None

        packet_type = data_bytes[10]
        
        # --- TEMPERATURE PACKET ---
        if packet_type == 0x01:
            temp_int = data_bytes[11]
            temp_frac = data_bytes[12]
            # Convert fractional byte to decimal precision
            actual_temp = temp_int + (temp_frac / 100.0) if temp_frac < 100 else temp_int + (temp_frac / 256.0)
            
            # Hotfix for calibration offset if needed
            latest_climate['Temperature'] = f"{actual_temp:.2f} °C"

        # --- HUMIDITY PACKET ---
        elif packet_type == 0x03:
            humidity_int = data_bytes[11]
            latest_climate['Humidity'] = f"{humidity_int} %"

        # --- STATUS PACKETS ---
        elif packet_type in [0x04, 0x06]:
            return None # Ignore heartbeat/status frames to keep terminal clean

        return {
            'Packet Type': 'Holy-IOT Sensor Sync',
            'Temperature': latest_climate['Temperature'],
            'Humidity': latest_climate['Humidity']
        }

    except Exception as e:
        return {"Error": f"Parsing failed: {str(e)}"}

def detection_callback(device, advertisement_data):
    if device.address.upper() == TARGET_DEVICE_MAC.upper():
        print("\n==================================================================")
        print(f"🎯 TARGET DETECTED! [Name: {device.name or 'Unknown'}] | RSSI: {advertisement_data.rssi} dBm")
        print("==================================================================")
        
        # 1. Log Raw Manufacturer Data Window
        if advertisement_data.manufacturer_data:
            print("--- Manufacturer Data ---")
            for company_id, raw_bytes in advertisement_data.manufacturer_data.items():
                print(f" Company Identifier ID: {company_id} (0x{company_id:04X})")
                print(f" Raw Hex Data payload : {raw_bytes.hex().upper()}")
        
        # 2. Log and Parse Service Data Payload Window
        if advertisement_data.service_data:
            print("\n--- Service Data Payload & Parsing ---")
            for service_uuid, raw_bytes in advertisement_data.service_data.items():
                print(f" Service Data UUID    : {service_uuid}")
                print(f" Raw Hex Data payload : {raw_bytes.hex().upper()}")
                print(f" Total Payload Length : {len(raw_bytes)} bytes")
                
                # If this matches our target environment service UUID, parse it!
                if service_uuid.lower() == TARGET_SERVICE_UUID.lower():
                    parsed_climate = decode_environmental_data(raw_bytes)
                    print(f" 🌟 Decoded Climate   : {parsed_climate}") if parsed_climate else None
                
        print("==================================================================")

async def main():
    print(f"Initializing BLE Scanning Engine for target: {TARGET_DEVICE_MAC}...")
    print("Press Ctrl+C inside your VS Code terminal window to terminate anytime.")
    
    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await scanner.stop()
        print("\nScanning sequence suspended successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")