#pragma once
#include <Arduino.h>

/*
 * File: config.h
 * Brief: Central configuration for display, pump driver, flow sensor,
 *        PID parameters, and other system-wide settings.
 */

// ---------------------------------------------------------------------------
// Constant Voltage Control
// ---------------------------------------------------------------------------
static const float kConstantVoltage = 80.0f; // Used in constant-voltage control mode


// ---------------------------------------------------------------------------
// Display
// ---------------------------------------------------------------------------
static const uint8_t SSD1306_DISPLAY_ADDR = 0x3C;


// ---------------------------------------------------------------------------
// Bartels Pump Driver
// ---------------------------------------------------------------------------
static const uint8_t BARTELS_DRIVER_ADDR   = 0x59;
static const uint8_t BARTELS_PAGE_REGISTER = 0xFF;
static const uint8_t BARTELS_CONTROL_DATA[] = {0x00, 0x3B, 0x01, 0x01};

static const float BARTELS_FREQ         = 300.0f;  // Desired pump frequency in Hz
static const float BARTELS_ABSOLUTE_MAX = 150.0f;
static const float BARTELS_MAX_VOLTAGE  = 150.0f;
static const float BARTELS_MIN_VOLTAGE  = 0.0f;


// ---------------------------------------------------------------------------
// Flow Sensor
// ---------------------------------------------------------------------------
static const uint8_t SLF_FLOW_SENSOR_ADDR     = 0x08;
static const uint8_t SLF_START_CMD            = 0x36;
static const uint8_t SLF_CALIBRATION_CMD_BYTE = 0x08;
static const uint8_t SLF_STOP_CMD             = 0x3F;
static const uint8_t SLF_STOP_BYTE            = 0xF9;

static const float SLF_SCALE_FACTOR_FLOW = 10000.0f;
static const float SLF_SCALE_FACTOR_TEMP = 200.0f;

// Maximum run duration (seconds) before auto-stop
static const float SLF_RUN_DURATION = 36000.0f; 


// ---------------------------------------------------------------------------
// Flow/Error Ranges
// ---------------------------------------------------------------------------
static const float FLOW_SP_MIN       = 0.0f;
static const float FLOW_SP_MAX       = 2.0f;
static const float ERROR_PERCENT_MIN = -50.0f;
static const float ERROR_PERCENT_MAX =  50.0f;

/**
 * FLOW_STEP_SIZE:
 *   Step amount for adjusting the flow setpoint via button presses (in buttons.cpp).
 */
static const float FLOW_STEP_SIZE = 0.05f;


// ---------------------------------------------------------------------------
// Exponential Gain Parameters for PID
//   f(x) = A + (K - A)*exp(-(1/B)*(x - C))
// ---------------------------------------------------------------------------

// Kp parameters
#define EXP_KP_A  0.0f
#define EXP_KP_K  0.0f
#define EXP_KP_B  0.0f
#define EXP_KP_C  0.0f

// Ki parameters
#define EXP_KI_A  0.001f
#define EXP_KI_K  0.23f
#define EXP_KI_B  40.0f
#define EXP_KI_C  0.0f

// Kd parameters
#define EXP_KD_A  0.0f
#define EXP_KD_K  0.0f
#define EXP_KD_B  0.0f
#define EXP_KD_C  0.0f


// ---------------------------------------------------------------------------
// Filter / Slope-Matching Parameters
// ---------------------------------------------------------------------------
/**
 * FILTER_T_REF:
 *   The reference "time" or error at which we match slopes for
 *   the primary vs. secondary exponential function.
 */
static const float FILTER_T_REF = 0.05f;

/**
 * FILTER_SECONDARY_A2 / K2:
 *   For the secondary function f2(t) = A2 + (K2 - A2)*exp(-1/(B2*t)),
 *   often pinned A2=0, K2=1 for slope matching approach.
 */
static const float FILTER_SECONDARY_A2 = 0.0f;
static const float FILTER_SECONDARY_K2 = 0.5f;

/**
 * FILTER_B2_GUESS:
 *   Initial guess for numeric solving to find B2.
 */
static const float FILTER_B2_GUESS = 3.0f;

// ─── Extra EMA pole ──────────────────────────────────────────────
// α close to 1.0  → heavy smoothing, more delay
// α close to 0.0  → no smoothing
#define EMA_ALPHA   0.85f          


// ---------------------------------------------------------------------------
// (Optional) Legacy logistic-based LPF params (you can remove if not in use)
// ---------------------------------------------------------------------------
static const float LPF_ALPHA_BASE      = 0.0f; 
static const float LPF_ALPHA_AMPLITUDE = 1.0f; 
static const float LPF_ALPHA_SLOPE     = 2000.0f; 
static const float LPF_ALPHA_MIDPOINT  = 0.005f;


// ---------------------------------------------------------------------------
// PID Configuration
// ---------------------------------------------------------------------------
static const float PID_ANTIWINDUP_GAIN    = 0.1f;
static const float PID_DERIV_FILTER_ALPHA = 0.8f;


// ---------------------------------------------------------------------------
// Timing / Loop
// ---------------------------------------------------------------------------
static const float FLUID_TIME_CONSTANT = 0.05f;
static const float LOOP_FREQ_FACTOR    = 15.0f;
static const unsigned long MAIN_LOOP_DELAY_MS =
    (unsigned long)((FLUID_TIME_CONSTANT / LOOP_FREQ_FACTOR) * 1000.0f);


// ---------------------------------------------------------------------------
// Function Prototypes
// ---------------------------------------------------------------------------
void loadDefaults();
