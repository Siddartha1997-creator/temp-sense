#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

#define BOOT_BUTTON 27 

BLEScan* pBLEScan;
const int SCAN_TIME_SECONDS = 1;        
unsigned long lastScanTime = 0;
const unsigned long SCAN_INTERVAL_MS = 6000; // Scans every 6 seconds

// --- GLOBAL TELEMETRY STORAGE ---
// Global state captures multiplexed values cycling through different packets
float globalTemperature = -999.0;
float globalHumidity = -999.0;

class HolyiotTelemetryLogger: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    
    int serviceDataCount = advertisedDevice.getServiceDataUUIDCount();
    
    // Target UUID for Climate Broadcasts
    BLEUUID targetUUID("00005242-0000-1000-8000-00805f9b34fb");

    for (int i = 0; i < serviceDataCount; i++) {
      BLEUUID currentUUID = advertisedDevice.getServiceDataUUID(i);
      
      if (currentUUID.equals(targetUUID)) {
        String rawData = advertisedDevice.getServiceData(i);
        int payloadLength = rawData.length();
        
        // Ensure payload captures all 13 required structural bytes
        if (payloadLength >= 13) {
          
          uint8_t packetType = (uint8_t)rawData[10];
          bool stateUpdated = false;

          // --- CASE 0x01: TEMPERATURE FRAME ---
          if (packetType == 0x01) {
            uint8_t temp_int = (uint8_t)rawData[11];
            uint8_t temp_frac = (uint8_t)rawData[12];
            
            // Replicate fractional byte conversion logic
            if (temp_frac < 100) {
              globalTemperature = temp_int + (temp_frac / 100.0);
            } else {
              globalTemperature = temp_int + (temp_frac / 256.0);
            }
            stateUpdated = true;
          }
          
          // --- CASE 0x03: HUMIDITY FRAME ---
          else if (packetType == 0x03) {
            uint8_t humidity_int = (uint8_t)rawData[11];
            globalHumidity = (float)humidity_int;
            stateUpdated = true;
          }

          // --- OUTPUT REFRESH ---
          if (stateUpdated) {
            Serial.println("\n==================================================");
            Serial.printf("🎯 TARGET DETECTED! [Name: Holy-IOT] | RSSI: %d dBm\n", advertisedDevice.getRSSI());
            Serial.printf("MAC Address          : %s\n", advertisedDevice.getAddress().toString().c_str());
            Serial.printf("Packet Type Filter   : 0x%02X\n", packetType);
            Serial.println("--------------------------------------------------");
            
            if (globalTemperature != -999.0) {
              Serial.printf("🌟 Temperature       : %.2f °C\n", globalTemperature);
            } else {
              Serial.println("🌟 Temperature       : Waiting for sync...");
            }

            if (globalHumidity != -999.0) {
              Serial.printf("🌟 Humidity          : %.1f %%\n", globalHumidity);
            } else {
              Serial.println("🌟 Humidity          : Waiting for sync...");
            }
            Serial.println("==================================================");
          }
          
          break; // Match confirmed, skip evaluation loops for this frame
        }
      }
    }
  }
};

void setup() {
  Serial.begin(115200);
  while(!Serial); 
  
  Serial.println("Initializing Calibrated Holyiot Multiplex Reader...");
  pinMode(BOOT_BUTTON, INPUT_PULLUP);

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); 
  pBLEScan->setAdvertisedDeviceCallbacks(new HolyiotTelemetryLogger());
  
  pBLEScan->setActiveScan(true); 
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99); 
  
  Serial.println("Scanner engine online. Awaiting sensor broadcasts...");
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastScanTime >= SCAN_INTERVAL_MS) {
    pBLEScan->start(SCAN_TIME_SECONDS, false);
    pBLEScan->clearResults(); 
    lastScanTime = millis();
  }
}