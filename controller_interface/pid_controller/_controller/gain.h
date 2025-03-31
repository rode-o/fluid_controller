#ifndef GAIN_H
#define GAIN_H

/*
 * File: gain.h
 * Brief: Declares logistic-based scheduling functions for PID gains.
 */

// Returns kP based on the absolute error using a logistic function
float getSigmoidKp(float absError);

// Returns kI based on the absolute error using a logistic function
float getSigmoidKi(float absError);

// Returns kD based on the absolute error using a logistic function
float getSigmoidKd(float absError);

#endif // GAIN_H
