#include <Wire.h>
#include <Arduino.h>

// --------------------------------------------------------------------------
// Adjust these for your sensor configuration:
static const uint8_t SLF_FLOW_SENSOR_ADDR     = 0x08;  // 7-bit address
static const uint8_t SLF_START_CMD            = 0x36;
static const uint8_t SLF_CALIBRATION_CMD_BYTE = 0x08;
static const uint8_t SLF_STOP_CMD             = 0x3F;
static const uint8_t SLF_STOP_BYTE            = 0xF9;

// Example scale factor for your sensor (check datasheet)
#define SLF_SCALE_FACTOR_FLOW 120.0f

// Low-pass filter factor
#define FLOW_FILTER_ALPHA 0.1f

// --------------------------------------------------------------------------
bool  measuringFlow = false;
float filteredFlow  = 0.0f;

// --------------------------------------------------------------------------
// Helper to interpret endTransmission() error codes.
String interpretWireError(uint8_t errCode) {
  switch (errCode) {
    case 0: return "Success (no error)";
    case 1: return "Data too long to fit in transmit buffer";
    case 2: return "Received NACK on transmit of address";
    case 3: return "Received NACK on transmit of data";
    case 4: return "Other error (could be bus-related, SDA/SCL shorted, etc.)";
#if (ARDUINO >= 10000) // Some cores define 5 as timeout
    case 5: return "Timeout";
#endif
    default: return "Unknown error code";
  }
}

// --------------------------------------------------------------------------
// I2C scan function: prints each device it finds, or if none found, warns user.
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
      Serial.println(" => Could not detect device (bus error?)");
    }
  }
  if (!deviceFound) {
    Serial.println("  No I2C devices found. (Check wiring/power!)");
  }
  Serial.println("[I2C SCAN END]\n");
}

// --------------------------------------------------------------------------
// A stub calibration factor function (replace as needed)
float getCalFactor() {
  return 1.0f;
}

// --------------------------------------------------------------------------
// Start continuous measurement
bool startFlowMeasurement() {
  Serial.print("[START] Sending Start Measurement command to 0x");
  Serial.println(SLF_FLOW_SENSOR_ADDR, HEX);

  Wire.beginTransmission(SLF_FLOW_SENSOR_ADDR);
  Wire.write(SLF_START_CMD);
  Wire.write(SLF_CALIBRATION_CMD_BYTE);
  uint8_t err = Wire.endTransmission(true);

  Serial.print("  -> Wire.endTransmission() returned: ");
  Serial.println(interpretWireError(err));

  if (err == 0) {
    measuringFlow = true;
    Serial.println("  -> Measurement mode command ACKed. Sensor should be in measurement mode now.\n");
    return true;
  } else {
    Serial.println("  -> Sensor did NOT ACK the start command. It may not be responding or at a different address.\n");
    return false;
  }
}

// --------------------------------------------------------------------------
// Stop measurement if needed
void stopFlowMeasurement() {
  Serial.print("[STOP] Sending Stop Measurement command to 0x");
  Serial.println(SLF_FLOW_SENSOR_ADDR, HEX);

  Wire.beginTransmission(SLF_FLOW_SENSOR_ADDR);
  Wire.write(SLF_STOP_CMD);
  Wire.write(SLF_STOP_BYTE);
  uint8_t err = Wire.endTransmission(true);

  Serial.print("  -> Wire.endTransmission() returned: ");
  Serial.println(interpretWireError(err));
  measuringFlow = false;
  Serial.println("  -> Measurement stopped.\n");
}

