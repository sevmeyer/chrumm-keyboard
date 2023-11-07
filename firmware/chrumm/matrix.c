#include "chrumm/matrix.h"
#include "chrumm/config.h"
#include "chrumm/hid.h"
#include "chrumm/usage.h"
#include <pico/bootrom.h>
#include <pico/stdlib.h>


static_assert(MATRIX_DEBOUNCE_TICKS <= UINT8_MAX/2);

static const uint rowPins[MATRIX_ROWS] = MATRIX_ROW_PINS;
static const uint colPins[MATRIX_COLS] = MATRIX_COL_PINS;

static void debounce(uint key, bool signal);
static void report(uint key, bool signal);


void matrix_init()
{
    //                         Pullup
    //              Switch  .--[ R ]-- V+
    //       Diode  __|__   |
    // Row ---|<|---O   O---+--------- Column

    for (uint r = 0; r < MATRIX_ROWS; ++r) {
        const uint pin = rowPins[r];
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_OUT);
        gpio_put(pin, 1);
    }

    for (uint c = 0; c < MATRIX_COLS; ++c) {
        const uint pin = colPins[c];
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_IN);
        gpio_pull_up(pin);
    }
}


void matrix_tick()
{
    // The columns are pulled up and therefore read 1 by default.
    // All rows are set to 1. During the scan, one row at a time
    // is set to 0. If a switch is pressed, the connected column
    // is grounded and reads 0 as well.

    for (uint r = 0; r < MATRIX_ROWS; ++r) {
        gpio_put(rowPins[r], 0);
        sleep_us(PIN_SETTLE_TIME_US);

        for (uint c = 0; c < MATRIX_COLS; ++c) {
            const uint key = r*MATRIX_COLS + c;
            const bool signal = gpio_get(colPins[c]);
            debounce(key, signal);
        }

        gpio_put(rowPins[r], 1);
    }
}


static void debounce(uint key, bool signal)
{
    // EvenOdd debounce algorithm
    // Based on the integrator algorithm by Kenneth A. Kuhn
    // https://www.kennethkuhn.com/electronics/debounce.c
    //
    // The progress is maintained in one byte per switch.
    // The lowest bit represents the inverse of the current
    // switch state. It is inverted so that the starting
    // value is zero and can be auto-initalized in an array.
    // The remaining bits are used as a hysterisis counter.
    //
    // .-------------.-.
    // |7 6 5 4 3 2 1|0|
    // '-------------'-'
    // Hysterisis    Inverted
    // counter       switch state

    static uint8_t states[MATRIX_ROWS*MATRIX_COLS] = {0};
    uint8_t state = states[key];

    // The hysterisis counter reflects how often the signal
    // has matched the state bit in recent history. We add
    // or subtract a value of 2 to jump over the state bit.
    //             _
    //           _/ \_   _ Counter
    //     _   _/     \_/
    // ___/ \_/
    // ! ! = ! = = = ! ! = Signal

    if (signal == state % 2)
        state += 2;
    else if (state >= 2)
        state -= 2;

    // When the signal has fully saturated the counter,
    // we assume that the switch has flipped its state.
    // Thus we invert the state bit and reset the counter.

    if (state >= MATRIX_DEBOUNCE_TICKS * 2) {
        report(key, signal);
        state = !signal;
    }

    states[key] = state;
}


static void report(uint key, bool signal)
{
    static const uint32_t layers[2][MATRIX_ROWS*MATRIX_COLS] = {
        MATRIX_BASE_LAYER,
        MATRIX_FN_LAYER };

    static bool layer = 0;
    static uint fnTaps = 0;
    static uint bootTaps = 0;

    const uint32_t active = layers[layer][key];
    const uint32_t inactive = layers[!layer][key];

    if (active == cFN || inactive == cFN) {
        if (signal) {
            if (fnTaps != FN_KEY_TAPS) layer = 0;
            if (fnTaps > FN_KEY_TAPS) fnTaps = 0;
        }
        else {
            ++fnTaps;
            layer = 1;
        }
    }
    else if (signal) {
        // Remove both codes, because the layer could
        // have changed between key press and release.
        hid_remove(active);
        hid_remove(inactive);
    }
    else if (active == kBOOT) {
        if (++bootTaps >= BOOT_KEY_TAPS)
            reset_usb_boot(0, 0);
    }
    else {
        hid_add(active);
        fnTaps = 0;
        bootTaps = 0;
    }
}
