// TorQ drive controller
// Board: Arduino Uno R3 + Arduino Motor Shield Rev3 (L298P)
//
// Serial protocol: 115200 baud, one ASCII command per line ('\n' terminated).
//
//   D <left> <right>   Drive. Each value -255..255, scaled by the speed limit.
//                      Must be resent at least every WATCHDOG_MS or motors stop.
//                      Silent on success.
//   S                  Stop (brake) now.                     -> OK STOP
//   E                  E-stop: brake and latch until R.      -> ESTOP
//   R                  Clear E-stop / fault latch.           -> OK RESET
//   L <0..255>         Set speed limit (default 160).        -> OK L <n>
//   P                  Ping.                                 -> PONG
//   ?                  Status.                               -> STATUS <left> <right> <limit> <estop> <mA_left> <mA_right>
//
// Unsolicited messages:
//   READY torq-drive <version>   after boot (opening the port resets the Uno)
//   WDT                          drive commands stopped arriving, motors stopped
//   FAULT OVERCURRENT <L|R>      a channel stayed over the current limit; latched until R
//   ERR <reason>                 bad command

#include <avr/wdt.h>
#include <stdlib.h>
#include <string.h>

const char *FIRMWARE_VERSION = "1";

// Motor Shield Rev3 fixed pins.
const uint8_t DIR_A = 12, PWM_A = 3, BRAKE_A = 9, SENSE_A = A0;
const uint8_t DIR_B = 13, PWM_B = 11, BRAKE_B = 8, SENSE_B = A1;

// Track mapping. Flip these if the robot drives or turns the wrong way.
const bool LEFT_IS_CHANNEL_A = true;
const bool INVERT_LEFT = false;
const bool INVERT_RIGHT = true;  // right motor is mounted mirrored (verified 2026-11-01)

const unsigned long WATCHDOG_MS = 300;
const int DEFAULT_SPEED_LIMIT = 160;  // out of 255
const int RAMP_STEP = 10;             // PWM change per ramp tick
const unsigned long RAMP_INTERVAL_MS = 5;
const long OVERCURRENT_MA = 1900;     // L298P is rated 2 A per channel
const unsigned long OVERCURRENT_MS = 300;

struct Motor {
  uint8_t dirPin, pwmPin, brakePin, sensePin;
  bool invert;
  int target;   // -255..255 after speed limit
  int current;  // ramped value actually applied
  unsigned long overSince;
};

Motor leftMotor, rightMotor;
int speedLimit = DEFAULT_SPEED_LIMIT;
bool latched = false;  // E-stop or fault
unsigned long lastDriveMs = 0;
unsigned long lastRampMs = 0;
bool watchdogTripped = true;  // start stopped; no WDT message until first drive

char lineBuf[32];
uint8_t lineLen = 0;
bool lineOverflow = false;

void setupMotor(Motor &m, bool isA, bool invert) {
  m.dirPin = isA ? DIR_A : DIR_B;
  m.pwmPin = isA ? PWM_A : PWM_B;
  m.brakePin = isA ? BRAKE_A : BRAKE_B;
  m.sensePin = isA ? SENSE_A : SENSE_B;
  m.invert = invert;
  m.target = 0;
  m.current = 0;
  m.overSince = 0;
  pinMode(m.dirPin, OUTPUT);
  pinMode(m.pwmPin, OUTPUT);
  pinMode(m.brakePin, OUTPUT);
  analogWrite(m.pwmPin, 0);
  digitalWrite(m.brakePin, HIGH);
}

void applyMotor(Motor &m) {
  if (m.current == 0) {
    analogWrite(m.pwmPin, 0);
    digitalWrite(m.brakePin, HIGH);
    return;
  }
  bool forward = (m.current > 0) != m.invert;
  digitalWrite(m.brakePin, LOW);
  digitalWrite(m.dirPin, forward ? HIGH : LOW);
  analogWrite(m.pwmPin, abs(m.current));
}

void stopNow() {
  leftMotor.target = leftMotor.current = 0;
  rightMotor.target = rightMotor.current = 0;
  applyMotor(leftMotor);
  applyMotor(rightMotor);
}

// Move current toward target. Speeding up and reversing are ramped;
// slowing toward zero is immediate so stops are never delayed.
void rampMotor(Motor &m) {
  if (m.current == m.target) return;
  bool sameSign = (m.current >= 0) == (m.target >= 0);
  if (sameSign && abs(m.target) < abs(m.current)) {
    m.current = m.target;
  } else if (m.target > m.current) {
    m.current = min(m.current + RAMP_STEP, m.target);
  } else {
    m.current = max(m.current - RAMP_STEP, m.target);
  }
  applyMotor(m);
}

