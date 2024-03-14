Chrumm keyboard STL generator
=============================

The STL files are generated with the `chrumm` package for Python 3.7+.
It has no dependencies and does not need to be compiled or installed.
Run it as a command-line tool from this directory:

    python3 -m chrumm --help

To generate the default STL files:

    python3 -m chrumm chrumm.json


Parameters
----------

The configuration parameters are provided via JSON files.
If a parameter appears multiple times, then its latest value
is used. Distances are given in millimeters, angles in degrees.

#### PCB compatibility

Unlike the body, the PCB is manually edited and not programmatic.
Changes to the body parameters may not be compatible with the PCB.
A flattened KiCad footprint (.kicad_mod) is generated to help with
the placement of the switches and screws on the PCB.

#### Parameter validation

The generator does not validate all of the parameters.
Most importantly, chamfers and switch notches are not
taken into account when placing the walls. Make sure
that the switch margin parameter provides enough room.

The generator should produce reasonable results for
split, tent, and tilt angles up to about 20 degrees.
Results may vary for more extreme angles.

#### Layout

The `layout.fingerStaggers` matrix represents the
offset of each key relative to its ortholinear position.

The matrix is a list of rows. Each row contains four
sublists, to represent the sections of the keyboard
(left pinky, left alnum, right alnum, right pinky).
Each section contains key offset coordinates.
A coordinate can be an empty list (key omitted), a single
number (y offset), or a list of two numbers (x and y offset).

Each section must have at least two key coordinates.
All rows must have the same column structure.

#### Omit items

Chamfers can be turned off by setting them to `0`.
The value of the following parameters can be set
to `false` in order to omit them from the output:

    bracket
    bumper
    cable
    encoder
    floor.hexHoles
    knob
    palm
    pcb
    pcb.mount
    support
    switch.clipNotch


Print
-----

I printed the parts on a Prusa Mini, with PLA filament,
on a smooth PEI sheet. The gcode was generated with
[PrusaSlicer] 2.6.0. The 3MF files with the exact settings
are available on the [releases] page.

[PrusaSlicer]: https://www.prusa3d.com/prusaslicer/
[releases]: https://github.com/sevmeyer/chrumm-keyboard/releases

Assembly
--------

The assembly is straightforward. See the [assembly guide](ASSEMBLY.md).
