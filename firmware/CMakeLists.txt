cmake_minimum_required(VERSION 3.20)

# Pico SDK (before project)
include($ENV{PICO_SDK_PATH}/pico_sdk_init.cmake)

# Project
project(chrumm VERSION 1.0.2)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

# Source
add_executable(chrumm
    chrumm/encoder.c
    chrumm/hid.c
    chrumm/led.c
    chrumm/main.c
    chrumm/matrix.c
    chrumm/usb.c)
target_link_libraries(chrumm pico_stdlib pico_unique_id tinyusb_device)
target_include_directories(chrumm PRIVATE ${CMAKE_CURRENT_LIST_DIR})
target_compile_definitions(chrumm PRIVATE CFG_TUSB_CONFIG_FILE="chrumm/usb.h")

# Binary
pico_set_program_version(chrumm "${PROJECT_VERSION}")
pico_set_program_description(chrumm "Chrumm keyboard firmware")
pico_set_binary_type(chrumm copy_to_ram)
pico_add_extra_outputs(chrumm)

# Verbose compiler warnings
if(MSVC)
    target_compile_options(chrumm PRIVATE /W4 /WX)
else()
    target_compile_options(chrumm PRIVATE -Wall -Wextra -Werror)
endif()
