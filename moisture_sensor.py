import machine
from machine import Pin, ADC
import network
import usocket
import time
from machine import Pin, ADC
from umqtt.simple import MQTTClient
import ujson
import gc
import ubinascii
import asyncio
import sys
import dht
import ntptime



print("Free memory before connecting to WiFi:", gc.mem_free())
global WIFI_SSID, WIFI_PASSWORD, MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, SLEEP_DURATION
# WiFi and MQTT Configuration
CONFIG_FILE = 'config.json'

MQTT_PORT = 1883
MQTT_CLIENT_ID = "esp32c3_moisture_sensor"

MQTT_TOPIC = "tele/sensor/moisture_sensor/state"
MQTT_LIGHT_TOPIC = "tele/sensor/light_sensor/state"
MQTT_AIR_TEMP_TOPIC = "tele/sensor/air_temp_sensor/state"
MQTT_HUMIDITY_TOPIC = "tele/sensor/humidity_sensor/state"

# Analog pin assignment
MOISTURE_SENSOR_PIN = 3
LIGHT_SENSOR_PIN = 2

#Power Pins
MOISTURE_PWR_PIN = 8
#LIGHT_PWR_PIN = 9

#LED pins
LED_PWR_PIN = 7
LED_BLUE_PIN = 6
LED_GREEN_PIN = 10


def connect_to_wifi(WIFI_SSID,WIFI_PASSWORD):
    global Connecting
    print(WIFI_SSID)
    print(WIFI_PASSWORD)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    LED_PWR = machine.Pin(LED_PWR_PIN, machine.Pin.OUT)
    LED_BLUE = machine.Pin(LED_BLUE_PIN, machine.Pin.OUT)
    LED_BLUE.value(0)
 #   if not wlan.isconnected():
    button_pin = machine.Pin(9, machine.Pin.IN)
    count = 0
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        button_press = button_pin.value()
        count = count + 1
        print("Connecting to WiFi...")
        LED_PWR.value(1)
        time.sleep(0.5)
        LED_PWR.value(0)
        time.sleep(0.5)
        if button_press == 0 or (count > 30 and not wlan.isconnected()):
            enter_configuration_mode()

    wifi_solid()
    print("Connected to WiFi:", wlan.ifconfig())
    
def disconnect_from_wifi():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        print("Disconnecting from WiFi...")
        wlan.disconnect()
        time.sleep(1)
    print("Disconnected from WiFi")

def connect_to_mqtt(MQTT_BROKER,MQTT_USERNAME,MQTT_PASSWORD):
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USERNAME, password=MQTT_PASSWORD)
    time.sleep(2)  # Add a short delay before connecting to MQTT
    client.connect()
    return client

def read_moisture():
    #ADC.width(ADC.WIDTH_9BIT)
    adc = ADC(Pin(MOISTURE_SENSOR_PIN))
    adc.init(atten=ADC.ATTN_11DB)
    moisture_value = adc.read()
    return moisture_value

def read_light():
    #ADC.width(ADC.WIDTH_9BIT)
    adc = ADC(Pin(LIGHT_SENSOR_PIN))
    adc.init(atten=ADC.ATTN_11DB)
    light_value = adc.read()
    return light_value

def publish_moisture(client, moisture_value):
    
    payload = {
        "moisture" : moisture_value
    }

    # Publish the message multiple times with short intervals
    for _ in range(2):
        client.publish(MQTT_TOPIC, ujson.dumps(payload).encode('utf-8'), retain=True)
        time.sleep(2.5)  # Adjust the delay as needed

    return payload

def publish_light(client, light_value):
    
    payload = {
        "light" : light_value
    }

    # Publish the message multiple times with short intervals
    for _ in range(2):
        client.publish(MQTT_LIGHT_TOPIC, ujson.dumps(payload).encode('utf-8'), retain=True)
        time.sleep(2.5)  # Adjust the delay as needed

    return payload

def publish_air_temp(client, air_temp):
    
    payload = {
        "temperature" : air_temp
    }

    # Publish the message multiple times with short intervals
    for _ in range(2):
        client.publish(MQTT_AIR_TEMP_TOPIC, ujson.dumps(payload).encode('utf-8'), retain=True)
        time.sleep(2.5)  # Adjust the delay as needed

    return payload


def publish_humidity(client, humidity):
    
    payload = {
        "humidity" : humidity
    }

    # Publish the message multiple times with short intervals
    for _ in range(2):
        client.publish(MQTT_HUMIDITY_TOPIC, ujson.dumps(payload).encode('utf-8'), retain=True)
        time.sleep(2.5)  # Adjust the delay as needed

    return payload

