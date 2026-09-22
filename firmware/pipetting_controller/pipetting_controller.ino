/*
 * Automated Micropipetting System - Gantry & UI Controller
 * Target: Elegoo Mega 2560 (ATmega2560)
 *
 * Drives a modified Creality Ender-3 gantry (3x A4988 stepper drivers),
 * homes against mechanical end-stops, and executes pipetting runs
 * received as packets from a Nextion NX4827T043 touchscreen on Serial1.
 *
 * Transcribed from Appendix G of the Group F final report (June 2025).
 * Logic is unchanged from the version demonstrated; see firmware/README.md
 * for the packet protocol and known limitations.
 */

#include <Arduino.h>

// --- Pin Definitions ---
constexpr uint8_t ENDSTOP_PIN_X = 5;
constexpr uint8_t DIR_PIN_X     = 7;
constexpr uint8_t STEP_PIN_X    = 6;

constexpr uint8_t ENDSTOP_PIN_Y = 8;
constexpr uint8_t DIR_PIN_Y     = 10;
constexpr uint8_t STEP_PIN_Y    = 9;

constexpr uint8_t ENDSTOP_PIN_Z = 11;
constexpr uint8_t DIR_PIN_Z     = 13;
constexpr uint8_t STEP_PIN_Z    = 12;

constexpr uint8_t BUZZER_PIN = 2;

// --- Motion configuration (units: steps) ---
constexpr int LIMIT_PRESSED = HIGH;
const long MAX_BACKWARD_XY = 1100;
const long MAX_BACKWARD_Z  = 1700;
const long MAX_HOMING_STEPS_Z = MAX_BACKWARD_Z + 100;
const long Z_SAFE_HEIGHT = 1700;   // travel height between positions
const long Z_WORK_HEIGHT = 300;    // tip-in-liquid height
unsigned long stepDelayXY = 1500;  // us, half-period of XY step pulse
unsigned long stepDelayZ  = 1200;  // us, half-period of Z step pulse

long stepPositionX = 0;
long stepPositionY = 0;
long stepPositionZ = 0;

constexpr uint8_t DIR_TOWARD_Z = HIGH;
constexpr uint8_t DIR_AWAY_Z   = LOW;

// --- Labware map (step coordinates relative to home) ---
struct Coord { long x; long y; };

// 5 x 8 tube rack, row-major (index 0..39), 50-step pitch (~10 mm)
Coord wells[] = {
  { 890, 500 }, { 940, 500 }, { 990, 500 }, { 1040, 500 }, { 1090, 500 },
  { 890, 550 }, { 940, 550 }, { 990, 550 }, { 1040, 550 }, { 1090, 550 },
  { 890, 600 }, { 940, 600 }, { 990, 600 }, { 1040, 600 }, { 1090, 600 },
  { 890, 650 }, { 940, 650 }, { 990, 650 }, { 1040, 650 }, { 1090, 650 },
  { 890, 700 }, { 940, 700 }, { 990, 700 }, { 1040, 700 }, { 1090, 700 },
  { 890, 750 }, { 940, 750 }, { 990, 750 }, { 1040, 750 }, { 1090, 750 },
  { 890, 800 }, { 940, 800 }, { 990, 800 }, { 1040, 800 }, { 1090, 800 },
  { 890, 850 }, { 940, 850 }, { 990, 850 }, { 1040, 850 }, { 1090, 850 }
};

// Source beakers: 1 = left, 2 = right
Coord beakers[] = {
  { 400, 700 },
  { 670, 700 }
};

// --- Nextion serial link ---
#define nextion Serial1
const size_t BUF_SIZE = 128;
uint8_t buf[BUF_SIZE];
size_t idx = 0;

// --- Low-level stepping ---
void pulseStepX() {
  digitalWrite(STEP_PIN_X, HIGH); delayMicroseconds(stepDelayXY);
  digitalWrite(STEP_PIN_X, LOW);  delayMicroseconds(stepDelayXY);
}
void pulseStepY() {
  digitalWrite(STEP_PIN_Y, HIGH); delayMicroseconds(stepDelayXY);
  digitalWrite(STEP_PIN_Y, LOW);  delayMicroseconds(stepDelayXY);
}
void pulseStepZ() {
  digitalWrite(STEP_PIN_Z, HIGH); delayMicroseconds(stepDelayZ);
  digitalWrite(STEP_PIN_Z, LOW);  delayMicroseconds(stepDelayZ);
}

