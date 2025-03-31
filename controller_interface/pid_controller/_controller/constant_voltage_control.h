#ifndef CONSTANT_VOLTAGE_CONTROL_H
#define CONSTANT_VOLTAGE_CONTROL_H

#include "config.h"

/*
 * File: constant_voltage_control.h
 * Brief: Provides a constant-voltage control mode for the Bartels pump.
 */

// Initializes any required state for constant-voltage control
void initConstantVoltageControl();

// Sets output voltage to a constant if systemOn is true; otherwise, sets it to 0.0
void updateConstantVoltageControl(bool systemOn, float &desiredVoltageOut);

#endif // CONSTANT_VOLTAGE_CONTROL_H
