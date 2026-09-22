"""Generate a KiCad 7-format schematic for the Automated Micropipetting System.
Connectivity is expressed with short wire stubs + net labels on every pin."""
import uuid

G = 2.54
PROJECT = "pcb_design"
LIB = "apms"
ROOT = str(uuid.uuid5(uuid.NAMESPACE_DNS, "apms-root"))
_c = 0
def U():
    global _c; _c += 1
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"apms-{_c}"))

def f(x): return f"{x:.2f}".rstrip("0").rstrip(".") if x != 0 else "0"
FONT = "(effects (font (size 1.27 1.27)))"

# ---------- symbol definitions ----------
# pins: list of (number, name, side, type) ; side in L R T B
SYMBOLS = {}
def rect_symbol(name, pins, ref_prefix, desc, min_w=10.16, min_h=10.16, show_names=True):
    sides = {s: [p for p in pins if p[2] == s] for s in "LRTB"}
    n_lr = max(len(sides["L"]), len(sides["R"]), 1)
    n_tb = max(len(sides["T"]), len(sides["B"]), 1)
    w = max(min_w, (n_tb + 1) * 2 * G); w = round(w / (2 * G) + 0.4999) * 2 * G
    h = max(min_h, (n_lr + 1) * G); h = round(h / (2 * G) + 0.4999) * 2 * G
    pl = []  # (num,name,type,x,y,ang,side)
    for s, lst in sides.items():
        for i, (num, nm, _, typ) in enumerate(lst):
            if s in "LR":
                y = h / 2 - G * (i + 1)
                x = -w / 2 - G if s == "L" else w / 2 + G
                ang = 0 if s == "L" else 180
            else:
                x = -w / 2 + 2 * G * (i + 1)
                y = h / 2 + G if s == "T" else -h / 2 - G
                ang = 270 if s == "T" else 90
            pl.append((num, nm, typ, x, y, ang, s))
    SYMBOLS[name] = dict(w=w, h=h, pins=pl, ref=ref_prefix, desc=desc, show_names=show_names)

def P(num, name, side, typ="passive"): return (str(num), name, side, typ)

rect_symbol("Elegoo_Mega_2560",
    [P(n, f"D{n}", "T") for n in range(13, 1, -1)]
    + [P(18,"TX1","T"),P(19,"RX1","T"),P(20,"SDA","T"),P(21,"SCL","T")]
    + [P(n, f"D{n}", "R") for n in (22,24,26,28,30,32,34)]
    + [P("5V","+5V","B","power_in"),P("GND1","GND","B","power_in"),P("GND2","GND","B","power_in"),
       P("VIN","VIN","B","power_in")],
    "A", "Elegoo Mega 2560 R3 (ATmega2560)", min_w=60.96, min_h=30.48)

rect_symbol("A4988_Module",
    [P(8,"DIR","T"),P(7,"STEP","T"),P(6,"~{SLP}","T"),P(5,"~{RST}","T"),P(4,"MS3","T"),
     P(3,"MS2","T"),P(2,"MS1","T"),P(1,"~{EN}","T"),
     P(9,"GND","B","power_in"),P(10,"VDD","B","power_in"),P(11,"1B","B"),P(12,"1A","B"),
     P(13,"2A","B"),P(14,"2B","B"),P(15,"GND","B","power_in"),P(16,"VMOT","B","power_in")],
    "U", "Pololu-style A4988 stepper driver carrier", min_h=15.24)

rect_symbol("Stepper_Bipolar",
    [P(1,"A1","T"),P(2,"A2","T"),P(3,"B1","T"),P(4,"B2","T")],
    "M", "NEMA17 bipolar stepper (Ender-3)", min_w=30.48)

rect_symbol("LM2596_Module",
    [P(1,"IN+","L","power_in"),P(2,"IN-","L","power_in"),P(3,"OUT+","R","power_out"),P(4,"OUT-","R","power_out")],
    "PS", "LM2596 adjustable buck converter module", min_w=25.4)

rect_symbol("DC_Supply",
    [P(1,"+","R","power_out"),P(2,"-","R","power_out")],
    "J", "External DC power input", min_w=20.32)

rect_symbol("Actuonix_LAC",
    [P(1,"+","R","power_in"),P(2,"-","R","power_in"),P(3,"VC","R","input")],
    "A", "Actuonix Linear Actuator Control board (actuator not shown)", min_w=25.4)

