#ifndef EXP_CONTROL_H
#define EXP_CONTROL_H

#include "system_state.h"

/**
 * Initializes the exponential-based controller (exp_control).
 */
void initExpController(SystemState &state);

/**
 * Updates the exponential-based controller once per loop iteration.
 *
 * @param state         Reference to the SystemState.
 * @param flow          Current measured flow rate.
 * @param flowSetpoint  Desired flow setpoint.
 * @param errorPercent  Error percentage (optional usage).
 * @param systemOn      Whether the system is currently ON or OFF.
 * @param desiredVoltage Output: The final voltage command for the pump.
 * @param pidFraction    Output: The PID output fraction (0..1).
 * @param bubbleDetected Reference to bubble detection flag.
 * @param pTermOut       Output: The proportional term for logging.
 * @param iTermOut       Output: The integral term for logging.
 * @param dTermOut       Output: The derivative term for logging.
 */
void updateExpController(
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

#endif // EXP_CONTROL_H
