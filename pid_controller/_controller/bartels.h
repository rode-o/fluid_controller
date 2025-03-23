#pragma once
#include <Arduino.h>

/*
 * File: bartels.h
 * Brief: Declares functions to control a Bartels micropump driver via I2C.
 */

// Initializes the driver state
bool initBartels();

// Writes amplitude and control data to the micropump
void runSequence(float voltage);

// Sets pump amplitude to zero (stop)
void stopPump();