// --------------------------------------------------------------------------
// Read flow from sensor (if measuring)
float readFlow() {
  if (!measuringFlow) {
    Serial.println("[READ] Attempted read, but measuringFlow == false. No data.\n");
    return 0.0f;
  }

  // Request 3 bytes: high, low, CRC
  Serial.print("[READ] Requesting 3 bytes from sensor 0x");
  Serial.print(SLF_FLOW_SENSOR_ADDR, HEX);
  Serial.println("...");

  uint8_t requested = 3;
  uint8_t received  = Wire.requestFrom(SLF_FLOW_SENSOR_ADDR, requested);

  // If we didn't get enough bytes, print possible reasons
  if (received < requested) {
    Serial.print("  WARNING: requested ");
    Serial.print(requested);
    Serial.print(" byte(s), got ");
    Serial.print(received);
    Serial.println(" byte(s). Potential issues:\n"
                   "   * Sensor not actually in measurement mode\n"
                   "   * Incorrect address/wiring\n"
                   "   * Insufficient time after start command\n"
                   "   * Bus lockup\n");
    return filteredFlow;
  }

  // Read the 3 bytes
  uint8_t highByte = Wire.read();
  uint8_t lowByte  = Wire.read();
  uint8_t crcByte  = Wire.read(); // ignoring actual CRC check in this example

  Serial.print("  [DEBUG] Raw I2C bytes => high=0x");
  Serial.print(highByte, HEX);
  Serial.print(" low=0x");
  Serial.print(lowByte, HEX);
  Serial.print(" crc=0x");
  Serial.println(crcByte, HEX);

  // Combine into signed 16-bit
  uint16_t raw = (uint16_t)(highByte << 8) | lowByte;
  int16_t signedFlow = (int16_t)raw;

  // Convert to flow units
  float flowRaw = (float)signedFlow / SLF_SCALE_FACTOR_FLOW;
  float cal     = getCalFactor();
  float flowCal = flowRaw * cal;

  // Low-pass filter
  filteredFlow = (FLOW_FILTER_ALPHA * flowCal) + 
                 ((1.0f - FLOW_FILTER_ALPHA) * filteredFlow);

  Serial.print("  [DEBUG] Signed raw = ");
  Serial.print(signedFlow);
  Serial.print(" => flowRaw = ");
  Serial.print(flowRaw, 4);
  Serial.print(" => calFactor = ");
  Serial.print(cal, 4);
  Serial.print(" => flowCal = ");
  Serial.print(flowCal, 4);
  Serial.print(" => filteredFlow = ");
  Serial.println(filteredFlow, 4);

  return filteredFlow;
}

// --------------------------------------------------------------------------
void setup() {
  // Start serial
  Serial.begin(115200);
  delay(100); // Let serial initialize

  Serial.println("\n=== Verbose Flow Debug Start ===");
  Serial.println("setup() initiated...\n");

  // Initialize I2C
  Wire.begin();
  Serial.println("[INIT] I2C bus initialized.\n");

  // Quick bus scan for info
  i2cScan();

  // Attempt to start the sensor measurement
  Serial.println("[INIT] Attempting to start sensor measurement...");
  bool success = startFlowMeasurement();
  if (!success) {
    Serial.println("[INIT] Could NOT start measurement. Check address, wiring, or sensor commands.\n");
  } else {
    // As per datasheet, we need ~12 ms after start for first measurement,
    // and ~60 ms for stable measurement. We'll wait 60 ms for reliability.
    Serial.println("[INIT] Waiting 60 ms for sensor warm-up...");
    delay(60);
    Serial.println("[INIT] Warm-up complete. Starting main loop.\n");
  }
}

// --------------------------------------------------------------------------
void loop() {
  Serial.println("--- [LOOP] ---");

  if (measuringFlow) {
    float flow = readFlow();
    Serial.print("[LOOP] Flow reading: ");
    Serial.print(flow);
    Serial.println(" mL/min (approx)\n");
  } else {
    Serial.println("[LOOP] Not measuring. (Either sensor didn't start or was stopped.)\n");
  }

  // OPTIONAL: If you want to confirm the device is still visible on the bus occasionally:
  // static uint8_t loopCount = 0;
  // loopCount++;
  // if (loopCount % 10 == 0) {
  //   Serial.println("[LOOP] Doing a quick I2C scan for debugging...");
  //   i2cScan();
  // }

  // Delay between loops
  delay(1000);
}
