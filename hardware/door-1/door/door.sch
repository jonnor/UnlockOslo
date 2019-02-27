EESchema Schematic File Version 4
EELAYER 26 0
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
L Relay:G6EU K1
U 1 1 5C75CFE7
P 6250 2550
F 0 "K1" H 6680 2596 50  0000 L CNN
F 1 "G6EU" H 6680 2505 50  0000 L CNN
F 2 "Relay_SMD:Relay_DPDT_Omron_G6H-2F" H 7380 2520 50  0001 C CNN
F 3 "https://www.omron.com/ecb/products/pdf/en-g6e.pdf" H 6250 2550 50  0001 C CNN
	1    6250 2550
	1    0    0    -1  
$EndComp
$Comp
L Relay:G6EU K2
U 1 1 5C75D031
P 7400 2550
F 0 "K2" H 7830 2596 50  0000 L CNN
F 1 "G6EU" H 7830 2505 50  0000 L CNN
F 2 "Relay_SMD:Relay_DPDT_Omron_G6H-2F" H 8530 2520 50  0001 C CNN
F 3 "https://www.omron.com/ecb/products/pdf/en-g6e.pdf" H 7400 2550 50  0001 C CNN
	1    7400 2550
	1    0    0    -1  
$EndComp
$Comp
L Relay:G6EU K3
U 1 1 5C75D071
P 8500 2550
F 0 "K3" H 8930 2596 50  0000 L CNN
F 1 "G6EU" H 8930 2505 50  0000 L CNN
F 2 "Relay_SMD:Relay_DPDT_Omron_G6H-2F" H 9630 2520 50  0001 C CNN
F 3 "https://www.omron.com/ecb/products/pdf/en-g6e.pdf" H 8500 2550 50  0001 C CNN
	1    8500 2550
	1    0    0    -1  
$EndComp
$Comp
L Connector_Generic:Conn_01x12 J1
U 1 1 5C75D32A
P 1450 3250
F 0 "J1" H 1370 2425 50  0000 C CNN
F 1 "Conn_01x12" H 1370 2516 50  0000 C CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-12_1x12_P5.00mm_Horizontal" H 1450 3250 50  0001 C CNN
F 3 "~" H 1450 3250 50  0001 C CNN
	1    1450 3250
	-1   0    0    1   
$EndComp
Text Notes 1300 2300 0    50   ~ 0
Inputs
$Comp
L Connector_Generic:Conn_01x09 J2
U 1 1 5C75D47B
P 3050 3150
F 0 "J2" H 3130 3192 50  0000 L CNN
F 1 "Conn_01x12" H 3130 3101 50  0000 L CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-9_1x09_P5.00mm_Horizontal" H 3050 3150 50  0001 C CNN
F 3 "~" H 3050 3150 50  0001 C CNN
	1    3050 3150
	1    0    0    -1  
$EndComp
Text Notes 2850 2350 0    50   ~ 0
Outputs
$Comp
L Connector_Generic:Conn_01x02 J3
U 1 1 5C75D985
P 3100 4050
F 0 "J3" H 3180 4042 50  0000 L CNN
F 1 "Conn_01x02" H 3180 3951 50  0000 L CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal" H 3100 4050 50  0001 C CNN
F 3 "~" H 3100 4050 50  0001 C CNN
	1    3100 4050
	1    0    0    -1  
$EndComp
Text Notes 2950 3900 0    50   ~ 0
Power
$Comp
L Mechanical:MountingHole H1
U 1 1 5C75E113
P 1200 5200
F 0 "H1" H 1300 5246 50  0000 L CNN
F 1 "MountingHole" H 1300 5155 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 1200 5200 50  0001 C CNN
F 3 "~" H 1200 5200 50  0001 C CNN
	1    1200 5200
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5C75E198
P 1200 5400
F 0 "H2" H 1300 5446 50  0000 L CNN
F 1 "MountingHole" H 1300 5355 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 1200 5400 50  0001 C CNN
F 3 "~" H 1200 5400 50  0001 C CNN
	1    1200 5400
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H3
U 1 1 5C75E1C4
P 1200 5600
F 0 "H3" H 1300 5646 50  0000 L CNN
F 1 "MountingHole" H 1300 5555 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 1200 5600 50  0001 C CNN
F 3 "~" H 1200 5600 50  0001 C CNN
	1    1200 5600
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H4
U 1 1 5C75E1F4
P 1200 5800
F 0 "H4" H 1300 5846 50  0000 L CNN
F 1 "MountingHole" H 1300 5755 50  0000 L CNN
F 2 "MountingHole:MountingHole_3.2mm_M3" H 1200 5800 50  0001 C CNN
F 3 "~" H 1200 5800 50  0001 C CNN
	1    1200 5800
	1    0    0    -1  
$EndComp
$EndSCHEMATC
