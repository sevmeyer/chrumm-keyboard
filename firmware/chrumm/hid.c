#include "chrumm/hid.h"
#include "chrumm/led.h"
#include "chrumm/usb.h"
#include <tusb.h>


static uint8_t keycodes[6] = {0};
static uint8_t modifiers = 0;
static uint16_t consumer = 0;

static bool isKeyboardStale = false;
static bool isConsumerStale = false;

static void addKeycode(uint8_t code);
static void removeKeycode(uint8_t code);
static void addConsumer(uint16_t code);


// Device to host
// --------------

void hid_tick()
{
    if (isKeyboardStale && tud_hid_n_ready(ITF_KEYBOARD))
        isKeyboardStale = !tud_hid_n_keyboard_report(ITF_KEYBOARD, 0, modifiers, keycodes);

    if (isConsumerStale && tud_hid_n_ready(ITF_CONSUMER))
        isConsumerStale = !tud_hid_n_report(ITF_CONSUMER, 0, &consumer, 2);
}


void hid_add(uint32_t usage)
{
    if (tud_suspended()) {
        tud_remote_wakeup();
        return;
    }

    switch (usage >> 16) {
        case HID_USAGE_PAGE_KEYBOARD: addKeycode(usage);  break;
        case HID_USAGE_PAGE_CONSUMER: addConsumer(usage); break;
    }
}


void hid_remove(uint32_t usage)
{
    switch (usage >> 16) {
        case HID_USAGE_PAGE_KEYBOARD: removeKeycode(usage); break;
        case HID_USAGE_PAGE_CONSUMER: addConsumer(0);       break;
    }
}


static void addKeycode(uint8_t code)
{
    if (0xE0 <= code && code <= 0xE7) {
        const uint8_t old = modifiers;
        modifiers |= 1u << (code - 0xE0);
        isKeyboardStale = modifiers != old;
        return;
    }

    for (uint i = 0; i < 6; ++i) {
        if (keycodes[i] == code)
            return;
    }

    for (uint i = 0; i < 6; ++i) {
        if (keycodes[i] == 0) {
            keycodes[i] = code;
            isKeyboardStale = true;
            return;
        }
    }
}


static void removeKeycode(uint8_t code)
{
    if (code == 0)
        return;

    if (0xE0 <= code && code <= 0xE7) {
        const uint8_t old = modifiers;
        modifiers &= ~(1u << (code - 0xE0));
        isKeyboardStale = modifiers != old;
        return;
    }

    for (uint i = 0; i < 6; ++i) {
        if (keycodes[i] == code) {
            keycodes[i] = 0;
            isKeyboardStale = true;
            return;
        }
    }
}


static void addConsumer(uint16_t code)
{
    if (consumer == code)
        return;

    consumer = code;
    isConsumerStale = true;
}


uint16_t tud_hid_get_report_cb(uint8_t itf, uint8_t id, hid_report_type_t type, uint8_t* buffer, uint16_t size)
{
    // Send host a report via the Control pipe.
    // Irrelevant callback required by TinyUSB.
    (void) itf;
    (void) id;
    (void) type;
    (void) buffer;
    (void) size;
    return 0; // STALL
}


// Host to device
// --------------

void tud_hid_set_report_cb(uint8_t itf, uint8_t id, hid_report_type_t type, const uint8_t* buffer, uint16_t size)
{
    // Set keyboard LEDs
    if (itf == ITF_KEYBOARD && id == 0 && type == HID_REPORT_TYPE_OUTPUT && size == 1) {
        // Bit 4:Kana 3:Compose 2:ScrollLock 1:CapsLock 0:NumLock
        switch (buffer[0] & 0b11) {
            case 0b00: led_blink(0b00000001); break;
            case 0b01: led_blink(0b00000000); break;
            case 0b10: led_blink(0b11111110); break;
            case 0b11: led_blink(0b11111111); break;
        }
    }
}
