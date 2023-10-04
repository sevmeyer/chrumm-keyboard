#include "chrumm/led.h"
#include "chrumm/config.h"
#include <pico/stdlib.h>


static uint8_t blinkPattern = 0;
static uint8_t blinkIndex = 0;
static uint32_t blinkTicks = LED_BLINK_TICKS;


void led_init()
{
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
}


void led_tick()
{
    static bool blinkState = false;

    if (!blinkPattern && !blinkState)
        return;

    if (++blinkTicks < LED_BLINK_TICKS)
        return;

    blinkTicks = 0;
    blinkIndex = (blinkIndex + 1) & 0b111;
    blinkState = blinkPattern & (1u << blinkIndex);
    gpio_put(LED_PIN, blinkState);
}


void led_blink(uint8_t pattern)
{
    if (pattern == blinkPattern)
        return;

    blinkPattern = pattern;
    blinkTicks = LED_BLINK_TICKS;
    blinkIndex = 7;
}
