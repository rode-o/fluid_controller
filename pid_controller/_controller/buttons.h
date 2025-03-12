#pragma once
#include <Arduino.h>

/*
 * File: buttons.h
 * Brief: Declares interfaces for managing six button inputs
 *        (ON/OFF, Flow Up/Down, Error% Up/Down, Mode Toggle).
 */

// Initializes button pins and loads stored values from EEPROM
void initButtons();

// Reads button inputs each loop and updates internal state
void updateButtons();

// Returns whether the system is currently ON
bool isSystemOn();

// Returns the current flow setpoint
float getFlowSetpoint();

// Returns the current error percentage
float getErrorPercent();

// Returns true if the mode toggle was pressed in the current loop iteration
bool wasModeTogglePressed();
