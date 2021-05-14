#!/usr/bin/env python3
import paho.mqtt.client as paho
import time
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import struct
from threading import Thread
import json

global flag_version
global flag_config
global flag_command
flag_command = True
flag_config = True
flag_version = 0

global error_count, uid, config_reply
error_count = 0
uid = 0
config_reply = bytearray(b"")

mac = "mac"
url = "url"
rf_channel = 0

command = [b"\x00", b"\x01", b"\x02", b"\x03", b"\x04", b"\x05", b"\x06", b"\x09", b"\x0A", b"\x0B", b"\x0C"]
subscribing_voltage = ["main_voltage"]
subscribing_list_0 = ["error", "canopen_error", "log", "config_reply", "command_reply"]
subscribing_list_probe = ["/probe", "/probe_response"]

def setup_logger(name, log_file, level=logging.INFO):
    handler = RotatingFileHandler(log_file, maxBytes=1e8, backupCount=10)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)
    return logger


voltage_logger = setup_logger("main_voltage", "mqtt_main_voltage.log")
command_logger = setup_logger("command", "mqtt_command.log")
config_logger = setup_logger("config", "mqtt_config.log")
error_logger = setup_logger("error", "mqtt_error.log")


# log with timestamp
def log_with_time(logger_name, string):
    logger_name.info("{} {}".format(datetime.datetime.now().isoformat(), string))
    return


# define callback
def on_message(client, userdata, message):
    global flag_command
    global flag_config
    global flag_version
    global error_count
    global uid
    if message.topic == "/probe_response":
        temp = json.loads(message.payload.decode('iso-8859-1').encode('utf8'))
        if "serial-number" in temp and "\u00ff" in temp["serial-number"]:
            temp["serial-number"] = "not set yet"
        log_with_time(
            command_logger,
            "subscribed -> topic: {} | data: {}".format(
                message.topic, json.dumps(temp, indent=4, sort_keys=False)
            ),
        )
        flag_version = True
    elif message.topic == "/{}/main_voltage".format(mac):
        log_with_time(
            voltage_logger,
            "subscribed -> topic: {} | voltage: {:.6f}V".format(
                message.topic, struct.unpack("f", message.payload)[0]
            ),
        )
    elif message.topic == "/{}/command_reply".format(mac):
        if message.payload[0] <= 0x05:  # version info
            # deprecated, not used any more
            pass
        elif message.payload[0] == 0x09:  # emergency poweroff
            if message.payload[1] == 0x01 and message.payload[2] == 0x01:
                log_with_time(
                    command_logger,
                    "subscribed -> topic: {} | cmd: {} | data: {} | pos: {}".format(
                        message.topic,
                        message.payload[0:1].hex(),
                        message.payload[1:3].hex(),
                        message.payload[3:].hex(),
                    ),
                )
            else:
                log_with_time(
                    command_logger,
                    "subscribed error -> topic: {} | cmd: {} | data: {} | pos: {}".format(
                        message.topic,
                        message.payload[0:1].hex(),
                        message.payload[1:3].hex(),
                        message.payload[3:].hex(),
                    ),
                )
                error_count += 1
            flag_command = True
        elif message.payload[0] == 0x0C:  # set rf channel
            if message.payload[1] == rf_channel:
                log_with_time(
                    command_logger,
                    "subscribed -> topic: {} | cmd: {} | rf channel: {}".format(
                        message.topic, message.payload[0:1].hex(), message.payload[1:].hex()
                    ),
                )
            else:
                log_with_time(
                    command_logger,
                    "subscribed error -> topic: {} | cmd: {} | rf channel: {}".format(
                        message.topic, message.payload[0:1].hex(), message.payload[1:].hex()
                    ),
                )
                error_count += 1
            flag_command = True
        else:  # 06, 07, 08, 0A
            if message.payload[1] == 0x01:
                log_with_time(
                    command_logger,
                    "subscribed -> topic: {} | cmd: {} | data: {}".format(
                        message.topic, message.payload[0:1].hex(), message.payload[1:].hex()
                    ),
                )
            else:
                log_with_time(
                    command_logger,
                    "subscribed error -> topic: {} | cmd: {} | data: {}".format(
                        message.topic, message.payload[0:1].hex(), message.payload[1:].hex()
                    ),
                )
                error_count += 1
            flag_command = True
    elif message.topic == "/{}/canopen_error".format(mac):
        log_with_time(
            error_logger,
            "subscribed -> topic: {} | servo node: {} | error code: {}".format(
                message.topic, message.payload[0:1].hex(), message.payload[1:].hex()
            ),
        )
    elif message.topic == "/{}/error".format(mac):
        log_with_time(
            error_logger,
            "subscribed -> topic: {} | error code: {}".format(message.topic, message.payload.hex()),
        )
    elif message.topic == "/{}/config_reply".format(mac):
        if not flag_config:
            # read config, only compare first four bytes
            # write config, should compare full message
            index = 4 if config_reply[0] == 0x43 else 8
            if config_reply == message.payload[0:index]:
                log_with_time(
                    config_logger,
                    "subscribed -> topic: {} | data: {}".format(message.topic, message.payload.hex()),
                )
                if message.payload[2] == 0x30:
                    uid = int.from_bytes(message.payload[4:8], byteorder='little', signed=False)
            else:
                log_with_time(
                    config_logger,
                    "subscribed error -> topic: {} | data: {}".format(message.topic, message.payload.hex()),
                )
                error_count += 1
            flag_config = True
        else:
            log_with_time(
                config_logger,
                "subscribed -> topic: {} | data: {}".format(message.topic, message.payload.hex()),
            )