def wait_for_ack(client, expected_ack):
    # Wait for a response (acknowledgment) from the MQTT server
    timeout = 10  # Adjust the timeout as needed
    start_time = time.time()

    while time.time() - start_time < timeout:

        msg = client.check_msg()
        if msg:
            # Check if the received message is the expected acknowledgment
            if msg[1] == expected_ack:
                return True
    
    return False

def deep_sleep(duration):
    print("Going into deep sleep for {} seconds...".format(duration))
    machine.deepsleep(duration * 1000)

def publish_discovery(client):
    topic = "homeassistant/sensor/moisture_sensor/config"
    payload = {
        "name": "Moisture Sensor",
        "state_topic": "tele/sensor/moisture_sensor/state",
        "device_class": "moisture",
        "unit_of_measurement": "%",
        "unique_id" : "54839_moisture",
        "value_template":"{{ value_json.moisture}}",
        "device": {
            "identifiers": [
                "Garden-Sensor"
            ],
            "manufacturer" : "Intellidwell",
            "name" : "Garden Sensor",
            "model" : "garden-sensor-v1"
        },
        "platform": "mqtt"
    }
    client.publish(topic, ujson.dumps(payload).encode('utf-8'), retain=True)
    
def publish_light_discovery(client):
    topic = "homeassistant/sensor/light_sensor/config"
    payload = {
        "name": "Light Sensor",
        "state_topic": "tele/sensor/light_sensor/state",
        "icon":"mdi:sun-wireless",
        "unit_of_measurement": "%",
        "unique_id" : "54839_light",
        "value_template":"{{ value_json.light}}",
        "device": {
            "identifiers": [
                "Garden-Sensor"
            ],
            "manufacturer" : "Intellidwell",
            "name" : "Garden Sensor",
            "model" : "garden-sensor-v1"
        },
        "platform": "mqtt"
    }
    client.publish(topic, ujson.dumps(payload).encode('utf-8'), retain=True)
    
def publish_air_temp_discovery(client):
    topic = "homeassistant/sensor/air_temp_sensor/config"
    payload = {
        "name": "Air Temperature Sensor",
        "state_topic": "tele/sensor/air_temp_sensor/state",
        "device_class": "temperature",
        "unit_of_measurement": "°F",
        "unique_id" : "54839_air_temp",
        "value_template":"{{ value_json.temperature}}",
        "device": {
            "identifiers": [
                "Garden-Sensor"
            ],
            "manufacturer" : "Intellidwell",
            "name" : "Garden Sensor",
            "model" : "garden-sensor-v1"
        },
        "platform": "mqtt"
    }
    client.publish(topic, ujson.dumps(payload).encode('utf-8'), retain=True)
    
def publish_humidity_discovery(client):
    topic = "homeassistant/sensor/humidity_sensor/config"
    payload = {
        "name": "Humidity Sensor",
        "state_topic": "tele/sensor/humidity_sensor/state",
        "device_class": "humidity",
        "unit_of_measurement": "%",
        "unique_id" : "54839_humidity",
        "value_template":"{{ value_json.humidity}}",
        "device": {
            "identifiers": [
                "Garden-Sensor"
            ],
            "manufacturer" : "Intellidwell",
            "name" : "Garden Sensor",
            "model" : "garden-sensor-v1"
        },
        "platform": "mqtt"
    }
    client.publish(topic, ujson.dumps(payload).encode('utf-8'), retain=True)

def get_bootcount_prev():
    try:
        with open('boot_count_update.txt', 'r') as f:
            count = int(f.read())
    except OSError:
        count = 0
    return count

def save_boot_count(bootcount):
    count = bootcount
    with open('boot_count_update.txt', 'w') as f:
        f.write(str(count))
        
def get_boot_count():
    try:
        with open('boot_count.txt', 'r') as f:
            count = int(f.read())
    except OSError:
        count = 0
    return count

def increment_boot_count():
    count = get_boot_count() + 1
    with open('boot_count.txt', 'w') as f:
        f.write(str(count))
        
def reset_boot_count():
    with open('boot_count.txt', 'w') as f:
        f.write('0')

def get_prev():
    try:
        with open('moisture_prev.txt', 'r') as f:
            moisture_prev = float(f.read())
    except OSError:
        moisture_prev = 0
    return moisture_prev

def write_prev(moisture_prev):
    with open('moisture_prev.txt', 'w') as f:
        f.write(str(moisture_prev))
        
def get_prev_light():
    try:
        with open('light_prev.txt', 'r') as f:
            light_prev = float(f.read())
    except OSError:
        light_prev = 0
    return light_prev

