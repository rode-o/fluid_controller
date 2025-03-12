/*
 * File: constant_voltage_control.cpp
 * Brief: Implements a constant-voltage control mode for the Bartels pump.
 */

 #include "constant_voltage_control.h"
 #include "bartels.h"
 #include "config.h"
 #include <Arduino.h>
 
 
 
 void initConstantVoltageControl() {
   // Any required initialization can be done here if needed
 }
 
 void updateConstantVoltageControl(bool systemOn, float &desiredVoltageOut) {
   if (!systemOn) {
     desiredVoltageOut = 0.0f;
     stopPump();
     return;
   }
 
   float voltageCmd = kConstantVoltage;
   if (voltageCmd > BARTELS_MAX_VOLTAGE) {
     voltageCmd = BARTELS_MAX_VOLTAGE;
   }
 
   runSequence(voltageCmd);
   desiredVoltageOut = voltageCmd;
 }
 