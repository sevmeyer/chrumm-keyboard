#include "chrumm/matrix.h"
#include "chrumm/config.h"
#include "chrumm/hid.h"
#include <pico/stdlib.h>


static_assert(MATRIX_DEBOUNCE_TICKS <= UINT8_MAX/2);

static const uint rowPins[MATRIX_ROWS] = MATRIX_ROW_PINS;
static const uint colPins[MATRIX_COLS] = MATRIX_COL_PINS;

static void debounce(uint key, bool signal);
static void report(uint key, bool signal);


void matrix_init()
{
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
    // The columns are set to GPIO_IN with pull-up and therefore
    // read 1 by default. All rows are set to 1. During the scan,
    // one row at a time is set to 0. If a switch is pressed,
    // the connected column is grounded and reads 0 as well.

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
    // The goal is to detect state changes in a noisy signal.
    // One byte is stored per switch. Its Least Significant bit
    // represents the next switch state. The remaining bits
    // represent a saturation counter. When the input is equal to
    // the LSb, the counter is incremented, otherwise decremented.
    // Once the saturation threshold is reached, we report a
    // state change, reset the counter, and invert the LSb.
    //
    // 1100000 00000000011111 111  Ideal signal
    // 1101000 00100000011011 111  Noisy signal
    // 0010123 00100000012123 000  Saturation counter (threshold = 3)
    // 0000000 11111111111111 000  Next switch state (!current state)
    // 0020246 11311111135357 000  State variable (saturation*2 + next)
    // ......0 .............1 ...  State change report
    //
    // Partially based on debounce.c by Kenneth A. Kuhn
    // https://www.kennethkuhn.com/electronics/debounce.c

    static uint8_t states[MATRIX_ROWS*MATRIX_COLS] = {0};
    uint8_t state = states[key];

    if (signal == state % 2)
        state += 2;
    else if (state >= 2)
        state -= 2;

    if (state >= MATRIX_DEBOUNCE_TICKS * 2) {
        report(key, signal);
        state = !signal;
    }

    states[key] = state;
}


static void report(uint key, bool signal)
{
    static const uint32_t layers[2][MATRIX_ROWS*MATRIX_COLS] = {
        MATRIX_MAIN_LAYER,
        MATRIX_FN_LAYER};

    static uint layer = 0;
    static uint fnTaps = 0;

    if (layers[0][key] == cFN || layers[1][key] == cFN) {
        if (signal) {
            // Reset layer unless there was a double tap.
            if (fnTaps != 2) layer = 0;
            if (fnTaps  > 2) fnTaps = 0;
        }
        else {
            layer = 1;
            fnTaps += 1;
        }
    }
    else if (signal) {
        // Remove both codes, because the layer could
        // have changed between key press and release.
        hid_remove(layers[0][key]);
        hid_remove(layers[1][key]);
    }
    else {
        hid_add(layers[layer][key]);
        fnTaps = 0;
    }
}
