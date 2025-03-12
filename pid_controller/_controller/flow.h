#pragma once

/*
 * File: flow.h
 * Brief: Declares functions to manage and read data from the flow sensor.
 */

#include <stdint.h>

// Starts continuous flow measurement; returns true if successful
bool     startFlowMeasurement();

// Stops continuous flow measurement; returns true if successful
bool     stopFlowMeasurement();

// Reads the current flow (mL/min), applying any user error compensation
float    readFlow();

// Returns the most recent temperature reading in °C
float    getTempC();

// Returns the most recent sensor flags
uint16_t getLastFlags();

// Returns the raw flow reading in mL/min without compensation
float    getRawFlow();

// Returns the raw temperature reading in °C (if implemented for debugging)
float    getRawTemp();
