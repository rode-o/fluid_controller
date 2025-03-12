#include <Wire.h>
#include <Arduino.h>

//=============================================================================
//  SLF3S-0600F I2C Settings & Commands
//=============================================================================
static const uint8_t  SLF_SENSOR_ADDR   = 0x08;   // Default I2C address from datasheet
static const uint16_t CMD_START_WATER   = 0x3608; // Start continuous measurement: Water calibration
static const uint16_t CMD_START_IPA     = 0x3615; // Start continuous measurement: IPA calibration
static const uint16_t CMD_STOP          = 0x3FF9; // Stop continuous measurement

// Scale factors from Table 16 in your datasheet (SLF3S-0600F).
// Flow factor: raw / 10 => µL/min
// Temperature factor: raw / 200 => °C
#define FLOW_SCALE_FACTOR     10.0f
#define TEMP_SCALE_FACTOR     200.0f

//=============================================================================
// Toggle: Change this to 'true' if you want to start with IPA calibration
// instead of the default Water calibration.
//=============================================================================
static bool useIpaCalibration = false;

//=============================================================================
//  Setup
//=============================================================================
void setup() {
  Serial.begin(115200);
  Wire.begin();

  delay(100);  // small delay to let everything power up

  Serial.println("Starting SLF3S-0600F Test...");

  // Depending on our toggle, pick which calibration to start with
  if (useIpaCalibration) {
    Serial.println("Using IPA calibration...");
    if (!startFlowMeasurementIPA()) {
      Serial.println("Failed to start continuous measurement (IPA)!");
    } else {
      Serial.println("Continuous measurement (IPA) started.");
    }
  } else {
    Serial.println("Using Water calibration...");
    if (!startFlowMeasurementWater()) {
      Serial.println("Failed to start continuous measurement (Water)!");
    } else {
      Serial.println("Continuous measurement (Water) started.");
    }
  }
}

//=============================================================================
//  Main Loop
//=============================================================================
void loop() {
  // Read sensor data (Flow, Temp, Flags)
  readAndPrintSensorData();

  delay(250);  // adjust as needed for your test logging rate
}

//=============================================================================
//  Start measurement: Water calibration
//=============================================================================
bool startFlowMeasurementWater() {
  Wire.beginTransmission(SLF_SENSOR_ADDR);
  Wire.write((uint8_t)(CMD_START_WATER >> 8));
  Wire.write((uint8_t)(CMD_START_WATER & 0xFF));
  uint8_t err = Wire.endTransmission(true);
  return (err == 0);
}

//=============================================================================
//  Start measurement: IPA calibration
//=============================================================================
bool startFlowMeasurementIPA() {
  Wire.beginTransmission(SLF_SENSOR_ADDR);
  Wire.write((uint8_t)(CMD_START_IPA >> 8));
  Wire.write((uint8_t)(CMD_START_IPA & 0xFF));
  uint8_t err = Wire.endTransmission(true);
  return (err == 0);
}

//=============================================================================
//  Stop measurement
//=============================================================================
bool stopFlowMeasurement() {
  Wire.beginTransmission(SLF_SENSOR_ADDR);
  Wire.write((uint8_t)(CMD_STOP >> 8));
  Wire.write((uint8_t)(CMD_STOP & 0xFF));
  uint8_t err = Wire.endTransmission(true);
  return (err == 0);
}

//=============================================================================
//  Read the sensor data (Flow, Temp, Signaling Flags) and print
//=============================================================================
void readAndPrintSensorData() {
  // Request 9 bytes total:
  //   Word1 (Flow) + CRC
  //   Word2 (Temperature) + CRC
  //   Word3 (Signaling Flags) + CRC
  const uint8_t NUM_BYTES = 9;
  Wire.requestFrom((uint8_t)SLF_SENSOR_ADDR, NUM_BYTES);

  if (Wire.available() < NUM_BYTES) {
    Serial.println("Not enough bytes returned from sensor.");
    return;
  }

  // --- Flow (2 bytes), discard CRC ---
  uint8_t flowHigh = Wire.read();
  uint8_t flowLow  = Wire.read();
  (void)Wire.read(); // discard CRC
  int16_t rawFlow = (int16_t)((flowHigh << 8) | flowLow);

  // --- Temperature (2 bytes), discard CRC ---
  uint8_t tempHigh = Wire.read();
  uint8_t tempLow  = Wire.read();
  (void)Wire.read(); // discard CRC
  int16_t rawTemp = (int16_t)((tempHigh << 8) | tempLow);

  // --- Flags (2 bytes), discard CRC ---
  uint8_t flagHigh = Wire.read();
  uint8_t flagLow  = Wire.read();
  (void)Wire.read(); // discard CRC
  uint16_t flags = (uint16_t)((flagHigh << 8) | flagLow);

  // Convert to physical units
  float flow_uLmin   = rawFlow / FLOW_SCALE_FACTOR; 
  float flow_mLmin   = flow_uLmin / 1000.0f;         
  float temperatureC = rawTemp / TEMP_SCALE_FACTOR;  

  // Decode flags
  bool airInLine     = (flags & (1 << 0)) != 0;  
  bool highFlow      = (flags & (1 << 1)) != 0;  
  bool expSmoothing  = (flags & (1 << 5)) != 0;  

  // Print results
  Serial.println("-----------------------------");
  Serial.print("Raw Flow: ");
  Serial.print(rawFlow);
  Serial.print("  => Flow: ");
  Serial.print(flow_mLmin, 3);
  Serial.println(" mL/min");

  Serial.print("Raw Temp: ");
  Serial.print(rawTemp);
  Serial.print("  => Temp: ");
  Serial.print(temperatureC, 2);
  Serial.println(" degC");

  Serial.print("Flags (hex): 0x");
  Serial.println(flags, HEX);

  Serial.print("  Air in line? ");
  Serial.println(airInLine ? "YES" : "NO");
  Serial.print("  High flow?   ");
  Serial.println(highFlow ? "YES" : "NO");
  Serial.print("  Exponential smoothing active? ");
  Serial.println(expSmoothing ? "YES" : "NO");
}

//=============================================================================
