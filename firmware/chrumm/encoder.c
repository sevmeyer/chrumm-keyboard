#include "chrumm/encoder.h"
#include "chrumm/config.h"
#include "chrumm/hid.h"
#include "chrumm/usage.h"
#include <pico/stdlib.h>


#if defined(ENCODER_A_PIN) && defined(ENCODER_B_PIN)

static void report(uint32_t usage);


void encoder_init()
{
    gpio_init(ENCODER_A_PIN);
    gpio_set_dir(ENCODER_A_PIN, GPIO_IN);
    gpio_pull_up(ENCODER_A_PIN);

    gpio_init(ENCODER_B_PIN);
    gpio_set_dir(ENCODER_B_PIN, GPIO_IN);
    gpio_pull_up(ENCODER_B_PIN);
}


void encoder_tick()
{
    // The signal is decoded with a simple state machine,
    // using a lookup table to determine the next state.
    // Rotation events are only reported if the signal goes
    // through the correct sequence of states. This filters out
    // contact bounces, without the need for extra hardware.
    //
    // EC11 quadrature signal
    //
    // _|_  |   |  _|___ A pin
    //  | \_|___|_/ |
    // _|___|_  |   |  _ B pin
    //  |   | \_|___|_/
    // 11  01  00  10    AB
    //
    // Signal state machine
    //
    // .---. <-01.---. <-00.---. <-10.---.01-> .---.00-> .---.10-> .---.
    // |001|     |000|     |010|     |   |     |101|     |100|     |110|
    // '---'00-> '---'10-> '---'11-> |011| <-11'---' <-01'---' <-00'---'
    // 11                            |   |                            11
    // '-------------CCW EVENT-----> '---' <-----CW EVENT--------------'

    static const uint8_t next[28] = {
        0b000, 0b001, 0b010, 0b000,  // 000AB
        0b000, 0b001, 0b001, 0b011,  // 001AB
        0b000, 0b010, 0b010, 0b011,  // 010AB
        0b011, 0b101, 0b010, 0b011,  // 011AB
        0b100, 0b101, 0b110, 0b100,  // 100AB
        0b100, 0b101, 0b101, 0b011,  // 101AB
        0b100, 0b110, 0b110, 0b011}; // 110AB

    static uint8_t state = 0b011;
    state = state<<1 | gpio_get(ENCODER_A_PIN);
    state = state<<1 | gpio_get(ENCODER_B_PIN);

    switch (state) {
        case 0b00111: report(ENCODER_CCW_USAGE); break;
        case 0b11011: report(ENCODER_CW_USAGE);  break;
        default:      report(kNONE);             break;
    }

    state = next[state];
}


static void report(uint32_t usage)
{
    static uint32_t current = kNONE;
    static uint32_t timeout = 0;

    if (timeout)
        --timeout;
    else {
        if (current != kNONE) {
            hid_remove(current);
            current = kNONE;
        }
        if (usage != kNONE) {
            hid_add(usage);
            current = usage;
            timeout = ENCODER_KEYPRESS_TICKS;
        }
    }
}

#else

void encoder_init() {}
void encoder_tick() {}

#endif
