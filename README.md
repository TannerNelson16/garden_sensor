This Garden Sensor developed by Intellidwell is one of a kind. I wanted to develop something completely customizable that uses smart home standards. It was important to me that this unit be completely wireless and low power. The sensors on this unit will include the following:

* Soil Moisture Sensing

* Soil Temperature Sensing

* Light Sensing

* Air Temperature Sensing

* Air Humidity Sensing

The code is designed to allow the user to start up the device and connect to the device as an access point to setup credentials and configuration. When connected, the user will enter the info into the following fields:

* WiFi SSID

* WiFi Password

* MQTT IP Address

* MQTT Username

* MQTT Password

* Sleep Interval (in seconds)

* Minimum Update Interval (in cycles)

This information is then stored in memory to allow the device to sleep and wake without any need for reconfiguration.

The intent is that the user will place the device with the probes in the desired soil and allow it to take measurements. Those measurements are then published to an MQTT server (ideally Home Assistant with Mosquitto). And then, for example, wait 30 minutes until the next measurement is taken. Currently the code is designed not to reconnect to wifi or the MQTT server unless there is a change of 3% or more in soil moisture. This allows the device to monitor condition, but only update when changes are signifcant. I believe this design will conserve ample power.

Eventually I plan to design a PCB and waterproof housing for this unit, but this is my progress so far.
