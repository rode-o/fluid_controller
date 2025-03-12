#include "report.h"
#include "system_state.h"
#include <Arduino.h>

void reportAllStateJSON(const SystemState &s)
{
  Serial.print("{\"timeMs\":");
  Serial.print(s.currentTimeMs);

  Serial.print(",\"flow\":");
  Serial.print(s.flow, 3);

  Serial.print(",\"setpt\":");
  Serial.print(s.setpoint, 3);

  Serial.print(",\"errorPct\":");
  Serial.print(s.errorPercent, 3);

  Serial.print(",\"pidOut\":");
  Serial.print(s.pidOutput, 3);

  Serial.print(",\"volt\":");
  Serial.print(s.desiredVoltage, 2);

  Serial.print(",\"temp\":");
  Serial.print(s.temperature, 2);

  Serial.print(",\"bubble\":");
  Serial.print(s.bubbleDetected ? "true" : "false");

  Serial.print(",\"on\":");
  Serial.print(s.systemOn ? "true" : "false");

  // Indicate which mode we're in (optional)
  Serial.print(",\"mode\":");
  Serial.print(s.controlMode == CONTROL_MODE_SIGMOIDAL ? "\"SIG\"" : "\"CONST\"");

  Serial.print(",\"P\":");
  Serial.print(s.pTerm, 3);

  Serial.print(",\"I\":");
  Serial.print(s.iTerm, 3);

  Serial.print(",\"D\":");
  Serial.print(s.dTerm, 3);

  Serial.print(",\"pGain\":");
  Serial.print(s.pGain, 3);

  Serial.print(",\"iGain\":");
  Serial.print(s.iGain, 3);

  Serial.print(",\"dGain\":");
  Serial.print(s.dGain, 3);

  Serial.print(",\"filteredErr\":");
  Serial.print(s.filteredError, 3);

  Serial.print(",\"currentAlpha\":");
  Serial.print(s.currentAlpha, 3);

  Serial.println("}");
}