rect_symbol("Limit_Switch",
    [P(1,"SIG","R"),P(2,"GND","R")],
    "SW", "Mechanical end-stop (Ender-3)", min_w=25.4)

rect_symbol("Resistor",
    [P(1,"~","T"),P(2,"~","B")],
    "R", "Resistor", min_w=5.08, min_h=7.62, show_names=False)

rect_symbol("Nextion_NX4827T043",
    [P(1,"GND","B","power_in"),P(2,"RX","B","input"),P(3,"TX","B","output"),P(4,"VCC","B","power_in")],
    "DS", "Nextion 4.3in HMI, UART 9600 baud", min_w=30.48, min_h=15.24)

rect_symbol("I2C_LCD",
    [P(1,"SDA","B"),P(2,"SCL","B"),P(3,"GND","B","power_in"),P(4,"VCC","B","power_in")],
    "DS", "I2C character LCD (legacy, not fitted)", min_w=30.48, min_h=15.24)

rect_symbol("Keypad_4x3",
    [P(i, str(i), "L") for i in range(1, 8)],
    "SW", "4x3 membrane keypad", min_w=20.32, min_h=20.32)

rect_symbol("Buzzer",
    [P(1,"+","L"),P(2,"-","L")],
    "BZ", "Piezo buzzer", min_w=20.32)

# power symbols
def power_symbol(name, down):
    SYMBOLS[name] = dict(power=True, down=down)
power_symbol("+5V", False)
power_symbol("GND", True)

def lib_symbol_text(name):
    s = SYMBOLS[name]
    if s.get("power"):
        down = s["down"]
        ref_y = -3.81 if down else 3.81
        val_y = -3.81 if down else 3.81
        if down:
            gfx = "(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))"
        else:
            gfx = "(polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))(polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))"
        return f'''(symbol "power:{name}" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
  (property "Reference" "#PWR" (at 0 {f(-6.35 if down else -3.81)} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" "{name}" (at 0 {f(val_y)} 0) {FONT})
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "{name}_0_1" {gfx})
  (symbol "{name}_1_1" (pin power_in line (at 0 0 {90 if not down else 270}) (length 0) hide (name "{name}" {FONT}) (number "1" {FONT}))))'''
    w, h = s["w"], s["h"]
    pins = "\n    ".join(
        f'(pin {typ} line (at {f(x)} {f(y)} {ang}) (length {f(G)}) (name "{nm}" {FONT}) (number "{num}" {FONT}))'
        for num, nm, typ, x, y, ang, side in s["pins"])
    names = "" if s["show_names"] else " hide"
    return f'''(symbol "{LIB}:{name}" (pin_names (offset 1.016){names}) (in_bom yes) (on_board yes)
  (property "Reference" "{s['ref']}" (at {f(-w/2)} {f(h/2 + 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
  (property "Value" "{name}" (at {f(-w/2)} {f(-h/2 - 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left top)))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "ki_description" "{s['desc']}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "{name}_0_1" (rectangle (start {f(-w/2)} {f(h/2)}) (end {f(w/2)} {f(-h/2)}) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "{name}_1_1"
    {pins}))'''

# ---------- footprints (project library apms.pretty) ----------
FOOTPRINTS = {
    "Elegoo_Mega_2560": "apms:Mega2560_Interface_2x14_P2.54mm",
    "A4988_Module": "apms:Pololu_A4988_Carrier_Socket",
    "Stepper_Bipolar": "apms:PinHeader_1x04_P2.54mm",
    "LM2596_Module": "apms:LM2596_Module_Header_1x04",
    "DC_Supply": "apms:TerminalBlock_1x02_P5.08mm",
    "Actuonix_LAC": "apms:PinHeader_1x03_P2.54mm",
    "Limit_Switch": "apms:PinHeader_1x02_P2.54mm",
    "Resistor": "apms:R_Axial_DIN0207_L6.3mm_P10.16mm",
    "Nextion_NX4827T043": "apms:PinHeader_1x04_P2.54mm",
    "I2C_LCD": "apms:PinHeader_1x04_P2.54mm",
    "Keypad_4x3": "apms:PinHeader_1x07_P2.54mm",
    "Buzzer": "apms:Buzzer_12x9.5RM7.6",
}

# ---------- placement & netlist ----------
items = []
used_libs = set()
ref_counter = {}
pwr_n = [0]

