EESchema Schematic File Version 2
LIBS:power
LIBS:device
LIBS:switches
LIBS:relays
LIBS:motors
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:connections-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Lamp LA?
U 1 1 5A13280B
P 6050 1850
F 0 "LA?" H 6075 2000 50  0000 L CNN
F 1 "Lamp" H 6075 1700 50  0000 L CNN
F 2 "" V 6050 1950 50  0001 C CNN
F 3 "" V 6050 1950 50  0001 C CNN
	1    6050 1850
	1    0    0    -1  
$EndComp
$Comp
L Lamp LA?
U 1 1 5A132856
P 6050 2400
F 0 "LA?" H 6075 2550 50  0000 L CNN
F 1 "Lamp" H 6075 2250 50  0000 L CNN
F 2 "" V 6050 2500 50  0001 C CNN
F 3 "" V 6050 2500 50  0001 C CNN
	1    6050 2400
	1    0    0    -1  
$EndComp
Wire Wire Line
	6050 2050 6050 2200
Text GLabel 6200 1450 2    60   Input ~ 0
lockstatus_open
Wire Wire Line
	6200 1450 6050 1450
Wire Wire Line
	6050 1450 6050 1650
Text GLabel 6200 2100 2    60   Input ~ 0
lockstatus_common
Wire Wire Line
	6200 2100 6050 2100
Connection ~ 6050 2100
Text GLabel 6250 2700 2    60   Input ~ 0
lockstatus_closed
Wire Wire Line
	6250 2700 6050 2700
Wire Wire Line
	6050 2700 6050 2600
$Comp
L L L?
U 1 1 5A132C2A
P 900 2900
F 0 "L?" V 850 2900 50  0000 C CNN
F 1 "L" V 975 2900 50  0000 C CNN
F 2 "" H 900 2900 50  0001 C CNN
F 3 "" H 900 2900 50  0001 C CNN
	1    900  2900
	1    0    0    -1  
$EndComp
$Comp
L SW_Push SW?
U 1 1 5A132C8B
P 2400 3000
F 0 "SW?" H 2450 3100 50  0000 L CNN
F 1 "SW_Push" H 2400 2940 50  0000 C CNN
F 2 "" H 2400 3200 50  0001 C CNN
F 3 "" H 2400 3200 50  0001 C CNN
	1    2400 3000
	0    -1   -1   0   
$EndComp
$Comp
L SW_Push SW?
U 1 1 5A132D12
P 2400 1900
F 0 "SW?" H 2450 2000 50  0000 L CNN
F 1 "SW_Push" H 2400 1840 50  0000 C CNN
F 2 "" H 2400 2100 50  0001 C CNN
F 3 "" H 2400 2100 50  0001 C CNN
	1    2400 1900
	0    -1   -1   0   
$EndComp
Wire Wire Line
	900  3150 900  3050
Text GLabel 2500 2250 2    60   Input ~ 0
openbutton_outside
Wire Wire Line
	2500 2250 2400 2250
Text GLabel 2500 3300 2    60   Input ~ 0
openbutton_inside
Wire Wire Line
	2500 3300 2400 3300
Wire Wire Line
	2400 2250 2400 2100
$Comp
L +24V #PWR?
U 1 1 5A133301
P 2400 1550
F 0 "#PWR?" H 2400 1400 50  0001 C CNN
F 1 "+24V" H 2400 1690 50  0000 C CNN
F 2 "" H 2400 1550 50  0001 C CNN
F 3 "" H 2400 1550 50  0001 C CNN
	1    2400 1550
	1    0    0    -1  
$EndComp
Wire Wire Line
	2400 1700 2400 1550
$Comp
L +24V #PWR?
U 1 1 5A133389
P 2400 2650
F 0 "#PWR?" H 2400 2500 50  0001 C CNN
F 1 "+24V" H 2400 2790 50  0000 C CNN
F 2 "" H 2400 2650 50  0001 C CNN
F 3 "" H 2400 2650 50  0001 C CNN
	1    2400 2650
	1    0    0    -1  
$EndComp
Wire Wire Line
	2400 2650 2400 2800
Wire Wire Line
	2400 3300 2400 3200
