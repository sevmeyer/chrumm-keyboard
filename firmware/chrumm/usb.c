#include "chrumm/usb.h"
#include "chrumm/config.h"
#include "chrumm/led.h"
#include <tusb.h>
#include <pico/unique_id.h>


// This ID combination is registered on <https://pid.codes>
// for the Chrumm keyboard. Do not use it for other firmware.
// Otherwise, you could mess up the host's driver selection.

#define USB_VID  0x1209
#define USB_PID  0x5E7C


// Device Descriptor
// -----------------

const tusb_desc_device_t deviceDesc = {
    .bLength            = sizeof(tusb_desc_device_t),
    .bDescriptorType    = TUSB_DESC_DEVICE,
    .bcdUSB             = 0x0200,
    .bDeviceClass       = 0,
    .bDeviceSubClass    = 0,
    .bDeviceProtocol    = 0,
    .bMaxPacketSize0    = CFG_TUD_ENDPOINT0_SIZE,
    .idVendor           = USB_VID,
    .idProduct          = USB_PID,
    .bcdDevice          = 0x0100,
    .iManufacturer      = 1,
    .iProduct           = 2,
    .iSerialNumber      = 3,
    .bNumConfigurations = 1};


const uint8_t* tud_descriptor_device_cb()
{
    return (const uint8_t*) &deviceDesc;
}


// HID Report Descriptor
// ---------------------

const uint8_t hidKeyboardDesc[] = { TUD_HID_REPORT_DESC_KEYBOARD() };
const uint8_t hidConsumerDesc[] = { TUD_HID_REPORT_DESC_CONSUMER() };


const uint8_t* tud_hid_descriptor_report_cb(uint8_t itf)
{
    switch (itf) {
        case ITF_KEYBOARD: return hidKeyboardDesc;
        case ITF_CONSUMER: return hidConsumerDesc;
        default: return NULL;
    }
}


// Configuration Descriptor
// ------------------------

const uint8_t configurationDesc[] = {
    TUD_CONFIG_DESCRIPTOR(
    /* CFG bConfigurationValue */ 1,
    /* CFG bNumInterfaces      */ 2,
    /* CFG iConfiguration      */ 0,
    /* CFG wTotalLength        */ TUD_CONFIG_DESC_LEN + 2*TUD_HID_DESC_LEN,
    /* CFG bmAttributes        */ TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP,
    /* CFG bMaxPower*2 (mA)    */ 100),
    TUD_HID_DESCRIPTOR(
    /* ITF bInterfaceNumber    */ ITF_KEYBOARD,
    /* ITF iInterface          */ 0,
    /* ITF bInterfaceProtocol  */ HID_ITF_PROTOCOL_KEYBOARD,
    /* HID wDescriptorLength   */ sizeof(hidKeyboardDesc),
    /* EP  bEndpointAddress    */ 0x81,
    /* EP  wMaxPacketSize      */ CFG_TUD_HID_EP_BUFSIZE,
    /* EP  bInterval (ms)      */ 1),
    TUD_HID_DESCRIPTOR(
    /* ITF bInterfaceNumber    */ ITF_CONSUMER,
    /* ITF iInterface          */ 0,
    /* ITF bInterfaceProtocol  */ HID_ITF_PROTOCOL_NONE,
    /* HID wDescriptorLength   */ sizeof(hidConsumerDesc),
    /* EP  bEndpointAddress    */ 0x82,
    /* EP  wMaxPacketSize      */ CFG_TUD_HID_EP_BUFSIZE,
    /* EP  bInterval (ms)      */ 10)};


const uint8_t* tud_descriptor_configuration_cb(uint8_t index)
{
    (void) index;
    return configurationDesc;
}


// String Descriptors
// ------------------

#define SERIAL_DIGITS  (2*PICO_UNIQUE_BOARD_ID_SIZE_BYTES)


#pragma pack(push, 1)

const struct { uint8_t length; uint8_t type; uint16_t string[1]; }
    languageString = { sizeof(languageString), TUSB_DESC_STRING,
        {0x0409} }; // US English

const struct { uint8_t length; uint8_t type; uint16_t string[7]; }
    manufactString = { sizeof(manufactString), TUSB_DESC_STRING,
        {'s','e','v','.','d','e','v'} };

const struct { uint8_t length; uint8_t type; uint16_t string[15]; }
    productString = { sizeof(productString), TUSB_DESC_STRING,
        {'C','h','r','u','m','m',' ','k','e','y','b','o','a','r','d'} };

uint16_t serialString[SERIAL_DIGITS + 1] = {
    TUSB_DESC_STRING<<8 | sizeof(serialString) };

#pragma pack(pop)


const uint16_t* tud_descriptor_string_cb(uint8_t index, uint16_t lang)
{
    (void) lang;

    switch (index) {
        case 0: return (const uint16_t*) &languageString;
        case 1: return (const uint16_t*) &manufactString;
        case 2: return (const uint16_t*) &productString;
        case 3:
            char ascii[SERIAL_DIGITS + 1];
            pico_get_unique_board_id_string(ascii, sizeof(ascii));

            // Convert to UTF-16
            for(int i = 0; i < SERIAL_DIGITS; ++i)
                serialString[i+1] = ascii[i];

            return (const uint16_t*) &serialString;
        default: return NULL;
    }
}


// Device state
// ------------

void tud_suspend_cb(bool remote_wakeup_en)
{
    // TODO: Reduce power draw during suspend.
    //
    // According to the [USB spec] (7.2.3), suspended devices are
    // limited to a current of 0.5mA. If the device is a remote
    // wakeup source, it may draw up to 2.5mA during suspend.
    //
    // I don't know how to achieve this with the Pico and TinyUSB.
    // None of the example projects reduce power during suspend.
    // It does not seem possible to use the USB resume signal to
    // wake up from dormant mode. It does not seem possible to slow
    // down or pause the clocks without killing the USB connection.
    //
    // According to [USB in a NutShell], "[...] if you drain maybe 5mA
    // or even 10mA you should still be fine, bearing in mind that at
    // the end of the day, your device violates the USB specification."
    //
    // The current implementation draws about 8mA.
    //
    // [USB spec]: https://www.usb.org/document-library/usb-20-specification
    // [USB in a NutShell]: https://www.beyondlogic.org/usbnutshell/usb2.shtml

    (void) remote_wakeup_en;
    led_blink(0);
}

//void tud_mount_cb(void)  { }
//void tud_umount_cb(void) { }
//void tud_resume_cb(void) { }