def place(name, ref, value, x, y, nets, dnp=False, fields=None):
    """nets: dict pin_number -> net name. Unlisted pins get a no-connect."""
    s = SYMBOLS[name]; used_libs.add(name)
    w, h = s["w"], s["h"]
    if name == "Resistor":
        rx, ry, vx, vy, just = x + w/2 + 1.27, y - 1.27, x + w/2 + 1.27, y + 1.27, "left"
    else:
        rx, ry, vx, vy, just = x, y - 1.27, x, y + 1.27, "center"
    jr = "(justify left bottom)" if just == "left" else ""
    jv = "(justify left top)" if just == "left" else ""
    props = [
        f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} 0) (effects (font (size 1.524 1.524) bold) {jr}))',
        f'(property "Value" "{value}" (at {f(vx)} {f(vy)} 0) (effects (font (size 1.27 1.27)) {jv}))',
        f'(property "Footprint" "{FOOTPRINTS[name]}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))',
        f'(property "Datasheet" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))',
    ]
    for k, v in (fields or {}).items():
        props.append(f'(property "{k}" "{v}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide))')
    pinuuids = " ".join(f'(pin "{p[0]}" (uuid {U()}))' for p in s["pins"])
    items.append(f'''(symbol (lib_id "{LIB}:{name}") (at {f(x)} {f(y)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid {U()})
  {" ".join(props)}
  {pinuuids}
  (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1)))))''')
    for num, nm, typ, px, py, ang, side in s["pins"]:
        ex, ey = x + px, y - py   # lib y-up -> sheet y-down
        net = nets.get(num)
        if net is None:
            items.append(f"(no_connect (at {f(ex)} {f(ey)}) (uuid {U()}))")
            continue
        d = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}[side]
        L = 2 * G
        sx, sy = ex + d[0] * L, ey + d[1] * L
        items.append(f"(wire (pts (xy {f(ex)} {f(ey)}) (xy {f(sx)} {f(sy)})) (stroke (width 0) (type default)) (uuid {U()}))")
        if net in ("GND", "+5V"):
            pwr_n[0] += 1
            used_libs.add(net)
            items.append(f'''(symbol (lib_id "power:{net}") (at {f(sx)} {f(sy)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
  (property "Reference" "#PWR{pwr_n[0]:02d}" (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" "{net}" (at {f(sx)} {f(sy + (3.81 if net == "GND" else -3.81))} 0) {FONT})
  (property "Footprint" "" (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at {f(sx)} {f(sy)} 0) (effects (font (size 1.27 1.27)) hide))
  (pin "1" (uuid {U()}))
  (instances (project "{PROJECT}" (path "/{ROOT}" (reference "#PWR{pwr_n[0]:02d}") (unit 1)))))''')
        else:
            ang_l, just = {"L": (180, "right"), "R": (0, "left"), "T": (90, "left"), "B": (270, "right")}[side]
            items.append(f'(label "{net}" (at {f(sx)} {f(sy)} {ang_l}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {U()}))')

def text(t, x, y, size=1.27):
    t = t.replace('"', '\\"')
    items.append(f'(text "{t}" (at {f(x)} {f(y)} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid {U()}))')

# --- Microcontroller (pin assignments follow the firmware) ---
place("Elegoo_Mega_2560", "A1", "Elegoo Mega 2560 R3", 269.24, 139.7, {
    "13": "Z_DIR", "12": "Z_STEP", "11": "Z_ENDSTOP",
    "10": "Y_DIR", "9": "Y_STEP", "8": "Y_ENDSTOP",
    "7": "X_DIR", "6": "X_STEP", "5": "X_ENDSTOP",
    "4": "LAC_PWM", "3": None, "2": "BUZZER",
    "18": "NEX_RX", "19": "NEX_TX", "20": "SDA", "21": "SCL",
    "22": "KP1", "24": "KP2", "26": "KP3", "28": "KP4", "30": "KP5", "32": "KP6", "34": "KP7",
    "5V": "+5V", "GND1": "GND", "GND2": "GND", "VIN": "VIN_PWR"})

# --- Stepper drivers + motors, one per axis ---
for i, ax in enumerate("XYZ"):
    x = 45.72 + i * 58.42
    place("A4988_Module", f"U{i+1}", f"A4988 ({ax} axis)", x, 111.76, {
        "8": f"{ax}_DIR", "7": f"{ax}_STEP", "6": f"{ax}_SLP_RST", "5": f"{ax}_SLP_RST",
        "9": "GND", "10": "+5V", "11": f"{ax}_1B", "12": f"{ax}_1A", "13": f"{ax}_2A", "14": f"{ax}_2B",
        "15": "VMOT_GND", "16": "VMOT"})
    place("Stepper_Bipolar", f"M{i+1}", f"Stepper motor ({ax})", x, 162.56, {
        "1": f"{ax}_2A", "2": f"{ax}_2B", "3": f"{ax}_1A", "4": f"{ax}_1B"})

