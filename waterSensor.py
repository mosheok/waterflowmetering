#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import json
import boto3

def create_cloudwatch_client(credentials_file):
    """
    Reads AWS credentials from a JSON file and creates a CloudWatch client.

    Args:
        credentials_file (str): Path to the JSON file containing the credentials.

    Returns:
        boto3.client: A CloudWatch client object.
    """

    with open(credentials_file, 'r') as f:
        credentials = json.load(f)

    access_key = credentials['accessKey']
    secret_key = credentials['secret']

    cloudwatch = boto3.client(
        'cloudwatch',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='il-central-1'  # Replace with your desired region
    )

    return cloudwatch




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
INTERVAL = 5        # seconds

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
# def gpio_callback(channel):
#     # global S1SigCurrVal
#     # global S2SigCurrVal
#     if GPIO.input(channel):     # The signal changed to HIGH.
#         if channel == SENSOR_PIN1:   # This is the first sensor
#             GPIO.output(LAST_S1Out,True)
#             # S1SigCurrVal = True
#         else:
#             GPIO.output(LAST_S2Out,True)
#             # S2SigCurrVal = True

#     else:        # The signal changed to LOW
#         if channel == SENSOR_PIN1:   # This is the first sensor.
#             GPIO.output(LAST_S1Out,False)
#             # S1SigCurrVal = False
#         else:
#             GPIO.output(LAST_S2Out,False)
#             # S2SigCurrVal = False


# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SENSOR_PIN2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LAST_S1Out, GPIO.OUT)
GPIO.setup(LAST_S2Out, GPIO.OUT)
GPIO.output(LAST_S1Out,False)   # Initialize the LED (Will turn ON if Enabled.)
GPIO.output(LAST_S2Out,False)   # Initialize the LED (Will turn ON if Enabled.)

# Add event detection for rising edges on each sensor pin
# GPIO.add_event_detect(SENSOR_PIN1, GPIO.BOTH, callback=gpio_callback, bouncetime=DEBOUNCE_TIME) 
# GPIO.add_event_detect(SENSOR_PIN2, GPIO.BOTH, callback=gpio_callback, bouncetime=DEBOUNCE_TIME) 
GPIO.add_event_detect(SENSOR_PIN1, GPIO.RISING, callback=count_pulse1, bouncetime=DEBOUNCE_TIME) 
GPIO.add_event_detect(SENSOR_PIN2, GPIO.RISING, callback=count_pulse2, bouncetime=DEBOUNCE_TIME) 

try:
    cloudwatch  = create_cloudwatch_client("./aws-credentials.json")
    while True:
        # Wait for the specified interval
        time.sleep(INTERVAL)
        intervalsCounter += INTERVAL
        dayCycleSeconds = intervalsCounter % 60
        dayCycleMinutes = int(intervalsCounter / 60) % 60
        dayCycleHours = int(intervalsCounter / 3600) % 25
        if dayCycleHours ==24:
            dayCycleHours = 0
            intervalsCounter = 0

        firstMeter += ( pulse_count1 / PULSES_PER_LITER )
        secondMeter += ( pulse_count2 / PULSES_PER_LITER )
        
        # Publish metric to CloudWatch
        response = cloudwatch.put_metric_data(
            Namespace='WaterFlowMonitor',  # Choose a namespace for your metrics
            MetricData=[
                {
                    'MetricName': 'FlowSensor',
                    'Dimensions': [
                        {'Name': 'SensorID', 'Value': 'sensor1'}  # Add dimensions if needed
                    ],
                    'Value': pulse_count1 / PULSES_PER_LITER,
                    'Unit': 'Count/Second'  # Or specify a unit like 'Count', 'Seconds', etc.
                },
                {
                    'MetricName': 'FlowSensor',
                    'Dimensions': [
                        {'Name': 'SensorID', 'Value': 'sensor2'}  # Add dimensions if needed
                    ],
                    'Value': pulse_count2 / PULSES_PER_LITER,
                    'Unit': 'Count/Second'  # Or specify a unit like 'Count', 'Seconds', etc.
                },
            ]
        )

        # Print the pulse count
        #print(f"Pulses in {INTERVAL} seconds: {pulse_count1}")
        #print(f"Liters measured from program start : {liters:.2f}")
        print (f"{dayCycleHours:02}:{dayCycleMinutes:02}:{dayCycleSeconds:02} - 1st counter {pulse_count1}, 2nd counter {pulse_count2}")
        print (f"{dayCycleHours:02}:{dayCycleMinutes:02}:{dayCycleSeconds:02} - 1st meter {firstMeter}, 2nd meter {secondMeter}")
        

        # Reset the pulse count for the next interval
        pulse_count1 = 0
        pulse_count2 = 0

except KeyboardInterrupt:
    # Clean up GPIO on CTRL+C exit
    GPIO.cleanup()