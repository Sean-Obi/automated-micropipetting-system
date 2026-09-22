# PCB generation scripts

These scripts rebuild `pcb_design.kicad_pcb` from the schematic. They need KiCad 7 (`pcbnew` Python module + `kicad-cli`) and Java 21 for [Freerouting](https://github.com/freerouting/freerouting).

Run the commands below from `hardware/`, in order:

```bash
python3 tools/make_sch.py pcb_design.kicad_sch                  # schematic
python3 tools/pcb/footprints.py apms.pretty                      # footprint library
kicad-cli sch export netlist -o board.net pcb_design.kicad_sch  # netlist
python3 tools/pcb/build_board.py board.net apms.pretty placed.kicad_pcb board.dsn   # placement
python3 tools/pcb/prep_dsn.py board.dsn routed_in.dsn          # net classes: power 1.0 mm, motor 0.8 mm, signal 0.3 mm
java -jar freerouting.jar -de routed_in.dsn -do board.ses -mp 40 --gui.enabled=false   # autoroute
python3 tools/pcb/finish_board.py placed.kicad_pcb board.ses pcb_design.kicad_pcb     # import routes, clean up, GND pours
```

Freerouting is non-deterministic, and a run can occasionally drop a net. `finish_board.py` prints the number of unrouted connections. Re-run the routing step until it reports 0.