$Comp
L +24V #PWR?
U 1 1 5A133449
P 900 2700
F 0 "#PWR?" H 900 2550 50  0001 C CNN
F 1 "+24V" H 900 2840 50  0000 C CNN
F 2 "" H 900 2700 50  0001 C CNN
F 3 "" H 900 2700 50  0001 C CNN
	1    900  2700
	1    0    0    -1  
$EndComp
Wire Wire Line
	900  2750 900  2700
Text GLabel 1100 3150 2    60   Input ~ 0
lock
Wire Wire Line
	1100 3150 900  3150
$Comp
L SW_SPDT SW?
U 1 1 5A1337FA
P 950 2050
F 0 "SW?" H 950 2220 50  0000 C CNN
F 1 "SW_SPDT" H 950 1850 50  0000 C CNN
F 2 "" H 950 2050 50  0001 C CNN
F 3 "" H 950 2050 50  0001 C CNN
	1    950  2050
	0    1    -1   0   
$EndComp
$Comp
L +24V #PWR?
U 1 1 5A1339D3
P 850 1750
F 0 "#PWR?" H 850 1600 50  0001 C CNN
F 1 "+24V" H 850 1890 50  0000 C CNN
F 2 "" H 850 1750 50  0001 C CNN
F 3 "" H 850 1750 50  0001 C CNN
	1    850  1750
	1    0    0    -1  
$EndComp
Text GLabel 1150 2350 2    60   Input ~ 0
door_present
Wire Wire Line
	1150 2350 950  2350
Wire Wire Line
	950  2350 950  2250
Wire Wire Line
	850  1850 850  1750
$Comp
L SW_SPDT SW?
U 1 1 5A133CB7
P 5000 2900
F 0 "SW?" H 5000 3070 50  0000 C CNN
F 1 "SW_SPDT" H 5000 2700 50  0000 C CNN
F 2 "" H 5000 2900 50  0001 C CNN
F 3 "" H 5000 2900 50  0001 C CNN
	1    5000 2900
	0    1    1    0   
$EndComp
$Comp
L +24V #PWR?
U 1 1 5A133D7D
P 5000 2400
F 0 "#PWR?" H 5000 2250 50  0001 C CNN
F 1 "+24V" H 5000 2540 50  0000 C CNN
F 2 "" H 5000 2400 50  0001 C CNN
F 3 "" H 5000 2400 50  0001 C CNN
	1    5000 2400
	1    0    0    -1  
$EndComp
Wire Wire Line
	5000 2400 5000 2700
Text GLabel 5000 3400 2    60   Input ~ 0
holdbutton
Wire Wire Line
	5000 3400 4900 3400
Wire Wire Line
	4900 3400 4900 3100
$Comp
L R R?
U 1 1 5A13429C
P 4350 1700
F 0 "R?" V 4430 1700 50  0000 C CNN
F 1 "10k" V 4350 1700 50  0000 C CNN
F 2 "" V 4280 1700 50  0001 C CNN
F 3 "" H 4350 1700 50  0001 C CNN
	1    4350 1700
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR?
U 1 1 5A134317
P 4350 2000
F 0 "#PWR?" H 4350 1750 50  0001 C CNN
F 1 "GND" H 4350 1850 50  0000 C CNN
F 2 "" H 4350 2000 50  0001 C CNN
F 3 "" H 4350 2000 50  0001 C CNN
	1    4350 2000
	1    0    0    -1  
$EndComp
Wire Wire Line
	4350 2000 4350 1850
Text GLabel 4250 1400 0    60   Input ~ 0
dooropener
Wire Wire Line
	4250 1400 4350 1400
Wire Wire Line
	4350 1400 4350 1550
Wire Notes Line
	550  1250 7300 1250
Wire Notes Line
	2000 1250 2000 3500
Wire Notes Line
	550  1250 550  3500
Wire Notes Line
	550  3500 7300 3500
Wire Notes Line
	3600 3500 3600 1250
Wire Notes Line
	4650 3500 4650 1250
Wire Notes Line
	5650 3500 5650 1250
Wire Notes Line
	7300 3500 7300 1250
$EndSCHEMATC
