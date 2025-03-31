#pragma once

// Forward-declare any enums if needed:
enum ControlMode {
  CONTROL_MODE_SIGMOIDAL = 0,
  CONTROL_MODE_CONST_VOLTAGE
};

/**
 * Contains all runtime state for logging, control, etc.
 */
struct SystemState {
  // --- Timing ---
  unsigned long currentTimeMs;

  // --- Sensor data ---
  float flow;
  float setpoint;      // Flow setpoint
  float errorPercent;
  float temperature;
  bool  bubbleDetected;

  // --- Control mode and flags ---
  bool        systemOn;
  ControlMode controlMode;

  // --- Control outputs ---
  float pidOutput;      // e.g., fraction [0..1]
  float desiredVoltage; // final voltage command to pump

  // --- PID term breakdown (if you need to log them) ---
  float pTerm;
  float iTerm;
  float dTerm;

  // --- Current gains (if dynamically updated) ---
  float pGain;
  float iGain;
  float dGain;

  // --- Filtered signals ---
  float filteredError;
  float currentAlpha;
};
