"""Write the project footprint library (apms.pretty) used by pcb_design."""
import os, sys
P = 2.54

def pad(num, x, y, square=False, drill=1.0, size=1.7):
    shape = "rect" if square else "circle"
    return (f'  (pad "{num}" thru_hole {shape} (at {x:.3f} {y:.3f}) (size {size} {size}) '
            f'(drill {drill}) (layers "*.Cu" "*.Mask"))')

def rect(layer, x1, y1, x2, y2, w):
    return (f'  (fp_rect (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) '
            f'(stroke (width {w}) (type default)) (fill none) (layer "{layer}"))')

def text(kind, val, x, y, layer, hide=False):
    h = " hide" if hide else ""
    return (f'  (fp_text {kind} "{val}" (at {x:.3f} {y:.3f}) (layer "{layer}"){h}\n'
            f'    (effects (font (size 1 1) (thickness 0.15))))')

def footprint(name, desc, pads, body, ref_xy, val_xy, courtyard_margin=0.5):
    x1, y1, x2, y2 = body
    cm = courtyard_margin
    lines = [f'(footprint "{name}" (version 20221018) (generator pcbnew)',
             '  (layer "F.Cu")',
             f'  (descr "{desc}")',
             '  (attr through_hole)',
             text("reference", "REF**", *ref_xy, "F.SilkS"),
             text("value", name, *val_xy, "F.Fab"),
             rect("F.SilkS", x1, y1, x2, y2, 0.12),
             rect("F.Fab", x1, y1, x2, y2, 0.1),
             rect("F.CrtYd", x1 - cm, y1 - cm, x2 + cm, y2 + cm, 0.05)]
    lines += pads
    lines.append(")")
    return name, "\n".join(lines) + "\n"

def header_1xN(n, names=None, name=None, desc=None):
    names = names or [str(i + 1) for i in range(n)]
    pads = [pad(nm, 0, i * P, square=(i == 0)) for i, nm in enumerate(names)]
    return footprint(name or f"PinHeader_1x{n:02d}_P2.54mm",
                     desc or f"1x{n} 2.54 mm pin header", pads,
                     (-1.27, -1.27, 1.27, (n - 1) * P + 1.27), (0, -2.6), (0, (n - 1) * P + 2.6))

FPS = []
for n in (2, 3, 4, 7):
    FPS.append(header_1xN(n))

# Pololu A4988 carrier socket: two 1x8 rows 12.7 mm apart.
# Left row top->bottom: EN MS1 MS2 MS3 RST SLP STEP DIR (1..8)
# Right row top->bottom: VMOT GND 2B 2A 1A 1B VDD GND (16..9)
left = [str(i) for i in range(1, 9)]
right = [str(i) for i in range(16, 8, -1)]
pads = [pad(n, 0, i * P, square=(n == "1")) for i, n in enumerate(left)]
pads += [pad(n, 12.7, i * P) for i, n in enumerate(right)]
FPS.append(footprint("Pololu_A4988_Carrier_Socket",
    "Socket for Pololu-format A4988 carrier (2x 1x8 female headers, 0.5 in row spacing)",
    pads, (-1.27, -1.27, 13.97, 19.05), (6.35, -2.6), (6.35, 20.6)))

# Mega interface header, 2x14, pads named after the Mega pins used.
mega = ["13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2", "18", "19",
        "20", "21", "22", "24", "26", "28", "30", "32", "34", "5V", "GND1", "GND2", "VIN"]
pads = []
for i, nm in enumerate(mega):
    col, row = i % 2, i // 2
    pads.append(pad(nm, col * P, row * P, square=(i == 0)))
FPS.append(footprint("Mega2560_Interface_2x14_P2.54mm",
    "2x14 header carrying the used Elegoo Mega 2560 signals (ribbon/jumpers to the Mega)",
    pads, (-1.27, -1.27, 3.81, 13 * P + 1.27), (1.27, -2.6), (1.27, 13 * P + 2.6)))

# 2-position 5.08 mm screw terminal (e.g. 277-1258-ND)
pads = [pad("1", 0, 0, square=True, drill=1.3, size=2.6), pad("2", 5.08, 0, drill=1.3, size=2.6)]
FPS.append(footprint("TerminalBlock_1x02_P5.08mm",
    "2-pos 5.08 mm side-entry PCB terminal block", pads,
    (-2.54, -4.2, 7.62, 4.2), (2.54, -5.4), (2.54, 5.4)))

# LM2596 module wiring header: IN+ IN- OUT+ OUT-
FPS.append(header_1xN(4, ["1", "2", "3", "4"], "LM2596_Module_Header_1x04",
                      "Wiring header for off-board LM2596 module: IN+, IN-, OUT+, OUT-"))

# Axial resistor, 10.16 mm pitch
pads = [pad("1", 0, 0), pad("2", 10.16, 0)]
FPS.append(footprint("R_Axial_DIN0207_L6.3mm_P10.16mm",
    "Axial resistor 0207, 10.16 mm pitch", pads, (1.93, -1.25, 8.23, 1.25), (5.08, -2.4), (5.08, 2.4)))

# 12 mm THT buzzer, 7.62 mm pitch
pads = [pad("1", 0, 0, square=True), pad("2", 7.62, 0)]
FPS.append(footprint("Buzzer_12x9.5RM7.6",
    "12 mm through-hole piezo buzzer, 7.62 mm pitch", pads,
    (-2.19, -6.0, 9.81, 6.0), (3.81, -7.2), (3.81, 7.2)))

# M3 mounting hole (NPTH)
FPS.append(("MountingHole_3.2mm_M3", """(footprint "MountingHole_3.2mm_M3" (version 20221018) (generator pcbnew)
  (layer "F.Cu")
  (descr "M3 mounting hole, unplated")
  (attr exclude_from_pos_files exclude_from_bom)
  (fp_text reference "REF**" (at 0 -4.2) (layer "F.SilkS") hide
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value "MountingHole_3.2mm_M3" (at 0 4.2) (layer "F.Fab") hide
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_circle (center 0 0) (end 3.45 0) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
  (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask"))
)
"""))

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, txt in FPS:
        open(os.path.join(out, name + ".kicad_mod"), "w").write(txt)
    print("wrote", len(FPS), "footprints to", out)
