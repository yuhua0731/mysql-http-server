#!/usr/bin/env python3
import test_mqtt
import csv
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="mqtt arguments")
    parser.add_argument("mqtt_broker", help="address of mqtt broker", type=str)
    parser.add_argument("mqtt_broker_port", help="port of mqtt broker", type=str)
    parser.add_argument("mac_address", help="mac address", type=str)

    mac_addr = parser.parse_args().mac_address
    broker = parser.parse_args().mqtt_broker
    port = int(parser.parse_args().mqtt_broker_port)

    test_mqtt.mac = mac_addr.upper()
    test_mqtt.error_count = 0
    client = test_mqtt.client_init(broker, port, test_mqtt.on_message)
    test_mqtt.subscribing(client)
    test_mqtt.flag_config = True
    res = test_mqtt.request_uid(client)
    # res = [pass/timeout, error_count, uid_list]
    pass_count = 1 if res[0] == "pass" else 0
    timeout_count = 1 if res[0] == "timeout" else 0
    test_mqtt.client_close(client)
    print(f"{pass_count} {timeout_count} {res[1]} {res[2][0]} {res[2][1]} {res[2][2]}", end="")


if __name__ == "__main__":
    main()
