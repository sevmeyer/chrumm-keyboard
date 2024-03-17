Chrumm firmware
===============

The firmware is written in C for the [Raspberry Pi Pico].
If you instead prefer a more standard toolkit, check out
the experimental [QMK config] for Chrumm.

[Raspberry Pi Pico]: https://www.raspberrypi.com/products/raspberry-pi-pico/
[QMK config]: https://github.com/sevmeyer/chrumm-qmk


Features
--------

The firmware implements two [USB HID] interfaces. Interface 0 acts
as a standard Boot Keyboard. Interface 1 sends HID Consumer codes
for application-specific controls, including multimedia.

Two layers are available. Hold down the `Fn` key to momentarily
activate the alternative layer. Double tap `Fn` to stay on the
alternative layer until `Fn` is tapped again.

Optionally, the rotation signals of an EC11 encoder can be
mapped to virtual key presses.

The special `kBOOT` keycode (Fn+Z) can be tapped three times
to put the keyboard into bootloader mode without the need to
unplug the USB cable.

For debugging purposes, the on-board LED of the Pico indicates
non-default lock states. When Caps Lock is on, the LED is on.
When Num Lock is off, the LED blinks once every 2 seconds.

[USB HID]: https://www.usb.org/document-library/device-class-definition-hid-111


Compile
-------

The default UF2 binary is available on the [Releases] page.

To compile a custom version, install the [Pico SDK] and [Arm GNU Toolchain].
Set the `PICO_SDK_PATH` environment variable to the SDK directory.
Append the Arm `bin` directory to the `PATH` environment variable.
The firmware can then be prepared and compiled with:

    cmake -B build
    cmake --build build

[Releases]: https://github.com/sevmeyer/chrumm-keyboard/releases
[Pico SDK]: https://github.com/raspberrypi/pico-sdk
[Arm GNU Toolchain]: https://developer.arm.com/Tools%20and%20Software/GNU%20Toolchain


Install
-------

Hold down the `BOOTSEL` button on the Pico while plugging in
the USB cable. It should show up as a USB storage device.
After the first install, you can keep the keyboard plugged in
and instead tap Fn+Z three times.

Drag-and-drop the UF2 binary from the build directory onto the device.
The Pico should automatically restart and run the firmware.
Alternatively, install [picotool] and use:

    picotool load build/chrumm.uf2 --force
    picotool reboot

[picotool]: https://github.com/raspberrypi/picotool
