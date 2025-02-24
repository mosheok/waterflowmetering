#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import json
import boto3
import threading
import http.server
import urllib.parse



#Notes: 
#1. GPIO BOARD - This type of pin numbering refers to the number of the pin in the plug.
#2. GPIO BCM - The BCM option refers to the pin by “Broadcom SOC Channel. They signify 
#              the Broadcom SOC channel designation. The BCM channel changes as the version number changes.

configuration = {
    "PULSES_PER_LITER" : 574,
    "firstMeterInitial" : 1673.707
}


# Define the GPIO pin connected to the sensor
SENSOR_PIN1 = 24    # This is the BOARD pin number.
SENSOR_PIN2 = 23    # This is the BOARD pin number.
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
html_content = ""

def load_configuration(filepath):
    """
    Loads JSON data from a file into the global variable 'global_json_data'.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        bool: True if the JSON data was loaded successfully, False otherwise.
              Also sets the global variable 'global_json_data'.
    """
    global configuration  # Declare that we are using the global variable

    try:
        with open(filepath, 'r') as f:
            configuration = json.load(f)  # Load JSON data from the file
        return True  # Indicate successful loading

    except FileNotFoundError:
        print(f"Error: File not found at path: {filepath}")
        return False

    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file: {filepath}")
        return False

    except Exception as e:  # Catch any other potential errors
        print(f"An unexpected error occurred: {e}")
        return False



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

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    routes = {}  # Dictionary to store routes (path: function)

    @classmethod
    def add_route(cls, path, handler_function, content_type=None):
        """Decorator to add a route and its handler function, and content type."""
        cls.routes[path] = {'handler': handler_function, 'content_type': content_type}

    def do_GET(self):
        """Handles GET requests, including routing and parameter parsing."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        route_info = self.routes.get(path) # Get route info (handler and content_type)

        if route_info:
            handler = route_info['handler']
            content_type = route_info.get('content_type', 'application/json') # Default to json if not specified

            # Call the handler function, passing request and parameters
            response_data = handler(self, query_params)

            if response_data is not None:
                self.send_response(200) # HTTP OK
                self.send_header('Content-type', content_type) # Set content type from route info
                self.end_headers()
                if content_type is None or content_type == "application/json":
                    json_response = json.dumps(response_data).encode() # Convert to JSON and bytes
                else:
                    json_response = response_data.encode('utf-8') # Encode string to bytes for text-based content
                self.wfile.write(json_response)
            else:
                self.send_error(500, "Internal Server Error: Handler returned None") # Or handle differently

        else:
            self.send_error(404, "Not Found") # Path not found

def route(path, content_type=None):
    """Decorator to register a function as a route handler."""
    def decorator(func):
        SimpleHTTPRequestHandler.add_route(path, func, content_type)
        return func
    return decorator

# --- Define your route handler functions below, using the @route decorator ---

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



def report_to_cloud():
    global configuration
    global pulse_count1
    global pulse_count2
    global firstMeter
    global secondMeter
    try:
        intervalsCounter = 0
        cloudwatch  = create_cloudwatch_client("./aws-credentials.json")
        while True:
            # Wait for the specified interval
            time.sleep(INTERVAL)
            intervalsCounter += INTERVAL
            # dayCycleSeconds = intervalsCounter % 60
            # dayCycleMinutes = int(intervalsCounter / 60) % 60
            # dayCycleHours = int(intervalsCounter / 3600) % 25
            # if dayCycleHours ==24:
            #     dayCycleHours = 0
            #     intervalsCounter = 0

            firstMeter += ( pulse_count1 / configuration["PULSES_PER_LITER"] )
            secondMeter += ( pulse_count2 / configuration["PULSES_PER_LITER"] )
            
            # Publish metric to CloudWatch
            response = cloudwatch.put_metric_data(
                Namespace='WaterFlowMonitor',  # Choose a namespace for your metrics
                MetricData=[
                    {
                        'MetricName': 'FlowSensor',
                        'Dimensions': [
                            {'Name': 'SensorID', 'Value': 'sensor1'}  # Add dimensions if needed
                        ],
                        'Value': pulse_count1 / configuration["PULSES_PER_LITER"],
                        'Unit': 'Count/Second'  # Or specify a unit like 'Count', 'Seconds', etc.
                    },
                    {
                        'MetricName': 'FlowSensor',
                        'Dimensions': [
                            {'Name': 'SensorID', 'Value': 'sensor2'}  # Add dimensions if needed
                        ],
                        'Value': pulse_count2 / configuration["PULSES_PER_LITER"],
                        'Unit': 'Count/Second'  # Or specify a unit like 'Count', 'Seconds', etc.
                    },
                ]
            )

            # # Print the pulse count
            # #print(f"Pulses in {INTERVAL} seconds: {pulse_count1}")
            # #print(f"Liters measured from program start : {liters:.2f}")
            # print (f"{dayCycleHours:02}:{dayCycleMinutes:02}:{dayCycleSeconds:02} - 1st counter {pulse_count1}, 2nd counter {pulse_count2}")
            # print (f"{dayCycleHours:02}:{dayCycleMinutes:02}:{dayCycleSeconds:02} - 1st meter {firstMeter}, 2nd meter {secondMeter}")
            

            # Reset the pulse count for the next interval
            pulse_count1 = 0
            pulse_count2 = 0

    except KeyboardInterrupt:
        # Clean up GPIO on CTRL+C exit
        GPIO.cleanup()

@route("/setFirstMeter")
def set_first_meter(handler, params):
    global configuration
    global firstMeter
    if "value" not in params:
        return {"error": "missing parameter value"}

    try:
        ppl = int(params["value"][0])
        configuration["firstMeterInitial"] = ppl 
        firstMeter = ppl
        with open("./waterflowmeter.json", 'w') as f:
            json.dump(configuration, f, indent=4)

        return {"status": "success", "value": ppl}
    except Exception as e:
        return {"error": e}

@route("/setPPL")
def set_pulses_per_liter(handler, params):
    global configuration
    if "ppl" not in params:
        return {"error": "missing parameter ppl"}

    try:
        ppl = int(params["ppl"][0])
        configuration["PULSES_PER_LITER"] = ppl
        with open("./waterflowmeter.json", 'w') as f:
            json.dump(configuration, f, indent=4)

        return {"status": "success", "value": ppl}
    except Exception as e:
        return {"error": e}
    

@route('/sensor')
def sensor_handler(handler, params):
    global firstMeter
    global secondMeter
    if "sensor" in params:
        sensorId = params["sensor"][0]
        if sensorId == "1":
            return [{"sensorId": sensorId, "value": f"{firstMeter/1000:0.3f}"}]
        elif sensorId == "2":
            return [{"sensorId": sensorId, "value": f"{secondMeter/1000:0.3f}"}]

        return {"error": "No such sensor", "sensorId": sensorId}
    
    return [
     {"sensorId": "1", "value": f"{firstMeter/1000:0.2f}"},
     {"sensorId": "2", "value": f"{secondMeter/1000:0.2f}"},
     {"sensorId": "total", "value": f"{(secondMeter+firstMeter)/1000:0.3f}"}
    ]

@route('/sensors.html', "text/html")
def sensors_html_handler(handler, params):
    global html_content
    return html_content # Return the HTML content as a string

def main():
    global firstMeter
    global configuration

    load_configuration("./waterflowmeter.json")
    firstMeter = configuration["firstMeterInitial"]

    global html_content
    with open('niceSensors.html', 'r') as f:
            html_content = f.read()

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

    reporting_thread = threading.Thread(target=report_to_cloud)
    reporting_thread.start()

    port = 1234
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server started on port {port}")
    httpd.serve_forever()

    

if __name__ == "__main__":
  main()