// --- Coordinated XY move (Bresenham-style interpolation) ---
void moveToXY(long targetX, long targetY) {
  moveToZ(Z_SAFE_HEIGHT);

  long dx = targetX - stepPositionX;
  long dy = targetY - stepPositionY;

  int dirX = dx >= 0 ? 1 : -1;
  int dirY = dy >= 0 ? 1 : -1;

  digitalWrite(DIR_PIN_X, dirX > 0 ? HIGH : LOW);
  digitalWrite(DIR_PIN_Y, dirY > 0 ? HIGH : LOW);

  dx = abs(dx);
  dy = abs(dy);

  long steps = max(dx, dy);
  long errorX = 0, errorY = 0;

  for (long i = 0; i < steps; ++i) {
    errorX += dx;
    errorY += dy;

    if (errorX >= steps) {
      pulseStepX();
      stepPositionX += dirX;
      errorX -= steps;
    }

    if (errorY >= steps) {
      pulseStepY();
      stepPositionY += dirY;
      errorY -= steps;
    }

    delayMicroseconds(stepDelayXY * 2);
  }
}

// --- Z move with end-stop guard ---
void moveToZ(long targetZ) {
  if (targetZ == stepPositionZ && digitalRead(ENDSTOP_PIN_Z) != LIMIT_PRESSED) return;
  digitalWrite(DIR_PIN_Z, targetZ < stepPositionZ ? DIR_TOWARD_Z : DIR_AWAY_Z);
  long steps = abs(targetZ - stepPositionZ);
  for (long i = 0; i < steps; ++i) {
    if (digitalRead(ENDSTOP_PIN_Z) == LIMIT_PRESSED && targetZ < stepPositionZ) {
      stepPositionZ = 0;
      return;
    }
    pulseStepZ();
    stepPositionZ += targetZ < stepPositionZ ? -1 : 1;
  }
}

// Dip to working height, dwell, retract
void holdZatWorkHeight() {
  moveToZ(Z_WORK_HEIGHT);
  delay(3000);
  moveToZ(Z_SAFE_HEIGHT);
}

// --- Homing ---
void homeAxisX() {
  digitalWrite(DIR_PIN_X, LOW);
  while (digitalRead(ENDSTOP_PIN_X) != LIMIT_PRESSED) pulseStepX();
  stepPositionX = 0;
}
void homeAxisY() {
  digitalWrite(DIR_PIN_Y, LOW);
  while (digitalRead(ENDSTOP_PIN_Y) != LIMIT_PRESSED) pulseStepY();
  stepPositionY = 0;
}
void homeAxisZ() {
  digitalWrite(DIR_PIN_Z, DIR_TOWARD_Z);
  for (int i = 0; i < MAX_HOMING_STEPS_Z && digitalRead(ENDSTOP_PIN_Z) != LIMIT_PRESSED; ++i) pulseStepZ();
  stepPositionZ = 0;
  moveToZ(Z_SAFE_HEIGHT);
}

// --- Audio feedback ---
// Confirmation beep (2 quick notes) when a job is received
void playConfirmationBeep() {
  tone(BUZZER_PIN, 1000, 100);
  delay(150);
  tone(BUZZER_PIN, 1500, 100);
  delay(150);
  noTone(BUZZER_PIN);
}

// Melody when a job completes and the head returns home
void playEndMelody() {
  tone(BUZZER_PIN, 988, 150);  delay(200);  // B5
  tone(BUZZER_PIN, 1319, 150); delay(200);  // E6
  tone(BUZZER_PIN, 1047, 200); delay(250);  // C6
  noTone(BUZZER_PIN);
}

// --- Labware moves ---
void moveToWell(uint8_t n) {
  if (n >= sizeof(wells)/sizeof(wells[0])) return;
  moveToXY(wells[n].x, wells[n].y);
  holdZatWorkHeight();
}
void moveToBeaker(uint8_t n) {
  if (n < 1 || n > 2) return;
  moveToXY(beakers[n-1].x, beakers[n-1].y);
  holdZatWorkHeight();
}

