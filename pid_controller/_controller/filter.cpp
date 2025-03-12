/*
 * File: filter.cpp
 * Brief: Implements a dynamic low-pass filter with a logistic-based alpha.
 */

 #include "filter.h"
  #include "config.h"
 #include <math.h>
 #include <Arduino.h>
 
 // Computes the adaptive alpha value in [0..1] using a logistic function
 static float computeAlpha(float absError) {
  // Use values from config.h
  return LPF_ALPHA_BASE +
         (LPF_ALPHA_AMPLITUDE / (1.0f + expf(-LPF_ALPHA_SLOPE * (absError - LPF_ALPHA_MIDPOINT))));
}
 
 // Initializes the filter state
 void initDynamicLPFilter(DynamicLPFilter &filter) {
   filter.state = 0.0f;
 }
 
 // Updates the filter output using a first-order LPF with adaptive alpha
 float updateDynamicLPFilter(DynamicLPFilter &filter, float rawValue) {
   float alpha     = computeAlpha(fabs(rawValue));
   float newOutput = alpha * rawValue + (1.0f - alpha) * filter.state;

   filter.currentAlpha = alpha;
   filter.state    = newOutput;
   return newOutput;
 }
 