# initialize a client
def client_init(broker, broker_port, message):
    client = paho.Client("sort_mqtt_test")
    # bind function to callback
    client.on_message = message
    # connect to broker
    client.connect(broker, port=broker_port)
    client.loop_start()  # start loop to process received messages
    return client


# close a client
def client_close(client):
    client.disconnect()
    client.loop_stop()


# subscribe voltage topic
def subscribing_voltage(client):
    global mac
    for i in subscribing_voltage:
        client.subscribe("/" + mac + "/" + i, 0)

# load subscribing list
def subscribing(client):
    global mac
    for i in subscribing_list_0:
        client.subscribe("/" + mac + "/" + i, 0)
    for i in subscribing_list_probe:
        client.subscribe(i, 0)


# probe
def probe(client):
    log_with_time(command_logger, "publishing probe request")
    client.publish("/probe", 0)
    time.sleep(10)
    return ["pass", 0]


# request version info(deprecated)
def request_version(client):
    global flag_version
    log_with_time(command_logger, "publishing command request")
    flag_version = False
    for i in command[0:6]:
        log_with_time(
            command_logger, "published -> topic: {} | cmd: {}".format("/" + mac + "/command_request", i.hex())
        )
        client.publish("/" + mac + "/command_request", i, 0)
    timeout = time.time() + 10
    while not flag_version:
        if time.time() > timeout:
            log_with_time(command_logger, "timeout")
            return ["timeout", error_count]
    return ["pass", error_count]


# upgrade STM32
def upgrade_STM32(client):
    global flag_command
    global flag_version
    log_with_time(command_logger, "publishing upgrade stm32")
    if flag_command:
        flag_command = False
        log_with_time(
            command_logger, "published -> topic: {} | url: {}".format("/" + mac + "/STM32_upgrade", url)
        )
        client.publish("/" + mac + "/STM32_upgrade", url, 0)
    timeout = time.time() + 60
    while not flag_command:
        if time.time() > timeout:
            log_with_time(command_logger, "timeout")
            return ["timeout", error_count]
    else:
        flag_version = False
        timeout = time.time() + 30
        while not flag_version:
            if time.time() > timeout:
                log_with_time(command_logger, "timeout")
                return ["timeout", error_count]
    return ["pass", error_count]


# upgrade ESP32
def upgrade_ESP32(client):
    global flag_command
    global flag_version
    log_with_time(command_logger, "publishing upgrade esp32")
    if flag_command:
        flag_command = False
        log_with_time(
            command_logger, "published -> topic: {} | url: {}".format("/" + mac + "/ESP32_upgrade", url)
        )
        client.publish("/" + mac + "/ESP32_upgrade", url, 0)
    timeout = time.time() + 60
    while not flag_command:
        if time.time() > timeout:
            log_with_time(command_logger, "timeout")
            return ["timeout", error_count]
    else:
        flag_version = False
        timeout = time.time() + 30
        while not flag_version:
            if time.time() > timeout:
                log_with_time(command_logger, "timeout")
                return ["timeout", error_count]
    return ["pass", error_count]


