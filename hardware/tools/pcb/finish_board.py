import sys, pcbnew
from pcbnew import FromMM, VECTOR2I
src, ses, out = sys.argv[1:4]
board = pcbnew.LoadBoard(src)
import re
def tokens(t):
    return re.findall(r'"[^"]*"|\(|\)|[^\s()]+', t)
def parse(tok, i=0):
    out = []
    while i < len(tok):
        t = tok[i]
        if t == "(":
            sub, i = parse(tok, i + 1); out.append(sub)
        elif t == ")":
            return out, i + 1
        else:
            out.append(t.strip('"')); i += 1
    return out, i
tree = parse(tokens(open(ses).read()))[0][0]
def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]
routes = find(tree, "routes")[0]
res = 10000.0  # 'resolution um 10' -> 0.1 um units
layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
nw = find(routes, "network_out")[0]
ntr = nvia = 0
for net in find(nw, "net"):
    ni = board.FindNet(net[1])
    for w in find(net, "wire"):
        p = find(w, "path")[0]
        layer, width, coords = p[1], float(p[2]) / res, [float(v) / res for v in p[3:]]
        pts = [(coords[k], -coords[k + 1]) for k in range(0, len(coords), 2)]
        for a, b in zip(pts, pts[1:]):
            tr = pcbnew.PCB_TRACK(board)
            tr.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1]))); tr.SetEnd(VECTOR2I(FromMM(b[0]), FromMM(b[1])))
            tr.SetWidth(FromMM(width)); tr.SetLayer(layers[layer]); tr.SetNet(ni)
            board.Add(tr); ntr += 1
    for v in find(net, "via"):
        m = re.match(r"Via\[\d-\d\]_(\d+):(\d+)_um", v[1])
        dia, drill = int(m.group(1)) / 1000, int(m.group(2)) / 1000
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(VECTOR2I(FromMM(float(v[2]) / res), FromMM(-float(v[3]) / res)))
        via.SetWidth(FromMM(dia)); via.SetDrill(FromMM(drill)); via.SetNet(ni)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        board.Add(via); nvia += 1
print("imported", ntr, "segments", nvia, "vias")
# --- clean autorouter leftovers: duplicate, zero-length and dangling segments ---
def key(p): return (round(p.x / 1000), round(p.y / 1000))
seen = set()
for t in [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]:
    k = (t.GetLayer(), t.GetNetCode(), frozenset([key(t.GetStart()), key(t.GetEnd())]))
    if k in seen or key(t.GetStart()) == key(t.GetEnd()):
        board.Remove(t)
    else:
        seen.add(k)
for _ in range(50):
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    dangling = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and conn.TestTrackEndpointDangling(t, False)]
    if not dangling:
        break
    for t in dangling:
        board.Remove(t)
board.BuildConnectivity()

# GND pour on both layers
gnd = board.FindNet("GND")
X0, Y0, W, H = 100, 100, 132, 80
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(gnd)
    z.SetLocalClearance(FromMM(0.4))
    z.SetMinThickness(FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(FromMM(0.5)); z.SetThermalReliefSpokeWidth(FromMM(0.5))
    ol = z.Outline(); ol.NewOutline()
    m = 0.5
    for x, y in [(m, m), (W - m, m), (W - m, H - m), (m, H - m)]:
        ol.Append(FromMM(X0 + x), FromMM(Y0 + y))
    z.SetIsFilled(False)
    board.Add(z)
board.BuildConnectivity()
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.BuildConnectivity()
conn = board.GetConnectivity()
print("unrouted connections:", conn.GetUnconnectedCount(True))
print("tracks:", len(board.GetTracks()))
board.Save(out)
