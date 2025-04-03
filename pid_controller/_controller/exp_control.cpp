/*
 * File: exp_control.cpp
 * Brief: Implements a reciprocal-exponential-style PID control using
 *        f(x) = A + (K - A)*exp( -1 / [ B*(x - c) ] ).
 *
 *        The error is also filtered by a dynamic low-pass filter
 *        (updateDynamicLPFilter), which internally uses a slope-matched
 *        exponential function derived from Ki parameters.
 */

 #include "exp_control.h"
 #include "config.h"     // for BARTELS_MAX_VOLTAGE, BARTELS_MIN_VOLTAGE, etc.
 #include "gain.h"
 #include "filter.h"
 #include "pid.h"
 #include "bartels.h"
 #include <Arduino.h>
 
 // External PID integrator variables (declared in pid.cpp)
 extern float integralTerm;
 extern float g_lastIntegralIncrement;
 
 // Keeps track of the previous Ki for integrator rescaling
 static float s_lastKi = 0.0f;
 
 // Optional global smoothed error for logging
 static float g_errSmooth = 0.0f;
 
 // Dynamic low-pass filter for the error term
 static DynamicLPFilter s_errorFilter;
 
 
 //=============================================================================
 // Forward-declared internal functions to compute reciprocal-based gains:
 //   f(x) = A + (K - A)*exp( -1 / [B*(x - C)] )
 //=============================================================================
 static float getExpKp(float x);
 static float getExpKi(float x);
 static float getExpKd(float x);
 
 
 //=============================================================================
 // initExpController
 // Resets local state, integrator, and dynamic filter for this exp-based PID.
 //=============================================================================
 void initExpController(SystemState &state)
 {
     state.pGain         = 0.0f;
     state.iGain         = 0.0f;
     state.dGain         = 0.0f;
     state.filteredError = 0.0f;
     state.currentAlpha  = 0.0f;
 
     // Reset the PID integrator, derivative filter, etc.
     initPID();  // sets integralTerm = 0.0f
     s_lastKi = 0.0f;
 
     // Initialize the dynamic error filter (which does slope-matching internally)
     initDynamicLPFilter(s_errorFilter);
 
     // For optional smoothed error logging
     g_errSmooth = 0.0f;
 
     // Debug
     Serial.println("[EXP_CONTROL] initExpController() -> PID + filter reset");
 }
 
 
 //=============================================================================
 // updateExpController
 // Main control loop logic using the custom
 //   f(x) = A + (K - A)*exp( -1 / [B*(x - c)] ) gains.
 //
 // If 'systemOn' is false, we simply return and do nothing.
 //=============================================================================
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
 
     // 1) Filter the error (filter.cpp handles slope matching)
     float errFiltered = updateDynamicLPFilter(s_errorFilter, errRaw);
     g_errSmooth       = errFiltered;
     state.filteredError = errFiltered;
     state.currentAlpha  = s_errorFilter.currentAlpha;
 
     // We'll use absolute error for the gain calculation
     float absE = fabs(errFiltered);
 
     // 2) Get exponential-based P, I, D gains
     float kp = getExpKp(absE);
     float ki = getExpKi(absE);
     float kd = getExpKd(absE);
 
     // Optional debug: show old vs new Ki
     Serial.print("[DEBUG] oldKi=");
     Serial.print(s_lastKi, 6);
     Serial.print(", newKi=");
     Serial.print(ki, 6);
 
     // 3) Rescale integrator if Ki changed significantly
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
 
     // 4) Apply new gains to PID
     setPIDGains(kp, ki, kd);
 
     // Store them in the system state (for logging/monitoring)
     state.pGain = kp;
     state.iGain = ki;
     state.dGain = kd;
 
     // 5) Normal PID update
     pidFraction = updatePIDNormal(errFiltered, pTermOut, iTermOut, dTermOut);
 
     // 6) Check saturation / clamp
     if (pidFraction > 1.0f) {
         // minor anti-windup
         integralTerm -= g_lastIntegralIncrement;
         pidFraction = 1.0f;
     } else if (pidFraction < 0.0f) {
         pidFraction = 0.0f;
     }
 
     // 7) Convert PID output fraction to voltage
     desiredVoltage = pidFraction * BARTELS_MAX_VOLTAGE;
 
     // Enforce min voltage if above 0 but below min
     if (desiredVoltage > 0.0f && desiredVoltage < BARTELS_MIN_VOLTAGE) {
         desiredVoltage = BARTELS_MIN_VOLTAGE;
     }
 
     // Enforce max voltage
     if (desiredVoltage > BARTELS_MAX_VOLTAGE) {
         desiredVoltage = BARTELS_MAX_VOLTAGE;
     }
 
     // 8) Command the pump hardware
     runSequence(desiredVoltage);
 
     // Debug: final integrator after this loop
     Serial.print("[DEBUG] PID loop done. integralTerm=");
     Serial.print(integralTerm, 6);
     Serial.print(", pidFraction=");
     Serial.print(pidFraction, 6);
     Serial.print(", desiredVoltage=");
     Serial.println(desiredVoltage, 6);
 }
 
 
 //=============================================================================
 // getExpKp / getExpKi / getExpKd
 // Each returns A + (K - A)*exp( -1 / [ B*(x - C) ] ) using config-defined params
 //=============================================================================
 
 static float getExpKp(float x)
 {
     float A = EXP_KP_A;
     float K = EXP_KP_K;
     float B = EXP_KP_B;
     float C = EXP_KP_C;
 
     // We'll compute the reciprocal-based exponent:
     // exponent = -1 / (B*(x - C))
     // Guard vs. near-zero denominators
     if (fabs(B) < 1e-9f) {
         // fallback or clamp
         return A;
     }
     float denom = B * (x - C);
     if (fabs(denom) < 1e-9f) {
         // fallback or clamp
         return A;
     }
 
     float exponent = -1.0f / denom;
     float val = A + (K - A) * expf(exponent);
 
     // Optional: clamp result to [A, K]
     if (val < A) val = A;
     if (val > K) val = K;
 
     return val;
 }
 
 static float getExpKi(float x)
 {
     float A = EXP_KI_A;
     float K = EXP_KI_K;
     float B = EXP_KI_B;
     float C = EXP_KI_C;
 
     if (fabs(B) < 1e-9f) {
         return A;
     }
     float denom = B * (x - C);
     if (fabs(denom) < 1e-9f) {
         return A;
     }
 
     float exponent = -1.0f / denom;
     float val = A + (K - A) * expf(exponent);
 
     if (val < A) val = A;
     if (val > K) val = K;
 
     return val;
 }
 
 static float getExpKd(float x)
 {
     float A = EXP_KD_A;
     float K = EXP_KD_K;
     float B = EXP_KD_B;
     float C = EXP_KD_C;
 
     if (fabs(B) < 1e-9f) {
         return A;
     }
     float denom = B * (x - C);
     if (fabs(denom) < 1e-9f) {
         return A;
     }
 
     float exponent = -1.0f / denom;
     float val = A + (K - A) * expf(exponent);
 
     if (val < A) val = A;
     if (val > K) val = K;
 
     return val;
 }
 