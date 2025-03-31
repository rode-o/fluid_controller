#pragma once

/*
 * File: display.h
 * Brief: Declarations for initializing and updating the SSD1306 display.
 */

// Initializes the SSD1306 display. Returns true if successful.
bool initDisplay();

// Displays key status parameters (flow, setpoint, error%, voltage, temperature,
// bubble detection, system on/off state).
void showStatus(float flow,
                float setpoint,
                float errorPct,
                float bartelsVoltage,
                bool systemOn,
                float temperature,
                bool bubbleDetected);
