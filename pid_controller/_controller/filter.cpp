/*
 * File: filter.cpp
 * Purpose
 *   1) Adaptive first-order LPF whose α(|e|) is slope–matched to the Ki curve.
 *   2) Tiny fixed-α EMA pole for extra polish.
 *   3) Optional wrapper (TwoPoleFilter) that cascades the two.
 *
 *   Header/implementation split:
 *     • All type declarations & prototypes  →  filter.h
 *     • All logic lives here                →  filter.cpp
 */

 #include "filter.h"
 #include "config.h"      // EXP_KI_*, FILTER_*, EMA_ALPHA
 #include <Arduino.h>
 #include <math.h>
 
 /*──────────────────────── INTERNALS FOR ADAPTIVE α ───────────────────────*/
 static float s_b2 = 0.0f;   // solved once (slope-matching)
 
 static float customExpDerivative(float t, float A, float K, float B)
 {
     if (t <= 1e-9f) return 0.0f;
     float factor = (K - A) * expf(-1.0f / (B * t));
     return factor / (B * t * t);
 }
 
 static float computeB2ViaSlope(float A1,float K1,float B1,
                                float A2,float K2,float Tref)
 {
     float slopeP = customExpDerivative(Tref,A1,K1,B1);
     float lo=1e-3f, hi=100.0f, eps=1e-6f, mid=FILTER_B2_GUESS;
 
     for (int i=0;i<60;i++) {
         mid  = 0.5f*(lo+hi);
         float slope2 = customExpDerivative(Tref,A2,K2,mid);
         (slope2 > slopeP) ? lo = mid : hi = mid;
         if ((hi-lo) < eps) break;
     }
     return mid;
 }
 
 static float computeAlphaSecondary(float e,float A2,float K2)
 {
     if (e < 1e-9f) return 1.0f;
     float val = A2 + (K2 - A2) * expf(-1.0f / (s_b2 * e));
     if (val < 0.0f) val = 0.0f;
     if (val > 1.0f) val = 1.0f;
     return val;
 }
 
 /*──────────────────────── PUBLIC ADAPTIVE FILTER ─────────────────────────*/
 void initDynamicLPFilter(DynamicLPFilter &f)
 {
     Serial.println(F("[FILTER] slope-matching B2 …"));
     s_b2 = computeB2ViaSlope(EXP_KI_A,EXP_KI_K,EXP_KI_B,
                              FILTER_SECONDARY_A2,FILTER_SECONDARY_K2,
                              FILTER_T_REF);
     Serial.print  (F("[FILTER] B2 = ")); Serial.println(s_b2,6);
 
     f.state = 0.0f;
     f.currentAlpha = 0.0f;
 }
 
 float updateDynamicLPFilter(DynamicLPFilter &f, float in)
 {
     float a   = computeAlphaSecondary(fabsf(in),
                                       FILTER_SECONDARY_A2,
                                       FILTER_SECONDARY_K2);
     float out = a*in + (1.0f-a)*f.state;
     f.state = out;  f.currentAlpha = a;
     return out;
 }
 
 /*──────────────────────── FIXED-α  EMA POLE ──────────────────────────────*/
 void resetEMA(SimpleEMA &e)         { e = {0.0f, false}; }
 
 float updateEMA(SimpleEMA &e, float in)
 {
     if (!e.primed) { e.state=in; e.primed=true; return in; }
     e.state = EMA_ALPHA*in + (1.0f-EMA_ALPHA)*e.state;
     return e.state;
 }
 
 /*──────────────────────── TWO-POLE WRAPPER ───────────────────────────────*/
 void initTwoPoleFilter(TwoPoleFilter &f)
 {
     initDynamicLPFilter(f.dyn);
     resetEMA(f.ema);
 }
 
 float updateTwoPoleFilter(TwoPoleFilter &f, float in)
 {
     float stage1 = updateDynamicLPFilter(f.dyn, in);
     return       updateEMA           (f.ema, stage1);
 }
 