#pragma once
#include <Arduino.h>

/*
 * File: pid.h
 * Brief: Declares a normal PID controller with dynamic gains.
 */

// Externally accessible PID integrator and anti-windup references
extern float integralTerm;
extern float g_lastIntegralIncrement;
extern float g_lastErrorForAW;

// Initializes PID states (integrator, derivative filter, etc.)
void initPID();

// Dynamically sets the PID gains
void setPIDGains(float p, float i, float d);

// Updates the PID using a pre-computed error, returning the clamped output [0..1]
float updatePIDNormal(float error,
                      float &pTermOut,
                      float &iTermOut,
                      float &dTermOut);
