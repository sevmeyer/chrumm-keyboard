#pragma once

#include "chrumm/usage.h"


// GPIO pins
// ---------

#define MATRIX_ROWS  5
#define MATRIX_COLS  13

#define MATRIX_ROW_PINS  { 2, 3, 4, 5, 8 }
#define MATRIX_COL_PINS  { 17, 18, 19, 20, 21, 22, 9, 10, 11, 12, 13, 14, 15 }

#define ENCODER_A_PIN  0
#define ENCODER_B_PIN  1

#define LED_PIN  25


// HID usage
// ---------

#define MATRIX_BASE_LAYER  {\
    kESC,   k1,     k2,     k3,     k4,     k5,     k6,     k7,     k8,     k9,     k0,     kMINUS, kEQUAL, \
    kTAB,   kQ,     kW,     kE,     kR,     kT,     kY,     kU,     kI,     kO,     kP,     kLBRAC, kRBRAC, \
    cFN,    kA,     kS,     kD,     kF,     kG,     kH,     kJ,     kK,     kL,     kCOLON, kQUOTE, kBKSL,  \
    kLSHFT, kZ,     kX,     kC,     kV,     kB,     kN,     kM,     kCOMMA, kDOT,   kSLASH, kUP,    kRSHFT, \
    kLCTRL, kNONE,  kLGUI,  kLALT,  kSPACE, kBKSP,  kENTER, kSPACE, kRALT,  kDEL,   kLEFT,  kDOWN,  kRIGHT  }

#define MATRIX_FN_LAYER  {\
    kTILDE, kF7,    kF8,    kF9,    kF10,   kF11,   kF12,   kp7,    kp8,    kp9,    kpSUB,  kBKSP,  kESC,   \
    kCAPLK, kF1,    kF2,    kF3,    kF4,    kF5,    kF6,    kp4,    kp5,    kp6,    kpADD,  kpLPAR, kpRPAR, \
    cFN,    cPLAY,  cPREV,  cPAUSE, cNEXT,  cSTOP,  kNONE,  kp1,    kp2,    kp3,    kpDIV,  kNONE,  kNONE,  \
    kLSHFT, kBOOT,  kNONE,  cCALC,  kNONE,  kMUTE,  kNUMLK, kp0,    kpDOT,  kpENT,  kpMUL,  kPGUP,  kRSHFT, \
    kLCTRL, kNONE,  kLGUI,  kLALT,  kSPACE, kBKSP,  kENTER, kSPACE, kRALT,  kINS,   kHOME,  kPGDN,  kEND    }

#define ENCODER_CW_USAGE   kVOLUP
#define ENCODER_CCW_USAGE  kVOLDN


// Timing
// ------

#define WATCHDOG_TIMEOUT_MS  100
#define PIN_SETTLE_TIME_US   10
#define TICK_INTERVAL_US     500

#define MATRIX_DEBOUNCE_TICKS   8
#define ENCODER_KEYPRESS_TICKS  30
#define LED_BLINK_TICKS         500

#define FN_KEY_TAPS    2
#define BOOT_KEY_TAPS  3
