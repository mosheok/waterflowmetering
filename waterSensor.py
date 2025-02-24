#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

#Notes: 
#1. GPIO BOARD - This type of pin numbering refers to the number of the pin in the plug.
#2. GPIO BCM - The BCM option refers to the pin by “Broadcom SOC Channel. They signify 
#              the Broadcom SOC channel designation. The BCM channel changes as the version number changes.


# Define the GPIO pin connected to the sensor
SENSOR_PIN1 = 23    # This is the BOARD pin number.
SENSOR_PIN2 = 24    # This is the BOARD pin number.
LAST_S1Out = 27     # This is the BOARD pin number.
LAST_S2Out = 22     # This is the BOARD pin number.

# Define the time interval for pulse counting
INTERVAL = 1        # seconds

# Define a lower debounce time (e.g., 5 milliseconds)
DEBOUNCE_TIME = 1  # milliseconds

# Initialize pulse count
pulse_count1 = 0
pulse_count2 = 0
firstMeter = 0.0
secondMeter = 0.0
intervalsCounter = 0
dayCycleHours = 0
dayCycleMinutes = 0
dayCycleSeconds = 0
S1SigCurrVal = False
S2SigCurrVal = False



PULSES_PER_LITER = 574

# Callback function for GPIO pin edge detection
def count_pulse1(channel):
    global pulse_count1
    pulse_count1 += 1

# Callback function for GPIO pin edge detection
def count_pulse2(channel):
    global pulse_count2
    pulse_count2 += 1

# Function to handle pin state changes
def gpio_callback(channel):
    # global S1SigCurrVal
    # global S2SigCurrVal
    if GPIO.input(channel):     # The signal changed to HIGH.
        if channel == SENSOR_PIN1:   # This is the first sensor
            GPIO.output(LAST_S1Out,True)
            # S1SigCurrVal = True
        else:
            GPIO.output(LAST_S2Out,True)
            # S2SigCurrVal = True

    else:        # The signal changed to LOW
        if channel == SENSOR_PIN1:   # This is the first sensor.
            GPIO.output(LAST_S1Out,False)
            # S1SigCurrVal = False
        else:
            GPIO.output(LAST_S2Out,False)
            # S2SigCurrVal = False


# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SENSOR_PIN2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LAST_S1Out, GPIO.OUT)
GPIO.setup(LAST_S2Out, GPIO.OUT)
GPIO.output(LAST_S1Out,False)   # Initialize the LED (Will turn ON if Enabled.)
GPIO.output(LAST_S2Out,False)   # Initialize the LED (Will turn ON if Enabled.)

# Add event detection for rising edges on each sensor pin
GPIO.add_event_detect(SENSOR_PIN1, GPIO.BOTH, callback=gpio_callback, bouncetime=DEBOUNCE_TIME) 
GPIO.add_event_detect(SENSOR_PIN2, GPIO.BOTH, callback=gpio_callback, bouncetime=DEBOUNCE_TIME) 

try:
    while True:
        # Wait for the specified interval
        time.sleep(INTERVAL)
        # intervalsCounter += 1
        # dayCycleSeconds = intervalsCounter % 60
        # dayCycleMinutes = (intervalsCounter / 60) % 60
        # dayCycleHours = (intervalsCounter / 3600) % 24

        # firstMeter += ( pulse_count1 / PULSES_PER_LITER )
        # secondMeter += ( pulse_count2 / PULSES_PER_LITER )
        
        # # Print the pulse count
        # #print(f"Pulses in {INTERVAL} seconds: {pulse_count1}")
        # #print(f"Liters measured from program start : {liters:.2f}")
        # print (f"{dayCycleHours}:{dayCycleMinutes}:{dayCycleSeconds} - 1st counter {pulse_count1}, 2nd counter {pulse_count2}")
        # print (f"{dayCycleHours}:{dayCycleMinutes}:{dayCycleSeconds} - 1st meter {firstMeter}, 2nd meter {secondMeter}")
        

        # # Reset the pulse count for the next interval
        # pulse_count1 = 0
        # pulse_count2 = 0

except KeyboardInterrupt:
    # Clean up GPIO on CTRL+C exit
    GPIO.cleanup()