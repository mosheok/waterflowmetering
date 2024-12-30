#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Define the GPIO pin connected to the sensor
SENSOR_PIN = 17

# Define the time interval for pulse counting
INTERVAL = 1  # seconds

# Define a lower debounce time (e.g., 5 milliseconds)
DEBOUNCE_TIME = 1  # milliseconds

# Initialize pulse count
pulse_count = 0
liters = 0.0

PULSES_PER_LITER = 574

# Callback function for GPIO pin edge detection
def count_pulse(channel):
    global pulse_count
    pulse_count += 1

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Add event detection for rising edges on the sensor pin
GPIO.add_event_detect(SENSOR_PIN, GPIO.RISING, callback=count_pulse, bouncetime=DEBOUNCE_TIME) 

try:
    while True:
        # Wait for the specified interval
        time.sleep(INTERVAL)

        liters += ( pulse_count / PULSES_PER_LITER )
        # Print the pulse count
        print(f"Pulses in {INTERVAL} seconds: {pulse_count}")
        print(f"Liters measured from program start : {liters:.2f}")

        # Reset the pulse count for the next interval
        pulse_count = 0

except KeyboardInterrupt:
    # Clean up GPIO on CTRL+C exit
    GPIO.cleanup()