long readMilliamps(const Motor &m) {
  // Shield current sense: 3.3 V at 2 A full scale -> 1.65 V per amp.
  long raw = analogRead(m.sensePin);
  return raw * 5000L * 100L / 1023L / 165L;
}

void checkOvercurrent(Motor &m, char label, unsigned long now) {
  if (m.current == 0) {
    m.overSince = 0;
    return;
  }
  if (readMilliamps(m) < OVERCURRENT_MA) {
    m.overSince = 0;
    return;
  }
  if (m.overSince == 0) {
    m.overSince = now;
  } else if (now - m.overSince >= OVERCURRENT_MS) {
    stopNow();
    latched = true;
    m.overSince = 0;
    Serial.print(F("FAULT OVERCURRENT "));
    Serial.println(label);
  }
}

int clampSpeed(long value) {
  if (value > 255) value = 255;
  if (value < -255) value = -255;
  return (int)(value * speedLimit / 255);
}

// Parse a signed integer token; returns false if missing or not a number.
bool parseInt(char *&cursor, long &out) {
  while (*cursor == ' ') cursor++;
  if (*cursor == '\0') return false;
  char *end;
  out = strtol(cursor, &end, 10);
  if (end == cursor || (*end != ' ' && *end != '\0')) return false;
  cursor = end;
  return true;
}

void handleLine(char *line) {
  char cmd = line[0];
  char *args = line + 1;

  switch (cmd) {
    case 'D': {
      long l, r;
      if (!parseInt(args, l) || !parseInt(args, r)) {
        Serial.println(F("ERR usage: D <left> <right>"));
        return;
      }
      if (latched) {
        Serial.println(F("ERR latched, send R"));
        return;
      }
      leftMotor.target = clampSpeed(l);
      rightMotor.target = clampSpeed(r);
      lastDriveMs = millis();
      watchdogTripped = false;
      return;
    }
    case 'S':
      stopNow();
      watchdogTripped = true;
      Serial.println(F("OK STOP"));
      return;
    case 'E':
      stopNow();
      latched = true;
      watchdogTripped = true;
      Serial.println(F("ESTOP"));
      return;
    case 'R':
      stopNow();
      latched = false;
      Serial.println(F("OK RESET"));
      return;
    case 'L': {
      long n;
      if (!parseInt(args, n) || n < 0 || n > 255) {
        Serial.println(F("ERR usage: L <0..255>"));
        return;
      }
      speedLimit = (int)n;
      Serial.print(F("OK L "));
      Serial.println(speedLimit);
      return;
    }
    case 'P':
      Serial.println(F("PONG"));
      return;
    case '?':
      Serial.print(F("STATUS "));
      Serial.print(leftMotor.current);
      Serial.print(' ');
      Serial.print(rightMotor.current);
      Serial.print(' ');
      Serial.print(speedLimit);
      Serial.print(' ');
      Serial.print(latched ? 1 : 0);
      Serial.print(' ');
      Serial.print(readMilliamps(leftMotor));
      Serial.print(' ');
      Serial.println(readMilliamps(rightMotor));
      return;
    default:
      Serial.print(F("ERR unknown command: "));
      Serial.println(line);
  }
}

void readSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (lineOverflow) {
        Serial.println(F("ERR line too long"));
      } else if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        handleLine(lineBuf);
      }
      lineLen = 0;
      lineOverflow = false;
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    } else {
      lineOverflow = true;
    }
  }
}

void setup() {
  // Brake both channels before anything else so motors can't twitch on boot.
  setupMotor(leftMotor, LEFT_IS_CHANNEL_A, INVERT_LEFT);
  setupMotor(rightMotor, !LEFT_IS_CHANNEL_A, INVERT_RIGHT);

  // Hardware watchdog: if this loop ever hangs, the Uno resets and the
  // motor pins fall back to stopped.
  wdt_enable(WDTO_250MS);

  Serial.begin(115200);
  Serial.print(F("READY torq-drive "));
  Serial.println(FIRMWARE_VERSION);
}

void loop() {
  wdt_reset();

  readSerial();

  // Read the clock after handling commands: a D command stamps lastDriveMs
  // with millis(), and a 'now' taken earlier would make now - lastDriveMs
  // underflow and trip the watchdog falsely.
  unsigned long now = millis();

  if (!watchdogTripped && now - lastDriveMs > WATCHDOG_MS) {
    stopNow();
    watchdogTripped = true;
    Serial.println(F("WDT"));
  }

  if (now - lastRampMs >= RAMP_INTERVAL_MS) {
    lastRampMs = now;
    rampMotor(leftMotor);
    rampMotor(rightMotor);
  }

  checkOvercurrent(leftMotor, 'L', now);
  checkOvercurrent(rightMotor, 'R', now);
}
