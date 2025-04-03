/*
 * File: gain.cpp
 * Brief: Implements reciprocal-based gain scheduling for PID parameters,
 *        using f(t) = A + (K - A)*exp( - 1 / (B*(t - c)) ).
 */

 #include "gain.h"
 #include "config.h"
 #include <math.h>
 
 /**
  * @brief exponentialFunctionReciprocal
  *
  * Implements the reciprocal form:
  *   f(t) = A + (K - A)*exp( -1 / (B*(t - c)) )
  *
  * @param t   Input value (e.g. time, or maybe an error magnitude if you rename variables).
  * @param A   Lower asymptote.
  * @param K   Upper asymptote.
  * @param B   Scaling factor for the reciprocal portion.
  * @param c   Horizontal shift.
  * @return    The reciprocal-based gain value.
  */
 static float exponentialFunctionReciprocal(float t, float A, float K, float B, float c)
 {
     // Avoid dividing by zero if |B| < small threshold.
     if (fabsf(B) < 1e-9f) {
         // fallback or clamp
         return A; 
     }
     // Avoid dividing by zero if t == c.
     float denominator = B * (t - c);
     if (fabsf(denominator) < 1e-9f) {
         // fallback or clamp
         return A;
     }
 
     float exponent = -1.0f / denominator;
     return A + (K - A) * expf(exponent);
 }
 
 /**
  * @brief getExpKp
  *        Returns the reciprocal-based Kp using parameters from config.h
  */
 float getExpKp(float t)
 {
     return exponentialFunctionReciprocal(t, 
                                          EXP_KP_A, 
                                          EXP_KP_K, 
                                          EXP_KP_B, 
                                          EXP_KP_C);
 }
 
 /**
  * @brief getExpKi
  *        Returns the reciprocal-based Ki using parameters from config.h
  */
 float getExpKi(float t)
 {
     return exponentialFunctionReciprocal(t, 
                                          EXP_KI_A, 
                                          EXP_KI_K, 
                                          EXP_KI_B, 
                                          EXP_KI_C);
 }
 
 /**
  * @brief getExpKd
  *        Returns the reciprocal-based Kd using parameters from config.h
  */
 float getExpKd(float t)
 {
     return exponentialFunctionReciprocal(t, 
                                          EXP_KD_A, 
                                          EXP_KD_K, 
                                          EXP_KD_B, 
                                          EXP_KD_C);
 }
 