#include <Arduino.h>
#include <Wire.h>
#include <EEPROM.h>

// Project headers
#include "config.h"
#include "flow.h"
#include "bartels.h"
#include "buttons.h"
#include "pid.h"
#include "display.h"
#include "report.h"
// Removed old includes:
// #include "sigmoidal_control.h"
// #include "log_control.h"
#include "exp_control.h"  // Exponential-based control
#include "constant_voltage_control.h"
#include "filter.h"

// Combined runtime state
#include "system_state.h"

// Global system state
static SystemState g_systemState;

// Timing and reporting flags
static unsigned long startTime = 0;
static bool timeReportingEnabled = false;

// Track systemOn transitions in the main loop
static bool previousSystemOn = false;

void setup() {
    Serial.begin(115200);
    Wire.begin();
    EEPROM.begin(512);

    initButtons();
    initBartels();
    initDisplay();

    // Default control mode => EXP
    g_systemState.controlMode = CONTROL_MODE_EXP;

    // Initialize control modules
    initExpController(g_systemState); 
    initConstantVoltageControl();

    // Start flow measurement
    bool ok = startFlowMeasurement();
    if (!ok) {
        Serial.println("[MAIN DEBUG] startFlowMeasurement() failed (I2C error?).");
    }

    startTime = millis();
    Serial.println("[MAIN DEBUG] Setup complete. Entering main loop...");
}

void loop() {
    // 1) Check serial input for time-report toggle
    if (Serial.available() > 0) {
        char c = Serial.read();
        if (c == 'T' || c == 't') {
            timeReportingEnabled = !timeReportingEnabled;
            Serial.print("[MAIN DEBUG] Timing report: ");
            Serial.println(timeReportingEnabled ? "ENABLED" : "DISABLED");
        }
    }

    // 2) Update system-on state from buttons
    updateButtons();
    bool currentSystemOn = isSystemOn();
    g_systemState.systemOn = currentSystemOn;

    // Detect OFF->ON or ON->OFF transitions here in the main loop
    if (!previousSystemOn && currentSystemOn) {
        // System just turned ON
        Serial.println("[MAIN DEBUG] System turned ON (main loop) -> initExpController()");
        initExpController(g_systemState);
    } 
    else if (previousSystemOn && !currentSystemOn) {
        // System just turned OFF
        Serial.println("[MAIN DEBUG] System turned OFF (main loop) -> initExpController()");
        initExpController(g_systemState);
        // Optionally stop pump
        // stopPump();
    }
    previousSystemOn = currentSystemOn;

    // 3) Toggle control mode if requested
    if (wasModeTogglePressed()) {
        // Flip between EXP and CONST_VOLTAGE
        if (g_systemState.controlMode == CONTROL_MODE_EXP) {
            g_systemState.controlMode = CONTROL_MODE_CONST_VOLTAGE;
            Serial.println("[MAIN DEBUG] Mode changed -> CONSTANT VOLTAGE");
        } else {
            g_systemState.controlMode = CONTROL_MODE_EXP;
            Serial.println("[MAIN DEBUG] Mode changed -> EXP CONTROL");
        }
    }

    // 4) Acquire sensor inputs
    g_systemState.flow         = readFlow();
    g_systemState.setpoint     = getFlowSetpoint();
    g_systemState.errorPercent = getErrorPercent();
    g_systemState.temperature  = getTempC();

    uint16_t flags = getLastFlags();
    g_systemState.bubbleDetected = ((flags & (1 << 0)) != 0);

    // 5) Control logic
    float desiredVoltage = 0.0f;
    float pidFraction    = 0.0f;
    float pTerm          = 0.0f;
    float iTerm          = 0.0f;
    float dTerm          = 0.0f;

    if (g_systemState.systemOn) {
        switch (g_systemState.controlMode) {
            case CONTROL_MODE_EXP:
                Serial.println("[MAIN DEBUG] (ON) Calling updateExpController()...");
                updateExpController(
                    g_systemState,
                    g_systemState.flow,
                    g_systemState.setpoint,
                    g_systemState.errorPercent,
                    g_systemState.systemOn,
                    desiredVoltage,
                    pidFraction,
                    g_systemState.bubbleDetected,
                    pTerm,
                    iTerm,
                    dTerm
                );
                Serial.println("[MAIN DEBUG] Returned from updateExpController()");
                break;

            case CONTROL_MODE_CONST_VOLTAGE:
                Serial.println("[MAIN DEBUG] (ON) Calling updateConstantVoltageControl()...");
                updateConstantVoltageControl(g_systemState.systemOn, desiredVoltage);
                Serial.println("[MAIN DEBUG] Returned from updateConstantVoltageControl()");
                break;
        }
    } else {
        // If system is OFF, no controller updates
        stopPump();
        desiredVoltage = 0.0f;
        pidFraction = 0.0f;
        pTerm = 0.0f;
        iTerm = 0.0f;
        dTerm = 0.0f;
    }

    // 6) Save final results in g_systemState
    g_systemState.desiredVoltage = desiredVoltage;
    g_systemState.pidOutput      = pidFraction;
    g_systemState.pTerm          = pTerm;
    g_systemState.iTerm          = iTerm;
    g_systemState.dTerm          = dTerm;

    // 7) Display the current status
    showStatus(
        g_systemState.flow,
        g_systemState.setpoint,
        g_systemState.errorPercent,
        g_systemState.desiredVoltage,
        g_systemState.systemOn,
        g_systemState.temperature,
        g_systemState.bubbleDetected
    );

    // 8) JSON reporting
    g_systemState.currentTimeMs = millis();
    reportAllStateJSON(g_systemState);

    // 9) Auto-stop if run duration exceeded
    unsigned long elapsed = (g_systemState.currentTimeMs - startTime) / 1000UL;
    if (elapsed > SLF_RUN_DURATION) {
        stopFlowMeasurement();
        stopPump();
        Serial.println("[MAIN DEBUG] Timer expired. Flow + pump stopped.");
        while (true) {
            delay(100);
        }
    }

    // 10) Delay loop
    delay(MAIN_LOOP_DELAY_MS);

    // 11) Optional timing info
    if (timeReportingEnabled) {
        Serial.println("[MAIN DEBUG] Loop iteration complete.");
    }

    // 12) Loop frequency measurement
    static unsigned long loopCount       = 0;
    static unsigned long lastFreqCheckMs = 0;
    loopCount++;
    unsigned long nowMs = millis();
    if (nowMs - lastFreqCheckMs >= 2000UL) {
        float loopsPerSecond =
            1000.0f * (static_cast<float>(loopCount) / (nowMs - lastFreqCheckMs));

        Serial.print("[MAIN DEBUG] ~");
        Serial.print(loopsPerSecond, 2);
        Serial.println(" Hz loop frequency.");

        loopCount = 0;
        lastFreqCheckMs = nowMs;
    }
}