# set configuration
def request_config(client, msg):
    global flag_config
    log_with_time(config_logger, "publishing request configuration")
    if flag_config:
        flag_config = False
        log_with_time(
            config_logger, "published -> topic: {} | msg: {}".format("/" + mac + "/config_request", msg.hex())
        )
        client.publish("/" + mac + "/config_request", msg, 0)
        timeout = time.time() + 5
        while not flag_config:
            if time.time() > timeout:
                log_with_time(config_logger, "timeout")
                return ["timeout", error_count]
        return ["pass", error_count]


# reboot to save configurations
def reboot(client, msg):
    log_with_time(config_logger, "rebooting...")
    client.publish("/" + mac + "/config_request", msg, 0)
    time.sleep(2)


# get st-uid, return in uint32_t list
def request_uid(client):
    global flag_config
    global config_reply
    log_with_time(config_logger, "publishing request configuration")
    uid_list = [0] * 3
    get_uid_msg = bytearray(b"\x40\x00\x30\x00\x00\x00\x00\x00")
    for index in range(1, 4):
        get_uid_msg[1] = index
        config_reply = bytearray(b"\x43") + get_uid_msg[1:4]
        if flag_config:
            flag_config = False
            log_with_time(
                config_logger, "published -> topic: {} | msg: {}".format("/" + mac + "/config_request", get_uid_msg.hex())
            )
            client.publish("/" + mac + "/config_request", get_uid_msg, 0)
            timeout = time.time() + 5
            while not flag_config:
                if time.time() > timeout:
                    log_with_time(config_logger, "timeout")
                    return ["timeout", error_count, uid_list]
        uid_list[index - 1] = uid
    return ["pass", error_count, uid_list]


# reset servo error
def reset_servo_error(client):
    global flag_command
    log_with_time(command_logger, "publishing reset servo error")
    if flag_command:
        flag_command = False
        log_with_time(
            command_logger,
            "published -> topic: {} | cmd: {}".format("/" + mac + "/command_request", command[6].hex()),
        )
        client.publish("/" + mac + "/command_request", command[6], 0)
        timeout = time.time() + 5
        while not flag_command:
            if time.time() > timeout:
                log_with_time(command_logger, "timeout")
                return ["timeout", error_count]
    return ["pass", error_count]


# emergency poweroff
def emergency_poweroff(client):
    global flag_command
    log_with_time(command_logger, "publishing emergency poweroff")
    if flag_command:
        flag_command = False
        log_with_time(
            command_logger,
            "published -> topic: {} | cmd: {}".format("/" + mac + "/command_request", command[7].hex()),
        )
        client.publish("/" + mac + "/command_request", command[7], 0)
        timeout = time.time() + 5
        while not flag_command:
            if time.time() > timeout:
                log_with_time(command_logger, "timeout")
                return ["timeout", error_count]
    return ["pass", error_count]


# emergency power off recover
def emergency_poweroff_recover(client):
    global flag_command
    log_with_time(command_logger, "publishing emergency poweroff recover")
    if flag_command:
        flag_command = False
        log_with_time(
            command_logger,
            "published -> topic: {} | cmd: {}".format("/" + mac + "/command_request", command[8].hex()),
        )
        client.publish("/" + mac + "/command_request", command[8], 0)
        timeout = time.time() + 5
        while not flag_command:
            if time.time() > timeout:
                log_with_time(command_logger, "timeout")
                return ["timeout", error_count]
        return ["pass", error_count]


# clear wifi config
def clear_wifi(client):
    log_with_time(command_logger, "publishing clear wifi config")
    log_with_time(
        command_logger,
        "published -> topic: {} | cmd: {}".format("/" + mac + "/command_request", command[9].hex()),
    )
    client.publish("/" + mac + "/command_request", command[9], 0)
    time.sleep(3)
    return ["pass", 0]


# set rf channel
def set_rf_channel(client, channel):
    global flag_command
    log_with_time(command_logger, "publishing rf channel")
    if flag_command:
        flag_command = False
        data = command[10]
        data += channel.to_bytes(1, byteorder="little")
        log_with_time(
            command_logger,
            "published -> topic: {} | cmd: {}".format("/" + mac + "/command_request", data.hex()),
        )
        client.publish("/" + mac + "/command_request", data, 0)
        timeout = time.time() + 5
        while not flag_command:
            if time.time() > timeout:
                log_with_time(command_logger, "timeout")
                return ["timeout", error_count]
        return ["pass", error_count]


# listening...
def listening(client):
    print("listening...")
    while True:
        pass
