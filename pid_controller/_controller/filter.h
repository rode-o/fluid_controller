#ifndef FILTER_H
#define FILTER_H

/*
 * File: filter.h
 * Brief: Defines a dynamic low-pass filter with an adaptive alpha.
 */

// Holds the last filtered value
struct DynamicLPFilter {
    float state;
    float currentAlpha;
};

// Initializes the filter (e.g., sets state to 0).
void initDynamicLPFilter(DynamicLPFilter &filter);

// Updates the filter with a new input, returning the filtered output.
float updateDynamicLPFilter(DynamicLPFilter &filter, float rawValue);

#endif // FILTER_H
