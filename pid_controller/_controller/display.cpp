/*
 * File: display.cpp
 * Brief: Manages the SSD1306 display for system status reporting.
 */

 #include "display.h"
 #include "config.h"
 #include <Wire.h>
 #include <Adafruit_GFX.h>
 #include <Adafruit_SSD1306.h>
 
 // Display configuration
 static const int SCREEN_WIDTH  = 128;
 static const int SCREEN_HEIGHT = 64;
 static Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
 
 // Tracks whether the display was successfully initialized
 static bool displayInited = false;
 
 /*
  * Function: initDisplay
  * Brief: Initializes the SSD1306 display with the address from config.h.
  * Returns: True if successful, false otherwise.
  */
 bool initDisplay() {
   if (!display.begin(SSD1306_SWITCHCAPVCC, SSD1306_DISPLAY_ADDR)) {
     displayInited = false;
     return false;
   }
   display.setRotation(2);
   display.clearDisplay();
   display.display();
   displayInited = true;
   return true;
 }
 
 /*
  * Function: showStatus
  * Brief: Displays flow rate, setpoint, error %, voltage, temperature, 
  *        bubble detection status, and system power state.
  */
 void showStatus(float flow,
                 float setpoint,
                 float errorPct,
                 float bartelsVoltage,
                 bool systemOn,
                 float temperature,
                 bool bubbleDetected)
 {
   if (!displayInited) return;
 
   display.clearDisplay();
   display.setTextSize(1);
   display.setTextColor(SSD1306_WHITE);
   display.setCursor(0, 0);
 
   display.print("Flow: ");
   display.print(flow, 3);
   display.println(" mL/min");
 
   display.print("Setpt: ");
   display.print(setpoint, 3);
   display.println(" mL/min");
 
   display.print("Err%: ");
   display.print(errorPct, 1);
   display.println();
 
   display.print("Volt: ");
   display.print(bartelsVoltage, 1);
   display.println();
 
   display.print("Temp: ");
   display.print(temperature, 1);
   display.println(" C");
 
   display.print("Bubble: ");
   display.println(bubbleDetected ? "YES" : "NO");
 
   display.print("System: ");
   display.println(systemOn ? "ON" : "OFF");
 
   display.display();
 }
 