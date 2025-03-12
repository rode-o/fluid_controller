/*
 * File: bartels.cpp
 * Brief: Manages the Bartels micropump driver (amplitude/frequency control).
 */

 #include "bartels.h"
 #include "config.h"
 #include <Wire.h>
 #include <Arduino.h>
 
 // Single default delay (milliseconds)
 static const uint16_t default_delay = 40; 
 
 // Driver state
 static bool bartelsInited = false;
 static bool firstRun       = true;
 
 // Forward declarations
 static void writeWaveformData(float voltage, uint8_t freqByte);
 static void writeControlData();
 
 // ---------------------------------------------------------------------------
 // OEM-like conversion: freq (Hz) → 0..255 (Bartels register).
 // According to the OEM snippet, freqByte = frequency / 7.8125.
 // They simply truncated. Below, we do the same or we can add +0.5f for rounding.
 // ---------------------------------------------------------------------------
 static uint8_t computeFreqByte(float desiredHz) {
   float temp = desiredHz / 7.8125f;
 
   // OEM snippet does truncation:
   uint8_t freqByte = (uint8_t)temp;
   // Alternatively (round): uint8_t freqByte = (uint8_t)(temp + 0.5f);
 
   if (freqByte == 0) {
     freqByte = 1;  // prevent zero
   }
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
  *        Includes a two-pass initialization on the first run.
  */
 void runSequence(float voltage) {
   if (!bartelsInited) return;
 
   // Clamp voltage to valid range
   if (voltage > BARTELS_MAX_VOLTAGE) voltage = BARTELS_MAX_VOLTAGE;
   if (voltage < BARTELS_MIN_VOLTAGE) voltage = BARTELS_MIN_VOLTAGE;
 
   // Pull the new "desired frequency" in Hz from config.h
   float   pumpBaseFreqHz = BARTELS_FREQ;
   // Convert it to the driver register byte:
   uint8_t freqByte       = computeFreqByte(pumpBaseFreqHz);
 
   // Double-pass initialization
   if (firstRun) {
     for (int i = 0; i < 2; i++) {
       writeWaveformData(voltage, freqByte);
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
 
   // Normal operation after first run
   writeWaveformData(voltage, freqByte);
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
     // amplitude=0, same frequency
     uint8_t freqByte = computeFreqByte(BARTELS_FREQ);
 
     writeWaveformData(0.0f, freqByte);
     writeControlData();
 
     Wire.beginTransmission(BARTELS_DRIVER_ADDR);
     Wire.write(BARTELS_PAGE_REGISTER);
     Wire.write(0);
     Wire.endTransmission();
 
     delay(default_delay);
   }
 }
 
 /*
  * Function: writeWaveformData
  * Brief: Writes amplitude and frequency data to page=1 of the Bartels driver.
  */
 static void writeWaveformData(float voltage, uint8_t freqByte) {
   float ratio = voltage / BARTELS_ABSOLUTE_MAX;
   if (ratio < 0.0f) ratio = 0.0f;
   if (ratio > 1.0f) ratio = 1.0f;
 
   uint8_t amplitude_value = (uint8_t)(ratio * 255.0f);
 
   // Example 10-byte waveform configuration
   uint8_t waveformData[10] = {
     0x05, 0x80, 0x06, 0x00, 0x09, 0x00,
     amplitude_value,
     freqByte,
     0x64,  // cycle count
     0x00
   };
 
   // Switch to page=1
   Wire.beginTransmission(BARTELS_DRIVER_ADDR);
   Wire.write(BARTELS_PAGE_REGISTER);
   Wire.write(1);
   Wire.endTransmission();
 
   // Write waveform bytes
   for (uint8_t i = 0; i < 10; i++) {
     Wire.beginTransmission(BARTELS_DRIVER_ADDR);
     Wire.write(i);
     Wire.write(waveformData[i]);
     Wire.endTransmission();
   }
 
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
 