def write_prev_light(light_prev):
    with open('light_prev.txt', 'w') as f:
        f.write(str(light_prev))
        
def get_prev_air_temp():
    try:
        with open('air_temp_prev.txt', 'r') as f:
            air_temp_prev = float(f.read())
    except OSError:
        air_temp_prev = 0
    return air_temp_prev

def write_prev_air_temp(air_temp_prev):
    with open('air_temp_prev.txt', 'w') as f:
        f.write(str(air_temp_prev))
        
def get_prev_humidity():
    try:
        with open('humidity_prev.txt', 'r') as f:
            humidity_prev = float(f.read())
    except OSError:
        humidity_prev = 0
    return humidity_prev

def write_prev_humidity(humidity_prev):
    with open('humidity_prev.txt', 'w') as f:
        f.write(str(humidity_prev))
        
        
# AP configuration

def enter_configuration_mode():
    # Disconnect from WiFi
    disconnect_from_wifi()
    
    # Create an Access Point for configuration
    ap_ssid = "Intellidwell_Garden_Sensor"
    #ap_ssid = "Mosby2"
    ap_password = "MyGarden12345"
    
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_ssid, password=ap_password)

    print("Configuration mode activated. Connect to AP:", ap_ssid, "with password:", ap_password)
    print("Visit http://192.168.4.1 in your web browser to configure.")

    # Serve the configuration page
    serve_configuration_page()

        
def serve_configuration_page():
    # HTML code for the configuration page
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>ESP32C3 Configuration</title>
</head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">

<body>
    <h2>ESP32C3 Configuration</h2>
    <form action="/configure" method="post">
        <label for="wifi_ssid">WiFi SSID:</label>
        <input type="text" id="wifi_ssid" name="wifi_ssid" required><br>

        <label for="wifi_password">WiFi Password:</label>
        <input type="password" id="wifi_password" name="wifi_password" required><br>

        <label for="mqtt_broker">MQTT Broker:</label>
        <input type="text" id="mqtt_broker" name="mqtt_broker" required><br>

        <label for="mqtt_username">MQTT Username:</label>
        <input type="text" id="mqtt_username" name="mqtt_username" required><br>

        <label for="mqtt_password">MQTT Password:</label>
        <input type="password" id="mqtt_password" name="mqtt_password" required><br>

        <label for="interval">Sleep Interval (seconds):</label>
        <input type="number" id="interval" name="interval" required><br>
        
        <label for="min_update">Minimum Update Interval (cycles):</label>
        <input type="number" id="min_update" name="min_update" required><br>

        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

    # Set up a simple web server using usocket
    addr = usocket.getaddrinfo('0.0.0.0', 80)[0][-1]
    server_socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    server_socket.bind(addr)
    server_socket.listen(5)

        
    print("Listening on", addr)
    LED_PWR = machine.Pin(LED_PWR_PIN, machine.Pin.OUT)
    LED_BLUE = machine.Pin(LED_BLUE_PIN, machine.Pin.OUT)
    LED_BLUE.value(0)
    LED_PWR.value(1)
    
    while True:
        client_socket, addr = server_socket.accept()
        print("Client connected from", addr)

        req = client_socket.recv(4096)
        if req:
            if req.find(b'POST /configure') != -1:
                # Handle form submission
                handle_configuration_submission(req, client_socket)
            else:
                # Serve the HTML page
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{}".format(
                    len(html_content), html_content)
                client_socket.sendall(response)
        client_socket.close()
        
def replace_all(text, dic):
    for i,j in dic.items():
        
        text = text.replace(i,j)
    return text

