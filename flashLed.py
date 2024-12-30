#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Use BCM GPIO numbering
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin connected to the LED
LED_PIN = 17

# Set the GPIO pin as output
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    while True:
        # Turn on the LED
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(1)

        # Turn off the LED
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(1)

except KeyboardInterrupt:
    # Clean up GPIO on CTRL+C exit
    GPIO.cleanup()