# --- Motor supply: DC in -> buck -> VMOT ---
place("DC_Supply", "J2", "Motor power in", 45.72, 200.66, {"1": "MOT_IN+", "2": "MOT_IN-"})
place("LM2596_Module", "PS2", "LM2596 (motor)", 106.68, 200.66, {
    "1": "MOT_IN+", "2": "MOT_IN-", "3": "VMOT", "4": "VMOT_GND"})

# --- Actuator supply: DC in -> buck -> LAC ---
place("DC_Supply", "J1", "Actuator power in", 45.72, 50.8, {"1": "ACT_IN+", "2": "ACT_IN-"})
place("LM2596_Module", "PS1", "LM2596 (12 V actuator)", 106.68, 50.8, {
    "1": "ACT_IN+", "2": "ACT_IN-", "3": "LAC_V+", "4": "LAC_V-"})
place("Actuonix_LAC", "A2", "Actuonix LAC", 152.4, 50.8, {"1": "LAC_V+", "2": "LAC_V-", "3": "LAC_VC"})

# --- LAC control signal: D4 -> R2 -> node -> VC, with R1 to +5V ---
place("Resistor", "R1", "R_pullup (value TBD)", 193.04, 50.8, {"1": "+5V", "2": "LAC_VC"})
place("Resistor", "R2", "R_series (value TBD)", 193.04, 101.6, {"1": "LAC_VC", "2": "LAC_PWM"})

# --- Limit switch ---
for i, ax in enumerate("XYZ"):
    place("Limit_Switch", f"SW{i+1}", f"{ax} end-stop", 231.14, 45.72 + i * 17.78, {"1": f"{ax}_ENDSTOP", "2": "GND"})

# --- Displays ---
place("Nextion_NX4827T043", "DS1", "Nextion NX4827T043", 297.18, 50.8, {
    "1": "GND", "2": "NEX_TX", "3": "NEX_RX", "4": "+5V"})
place("I2C_LCD", "DS2", "I2C LCD (not used)", 342.9, 50.8, {
    "1": "SDA", "2": "SCL", "3": "GND", "4": "+5V"}, dnp=True)

# --- Keypad & buzzer ---
place("Keypad_4x3", "SW4", "4x3 keypad", 360.68, 134.62, {
    str(i): f"KP{i}" for i in range(1, 8)})
place("Buzzer", "BZ1", "Buzzer", 360.68, 172.72, {"1": "BUZZER", "2": "GND"})

# --- Logic supply: DC in -> buck -> Mega VIN ---
place("DC_Supply", "J3", "Logic power in", 218.44, 213.36, {"1": "LOGIC_IN+", "2": "LOGIC_IN-"})
place("LM2596_Module", "PS3", "LM2596 (logic)", 279.4, 213.36, {
    "1": "LOGIC_IN+", "2": "LOGIC_IN-", "3": "VIN_PWR", "4": "GND"})

text("Automated Micropipetting System - Imperial College London, DAPP Group F (2025)", 25.4, 22.86, 2.0)
text("Redrawn from the report's KiCad figure (Appendix F). Connectivity uses net labels.", 25.4, 27.94)
text("Pin assignments follow the firmware. The report figure differs: it shows one axis only, DIR/STEP on D6/D7 (swapped),", 25.4, 236.22)
text("the buzzer on D52 and the Nextion on TX0/RX0. The firmware uses buzzer D2 and Serial1 (TX1 = D18, RX1 = D19).", 25.4, 240.03)
text("R1/R2 values were not given in the report. VMOT_GND and LAC_V- are separate returns as drawn; tie to GND if supplies share a ground.", 25.4, 243.84)

# ---------- write ----------
libs = "\n".join(lib_symbol_text(n) for n in sorted(used_libs))
out = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT})
  (paper "A3")
  (title_block
    (title "Automated Micropipetting System")
    (date "2025-06-18")
    (rev "A")
    (company "Imperial College London - DAPP Group F")
    (comment 1 "Redrawn from final report Appendix F")
  )
  (lib_symbols
{libs}
  )
{chr(10).join(items)}
  (sheet_instances (path "/" (page "1")))
)
'''
import sys
open(sys.argv[1], "w").write(out)
print("written", len(items), "items")
