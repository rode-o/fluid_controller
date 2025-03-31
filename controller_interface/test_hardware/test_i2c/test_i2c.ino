#include <Wire.h>
#include <Arduino.h>

void setup() {
  // Start serial communication for debugging
  Serial.begin(115200);
  delay(100); // Allow serial to initialize
  Serial.println("\n=== Simple I2C Scanner ===");

  // Initialize I2C
  Wire.begin();
  Serial.println("[INIT] I2C bus initialized.\n");

  // Perform the initial I2C scan
  i2cScan();
}

void loop() {
  // Periodically scan for devices on the I2C bus
  Serial.println("\n--- [LOOP] Scanning I2C bus ---");
  i2cScan();
  delay(1000); // Delay between scans
}

void i2cScan() {
  Serial.println("[I2C SCAN] Searching for devices on the bus...");

  bool deviceFound = false;
  for (uint8_t address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    uint8_t error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("  Found device at 0x");
      if (address < 16) Serial.print('0');
      Serial.println(address, HEX);
      deviceFound = true;
    } else if (error == 4) {
      Serial.print("  Error at 0x");
      if (address < 16) Serial.print('0');
      Serial.print(address, HEX);
      Serial.println(" => Bus error");
    }
  }

  if (!deviceFound) {
    Serial.println("  No I2C devices found. (Check wiring/power!)");
  }

  Serial.println("[I2C SCAN END]\n");
}
