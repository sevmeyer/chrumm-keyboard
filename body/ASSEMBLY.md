# Chrumm-Keyboard Assembly Guide and Building Instructions


## 3D printing the parts

print the parts with the settings in the 3mf files

### Palm

- Infill: 10%
- Layer Height: 0.2mm

### Floor

- Infill: 100%
- Layer Height: 0.2mm

### Body

- Infill: 15%
- Layer Height: 0.2mm
- add generated supports to part as `part` of part


## Glueing the artifical leather

1. Roughly Cut the artificial leather to the 6size of the palm rest
2. Glue the leather onto the palm rest with the glue
3. Wait until glue is dry
4. Remove the excess leather on the long-side of the palm rest using a knife or scalpel, cutting on a cutting board
5. use scissors to cut the leather on the short sides to about 1cm remains
6. tug the 1cm of leather into the chasm on the side using something fleat


## Adding the threaded inserts

- Use a soldering iron
- - Make sure not to dirty the soldering tip with plastic
- Put the threaded insert onto the holes of the 3D printed parts. The thin part of the threaded insert should be in the hole.
- Heat the threaded insert with a soldering iron and gently push down until the threaded insert is all the way inside the 3D printed part and the end of the insert is level with the part. Keep the soldering iron aproximately vertical to avoid touching the plastic.


## Soldering Diodes

(Optional Alternative: edit the PCB in KiCAD, replace all TH diodes with SMD parts and order it pre-assembled)

- Use the diode bender to bend the diode's feet into place
- Look at the picture. The diodes will be mounted onto the downward side of the PCB, while the MX switches will be mounted onto the top side. The Raspberry Pico will face the same way as all the diodes.
- Insert all diodes into the marked places. 
- Check that all diodes face the correct way as marked on the PCB
- Slightly bend the leads of the diodes, about 20° to keep them in place
- Turn the PCBs over, so the PCBs  are lying on the diodes.
- All the leads of the diodes should more or less be facing up. Pull on them to make sure all dioes are snug on the PCB
- Solder the diodes
- clip the leads with an electric wire cutter


## Soldering Raspberry Pico

- Turn the PCBs over again so the diodes face up
- Use the M2 screw and nuts to mount the raspberry pico onto the correct PCB (see pictures)
- Make sure the pico's and the PCB's pads are aligned. You can check if the holes are aligned by temporarily putting some leads of leftover diodes through them. Remove them again, we don't want to solder any diodes anymore.
- Solder the pads of the pico onto the PCB


## Soldering Flexstrips and two PCBs together

- Solder the flexstrips onto the PCB with the pico, while you are at it.
  - the shorter 5pin flexstrip onto the PCB next to the pico (marked "rows")
  - the shorter 8pin flexstrip onto the Pico itself (marked "gpio22" to "gpio16")
  - the longer 3pin flexstrip onto the PCB where marked "ROT". Alternatively use 3 coloured wires.

- If you have generated a Chrumm with more than 12° of split, you might need to extend the flexstrip's length. Just take another flexstrip, cut it to lenght, strip off some of the insultation and wire the pins of the too-short flexstrips onto the seconds flexstrip.

- At the end, you should have two connected PCB halves


## Assemble the body and floor

- prepare the USB cable
  - ensure the cable is not too thick and fits into the hole formed when you put the two 3D printed body parts together. (See picture)
- on the 3D printed parts for body and floor, find the hexagonal shaped holes for the M3 nuts. 
  - 3 on the top body part and 2 on the floor part.
- Use a plier to insert the nuts into the holes.
- Use tape or a miniscule amount of superglue to fix the nut in place.
- insert the USB cable in the tiny hole onto the front, while putting together both halves of the body
- screw together the body halves using the M3 nuts and M3 socket head cap screws
- screw together the floor halves using the M3 nuts and M3 socket head cap screws


## Encoder

- Solder the encoder onto the small break-away PCB. Check the photos
- now solder the 3pin flexstrip, which is currently connected to the big PCB, to the break-away PCB. Check the fotos
- mount the encoder in the body and screw it on.


## Soldering the MX Switches

This step will permanently mount your MX switches to the PCB with the 3D printed body sandwiched in-between.

- insert all the MX switches into the printed body.
- the electrical pins of the switches all face toward the back concave side of the keyboard
- except the electrical pins of the four innermost thumbrow switches, which face the front convex side of the keyboard
- put the PCB onto the switches.
- compare with the PCB to make sure all pins are oriented correctly
- make sure all pins face straight up and fit into the PCB.
- AGAIN: make sure no pins is bent and missing. You can't fix this later.
- gently put the PCB onto the switch's pins.
- solder all the MX switches.


## Final Assembly

- connect the micro USB cable to the Raspberry Pico
- use a ziptie to fix the USB cable in place so no pull on the cable will transmit to the Pico. (Strain relief)
- Use the sunken M3 screws to assemble floor and body together.
- Use four more sunken M3 screws to screw the palm-rest into place