def handle_configuration_submission(req, client_socket):
    print("Received data (before decoding):", req)
    form_data = req.decode('utf-8').split('\r\n')[-1]
    form_data_dict = {}
    for pair in form_data.split("&"):
        key, value = pair.split("=")
        form_data_dict[key] = value

    # Use the entered values for configuration
    WIFI_SSID = form_data_dict.get("wifi_ssid", "")
    WIFI_PASSWORD = form_data_dict.get("wifi_password", "")
    MQTT_BROKER = form_data_dict.get("mqtt_broker", "")
    MQTT_USERNAME = form_data_dict.get("mqtt_username", "")
    MQTT_PASSWORD = form_data_dict.get("mqtt_password", "")
    SLEEP_DURATION = int(form_data_dict.get("interval", 0))
    min_update = int(form_data_dict.get("min_update",0))

    # Decode the MQTT password using the decode_url function
 #   MQTT_PASSWORD = decode_url(form_data_dict.get("mqtt_password", ""))
    
    # Update your existing configuration variables with the entered
    characters = {
      '%21': '!',  # !
      '%27': "'",  # '
      '%28': '(',  # (
      '%29': ')',  # )
      '%3A': ':',  # :
      '%3B': ';',  # ;
      '%40': '@',  # @
      '%26': '&',  # &
      '%3D': '=',  # =
      '%2B': '+',  # +
      '%24': '$',   # $
      }

    WIFI_PASSWORD = replace_all(WIFI_PASSWORD, characters)
    MQTT_PASSWORD = replace_all(MQTT_PASSWORD, characters)
    
    
    print("Configuration submitted successfully!")
    print("WiFi SSID:", WIFI_SSID)
    print("WiFi Password:", WIFI_PASSWORD)
    print("MQTT Broker:", MQTT_BROKER)
    print("MQTT Username:", MQTT_USERNAME)
    print("MQTT Password:", MQTT_PASSWORD)
    print("Sleep Interval:", SLEEP_DURATION)
    print("Minimum Update Interval:", min_update)
    
    
    save_config_to_file(WIFI_SSID,WIFI_PASSWORD,MQTT_BROKER,MQTT_USERNAME,MQTT_PASSWORD,SLEEP_DURATION,min_update)

    # Respond with a simple acknowledgment page
    acknowledgment = "Configuration submitted successfully!<br>Rebooting..."
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\n\r\n{}".format(
        len(acknowledgment), acknowledgment)
    client_socket.sendall(response)

    # Delay to allow the acknowledgment to be sent before rebooting
    time.sleep(2)
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    led_off()
    # Reboot the ESP32C3 to apply the new configuration

    machine.reset()

def save_config_to_file(WIFI_SSID,WIFI_PASSWORD,MQTT_BROKER,MQTT_USERNAME,MQTT_PASSWORD,SLEEP_DURATION,min_update):
    config_data = {
        "WIFI_SSID": WIFI_SSID,
        "WIFI_PASSWORD": WIFI_PASSWORD,
        "MQTT_BROKER": MQTT_BROKER,
        "MQTT_USERNAME": MQTT_USERNAME,
        "MQTT_PASSWORD": MQTT_PASSWORD,
        "SLEEP_DURATION": SLEEP_DURATION,
        "min_update": min_update,
    }

    with open(CONFIG_FILE, 'w') as f:
        ujson.dump(config_data, f)

def load_config_from_file():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = ujson.load(f)
            return config_data
    except (OSError, ValueError):
        return None
    
        
def wifi_solid():
    
    LED_PWR = machine.Pin(LED_PWR_PIN, machine.Pin.OUT)
    LED_GREEN = machine.Pin(LED_GREEN_PIN, machine.Pin.OUT)
    LED_BLUE = machine.Pin(LED_BLUE_PIN, machine.Pin.OUT)
    LED_BLUE.value(1)
    LED_GREEN.value(0)
    LED_PWR.value(1)
    
def led_off():
    
    LED_PWR = machine.Pin(LED_PWR_PIN, machine.Pin.OUT)
    LED_BLUE = machine.Pin(LED_BLUE_PIN, machine.Pin.OUT)
    LED_BLUE.value(0)
    LED_PWR.value(0)
    
    
