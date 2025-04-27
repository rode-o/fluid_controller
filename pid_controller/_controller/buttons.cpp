/*
 * File: buttons.cpp
 * Brief: Manages button input for system control and stores relevant data in EEPROM.
 */

 #include "buttons.h"
 #include "config.h"
 #include <Arduino.h>
 #include <EEPROM.h>
 
 // Pin assignments
 static const int PIN_ONOFF       = D6;
 static const int PIN_FLOW_UP     = D9;
 static const int PIN_FLOW_DOWN   = D3;
 static const int PIN_ERROR_UP    = D8;
 static const int PIN_ERROR_DOWN  = D7;
 static const int PIN_MODE_TOGGLE = D10;
 
 // Previous states for edge detection
 static int oldState_onoff       = HIGH;
 static int oldState_flowUp      = HIGH;
 static int oldState_flowDown    = HIGH;
 static int oldState_errorUp     = HIGH;
 static int oldState_errorDown   = HIGH;
 static int oldState_modeToggle  = HIGH;
 
 // System variables
 static bool  systemOn          = false;
 static float flowSetpointValue = 0.0f;
 static float errorPercentValue = 0.0f;
 static bool  modeTogglePressed = false;  // Set true if mode button pressed
 
 // EEPROM addresses
 static const int EEPROM_SIZE          = 512;
 static const int EEPROM_ADDR_ERROR    = 0;
 static const int EEPROM_ADDR_SETPOINT = 4;
 
 /*
  * Function: checkFallingEdge
  * Brief: Returns true if the given pin transitions from HIGH to LOW.
  */
 static bool checkFallingEdge(int pin, int &oldState) {
   int newState = digitalRead(pin);
   bool triggered = (newState == LOW && oldState == HIGH);
   oldState = newState;
   return triggered;
 }
 
 /*
  * Function: loadFromEEPROM
  * Brief: Loads stored error and setpoint values if they are valid.
  */
 static void loadFromEEPROM() {
   float storedError    = 0.0f;
   float storedSetpoint = 0.0f;
 
   EEPROM.get(EEPROM_ADDR_ERROR,    storedError);
   EEPROM.get(EEPROM_ADDR_SETPOINT, storedSetpoint);
 
   if (storedError < -50.0f || storedError > 50.0f) {
     storedError = 0.0f;
   }
   if (storedSetpoint < FLOW_SP_MIN || storedSetpoint > FLOW_SP_MAX) {
     storedSetpoint = (FLOW_SP_MIN + FLOW_SP_MAX) * 0.5f;
   }
 
   errorPercentValue = storedError;
   flowSetpointValue = storedSetpoint;
 }
 
 /*
  * Function: saveToEEPROM
  * Brief: Saves the current error and setpoint values to EEPROM.
  */
 static void saveToEEPROM() {
   EEPROM.put(EEPROM_ADDR_ERROR,    errorPercentValue);
   EEPROM.put(EEPROM_ADDR_SETPOINT, flowSetpointValue);
   EEPROM.commit();
 }
 
 /*
  * Function: initButtons
  * Brief: Initializes button inputs and loads stored values from EEPROM.
  * Note: EEPROM.begin(...) must be called before this function.
  */
 void initButtons() {
   pinMode(PIN_ONOFF,       INPUT_PULLUP);
   pinMode(PIN_FLOW_UP,     INPUT_PULLUP);
   pinMode(PIN_FLOW_DOWN,   INPUT_PULLUP);
   pinMode(PIN_ERROR_UP,    INPUT_PULLUP);
   pinMode(PIN_ERROR_DOWN,  INPUT_PULLUP);
   pinMode(PIN_MODE_TOGGLE, INPUT_PULLUP);
 
   loadFromEEPROM();
 
   oldState_onoff      = digitalRead(PIN_ONOFF);
   oldState_flowUp     = digitalRead(PIN_FLOW_UP);
   oldState_flowDown   = digitalRead(PIN_FLOW_DOWN);
   oldState_errorUp    = digitalRead(PIN_ERROR_UP);
   oldState_errorDown  = digitalRead(PIN_ERROR_DOWN);
   oldState_modeToggle = digitalRead(PIN_MODE_TOGGLE);
 }
 
 /*
  * Function: updateButtons
  * Brief: Reads button inputs each loop to update systemOn, setpoint, error%, 
  *        and mode toggle state. Saves changes to EEPROM if values changed.
  */
 void updateButtons() {
   bool changed = false;
   modeTogglePressed = false; // Reset each iteration
 
   // On/Off toggle
   if (checkFallingEdge(PIN_ONOFF, oldState_onoff)) {
     systemOn = !systemOn;
   }
 
   // Flow Up
   if (checkFallingEdge(PIN_FLOW_UP, oldState_flowUp)) {
     flowSetpointValue += FLOW_STEP_SIZE;
     if (flowSetpointValue > FLOW_SP_MAX) {
       flowSetpointValue = FLOW_SP_MAX;
     }
     changed = true;
   }
 
   // Flow Down
   if (checkFallingEdge(PIN_FLOW_DOWN, oldState_flowDown)) {
     flowSetpointValue -= FLOW_STEP_SIZE;
     if (flowSetpointValue < FLOW_SP_MIN) {
       flowSetpointValue = FLOW_SP_MIN;
     }
     changed = true;
   }
 
   // Error% Up
   if (checkFallingEdge(PIN_ERROR_UP, oldState_errorUp)) {
     errorPercentValue += 1.0f;
     if (errorPercentValue > 50.0f) {
       errorPercentValue = 50.0f;
     }
     changed = true;
   }
 
   // Error% Down
   if (checkFallingEdge(PIN_ERROR_DOWN, oldState_errorDown)) {
     errorPercentValue -= 1.0f;
     if (errorPercentValue < -50.0f) {
       errorPercentValue = -50.0f;
     }
     changed = true;
   }
 
   // Mode toggle
   if (checkFallingEdge(PIN_MODE_TOGGLE, oldState_modeToggle)) {
     modeTogglePressed = true;
   }
 
   // Save to EEPROM if values changed
   if (changed) {
     saveToEEPROM();
   }
 }
 
 // Accessors
 
 bool isSystemOn() {
   return systemOn;
 }
 
 float getFlowSetpoint() {
   return flowSetpointValue;
 }
 
 float getErrorPercent()
{
    /* Operator enters:
         error_hand = 100·(expected − measured)/expected
       Firmware needs:
         error_fw   = 100·(measured − expected)/expected
       → same magnitude, opposite sign
    */
    return -errorPercentValue;   //  ← single-point sign flip
}
 
 /*
  * Function: wasModeTogglePressed
  * Brief: Returns true if the mode toggle button was pressed in this loop iteration.
  */
 bool wasModeTogglePressed() {
   return modeTogglePressed;
 }
 