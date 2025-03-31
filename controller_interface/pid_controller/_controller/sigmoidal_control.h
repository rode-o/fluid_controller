#pragma once

#include "system_state.h"  // So we can use "SystemState"

/**
 * Initializes the sigmoidal (logistic) PID controller for the Bartels pump.
 * Resets PID integrator, dynamic filter, etc.
 */
void initSigmoidalController(SystemState &state);

/**
 * Main update function for sigmoidal-based PID control.
 *
 * Parameters:
 *  - state           : Reference to the global SystemState (holds pGain, iGain, etc.).
 *  - flow            : Current flow reading
 *  - flowSetpoint    : Desired flow
 *  - errorPercent    : Error in percent (if needed for logging/logic)
 *  - systemOn        : Whether the system is on
 *  - desiredVoltage  : (out) Voltage to drive the pump
 *  - pidFraction     : (out) PID output fraction in [0..1]
 *  - bubbleDetected  : (in/out) If needed, can set or read bubble state
 *  - pTermOut,
 *    iTermOut,
 *    dTermOut        : (out) The individual PID terms for logging or debugging
 */
void updateSigmoidalController(
    SystemState &state,
    float flow,
    float flowSetpoint,
    float errorPercent,
    bool systemOn,
    float &desiredVoltage,
    float &pidFraction,
    bool &bubbleDetected,
    float &pTermOut,
    float &iTermOut,
    float &dTermOut
);
