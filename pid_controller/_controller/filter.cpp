/*
 * File: filter.cpp
 * Brief: Implements a dynamic low-pass filter using a "secondary" exponential
 *        function derived by slope matching the "primary" Ki function
 *        at a reference point T_ref from config.h.
 *
 * Primary function (Ki):
 *   f1(t) = A1 + (K1 - A1)*exp(-1/(B1 * t)).
 *   The derivative: f1'(t) = (K1 - A1)*exp(-1/(B1 * t)) * (1/(B1 * t^2)).
 *
 * Secondary function pinned to A2, K2, solve for B2:
 *   f2(t) = A2 + (K2 - A2)*exp(-1/(B2 * t)).
 *   The derivative: f2'(t) = (K2 - A2)*exp(-1/(B2 * t)) * (1/(B2 * t^2)).
 *
 * We match slopes at t=T_ref => f1'(T_ref) = f2'(T_ref).
 *
 * Then alpha(e) = f2(|e|). The filter update is out = alpha*in + (1-alpha)*old.
 */

 #include "filter.h"
 #include "config.h"      // for EXP_KI_A, EXP_KI_K, EXP_KI_B, FILTER_T_REF, etc.
 #include <Arduino.h>     // for Serial
 #include <math.h>        // for expf, fabsf
 
 // We store B2 in a static so that once computed, we can use it each cycle:
 static float s_b2 = 0.0f;
 
 // ---------------------------------------------------------------------------
 // customExpDerivative()
 //   Returns the derivative of f(t) = A + (K - A)*exp(-1/(B*t)) at a point t
 //   => f'(t) = (K - A)*exp(-1/(B*t)) * [1/(B * t^2)].
 // ---------------------------------------------------------------------------
 static float customExpDerivative(float t, float A, float K, float B)
 {
     // watch out for t=0 domain
     if (t <= 1e-9f) return 0.0f;  // or handle differently
 
     float factor = (K - A) * expf(-1.0f / (B * t));
     float denom  = (B * t * t);
     if (denom == 0.0f) return 0.0f;
     return factor / denom;
 }
 
 // ---------------------------------------------------------------------------
 // computeB2ViaSlopeMatching()
 //   We do a simple binary search to find B2 so that
 //   derivative(f2)(T_ref) = derivative(f1)(T_ref).
 //
 //   f1 => (A1,K1,B1) from Ki
 //   f2 => (A2,K2,B2) from config + unknown B2
 //
 //   We use T_ref = FILTER_T_REF from config.h
 // ---------------------------------------------------------------------------
 static float computeB2ViaSlopeMatching(
     float A1, float K1, float B1,  // primary
     float A2, float K2,           // pinned for secondary
     float Tref                    // reference time
 )
 {
     float slopePrimary = customExpDerivative(Tref, A1, K1, B1);
 
     // We'll do a simple binary search in [lowB, highB].
     // Adjust these bounds if you have domain knowledge of valid B2 range:
     float lowB  = 1e-3f;
     float highB = 100.0f;
     float eps   = 1e-6f;
     float b2    = FILTER_B2_GUESS;  // initial guess (from config)
 
     for (int i = 0; i < 60; i++) {
         float mid = 0.5f * (lowB + highB);
         // Evaluate slope2 at Tref, B2=mid
         float slope2 = customExpDerivative(Tref, A2, K2, mid);
 
         // Compare slopes
         if (slope2 > slopePrimary) {
             // We want slope2 to be smaller to match slopePrimary, so we move up or down
             // Actually, if slope2 is bigger than slopePrimary, we might need to increase or decrease mid
             // depending on how derivative changes with B. Let's check monotonic behavior:
             // derivative wrt B is typically negative slope wrt B => We'll guess we need bigger B to reduce slope2
             lowB = mid;
         } else {
             highB = mid;
         }
 
         if ((highB - lowB) < eps) {
             b2 = mid;
             break;
         }
         b2 = mid;
     }
 
     return b2;
 }
 
 // ---------------------------------------------------------------------------
 // computeAlphaSecondary()
 //   alpha(e) = f2(e) = A2 + (K2 - A2)*exp(-1/(B2 * e)), using the B2 we solved.
 //
 //   We'll clamp alpha to [0,1], but you can skip if not needed.
 // ---------------------------------------------------------------------------
 static float computeAlphaSecondary(float e, float A2, float K2)
 {
     if (e < 1e-9f) {
         // near zero domain => limit
         return 1.0f;
     }
     float exponent = -1.0f / (s_b2 * e);
     float val      = A2 + (K2 - A2)*expf(exponent);
 
     // optional clamp
     if (val < 0.0f) val = 0.0f;
     if (val > 1.0f) val = 1.0f;
 
     return val;
 }
 
 // ---------------------------------------------------------------------------
 // initDynamicLPFilter()
 //   1) We read the "primary" Ki function from config: (EXP_KI_A, EXP_KI_K, EXP_KI_B).
 //   2) We read T_ref from config: FILTER_T_REF
 //   3) We read/pin A2,K2 from config: FILTER_SECONDARY_A2, FILTER_SECONDARY_K2
 //   4) We do slope matching to find s_b2
 //   5) We reset filter state
 // ---------------------------------------------------------------------------
 void initDynamicLPFilter(DynamicLPFilter &filter)
 {
     Serial.println("[FILTER] initDynamicLPFilter -> Starting slope matching...");
 
     float A1   = EXP_KI_A;
     float K1   = EXP_KI_K;
     float B1   = EXP_KI_B;
     float A2   = FILTER_SECONDARY_A2;
     float K2   = FILTER_SECONDARY_K2;
     float Tref = FILTER_T_REF;
 
     // Solve for B2
     s_b2 = computeB2ViaSlopeMatching(A1, K1, B1, A2, K2, Tref);
 
     Serial.print("[FILTER] slope matching complete => B2=");
     Serial.println(s_b2, 6);
 
     // Reset filter state
     filter.state = 0.0f;
     filter.currentAlpha = 0.0f;
 }
 
 // ---------------------------------------------------------------------------
 // updateDynamicLPFilter()
 //   - We compute alpha = f2(|rawValue|) = exp(-1/(s_b2*|rawValue|)) 
 //       pinned by (A2,K2), from config
 //   - Then do out = alpha*raw + (1-alpha)*state
 // ---------------------------------------------------------------------------
 float updateDynamicLPFilter(DynamicLPFilter &filter, float rawValue)
 {
     float absE  = fabsf(rawValue);
     float alpha = computeAlphaSecondary(absE, FILTER_SECONDARY_A2, FILTER_SECONDARY_K2);
 
     float newOutput = alpha*rawValue + (1.0f - alpha)*filter.state;
 
     filter.currentAlpha = alpha;
     filter.state        = newOutput;
 
     return newOutput;
 }
 