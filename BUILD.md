Chrumm build advice
===================

Printing
--------

I printed the parts on a Prusa Mini, with PLA filament, on a
smooth PEI sheet. The gcode was generated with [PrusaSlicer] 2.6.0.
The 3MF files with the exact print settings and part configurations
are available on the [Releases] page.

The body halves are printed sideways, with custom supports.
In PrusaSlicer, custom supports can be added in the
[Object list] (Advanced mode). Right-click on the body object
and load the support STL with "Add Part". Right-click on the
support object to adjust its print settings.

[PrusaSlicer]: https://www.prusa3d.com/prusaslicer/
[Object list]: https://help.prusa3d.com/article/object-list_1758
[Releases]: https://github.com/sevmeyer/chrumm-keyboard/releases


Diodes
------

Note that there is not much room between the switch plate and
the PCB. Therefore, I soldered the diode legs on the same side
as the diode body, and cut the legs reasonably short on the
switch-facing side with a [flush cutter]. To hold up the PCB
while soldering the diodes, I used standoff jigs that clip
into the stem holes (see photos).

The diode pads have a common pitch of 7.62mm (300mil).
To bend the legs in a uniform way, I used a bender jig.
Both jigs are available on the [Releases] page.

[flush cutter]: https://en.wikipedia.org/wiki/Diagonal_pliers#Variations


Flexstrip
---------

The PCB halves are connected via Flexstrip jumpers. To compensate
for the default split angle, the strips should be folded in a
specific way before installation. Check the image for reference.
I wrapped the strips around a thin screwdriver shaft, to maintain
a minimum bend radius of about 2mm.

![Fold lines for flexstrip jumpers](images/flexstrip.svg)


PCB installation
----------------

To install the PCB, I would first clip the corner switches
into the body, e.g. switches 12-64-58, 10-9-6, and 49-48-45.
Then align the PCB with the switch pins and push it flat
against the switch bottoms.

Before soldering any switches, check that the screw mount
next to the Pico does not bend the PCB. If the print is
misaligned, you might want to sand off a bit of the mount,
or extend its height with a washer.

When everything fits, the remaining switches can be inserted.
Note that the thumb switches are north-facing (upside down).
