#pragma once

// HID Usage Tables for USB
// https://usb.org/document-library/hid-usage-tables-14


#define kBOOT  0x000000


// Keyboard Page (0x07)
// --------------------

#define kNONE  0x070000

#define kA     0x070004
#define kB     0x070005
#define kC     0x070006
#define kD     0x070007
#define kE     0x070008
#define kF     0x070009
#define kG     0x07000A
#define kH     0x07000B
#define kI     0x07000C
#define kJ     0x07000D
#define kK     0x07000E
#define kL     0x07000F
#define kM     0x070010
#define kN     0x070011
#define kO     0x070012
#define kP     0x070013
#define kQ     0x070014
#define kR     0x070015
#define kS     0x070016
#define kT     0x070017
#define kU     0x070018
#define kV     0x070019
#define kW     0x07001A
#define kX     0x07001B
#define kY     0x07001C
#define kZ     0x07001D
#define k1     0x07001E
#define k2     0x07001F
#define k3     0x070020
#define k4     0x070021
#define k5     0x070022
#define k6     0x070023
#define k7     0x070024
#define k8     0x070025
#define k9     0x070026
#define k0     0x070027

#define kENTER 0x070028
#define kESC   0x070029
#define kBKSP  0x07002A
#define kTAB   0x07002B
#define kSPACE 0x07002C
#define kMINUS 0x07002D
#define kEQUAL 0x07002E
#define kLBRAC 0x07002F
#define kRBRAC 0x070030
#define kBKSL  0x070031
#define kRISO  0x070032
#define kCOLON 0x070033
#define kQUOTE 0x070034
#define kTILDE 0x070035
#define kCOMMA 0x070036
#define kDOT   0x070037
#define kSLASH 0x070038
#define kCAPLK 0x070039

#define kF1    0x07003A
#define kF2    0x07003B
#define kF3    0x07003C
#define kF4    0x07003D
#define kF5    0x07003E
#define kF6    0x07003F
#define kF7    0x070040
#define kF8    0x070041
#define kF9    0x070042
#define kF10   0x070043
#define kF11   0x070044
#define kF12   0x070045

#define kPRINT 0x070046
#define kSCRLK 0x070047
#define kPAUSE 0x070048
#define kINS   0x070049
#define kHOME  0x07004A
#define kPGUP  0x07004B
#define kDEL   0x07004C
#define kEND   0x07004D
#define kPGDN  0x07004E
#define kRIGHT 0x07004F
#define kLEFT  0x070050
#define kDOWN  0x070051
#define kUP    0x070052

#define kNUMLK 0x070053
#define kpDIV  0x070054
#define kpMUL  0x070055
#define kpSUB  0x070056
#define kpADD  0x070057
#define kpENT  0x070058
#define kp1    0x070059
#define kp2    0x07005A
#define kp3    0x07005B
#define kp4    0x07005C
#define kp5    0x07005D
#define kp6    0x07005E
#define kp7    0x07005F
#define kp8    0x070060
#define kp9    0x070061
#define kp0    0x070062
#define kpDOT  0x070063

#define kLISO  0x070064
#define kAPP   0x070065
#define kPOWER 0x070066
#define kpEQ   0x070067

#define kF13   0x070068
#define kF14   0x070069
#define kF15   0x07006A
#define kF16   0x07006B
#define kF17   0x07006C
#define kF18   0x07006D
#define kF19   0x07006E
#define kF20   0x07006F
#define kF21   0x070070
#define kF22   0x070071
#define kF23   0x070072
#define kF24   0x070073

#define kEXEC  0x070074
#define kHELP  0x070075
#define kMENU  0x070076
#define kSEL   0x070077
#define kSTOP  0x070078
#define kAGAIN 0x070079
#define kUNDO  0x07007A
#define kCUT   0x07007B
#define kCOPY  0x07007C
#define kPASTE 0x07007D
#define kFIND  0x07007E
#define kMUTE  0x07007F
#define kVOLUP 0x070080
#define kVOLDN 0x070081

#define kINT1  0x070087
#define kINT2  0x070088
#define kINT3  0x070089
#define kINT4  0x07008A
#define kINT5  0x07008B
#define kINT6  0x07008C
#define kINT7  0x07008D
#define kINT8  0x07008E
#define kINT9  0x07008F

#define kLANG1 0x070090
#define kLANG2 0x070091
#define kLANG3 0x070092
#define kLANG4 0x070093
#define kLANG5 0x070094
#define kLANG6 0x070095
#define kLANG7 0x070096
#define kLANG8 0x070097
#define kLANG9 0x070098

#define kpLPAR 0x0700B6
#define kpRPAR 0x0700B7

#define kLCTRL 0x0700E0
#define kLSHFT 0x0700E1
#define kLALT  0x0700E2
#define kLGUI  0x0700E3
#define kRCTRL 0x0700E4
#define kRSHFT 0x0700E5
#define kRALT  0x0700E6
#define kRGUI  0x0700E7


// Consumer Page (0x0C)
// --------------------

#define cNONE  0x0C0000
#define cFN    0x0C0097

// Multimedia
#define cPLAY  0x0C00B0
#define cPAUSE 0x0C00B1
#define cREC   0x0C00B2
#define cFFWD  0x0C00B3
#define cRWND  0x0C00B4
#define cNEXT  0x0C00B5
#define cPREV  0x0C00B6
#define cSTOP  0x0C00B7
#define cEJECT 0x0C00B8
#define cRANDM 0x0C00B9
#define cRPEAT 0x0C00BC
#define cMUTE  0x0C00E2
#define cVOLUP 0x0C00E9
#define cVOLDN 0x0C00EA

// Application Launch
#define cWORD  0x0C0184
#define cTEXT  0x0C0185
#define cSHEET 0x0C0186
#define cGRAPH 0x0C0187
#define cPRES  0x0C0188
#define cDATAB 0x0C0189
#define cEMAIL 0x0C018A
#define cNEWS  0x0C018B
#define cVOICE 0x0C018C
#define cADDR  0x0C018D
#define cCALEN 0x0C018E
#define cTASK  0x0C018F
#define cLOG   0x0C0190
#define cFIN   0x0C0191
#define cCALC  0x0C0192
#define cFILE  0x0C0194
#define cWWW   0x0C0196
#define cCHAT  0x0C0199
#define cLOGOF 0x0C019C
#define cLOCK  0x0C019E
#define cCTRL  0x0C019F
#define cHELP  0x0C01A6
#define cDOCS  0x0C01A7
#define cSPELL 0x0C01AB
#define cSCRSV 0x0C01B1
#define cIMG   0x0C01B6
#define cAUDIO 0x0C01B7
#define cVIDEO 0x0C01B8
#define cMSNGR 0x0C01BC
