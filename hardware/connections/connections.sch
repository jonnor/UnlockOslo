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
P 850 2000
F 0 "LA?" H 875 2150 50  0000 L CNN
F 1 "Lamp" H 875 1850 50  0000 L CNN
F 2 "" V 850 2100 50  0001 C CNN
F 3 "" V 850 2100 50  0001 C CNN
	1    850  2000
	1    0    0    -1  
$EndComp
$Comp
L Lamp LA?
U 1 1 5A132856
P 850 2550
F 0 "LA?" H 875 2700 50  0000 L CNN
F 1 "Lamp" H 875 2400 50  0000 L CNN
F 2 "" V 850 2650 50  0001 C CNN
F 3 "" V 850 2650 50  0001 C CNN
	1    850  2550
	1    0    0    -1  
$EndComp
Wire Wire Line
	850  2200 850  2250
Wire Wire Line
	850  2250 850  2350
$Comp
L Conn_02x12_Top_Bottom J?
U 1 1 5A1328C2
P 4500 1950
F 0 "J?" H 4550 2550 50  0000 C CNN
F 1 "Conn_02x12_Top_Bottom" H 4550 1250 50  0000 C CNN
F 2 "" H 4500 1950 50  0001 C CNN
F 3 "" H 4500 1950 50  0001 C CNN
	1    4500 1950
	1    0    0    -1  
$EndComp
Text GLabel 1000 1600 2    60   Input ~ 0
lockstatus_open
Wire Wire Line
	1000 1600 850  1600
Wire Wire Line
	850  1600 850  1800
Text GLabel 1000 2250 2    60   Input ~ 0
lockstatus_common
Wire Wire Line
	1000 2250 850  2250
Connection ~ 850  2250
Text GLabel 1050 2850 2    60   Input ~ 0
lockstatus_closed
Wire Wire Line
	1050 2850 850  2850
Wire Wire Line
	850  2850 850  2750
$Comp
L L L?
U 1 1 5A132C2A
P 2350 2850
F 0 "L?" V 2300 2850 50  0000 C CNN
F 1 "L" V 2425 2850 50  0000 C CNN
F 2 "" H 2350 2850 50  0001 C CNN
F 3 "" H 2350 2850 50  0001 C CNN
	1    2350 2850
	1    0    0    -1  
$EndComp
$Comp
L SW_Push SW?
U 1 1 5A132C8B
P 1000 5600
F 0 "SW?" H 1050 5700 50  0000 L CNN
F 1 "SW_Push" H 1000 5540 50  0000 C CNN
F 2 "" H 1000 5800 50  0001 C CNN
F 3 "" H 1000 5800 50  0001 C CNN
	1    1000 5600
	0    -1   -1   0   
$EndComp
$Comp
L SW_Push SW?
U 1 1 5A132D12
P 1000 4500
F 0 "SW?" H 1050 4600 50  0000 L CNN
F 1 "SW_Push" H 1000 4440 50  0000 C CNN
F 2 "" H 1000 4700 50  0001 C CNN
F 3 "" H 1000 4700 50  0001 C CNN
	1    1000 4500
	0    -1   -1   0   
$EndComp
Wire Wire Line
	2350 3100 2350 3000
Text GLabel 1100 4850 2    60   Input ~ 0
openbutton_outside
Wire Wire Line
	1100 4850 1000 4850
Text GLabel 1100 5900 2    60   Input ~ 0
openbutton_inside
Wire Wire Line
	1100 5900 1000 5900
Wire Wire Line
	1000 4850 1000 4700
$Comp
L +24V #PWR?
U 1 1 5A133301
P 1000 4150
F 0 "#PWR?" H 1000 4000 50  0001 C CNN
F 1 "+24V" H 1000 4290 50  0000 C CNN
F 2 "" H 1000 4150 50  0001 C CNN
F 3 "" H 1000 4150 50  0001 C CNN
	1    1000 4150
	1    0    0    -1  
$EndComp
Wire Wire Line
	1000 4300 1000 4150
