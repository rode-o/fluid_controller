/*
 * File: pid.cpp
 * Brief: Implements a basic PID controller with derivative filtering.
 */

 #include "pid.h"
 #include "config.h"
 #include <Arduino.h>
 
 // PID gains
 static float Kp = 0.0f;
 static float Ki = 0.0f;
 static float Kd = 0.0f;
 
 // Derivative filter
 static float derivFilterAlphaNormal = 0.0f;
 static float dErrorFilteredNormal   = 0.0f;
 
 // Exposed integrator term (extern in pid.h)
 float integralTerm = 0.0f;
 
 // Tracking variables for normal PID
 static float lastError         = 0.0f;
 static unsigned long lastTimeNormal = 0;
 
 // Externally referenced anti-windup data
 float g_lastIntegralIncrement = 0.0f;
 float g_lastErrorForAW        = 0.0f;
 
 /*
  * Re-initializes PID states (integrator, derivative filter).
  * Gains are set externally.
  */
 void initPID() {
   derivFilterAlphaNormal = PID_DERIV_FILTER_ALPHA;
   dErrorFilteredNormal   = 0.0f;
   integralTerm           = 0.0f;
   lastError              = 0.0f;
   lastTimeNormal         = millis();
   g_lastIntegralIncrement = 0.0f;
   g_lastErrorForAW        = 0.0f;
 }
 
 /*
  * Dynamically updates PID gains.
  */
 void setPIDGains(float p, float i, float d) {
   Kp = p;
   Ki = i;
   Kd = d;
 }
 
 /*
  * Executes a single PID iteration with derivative filtering.
  * Returns the clamped output fraction in [0..1].
  */
 float updatePIDNormal(float error,
                       float &pTermOut,
                       float &iTermOut,
                       float &dTermOut)
 {
   unsigned long now = millis();
   float dt = (now - lastTimeNormal) / 1000.0f;
   if (dt <= 0.0f) {
     dt = 0.001f;
   }
   lastTimeNormal = now;
 
   // Proportional term
   float Pout = Kp * error;
 
   // Integral term
   float integralIncrement = error * dt;
   integralTerm += integralIncrement;
   float Iout = Ki * integralTerm;
 
   g_lastIntegralIncrement = integralIncrement;
   g_lastErrorForAW        = error;
 
   // Derivative term (filtered)
   float dErrorRaw = (error - lastError) / dt;
   dErrorFilteredNormal = derivFilterAlphaNormal * dErrorRaw 
                        + (1.0f - derivFilterAlphaNormal) * dErrorFilteredNormal;
   float Dout = Kd * dErrorFilteredNormal;
 
   float rawOutput = Pout + Iout + Dout;
   if (rawOutput < 0.0f) rawOutput = 0.0f;
   else if (rawOutput > 1.0f) rawOutput = 1.0f;
 
   lastError = error;
 
   // Provide terms for debugging
   pTermOut = Pout;
   iTermOut = Iout;
   dTermOut = Dout;
 
   return rawOutput;
 }
 