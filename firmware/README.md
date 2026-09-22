# Firmware

`pipetting_controller/pipetting_controller.ino` is a single Arduino sketch for the Elegoo Mega 2560. It homes the gantry, receives jobs from the Nextion display on `Serial1`, and moves the pipette head between labware positions.

---

## Build

- **Arduino IDE:** open the sketch folder, select board **Arduino Mega or Mega 2560**, and upload. No external libraries are needed.
- **arduino-cli:**
  ```bash
  arduino-cli compile --fqbn arduino:avr:mega firmware/pipetting_controller
  arduino-cli upload  --fqbn arduino:avr:mega -p <PORT> firmware/pipetting_controller
  ```

---

## Pinout

| Signal | Mega pin | | Signal | Mega pin |
|---|---|---|---|---|
| X end-stop | D5 | | Z end-stop | D11 |
| X STEP / DIR | D6 / D7 | | Z STEP / DIR | D12 / D13 |
| Y end-stop | D8 | | Buzzer | D2 |
| Y STEP / DIR | D9 / D10 | | Nextion RX / TX | TX1 / RX1 (Serial1) |
| Keypad rows/cols | D22–D34 (per schematic) | | USB debug | Serial @ 9600 |

The end-stops use `INPUT_PULLUP`, and a limit reads as triggered when it is `HIGH`.

---

## Configuration

All positions are in **steps from home**, not mm (≈0.2 mm/step in X and Y, 0.04 mm/step in Z; see [calibration](../docs/calibration.md)).

| Constant | Value | Meaning |
|---|---|---|
| `Z_SAFE_HEIGHT` | 1700 | Travel height for all XY moves |
| `Z_WORK_HEIGHT` | 300 | Tip-in-liquid height |
| `MAX_HOMING_STEPS_Z` | 1800 | Z homing timeout |
| `stepDelayXY` / `stepDelayZ` | 1500 / 1200 µs | Step half-periods; sets speed |
| `wells[40]` | 5 × 8 grid, 50-step pitch | Tube rack origin at (890, 500) |
| `beakers[2]` | (400, 700), (670, 700) | Left / right source beaker |

If you change the base attachment, re-measure the `wells[]` and `beakers[]` coordinates.

---

## Motion

- **Homing:** runs X → Y → Z at boot. Z then retracts to safe height.
- **XY moves:** interpolated with an integer Bresenham-style error accumulator, so both axes arrive together. Z always rises to safe height before any XY move.
- **Z moves:** check the Z end-stop on the way down and re-zero if it trips early.
- **Pipetting step:** at each labware position, `holdZatWorkHeight()` lowers the head, dwells for 3 s, then retracts.
- **Debug commands:** sending `X0`, `Y0` or `Z0` over USB serial re-homes that axis.

---

## Nextion → Mega protocol

A job is one packet terminated by `#`. The fields can appear in any order.

| Field | Encoding | Meaning |
|---|---|---|
| `I=<digits>` | ASCII | Input (source) well index, 0–39 |
| `O=<d>,<d>,…;` | ASCII, `;`-terminated | Output well indices (≤ 40) |
| `V=` + 4 bytes | uint32 little-endian (Nextion `prints va,4`) | Volume, µL |
| `B=` + 4 bytes | uint32 LE | Beaker side: 1 = left, 2 = right |
| `T=` + 4 bytes | uint32 LE | Source type: 1 = beaker, 2 = tubes |

The job then runs in this order: confirmation beep → source → each output well in turn → return to (0, 0) → end melody.

---

## Known issues

These are in the sketch as submitted and are left unfixed so the code matches the report.

1. **The volume is parsed but not used.** `V=` is decoded and logged, but this sketch never generates the actuator PWM. Plunger actuation and the volume-to-position mapping via the LAC board sit outside this file. If that code exists in another revision, it belongs here.
2. **16-bit `int` overflow on AVR.** `data[i+4]<<16` and `data[i+5]<<24` shift a promoted 16-bit `int`, which is undefined behaviour. It works in practice only because the upper bytes are zero for small values. Fix it by declaring `volume` etc. as `int32_t`/`long` and casting each byte to `uint32_t` before shifting.
3. **XY homing is unbounded.** `homeAxisX/Y` loop until the switch trips. `MAX_BACKWARD_XY` is declared but never used, so a failed end-stop drives the axis indefinitely. Only Z has a homing timeout.
4. **Position drift.** After each job, the X and Y positions are reset to 0 without re-homing, so any lost steps accumulate across jobs.
5. **Everything blocks.** There is no way to cancel or emergency-stop mid-job, and the UART buffer is not serviced while motors run.
6. **The keypad is not implemented here.** It is wired to D22–D34 per the schematic, but this sketch never reads it.
