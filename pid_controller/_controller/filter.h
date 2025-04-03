#pragma once

struct DynamicLPFilter {
    float state;
    float currentAlpha;
};

// Initializes the dynamic filter (resets state, optionally pre-computes any needed parameters).
void initDynamicLPFilter(DynamicLPFilter &filter);

// Updates the filter output using your custom alpha logic derived from Ki's exponential parameters.
float updateDynamicLPFilter(DynamicLPFilter &filter, float rawValue);

