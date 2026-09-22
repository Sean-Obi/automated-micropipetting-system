# Testing & evaluation

---

## Volumetric accuracy

1. Set a target volume.
2. Dispense it and weigh the output on a balance.
3. Compare the result against a manual micropipette.
4. Recalibrate the pipette to minimise the error.

**Result:** The pipette alone met ±1% after its graduations were recalibrated. The actuator adds extra uncertainty at system level. Accuracy and precision drop as the volume decreases.

---

## Cross-contamination

1. Run dyed liquid through the system.
2. Replace the tip.
3. Dispense clear liquid.

**Result:** There was no visible carryover. This check was qualitative only. A spectrophotometer absorbance check would be the quantitative follow-up.

---

## Gantry

The gantry was tested for:

- positional error against target on each axis,
- repeatability, by returning to the same point over repeated cycles, and
- speed, timed with `micros()`.

All tests were run at room temperature and pressure. See [calibration](calibration.md).

---

## Display

The display was checked for:

- the correct default screen on boot,
- the GUI loading from microSD,
- the response of every touch element,
- uniform pixel brightness, and
- stability over several hours of running.

---

## User testing

There were 20 participants. Seven reported conditions that limit their mobility. The rest wore finger resistance bands to simulate reduced dexterity, and the team's disability consultant endorsed this as a reasonable proxy.

| Question | Result |
|---|---|
| Fits into a lab (aesthetics) | 90% rated 4–5 |
| UI clarity | 55% "minimal instructions", 20% "no instructions", 25% "somewhat easy" |
| Ease of dispensing | 65% rated 4–5, 35% rated 3 |
| Would use regularly | 70% rated 4–5 |
| Portability | 45% rated 3 ("easy in less intense periods"), 45% rated 4–5, 10% rated 2 |
| Aspirate vs. dispense difficulty | 100% saw no difference |

Participants' free-text comments asked for a bigger screen, bigger touch icons, tactile buttons, and higher speed or throughput.

---

## Evaluation against the product specification

| Requirement | Outcome |
|---|---|
| 100 µL–1 mL within ±1% | Partial: the pipette passes, the actuator adds error |
| Chemical compatibility | Partial: PLA is moderately resistant, but long-term exposure was not tested |
| Splash-free dispensing | Pass |
| Contamination-free | Partial: visual check only |
| Simple operation | Pass |
| Bluetooth control | Dropped in favour of touchscreen and keypad after user feedback |
| Fits on a lab bench | Pass (44 × 44 × 46.5 cm) |
| < 10 kg | Pass |
| Visual/audio feedback | Pass |
| Reduces physical strain | Pass |
| Mains-compatible power | Pass (24 W) |
| Maintainable | Pass |
| < £600 | Pass (£483.53) |
| Broad accessibility | Partial |
