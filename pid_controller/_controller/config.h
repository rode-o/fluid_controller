#pragma once
#include <Arduino.h>

/*
 * File: config.h
 * Brief: Central configuration for display, pump driver, flow sensor,
 *        PID parameters, and other system-wide settings.
 */


 static const float kConstantVoltage = 80.0f; //consts for constant voltage control

// Display
static const uint8_t SSD1306_DISPLAY_ADDR = 0x3C;

// Bartels pump driver
static const uint8_t BARTELS_DRIVER_ADDR   = 0x59;
static const uint8_t BARTELS_PAGE_REGISTER = 0xFF;
static const uint8_t BARTELS_CONTROL_DATA[] = {0x00, 0x3B, 0x01, 0x01};

// ---------------------------------------------------------------------------
// Define a single "desired" frequency in Hz that we'll use for the micropump.
// (Adjust this value as needed.)
static const float BARTELS_FREQ = 300.0f; 
// ---------------------------------------------------------------------------

// Voltage limits
static const float BARTELS_ABSOLUTE_MAX = 150.0f;
static const float BARTELS_MAX_VOLTAGE  = 150.0f;
static const float BARTELS_MIN_VOLTAGE  = 0.0f;

// Flow sensor
static const uint8_t SLF_FLOW_SENSOR_ADDR     = 0x08;
static const uint8_t SLF_START_CMD            = 0x36;
static const uint8_t SLF_CALIBRATION_CMD_BYTE = 0x08;
static const uint8_t SLF_STOP_CMD             = 0x3F;
static const uint8_t SLF_STOP_BYTE            = 0xF9;

static const float SLF_SCALE_FACTOR_FLOW = 10000.0f;
static const float SLF_SCALE_FACTOR_TEMP = 200.0f;
static const float SLF_RUN_DURATION      = 36000.0f; // in seconds

// First-order LPF parameters
static const float LPF_ALPHA_BASE      = 0.0f; 
static const float LPF_ALPHA_AMPLITUDE = 1.0f; 
static const float LPF_ALPHA_SLOPE     = 2000.0f; 
static const float LPF_ALPHA_MIDPOINT  = 0.005f; 

// Sigmoidal control gains
static const float P_BASE       = 0.0f;
static const float P_AMPLITUDE  = 0.0f;
static const float P_SLOPE      = 0.0f;
static const float P_MIDPOINT   = 0.0f;

static const float I_BASE       = 0.001f;
static const float I_AMPLITUDE  = 0.299f;
static const float I_SLOPE      = 1200.0f;
static const float I_MIDPOINT   = 0.0069f;

static const float D_BASE       = 0.0f;
static const float D_AMPLITUDE  = 0.0f;
static const float D_SLOPE      = 0.0f;
static const float D_MIDPOINT   = 0.0f;

// PID configuration
static const float PID_ANTIWINDUP_GAIN    = 0.1f;
static const float PID_DERIV_FILTER_ALPHA = 0.8f;

// Flow/error ranges
static const float FLOW_SP_MIN       = 0.0f;
static const float FLOW_SP_MAX       = 2.0f;
static const float ERROR_PERCENT_MIN = -50.0f;
static const float ERROR_PERCENT_MAX =  50.0f;

// Filters & step sizes
static const float FLOW_FILTER_ALPHA = 0.2f;
static const float FLOW_STEP_SIZE    = 0.05f;
static const float ERROR_STEP_SIZE   = 1.0f;

// (These are legacy or used elsewhere. Not needed for pump freq anymore.)
static const float FLUID_TIME_CONSTANT  = 0.05f;
static const float LOOP_FREQ_FACTOR     = 15.0f;
static const float PUMP_FREQ_FACTOR     = 15.0f;
static const unsigned long MAIN_LOOP_DELAY_MS =
    (unsigned long)((FLUID_TIME_CONSTANT / LOOP_FREQ_FACTOR) * 1000.0f);

// Forward declaration for loading defaults (defined in config.cpp)
void loadDefaults();
