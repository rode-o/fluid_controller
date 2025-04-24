/*
 * File: exp_control.cpp
 * Brief: PID controller whose gains follow
 *        f(x) = A + (K − A) · exp( −1 / (B · (x − c)) ).
 *
 * Error conditioning (2-pole cascade, hidden in TwoPoleFilter):
 *      raw → adaptive slope-matched LPF → fixed-α EMA → PID
 */

 #include "exp_control.h"
 #include "config.h"      // BARTELS_MAX_VOLTAGE, etc.
 #include "gain.h"
 #include "filter.h"      // TwoPoleFilter + wrapper API
 #include "pid.h"
 #include "bartels.h"
 #include <Arduino.h>
 
 // ─────────────────────────────────────────────
 // External integrator symbols (defined in pid.cpp)
 extern float integralTerm;
 extern float g_lastIntegralIncrement;
 
 // ─────────────────────────────────────────────
 // Local persistent state
 static TwoPoleFilter s_errFilter;   // composite 2-pole filter
 static float         s_lastKi   = 0.0f;   // for integrator rescaling
 static float         g_errSmooth = 0.0f;  // optional for logging
 
 // ─────────────────────────────────────────────
 // Forward-declared gain helpers
 static float getExpKp(float x);
 static float getExpKi(float x);
 static float getExpKd(float x);
 
 // ─────────────────────────────────────────────
 // initExpController — reset everything
 void initExpController(SystemState &state)
 {
     state = {};                    // zero public fields
     initPID();                     // clears integralTerm, etc.
 
     initTwoPoleFilter(s_errFilter);
     s_lastKi   = 0.0f;
     g_errSmooth = 0.0f;
 
     Serial.println(F("[EXP_CONTROL] initExpController → reset OK"));
 }
 
 // ─────────────────────────────────────────────
 // updateExpController — main control loop
 void updateExpController(
     SystemState &state,
     float flow,
     float flowSetpoint,
     float errorPercent,
     bool  systemOn,
     float &desiredVoltage,
     float &pidFraction,
     bool  &bubbleDetected,
     float &pTermOut,
     float &iTermOut,
     float &dTermOut)
 {
     /* 0. Safety: system OFF */
     if (!systemOn) {
         stopPump();
         pidFraction = desiredVoltage = pTermOut = iTermOut = dTermOut = 0.0f;
         return;
     }
 
     /* 1. Raw error */
     float errRaw = flowSetpoint - flow;
 
     /* 2. Two-pole filtering (adaptive + EMA) */
     float errSmooth = updateTwoPoleFilter(s_errFilter, errRaw);
 
     /* Log / expose */
     g_errSmooth         = errSmooth;
     state.filteredError = errSmooth;
     state.currentAlpha  = s_errFilter.dyn.currentAlpha;
 
     /* 3. Exponential gains */
     float absE = fabs(errSmooth);
     float kp = getExpKp(absE);
     float ki = getExpKi(absE);
     float kd = getExpKd(absE);
 
     /* Rescale integrator if Ki changes */
     if (fabs(s_lastKi - ki) > 1e-9f) {
         if (fabs(s_lastKi) > 1e-9f && fabs(ki) > 1e-9f)
             integralTerm *= s_lastKi / ki;
         s_lastKi = ki;
     }
 
     setPIDGains(kp, ki, kd);
     state.pGain = kp;  state.iGain = ki;  state.dGain = kd;
 
     /* 4. PID update */
     pidFraction = updatePIDNormal(errSmooth, pTermOut, iTermOut, dTermOut);
 
     /* Clamp & anti-windup */
     if (pidFraction > 1.0f) {
         integralTerm -= g_lastIntegralIncrement;
         pidFraction = 1.0f;
     } else if (pidFraction < 0.0f) {
         pidFraction = 0.0f;
     }
 
     /* 5. Voltage mapping + limits */
     desiredVoltage = pidFraction * BARTELS_MAX_VOLTAGE;
     if (desiredVoltage > 0.0f && desiredVoltage < BARTELS_MIN_VOLTAGE)
         desiredVoltage = BARTELS_MIN_VOLTAGE;
     if (desiredVoltage > BARTELS_MAX_VOLTAGE)
         desiredVoltage = BARTELS_MAX_VOLTAGE;
 
     /* 6. Drive pump */
     runSequence(desiredVoltage);
 }
 
 // ─────────────────────────────────────────────
 // Exponential gain helper
 static float expCurve(float x, float A, float K, float B, float C)
 {
     float denom = B * (x - C);
     if (fabs(denom) < 1e-9f) return A;
     float v = A + (K - A) * expf(-1.0f / denom);
     if (v < A) v = A;
     if (v > K) v = K;
     return v;
 }
 
 static float getExpKp(float x){ return expCurve(x,EXP_KP_A,EXP_KP_K,EXP_KP_B,EXP_KP_C); }
 static float getExpKi(float x){ return expCurve(x,EXP_KI_A,EXP_KI_K,EXP_KI_B,EXP_KI_C); }
 static float getExpKd(float x){ return expCurve(x,EXP_KD_A,EXP_KD_K,EXP_KD_B,EXP_KD_C); }
 