/*
 * File: gain.cpp
 * Brief: Implements logistic-based gain scheduling for PID parameters.
 */

 #include "gain.h"
 #include "config.h"
 #include <math.h>
 
 // Returns the logistic value given x, using specified base, amplitude, slope, and midpoint
 static float logisticFunction(float x, 
                               float base,
                               float amplitude,
                               float slope,
                               float midpoint)
 {
     return base + amplitude / (1.0f + expf(-slope * (x - midpoint)));
 }
 
 float getSigmoidKp(float absE) {
     return logisticFunction(absE, P_BASE, P_AMPLITUDE, P_SLOPE, P_MIDPOINT);
 }
 
 float getSigmoidKi(float absE) {
     return logisticFunction(absE, I_BASE, I_AMPLITUDE, I_SLOPE, I_MIDPOINT);
 }
 
 float getSigmoidKd(float absE) {
     return logisticFunction(absE, D_BASE, D_AMPLITUDE, D_SLOPE, D_MIDPOINT);
 }
 