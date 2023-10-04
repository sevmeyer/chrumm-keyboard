#pragma once

#include <stdint.h>


void hid_tick();
void hid_add(uint32_t usage);
void hid_remove(uint32_t usage);
