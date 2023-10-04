#pragma once

// Reference:
// https://github.com/hathach/tinyusb/tree/master/examples/device/hid_multiple_interface
// https://github.com/raspberrypi/pico-examples/tree/master/usb/device/dev_hid_composite

#define CFG_TUD_ENABLED  1

#define CFG_TUD_HID     2
#define CFG_TUD_CDC     0
#define CFG_TUD_MSC     0
#define CFG_TUD_MIDI    0
#define CFG_TUD_VENDOR  0

#define CFG_TUD_HID_EP_BUFSIZE  8

#define ITF_KEYBOARD  0
#define ITF_CONSUMER  1
