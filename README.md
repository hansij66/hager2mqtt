# Hager ECR380D MQTT
MQTT client for Hager ECR380D kWh/power meter. Written in Python 3.x
- Not all registers are implemented; adapt register.csv for your own needs
- Can be adapted for other Hager kWh meters, eg ECR180D.
- Use 190724_MODBUS_TABLE_FOR_ENERGY_METERS.XLS to adapt register.cv

## Usage:
* Copy `systemd/hager-mqtt.service` to `/etc/systemd/system`
* Adapt path in `hager-mqtt.service` to your install location (default: `/opt/iot/hager`)
* Copy `config.rename.py` to `config.py` and adapt for your configuration (minimal: mqtt ip, username, password)
* `sudo systemctl enable hager-mqtt`
* `sudo systemctl start hager-mqtt`

Use
http://mqtt-explorer.com/
to test & inspect MQTT messages

## Requirements
* paho-mqtt
* minimalmodbus
* pyserial
* python 3.x

Tested under Linux; there is no reason why it does not work under Windows.

## Licence
GPL v3

## Versions
1.0.0
* initial version