$Comp
L +24V #PWR?
U 1 1 5A133389
P 1000 5250
F 0 "#PWR?" H 1000 5100 50  0001 C CNN
F 1 "+24V" H 1000 5390 50  0000 C CNN
F 2 "" H 1000 5250 50  0001 C CNN
F 3 "" H 1000 5250 50  0001 C CNN
	1    1000 5250
	1    0    0    -1  
$EndComp
Wire Wire Line
	1000 5250 1000 5400
Wire Wire Line
	1000 5900 1000 5800
$Comp
L +24V #PWR?
U 1 1 5A133449
P 2350 2650
F 0 "#PWR?" H 2350 2500 50  0001 C CNN
F 1 "+24V" H 2350 2790 50  0000 C CNN
F 2 "" H 2350 2650 50  0001 C CNN
F 3 "" H 2350 2650 50  0001 C CNN
	1    2350 2650
	1    0    0    -1  
$EndComp
Wire Wire Line
	2350 2700 2350 2650
Text GLabel 2550 3100 2    60   Input ~ 0
lock
Wire Wire Line
	2550 3100 2350 3100
$Comp
L SW_SPDT SW?
U 1 1 5A1337FA
P 2400 2000
F 0 "SW?" H 2400 2170 50  0000 C CNN
F 1 "SW_SPDT" H 2400 1800 50  0000 C CNN
F 2 "" H 2400 2000 50  0001 C CNN
F 3 "" H 2400 2000 50  0001 C CNN
	1    2400 2000
	0    1    -1   0   
$EndComp
$Comp
L +24V #PWR?
U 1 1 5A1339D3
P 2300 1700
F 0 "#PWR?" H 2300 1550 50  0001 C CNN
F 1 "+24V" H 2300 1840 50  0000 C CNN
F 2 "" H 2300 1700 50  0001 C CNN
F 3 "" H 2300 1700 50  0001 C CNN
	1    2300 1700
	1    0    0    -1  
$EndComp
Text GLabel 2600 2300 2    60   Input ~ 0
door_present
Wire Wire Line
	2600 2300 2400 2300
Wire Wire Line
	2400 2300 2400 2200
Wire Wire Line
	2300 1800 2300 1700
$Comp
L SW_SPDT SW?
U 1 1 5A133CB7
P 2500 5650
F 0 "SW?" H 2500 5820 50  0000 C CNN
F 1 "SW_SPDT" H 2500 5450 50  0000 C CNN
F 2 "" H 2500 5650 50  0001 C CNN
F 3 "" H 2500 5650 50  0001 C CNN
	1    2500 5650
	0    1    1    0   
$EndComp
$Comp
L +24V #PWR?
U 1 1 5A133D7D
P 2500 5150
F 0 "#PWR?" H 2500 5000 50  0001 C CNN
F 1 "+24V" H 2500 5290 50  0000 C CNN
F 2 "" H 2500 5150 50  0001 C CNN
F 3 "" H 2500 5150 50  0001 C CNN
	1    2500 5150
	1    0    0    -1  
$EndComp
Wire Wire Line
	2500 5150 2500 5450
Text GLabel 2500 6150 2    60   Input ~ 0
holdbutton
Wire Wire Line
	2500 6150 2400 6150
Wire Wire Line
	2400 6150 2400 5850
$Comp
L R R?
U 1 1 5A13429C
P 2500 4300
F 0 "R?" V 2580 4300 50  0000 C CNN
F 1 "10k" V 2500 4300 50  0000 C CNN
F 2 "" V 2430 4300 50  0001 C CNN
F 3 "" H 2500 4300 50  0001 C CNN
	1    2500 4300
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR?
U 1 1 5A134317
P 2500 4600
F 0 "#PWR?" H 2500 4350 50  0001 C CNN
F 1 "GND" H 2500 4450 50  0000 C CNN
F 2 "" H 2500 4600 50  0001 C CNN
F 3 "" H 2500 4600 50  0001 C CNN
	1    2500 4600
	1    0    0    -1  
$EndComp
Wire Wire Line
	2500 4600 2500 4450
Text GLabel 2400 4000 0    60   Input ~ 0
dooropener
Wire Wire Line
	2400 4000 2500 4000
Wire Wire Line
	2500 4000 2500 4150
$EndSCHEMATC
