// Chrumm keyboard firmware
//   ___ _   _ ____  _   _ __  __ __  __
// .' __| |_| |  _ '| | | |  \/  |  \/  |
// | |__|  _  | |_) | |_| | |\/| | |\/| |
// '.___|_| |_|_| \_\.___.|_|  |_|_|  |_|
//
// Copyright 2023 Severin Meyer
// Licensed under CERN-OHL-W v2 or later

#include "chrumm/config.h"
#include "chrumm/encoder.h"
#include "chrumm/hid.h"
#include "chrumm/led.h"
#include "chrumm/matrix.h"

#include <tusb.h>
#include <hardware/clocks.h>
#include <hardware/watchdog.h>
#include <pico/stdlib.h>


int main()
{
    set_sys_clock_48mhz();
    clock_stop(clk_peri);
    clock_stop(clk_adc);
    clock_stop(clk_rtc);

    matrix_init();
    encoder_init();
    led_init();
    tud_init(0);

    watchdog_enable(WATCHDOG_TIMEOUT_MS, false);

    while (true) {
        absolute_time_t timeout = make_timeout_time_us(TICK_INTERVAL_US);

        matrix_tick();
        encoder_tick();
        hid_tick();
        led_tick();
        tud_task();
        watchdog_update();

        sleep_until(timeout);
    }
}
