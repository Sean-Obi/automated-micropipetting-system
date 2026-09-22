"""Place footprints for pcb_design and export a Specctra DSN for autorouting."""
import re, sys, pcbnew
from pcbnew import VECTOR2I, FromMM, EDA_ANGLE, DEGREES_T

NET, LIB, OUT, DSN = sys.argv[1:5]  # netlist, footprint lib dir, output .kicad_pcb, output .dsn

txt = open(NET).read()
# components: ref -> footprint
comps = dict(re.findall(r'\(comp \(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', txt, re.S))
comp_vals = dict(re.findall(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]+)"\)', txt, re.S))
nets = {}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', txt, re.S):
    nets[m.group(1)] = re.findall(r'\(ref "([^"]+)"\) \(pin "([^"]+)"', m.group(2))

board = pcbnew.BOARD()
ds = board.GetDesignSettings()
ds.SetBoardThickness(FromMM(1.6))

X0, Y0 = 100.0, 100.0
W, H = 132.0, 80.0
# (x, y, rotation) of each footprint's pad 1, in mm relative to board origin
PLACE = {
    "J1": (8, 22, 90),  "PS1": (19, 12, 0),
    "J2": (8, 44, 90),  "PS2": (19, 34, 0),
    "J3": (8, 67, 90),  "PS3": (19, 60, 0),
    "U1": (32, 24, 0),  "M1": (33, 55, 90), "SW1": (34, 66, 90),
    "U2": (57, 24, 0),  "M2": (58, 55, 90), "SW2": (59, 66, 90),
    "U3": (82, 24, 0),  "M3": (83, 55, 90), "SW3": (84, 66, 90),
    "A2": (32, 8, 90),  "R1": (48, 6, 0),   "R2": (48, 13, 0),
    "DS1": (72, 7, 90), "DS2": (86, 7, 90), "SW4": (100, 7, 90),
    "A1": (122, 14, 0), "BZ1": (108, 66, 0),
}
LABELS = {
    "J1": "ACT PWR IN", "J2": "MOTOR PWR IN", "J3": "LOGIC PWR IN",
    "PS1": "BUCK 12V", "PS2": "BUCK VMOT", "PS3": "BUCK 5V",
    "M1": "X MOTOR", "M2": "Y MOTOR", "M3": "Z MOTOR",
    "SW1": "X END", "SW2": "Y END", "SW3": "Z END",
    "A2": "LAC", "DS1": "NEXTION", "DS2": "I2C LCD", "SW4": "KEYPAD", "A1": "TO MEGA",
    "U1": "X DRV", "U2": "Y DRV", "U3": "Z DRV",
}

netinfo = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(board, name)
    board.Add(ni)
    netinfo[name] = ni
padnet = {}
for name, nodes in nets.items():
    for ref, pin in nodes:
        padnet[(ref, pin)] = name

def mm(x, y): return VECTOR2I(FromMM(X0 + x), FromMM(Y0 + y))

for ref, fpid in comps.items():
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(LIB, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref)
    fp.SetValue(comp_vals.get(ref, name))
    fp.Value().SetVisible(False)
    x, y, rot = PLACE[ref]
    fp.SetPosition(mm(x, y))
    fp.SetOrientation(EDA_ANGLE(rot, DEGREES_T))
    board.Add(fp)
    for p in fp.Pads():
        key = (ref, p.GetNumber())
        if key in padnet:
            p.SetNet(netinfo[padnet[key]])
    if ref == "DS2":
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP) if hasattr(pcbnew, "FP_DNP") else None
    if ref in LABELS:
        bb = fp.GetBoundingBox(False, False)
        t = pcbnew.PCB_TEXT(board)
        t.SetText(LABELS[ref])
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(VECTOR2I(FromMM(1.0), FromMM(1.0)))
        t.SetTextThickness(FromMM(0.15))
        if ref.startswith("J"):
            t.SetPosition(VECTOR2I(bb.GetCenter().x, bb.GetTop() - FromMM(1.4)))
        else:
            t.SetPosition(VECTOR2I(bb.GetCenter().x, bb.GetBottom() + FromMM(1.4)))
        board.Add(t)

# outline
pts = [(0, 0), (W, 0), (W, H), (0, H)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(mm(*pts[i])); seg.SetEnd(mm(*pts[(i + 1) % 4]))
    seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(FromMM(0.1))
    board.Add(seg)

# M3 mounting holes (board-only)
for i, (hx, hy) in enumerate([(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]):
    fp = pcbnew.FootprintLoad(LIB, "MountingHole_3.2mm_M3")
    fp.SetFPID(pcbnew.LIB_ID("apms", "MountingHole_3.2mm_M3"))
    fp.SetReference(f"H{i+1}"); fp.Reference().SetVisible(False)
    fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY)
    fp.SetPosition(mm(hx, hy))
    board.Add(fp)

# title block silk
for txtv, y, sz in [("MICROPIPETTING INTERFACE BOARD", H - 9, 1.5),
                    ("Rev A  |  Imperial College London  |  DAPP Group F", H - 6.5, 1.0)]:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txtv); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(VECTOR2I(FromMM(sz), FromMM(sz))); t.SetTextThickness(FromMM(0.15 if sz < 1.2 else 0.25))
    t.SetPosition(mm(60, y)); board.Add(t)

board.Save(OUT)
ok = pcbnew.ExportSpecctraDSN(board, DSN)
print("saved", OUT, "dsn", ok, "footprints", len(board.GetFootprints()))
