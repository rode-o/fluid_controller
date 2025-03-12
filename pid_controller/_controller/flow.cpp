/*
 * File: flow.cpp
 * Brief: Provides functions to manage the Sensirion flow sensor:
 *        start/stop measurement, read flow/temperature, and retrieve flags.
 */

 #include "flow.h"
 #include "config.h"
 #include "buttons.h"
 #include <Wire.h>
 #include <Arduino.h>
 
 static bool  measuringFlow  = false;
 static int   readAttemptCnt = 0;
 static float rawFlow_mLmin  = 0.0f;
 static float rawTempC       = 0.0f;
 static uint16_t lastFlags   = 0;
 
 /*
  * Starts continuous measurement mode for the flow sensor.
  * Returns true if successful; otherwise false on I2C error.
  */
 bool startFlowMeasurement() {
   Wire.beginTransmission(SLF_FLOW_SENSOR_ADDR);
   Wire.write(SLF_START_CMD);
   Wire.write(SLF_CALIBRATION_CMD_BYTE);
   uint8_t err = Wire.endTransmission(true);
   if (err != 0) {
     return false;
   }
   measuringFlow  = true;
   readAttemptCnt = 0;
   return true;
 }
 
 /*
  * Stops continuous measurement mode for the flow sensor.
  * Returns true if successful; otherwise false on I2C error.
  */
 bool stopFlowMeasurement() {
   Wire.beginTransmission(SLF_FLOW_SENSOR_ADDR);
   Wire.write(SLF_STOP_CMD);
   Wire.write(SLF_STOP_BYTE);
   uint8_t err = Wire.endTransmission(true);
   measuringFlow = false;
   return (err == 0);
 }
 
 /*
  * Reads sensor data (flow, temp, flags) and returns a compensated flow value.
  * If measurement is not active or data is unavailable, returns 0.0f.
  * The sensor stabilizes on early attempts (with a brief delay).
  */
 float readFlow() {
   if (!measuringFlow) {
     return 0.0f;
   }
 
   readAttemptCnt++;
   if (readAttemptCnt < 5) {
     delay(100);
   }
 
   Wire.requestFrom((uint8_t)SLF_FLOW_SENSOR_ADDR, (uint8_t)9);
   if (Wire.available() < 9) {
     return 0.0f;
   }
 
   // Read flow
   uint8_t flowHigh = Wire.read();
   uint8_t flowLow  = Wire.read();
   Wire.read(); // discard CRC
   int16_t rawFlowInt = (int16_t)((flowHigh << 8) | flowLow);
 
   // Read temperature
   uint8_t tempHigh = Wire.read();
   uint8_t tempLow  = Wire.read();
   Wire.read(); // discard CRC
   int16_t rawTempInt = (int16_t)((tempHigh << 8) | tempLow);
 
   // Read flags
   uint8_t flagHigh = Wire.read();
   uint8_t flagLow  = Wire.read();
   Wire.read(); // discard CRC
   lastFlags = (uint16_t)((flagHigh << 8) | flagLow);
 
   // Convert raw values
   rawFlow_mLmin = (float)rawFlowInt / SLF_SCALE_FACTOR_FLOW;
   rawTempC      = (float)rawTempInt / SLF_SCALE_FACTOR_TEMP;
 
   // Apply user-defined error compensation
   float errorPercent   = getErrorPercent();
   float compFactor     = 1.0f / (1.0f + (errorPercent / 100.0f));
   float compensatedFlow = rawFlow_mLmin * compFactor;
 
   return compensatedFlow;
 }
 
 // Returns the last temperature reading (°C)
 float getTempC() {
   return rawTempC;
 }
 
 // Returns the last sensor flags
 uint16_t getLastFlags() {
   return lastFlags;
 }
 
 // Returns the raw flow reading (mL/min) without compensation
 float getRawFlow() {
   return rawFlow_mLmin;
 }
 