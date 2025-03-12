/*
   XIAO RP2040 Button Test with Named Assignments
   Buttons: 
   RST, Sleep/WakeUp, Pump State, Flow Up, Flow Down, Error Up, Error Down

   Wire each button from the XIAO pad to GND.
   We enable INPUT_PULLUP, so pressed = LOW, not pressed = HIGH.
*/

#include <Arduino.h>

// Define button names and corresponding pin assignments
const int BUTTON_RST          = D6;  // Reset button
const int BUTTON_SLEEP_WAKEUP = D3;  // Sleep/WakeUp toggle
const int BUTTON_PUMP_STATE   = D9;  // Pump State toggle
const int BUTTON_FLOW_UP      = D8;  // Increase Flow
const int BUTTON_FLOW_DOWN    = D7;  // Decrease Flow
const int BUTTON_ERROR_UP     = D10;  // Increase Error Value
const int BUTTON_ERROR_DOWN   = D2; // Decrease Error Value

// Array to hold button pins for easy iteration
const int buttonPins[] = { 
  BUTTON_RST, 
  BUTTON_SLEEP_WAKEUP, 
  BUTTON_PUMP_STATE, 
  BUTTON_FLOW_UP, 
  BUTTON_FLOW_DOWN, 
  BUTTON_ERROR_UP, 
  BUTTON_ERROR_DOWN 
};

const char* buttonNames[] = { 
  "RST", 
  "Sleep/WakeUp", 
  "Pump State", 
  "Flow Up", 
  "Flow Down", 
  "Error Up", 
  "Error Down" 
};

const int numButtons = sizeof(buttonPins) / sizeof(buttonPins[0]);

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  // Set each pin as input pull-up
  for (int i = 0; i < numButtons; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
  Serial.println("Button Test with Assignments Started!");
}

void loop() {
  for (int i = 0; i < numButtons; i++) {
    int state = digitalRead(buttonPins[i]);
    Serial.print("Button: ");
    Serial.print(buttonNames[i]);
    Serial.print(" (Pin D");
    Serial.print(buttonPins[i]);
    Serial.print(") = ");
    if (state == LOW) {
      Serial.println("PRESSED (LOW)");
    } else {
      Serial.println("NOT PRESSED (HIGH)");
    }
  }
  Serial.println("-------------------");
  delay(500);
}
