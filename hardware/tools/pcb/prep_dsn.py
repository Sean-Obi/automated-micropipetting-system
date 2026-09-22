import re, sys
s = open(sys.argv[1]).read()
s = s.replace("Via[0-1]_600:300_um", "Via[0-1]_800:400_um").replace("(circle F.Cu 600)", "(circle F.Cu 800)").replace("(circle B.Cu 600)", "(circle B.Cu 800)")
s = s.replace("(width 200)\n      (clearance 200.1)\n      (clearance 200.1 (type default_smd))",
              "(width 300)\n      (clearance 250)\n      (clearance 250 (type default_smd))")
nets = re.findall(r'\(net ("[^"]+"|\S+)\n', s)
POWER = {"GND", "+5V", "/VMOT", "/VMOT_GND", "/LAC_V+", "/LAC_V-", "/ACT_IN+", "/ACT_IN-",
         "/MOT_IN+", "/MOT_IN-", "/LOGIC_IN+", "/LOGIC_IN-", "/VIN_PWR"}
def q(n): return n if n.startswith('"') else (f'"{n}"' if any(c in n for c in "-(){}~ ") else n)
def bare(n): return n.strip('"')
power = [n for n in nets if bare(n) in POWER]
motor = [n for n in nets if re.fullmatch(r"/[XYZ]_[12][AB]", bare(n))]
sig = [n for n in nets if n not in power and n not in motor and not bare(n).startswith("unconnected")]
def cls(name, lst, w, c):
    return (f'    (class {name} "" {" ".join(q(bare(n)) for n in lst)}\n'
            f'      (circuit\n        (use_via Via[0-1]_800:400_um)\n      )\n'
            f'      (rule\n        (width {w})\n        (clearance {c})\n      )\n    )\n')
start = s.index("    (class kicad_default")
end = s.index("  )\n  (wiring")
s = s[:start] + cls("power", power, 1000, 300) + cls("motor", motor, 800, 250) + cls("signal", sig, 300, 250) + s[end:]
open(sys.argv[2], "w").write(s)
print(len(power), "power", len(motor), "motor", len(sig), "signal")