def main():
    button_pin = machine.Pin(9, machine.Pin.IN)
    config_data = load_config_from_file()
    LED_PWR = machine.Pin(LED_PWR_PIN, machine.Pin.OUT)
    WIFI_SSID = config_data.get("WIFI_SSID", "")
    WIFI_PASSWORD = config_data.get("WIFI_PASSWORD", "")
    MQTT_BROKER = config_data.get("MQTT_BROKER", "")
    MQTT_USERNAME = config_data.get("MQTT_USERNAME", "")
    MQTT_PASSWORD = config_data.get("MQTT_PASSWORD", "")
    SLEEP_DURATION = config_data.get("SLEEP_DURATION", 0)
    
    print(WIFI_SSID)
    print(MQTT_BROKER)
    #reset_boot_count()

    # Retrieve and print the boot count
    boot_count = get_boot_count()
    print("Boot Count:", boot_count)
    print('Powering on sensors...')
    MOISTURE_PWR = machine.Pin(MOISTURE_PWR_PIN, machine.Pin.OUT)
    MOISTURE_PWR.value(1)
   # LIGHT_PWR = machine.Pin(LIGHT_PWR_PIN, machine.Pin.OUT)
    #LIGHT_PWR.value(1)
    time.sleep(10)
    button_press = button_pin.value()
    if button_press == 0:
            enter_configuration_mode()
    
    if boot_count < 1:
        connect_to_wifi()
        client = connect_to_mqtt()
        publish_discovery(client)
        
        initial_moisture = read_moisture()
        normalized_value = 1 - (initial_moisture / 4095)
        moisture_percentage_previous = round(normalized_value *100, 2)
        write_prev(moisture_percentage_previous)
    
    while True:
        
        moisture_percentage_previous = get_prev()
        print("Initial Moisture Value:", moisture_percentage_previous, " %")
        current_moisture = read_moisture()
        normalized_value = 1 - (current_moisture / 4095)
        
        # Moisture Calibration
        if normalized_value > 0.35:
            normalized_value = 1
        else:
            normalized_value = normalized_value*2.86
        moisture_percentage_current = round(normalized_value *100, 2)
        print("Current Moisture Value:", moisture_percentage_current, " %")
        
        
        # Light
        light_percentage_previous = get_prev_light()
        print("Initial Light Percentage:", light_percentage_previous, " %")
        current_light = read_light()
        normalized_light_value = current_light / 4095
        light_percentage_current = round(normalized_light_value *100, 2)
        print("Current Light Percentage:", light_percentage_current, " %")
        
        #Air Temp
        air_temp_previous = get_prev_air_temp()
        print("Initial Air Temperature: ", air_temp_previous, " °F")
        dht22sensor = dht.DHT22(Pin(4))
        dht22sensor.measure()
        air_temp_current = (dht22sensor.temperature() * (9/5) + 32)
        print("Current Air Temperature:", air_temp_current, " %")
        
        #Air Humidity
        humidity_previous = get_prev_humidity()
        print("Initial Humidity: ", humidity_previous, " %")
        #dht22sensor.measure()
        humidity_current = dht22sensor.humidity()
        print("Current Humidity:", humidity_current, " %")
        bootcount_prev = get_bootcount_prev()
        tracker = boot_count - bootcount_prev
        if tracker >= min_update or abs(moisture_percentage_current - moisture_percentage_previous) >= (3):
            print("Updating Server...")
            connect_to_wifi(WIFI_SSID,WIFI_PASSWORD)
            print(time.localtime())
            #ntptime.settime()
            #print(time.localtime())
            client = connect_to_mqtt(MQTT_BROKER,MQTT_USERNAME,MQTT_PASSWORD)
            
            #MQTT Moisture Messages
            publish_discovery(client)
            count = 0
            while True:
                print('Publishing moisture sensor discovery message to MQTT server...')
                count = count + 1
                LED_PWR.value(0)
                time.sleep(0.5)
                LED_PWR.value(1)
                time.sleep(0.5)
                if count > 3:
                    break
            print('Publishing moisture sensor value to MQTT server...')
            payload = publish_moisture(client, moisture_percentage_current)
            
            #MQTT Light Messages
            publish_light_discovery(client)
            count = 0
            while True:
                print('Publishing light sensor discovery message to MQTT server...')
                count = count + 1
                LED_PWR.value(0)
                time.sleep(0.5)
                LED_PWR.value(1)
                time.sleep(0.5)
                if count > 3:
                    break
            print('Publishing light sensor value to MQTT server...')
            payload = publish_light(client, light_percentage_current)
            
            #MQTT Air_Temp Messages
            publish_air_temp_discovery(client)
            count = 0
            while True:
                print('Publishing Air Temperature discovery message to MQTT server...')
                count = count + 1
                LED_PWR.value(0)
                time.sleep(0.5)
                LED_PWR.value(1)
                time.sleep(0.5)
                if count > 3:
                    break
            print('Publishing air temperature sensor value to MQTT server...')
            payload = publish_air_temp(client, air_temp_current)
            
            #MQTT Air_Hum Messages
            publish_humidity_discovery(client)
            count = 0
            while True:
                print('Publishing humidity sensor discovery message to MQTT server...')
                count = count + 1
                LED_PWR.value(0)
                time.sleep(0.5)
                LED_PWR.value(1)
                time.sleep(0.5)
                if count > 3:
                    break
            print('Publishing humidity sensor value to MQTT server...')
            payload = publish_humidity(client, humidity_current) 

            #Write sensor values to memory
            
            write_prev(moisture_percentage_current)
            write_prev_light(light_percentage_current)
            write_prev_air_temp(air_temp_current)
            write_prev_humidity(humidity_current)
            
            save_boot_count(boot_count)
            client.disconnect()
            disconnect_from_wifi()
        
        MOISTURE_PWR.value(0)
        #LIGHT_PWR.value(0)
        led_off()
        print('Powering off sensors...')
        #client.disconnect()
        #disconnect_from_wifi()
        increment_boot_count()
        deep_sleep(SLEEP_DURATION)
    
if __name__ == "__main__":
    main()
