__author__ = 'RoGeorge'
#
# TODO: Add command line parameters for a specified stop time or a specified logging duration
# TODO: Port for Linux
# TODO: Add GUI
# TODO: Create versioned executable distributions
#
from time import *
import os
import sys
from msvcrt import kbhit, getch

from functions import connect_verify

# Update the next lines for your own default settings:
logInterval = 1
IP_DP832 = "192.168.188.37"
savePath = "csvLog/"
haveMultipleDP832s = False

# CSV data format
csvHeader = "YYYY-MM-DD,HH:MM:SS,CH1(V),CH1(A),CH1(W),CH2(V),CH2(A),CH2(W),CH3(V),CH3(A),CH3(W)"

# Rigol/LXI specific constants
port = 5555

maxWaitForAnswer = 1

# Constants for field index of the instrument answer at a *IDN? command
COMPANY = 0
MODEL = 1
SERIAL = 2

# Print usage
def print_help():
    print()
    print("This program periodically reads the measured output values")
    print("    for all 3 channels of a Rigol DP832 power source.")
    print()
    print("    The reading time interval (in seconds) can be specified")
    print("    in the command line. A timestamp is added for each new reading.")
    print()
    print("    At each new reading, the Voltage, Current and Power for each channel")
    print("    are listed in CSV format, then saved in a log file. The log file")
    print("    is saved as 'MODEL_YYYY-MM-DD_HH.MM.SS.csv'")
    print()
    print("The program is using LXI protocol, so the computer")
    print("    must have LAN connection with the DP832 instrument.")
    print("    USB and/or GPIB connections are not used by this software.")
    print()
    print("    No VISA, IVI or Rigol drivers are needed.")
    print()
    print("Usage syntax:")
    print("    " + "python " + scriptName + " [read_interval [instrument_IP]]")
    print()
    print("Usage examples:")
    print("    " + "python " + scriptName + "                   # log outputs (1s, 192.168.1.4)")
    print("    " + "python " + scriptName + " 60                # log at each minute (192.168.1.4)")
    print("    " + "python " + scriptName + " 3600 192.168.1.7  # log hourly from IP 192.168.1.7")
    print()
    print("To end the logging, press 'ESC'.")
    print()
    print()
    print()


# Check command line parameter(s)
scriptName = os.path.basename(sys.argv[0])

# Read/verify logging interval
if len(sys.argv) == 1:
    print_help()
else:
    try:
        logInterval = int(sys.argv[1])
    except Exception:
        print_help()
        print('ERROR!!! command line argument "' + sys.argv[1] + '" is not a valid time interval.')
        sys.exit("ERROR")

    if logInterval == 0:
        print_help()
        print('ERROR!!! command line argument "' + sys.argv[1] + '" is not a valid time interval.')
        sys.exit("ERROR")

# Read/verify logging instrument IP
if len(sys.argv) == 3:
    isError = False
    IP_DP832 = sys.argv[2]
    ipNumbers = IP_DP832.split(".")

    if len(ipNumbers) != 4:
        isError = True

    for i in range(4):
        if not ipNumbers[i].isdigit():
            isError = True
            break
        if ipNumbers[i].count(",") > 0:
            isError = True
            break
        if not (0 <= int(ipNumbers[i]) <= 255):
            isError = True
            break

    if int(ipNumbers[0]) == 0:
        isError = True

    if isError:
        print_help()
        print('ERROR!!! command line argument "' + sys.argv[2] + '" is not a valid IPv4 address.')
        sys.exit("ERROR")

# Connect and check instruments
print(connect_verify("power supply", IP_DP832, port))
telnetToInstrument, idFields = connect_verify("power supply", IP_DP832, port)

fileName = savePath + idFields[MODEL] + "_" + strftime("%Y-%m-%d_%H.%M.%S", localtime())
if haveMultipleDP832s:
    fileName += "_" + idFields[SERIAL]
fileName += ".csv"

print()
print('Logging values in file "' + fileName + '":')
csvFile = open(fileName, "a")
csvFile.write(csvHeader + '\n')
csvFile.close()
print()
print(csvHeader)

# Logging loop
while True:
    t1 = time()
    timeString = strftime("%Y-%m-%d,%H:%M:%S", localtime(t1))
    csvLine = timeString

    # Read DP832 Channel 1
    telnetToInstrument.write(b":MEAS:ALL? CH1")
    buff = telnetToInstrument.read_until("\n", maxWaitForAnswer)
    csvLine += "," + buff[:-1].decode()

    # Read DP832 Channel 2
    telnetToInstrument.write(b":MEAS:ALL? CH2")
    buff = telnetToInstrument.read_until(b"\n", maxWaitForAnswer)
    csvLine += "," + buff[:-1].decode()

    # Read DP832 Channel 3
    telnetToInstrument.write(b":MEAS:ALL? CH3")
    buff = telnetToInstrument.read_until(b"\n", maxWaitForAnswer)
    csvLine += "," + buff[:-1].decode()

    csvFile = open(fileName, "a")
    csvFile.write(csvLine + '\n')
    csvFile.close()
    print(csvLine)

    # read pressed key without waiting http://code.activestate.com/recipes/197140/
    if kbhit():                         # Key pressed?
        key = ord(getch())              # get first byte of keyscan code
        if key == 0 or key == 224:      # is it a function key? (0 for F1..n, 224 for arrows & others)
            key = ord(getch())          # read second byte of key scan code
    else:
        key = 0

    if key == 27:   # exit if ESC pressed
        break

    # Wait for the specified logging time interval
    t2 = time()
    if t2-t1 > 1:
        sleep(t2-t1-1)

    t2 = time()
    while t2-t1 < logInterval:
        t2 = time()

# Close telnet sessions and exit
telnetToInstrument.close()
print("Normal exit. Bye!")
