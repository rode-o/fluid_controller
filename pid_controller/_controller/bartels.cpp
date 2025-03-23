/*
 * File: bartels.cpp
 * Brief: Manages the Bartels micropump driver (amplitude-only control after init).
 */

 #include "bartels.h"
 #include "config.h"
 #include <Wire.h>
 #include <Arduino.h>
 
 // Single default delay (milliseconds)
 static const uint16_t default_delay = 40;
 
 // Driver state
 static bool bartelsInited = false;
 static bool firstRun      = true;
 
 // Forward declarations
 static void writeFullWaveformData(float voltage, uint8_t freqByte);
 static void writeAmplitudeOnly(float voltage);
 static void writeControlData();
 
 // ---------------------------------------------------------------------------
 // OEM-like conversion: freq (Hz) → 0..255 (Bartels register).
 // According to the OEM snippet, freqByte = frequency / 7.8125.
 // ---------------------------------------------------------------------------
 static uint8_t computeFreqByte(float desiredHz) {
   float temp = desiredHz / 7.8125f;
   uint8_t freqByte = (uint8_t)temp; // truncate
   if (freqByte == 0) freqByte = 1;
   return freqByte;
 }
 
 /*
  * Function: initBartels
  * Brief: Initializes driver state and triggers a two-pass setup on the first run.
  */
 bool initBartels() {
   bartelsInited = true;
   firstRun      = true;
   return true;
 }
 
 /*
  * Function: runSequence
  * Brief: Updates driver settings based on the specified voltage.
  *        On first run: performs full configuration including frequency.
  *        After that: only updates amplitude (not frequency).
  */
 void runSequence(float voltage) {
   if (!bartelsInited) return;
 
   if (voltage > BARTELS_MAX_VOLTAGE) voltage = BARTELS_MAX_VOLTAGE;
   if (voltage < BARTELS_MIN_VOLTAGE) voltage = BARTELS_MIN_VOLTAGE;
 
   float pumpBaseFreqHz = BARTELS_FREQ;
   uint8_t freqByte     = computeFreqByte(pumpBaseFreqHz);
 
   if (firstRun) {
     for (int i = 0; i < 2; i++) {
       writeFullWaveformData(voltage, freqByte);
       writeControlData();
 
       Wire.beginTransmission(BARTELS_DRIVER_ADDR);
       Wire.write(BARTELS_PAGE_REGISTER);
       Wire.write(0);
       Wire.endTransmission();
 
       delay(default_delay);
     }
     firstRun = false;
     return;
   }
 
   writeAmplitudeOnly(voltage);
   writeControlData();
 
   Wire.beginTransmission(BARTELS_DRIVER_ADDR);
   Wire.write(BARTELS_PAGE_REGISTER);
   Wire.write(0);
   Wire.endTransmission();
 
   delay(default_delay);
 }
 
 /*
  * Function: stopPump
  * Brief: Sets pump amplitude to zero to halt operation, performing a two-pass write.
  */
 void stopPump() {
   for (int i = 0; i < 2; i++) {
     uint8_t freqByte = computeFreqByte(BARTELS_FREQ);
     writeFullWaveformData(0.0f, freqByte);
     writeControlData();
 
     Wire.beginTransmission(BARTELS_DRIVER_ADDR);
     Wire.write(BARTELS_PAGE_REGISTER);
     Wire.write(0);
     Wire.endTransmission();
 
     delay(default_delay);
   }
 }
 
 /*
  * Function: writeFullWaveformData
  * Brief: Writes the *entire* 10-byte waveform configuration
  *        (including amplitude and freq) to page=1.
  */
 static void writeFullWaveformData(float voltage, uint8_t freqByte) {
   float ratio = voltage / BARTELS_ABSOLUTE_MAX;
   if (ratio < 0.0f) ratio = 0.0f;
   if (ratio > 1.0f) ratio = 1.0f;
 
   uint8_t amplitude_value = (uint8_t)(ratio * 255.0f);
 
   uint8_t waveformData[10] = {
     0x05, 0x80, 0x06, 0x00, 0x09, 0x00,
     amplitude_value,
     freqByte,
     0x64,  // cycle count
     0x00
   };
 
   Wire.beginTransmission(BARTELS_DRIVER_ADDR);
   Wire.write(BARTELS_PAGE_REGISTER);
   Wire.write(1);
   Wire.endTransmission();
 
   for (uint8_t i = 0; i < 10; i++) {
     Wire.beginTransmission(BARTELS_DRIVER_ADDR);
     Wire.write(i);
     Wire.write(waveformData[i]);
     Wire.endTransmission();
   }
 
   delay(default_delay);
 }
 
 /*
  * Function: writeAmplitudeOnly
  * Brief: Writes *only* the amplitude register to page=1.
  */
 static void writeAmplitudeOnly(float voltage) {
   float ratio = voltage / BARTELS_ABSOLUTE_MAX;
   if (ratio < 0.0f) ratio = 0.0f;
   if (ratio > 1.0f) ratio = 1.0f;
 
   uint8_t amplitude_value = (uint8_t)(ratio * 255.0f);
 
   Wire.beginTransmission(BARTELS_DRIVER_ADDR);
   Wire.write(BARTELS_PAGE_REGISTER);
   Wire.write(1);
   Wire.endTransmission();
 
   Wire.beginTransmission(BARTELS_DRIVER_ADDR);
   Wire.write(6);  // Amplitude register index
   Wire.write(amplitude_value);
   Wire.endTransmission();
 
   delay(default_delay);
 }
 
 /*
  * Function: writeControlData
  * Brief: Writes control data from BARTELS_CONTROL_DATA[] to page=0.
  */
 static void writeControlData() {
   Wire.beginTransmission(BARTELS_DRIVER_ADDR);
   Wire.write(BARTELS_PAGE_REGISTER);
   Wire.write(0);
   Wire.endTransmission();
 
   for (uint8_t i = 0; i < 4; i++) {
     Wire.beginTransmission(BARTELS_DRIVER_ADDR);
     Wire.write(i);
     Wire.write(BARTELS_CONTROL_DATA[i]);
     Wire.endTransmission();
   }
 
   delay(default_delay);
 }
 