/*
 * File: sigmoidal_control.cpp
 * Brief: Implements a sigmoidal (logistic) PID control for the Bartels pump.
 */

 #include "sigmoidal_control.h"
 #include "config.h"      // Needed for BARTELS_MAX_VOLTAGE, BARTELS_MIN_VOLTAGE
 #include "gain.h"
 #include "filter.h"
 #include "pid.h"
 #include "bartels.h"
 #include <Arduino.h>
 
 // External PID integrator variables (declared in pid.cpp)
 extern float integralTerm;
 extern float g_lastIntegralIncrement;
 
 // Stores the previous Ki to rescale integrator if Ki changes significantly
 static float s_lastKi = 0.0f;
 
 // Optional global smoothed error for logging
 static float g_errSmooth = 0.0f;
 
 // Dynamic low-pass filter for the error term
 static DynamicLPFilter s_errorFilter;
 
 /**
  * initSigmoidalController
  * Resets local state, integrator, and dynamic filter for sigmoidal PID.
  */
 void initSigmoidalController(SystemState &state)
 {
     state.pGain         = 0.0f;
     state.iGain         = 0.0f;
     state.dGain         = 0.0f;
     state.filteredError = 0.0f;
     state.currentAlpha  = 0.0f;
 
     // Reset the PID integrator, derivative filter, etc.
     initPID();  // sets integralTerm = 0.0f
     s_lastKi = 0.0f;
 
     // Initialize the dynamic error filter
     initDynamicLPFilter(s_errorFilter);
 
     // For optional smoothed error logging
     g_errSmooth = 0.0f;
 
     // Debug
     Serial.println("[SIGMOIDAL] initSigmoidalController() -> PID + filter reset");
 }
 
 /**
  * updateSigmoidalController
  * Main control loop logic for sigmoidal-based PID.
  *
  * NOTE: We assume the main loop already handles OFF→ON/ON→OFF transitions
  *       and calls initSigmoidalController() as needed. If 'systemOn' is false,
  *       we simply return immediately without doing anything.
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
 )
 {
     // If system is OFF, don't run PID
     if (!systemOn) {
         Serial.println("[DEBUG] systemOn=false => skipping PID calculations");
         stopPump();
         pidFraction    = 0.0f;
         desiredVoltage = 0.0f;
         pTermOut       = 0.0f;
         iTermOut       = 0.0f;
         dTermOut       = 0.0f;
         return;
     }
 
     // Compute raw error
     float errRaw = flowSetpoint - flow;
 
     // Filter the error
     float errFiltered = updateDynamicLPFilter(s_errorFilter, errRaw);
     g_errSmooth       = errFiltered;
     state.filteredError = errFiltered;
     state.currentAlpha  = s_errorFilter.currentAlpha;
 
     float absE = fabs(errFiltered);
 
     // Compute logistic-based P, I, D gains
     float kp = getSigmoidKp(absE);
     float ki = getSigmoidKi(absE);
     float kd = getSigmoidKd(absE);
 
     // Optional debug: see old vs new Ki
     Serial.print("[DEBUG] oldKi=");
     Serial.print(s_lastKi, 6);
     Serial.print(", newKi=");
     Serial.print(ki, 6);
 
     // Rescale integrator if Ki changed significantly
     if (fabs(s_lastKi - ki) > 1e-9) {
         Serial.print(" -> Ki changed, rescaling integrator. Ratio=");
         if (fabs(s_lastKi) > 1e-9 && fabs(ki) > 1e-9) {
             float ratio = s_lastKi / ki;
             integralTerm *= ratio;
             Serial.print(ratio, 6);
             Serial.print(", integralTerm=");
             Serial.print(integralTerm, 6);
         } else {
             Serial.print(" (skipped because Ki or s_lastKi=0?)");
         }
         Serial.println();
         s_lastKi = ki;
     } else {
         Serial.println(" (no significant change)");
     }
 
     // Apply new gains to PID
     setPIDGains(kp, ki, kd);
 
     // Store them in the system state
     state.pGain = kp;
     state.iGain = ki;
     state.dGain = kd;
 
     // Normal PID update
     pidFraction = updatePIDNormal(errFiltered, pTermOut, iTermOut, dTermOut);
 
     // Check saturation / clamp
     if (pidFraction > 1.0f) {
         integralTerm -= g_lastIntegralIncrement;  // minor anti-windup
         pidFraction = 1.0f;
     } else if (pidFraction < 0.0f) {
         pidFraction = 0.0f;
     }
 
     // Convert PID output fraction to voltage
     desiredVoltage = pidFraction * BARTELS_MAX_VOLTAGE;
 
     // Enforce min voltage if above 0 but below min
     if (desiredVoltage > 0.0f && desiredVoltage < BARTELS_MIN_VOLTAGE) {
         desiredVoltage = BARTELS_MIN_VOLTAGE;
     }
 
     // Enforce max voltage
     if (desiredVoltage > BARTELS_MAX_VOLTAGE) {
         desiredVoltage = BARTELS_MAX_VOLTAGE;
     }
 
     // Command the pump hardware
     runSequence(desiredVoltage);
 
     // Optional debug: final integrator after this loop
     Serial.print("[DEBUG] PID loop done. integralTerm=");
     Serial.print(integralTerm, 6);
     Serial.print(", pidFraction=");
     Serial.print(pidFraction, 6);
     Serial.print(", desiredVoltage=");
     Serial.println(desiredVoltage, 6);
 }
 