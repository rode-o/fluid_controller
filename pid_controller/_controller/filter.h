#pragma once
#include <stdint.h>

/*──────── Slope-matched first-pole filter ────────*/
typedef struct {
    float state;
    float currentAlpha;
} DynamicLPFilter;

/*──────── Fixed-α EMA second pole ───────────────*/
typedef struct {
    float state;
    bool  primed;
} SimpleEMA;

/*──────── 2-pole composite convenience wrapper ──*/
typedef struct {
    DynamicLPFilter dyn;   // adaptive pole
    SimpleEMA       ema;   // fixed-α pole
} TwoPoleFilter;

/*———  Primary adaptive filter ————————————*/
void  initDynamicLPFilter (DynamicLPFilter &f);
float updateDynamicLPFilter(DynamicLPFilter &f, float in);

/*———  EMA second pole ————————————————*/
void  resetEMA(SimpleEMA &e);           // helper
float updateEMA(SimpleEMA &e, float in);

/*———  Composite wrapper ——————————————*/
void  initTwoPoleFilter (TwoPoleFilter &f);
float updateTwoPoleFilter(TwoPoleFilter &f, float in);
