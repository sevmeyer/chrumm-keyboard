Chrumm PCB
==========

The PCB is made with [KiCad], version 7.

The PCB is reversible. It covers half of the keyboard,
and is flipped over for the other half. It is intended
to slightly bend between the pinky and ring finger,
therefore the board thickness should not exceed 0.8mm.

All connections are through-hole (or castelated), so
that they can be soldered with basic hobby equipment.
The switch pin holes are implemented as slots, to
provide a snug fit for the flat pins, and thus
minimize the required amount of solder.

[KiCad]: https://www.kicad.org/


Teardrops
---------

The teardrops are generated with a custom [KiCad plugin],
using the following settings:

    PTH arc radius: 250%
    SMD arc radius: 250%
    Via arc radius: 350%

[KiCad plugin]: https://github.com/sevmeyer/kicad-arc-teardrops


Production
----------

I ordered the prototypes from [PCBWay] (no affiliation).
Other manufacturers are available, check for example
[PCBShopper] or [Manufacturing Reports]. Here are some of
the relevant specifications, use them at your own discretion:

- Standard PCB (not flex)
- Single pieces (not panelized)
- Layers: 2
- Material: FR4 TG 150-160
- Thickness: 0.8mm (at most)
- Surface finish: HASL (lead free)
- Copper thickness: 1oz

[PCBWay]: https://pcbway.com/
[PCBShopper]: https://pcbshopper.com/
[Manufacturing Reports]: https://manufacturingreports.com/category/electronics/rigid-pcb-fabrication/