// --- Nextion packet parser & job executor ---
// Packet fields (terminated by '#'):
//   I=<ascii digits>          input well index
//   O=<d>,<d>,...;            output well indices
//   V=<4 bytes LE>            volume (uL)
//   B=<4 bytes LE>            beaker side (1 = left, 2 = right)
//   T=<4 bytes LE>            source type (1 = beaker, 2 = tubes)
void parsePacket(const uint8_t *data, size_t len) {
  int inputWell = 0;
  bool hasInputWell = false;
  int outputWells[40];
  int outCount = 0;
  int volume = 0, beakerSide = 0, sourceType = 0;

  memset(outputWells, 0, sizeof(outputWells));

  playConfirmationBeep();

  for (size_t i = 0; i + 1 < len;) {
    if (data[i] == 'I' && data[i+1] == '=') {
      i += 2;
      inputWell = 0;
      hasInputWell = false;
      while (i < len && isdigit(data[i])) {
        inputWell = inputWell * 10 + (data[i++] - '0');
        hasInputWell = true;
      }
    } else if (data[i] == 'O' && data[i+1] == '=') {
      i += 2;
      while (i < len && data[i] != ';') {
        if (isdigit(data[i])) {
          int v = 0;
          while (i < len && isdigit(data[i])) v = v * 10 + (data[i++] - '0');
          if (outCount < 40) outputWells[outCount++] = v;
        } else i++;
      }
    } else if (data[i] == 'V' && data[i+1] == '=') {
      if (i+6 <= len) volume = data[i+2] | (data[i+3]<<8) | (data[i+4]<<16) | (data[i+5]<<24);
      i += 6;
    } else if (data[i] == 'B' && data[i+1] == '=') {
      if (i+6 <= len) beakerSide = data[i+2] | (data[i+3]<<8) | (data[i+4]<<16) | (data[i+5]<<24);
      i += 6;
    } else if (data[i] == 'T' && data[i+1] == '=') {
      if (i+6 <= len) sourceType = data[i+2] | (data[i+3]<<8) | (data[i+4]<<16) | (data[i+5]<<24);
      i += 6;
    } else i++;
  }

  Serial.print("Input Well: "); Serial.println(inputWell);
  Serial.print("Output Wells: "); for (int j = 0; j < outCount; ++j) { Serial.print(outputWells[j]); Serial.print(","); } Serial.println();
  Serial.print("Volume: "); Serial.println(volume);
  Serial.print("Beaker Side: "); Serial.println(beakerSide);
  Serial.print("Source Type: "); Serial.println(sourceType);

  if (sourceType == 1 && beakerSide >= 1 && beakerSide <= 2) {
    moveToBeaker(beakerSide);
    for (int i = 0; i < outCount; ++i) moveToWell(outputWells[i]);
  } else if (sourceType == 2 && hasInputWell) {
    moveToWell(inputWell);
    for (int i = 0; i < outCount; ++i) moveToWell(outputWells[i]);
  }

  moveToZ(Z_SAFE_HEIGHT);
  moveToXY(0, 0);

  stepPositionX = 0;
  stepPositionY = 0;

  playEndMelody();

  memset(buf, 0, sizeof(buf));
  idx = 0;
}

void setup() {
  Serial.begin(9600);
  nextion.begin(9600);
  delay(300);
  while (nextion.available()) nextion.read();

  pinMode(BUZZER_PIN, OUTPUT);

  pinMode(ENDSTOP_PIN_X, INPUT_PULLUP); pinMode(DIR_PIN_X, OUTPUT); pinMode(STEP_PIN_X, OUTPUT);
  pinMode(ENDSTOP_PIN_Y, INPUT_PULLUP); pinMode(DIR_PIN_Y, OUTPUT); pinMode(STEP_PIN_Y, OUTPUT);
  pinMode(ENDSTOP_PIN_Z, INPUT_PULLUP); pinMode(DIR_PIN_Z, OUTPUT); pinMode(STEP_PIN_Z, OUTPUT);

  homeAxisX(); homeAxisY(); homeAxisZ();
  Serial.println("Ready to receive Nextion packets...");
}

void loop() {
  while (nextion.available()) {
    uint8_t b = nextion.read();
    if (b == '#') {
      if (idx > 0) {
        parsePacket(buf, idx);
      }
    } else if (idx < BUF_SIZE) {
      buf[idx++] = b;
    }
  }

  // Debug: manual re-homing over USB serial
  if (Serial.available()) {
    String in = Serial.readStringUntil('\n');
    in.trim();
    if (in.equalsIgnoreCase("X0")) homeAxisX();
    else if (in.equalsIgnoreCase("Y0")) homeAxisY();
    else if (in.equalsIgnoreCase("Z0")) homeAxisZ();
  }
}
