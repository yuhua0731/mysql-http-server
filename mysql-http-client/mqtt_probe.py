#!/usr/bin/env python3
import test_mqtt
import csv
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="mqtt arguments")
    parser.add_argument("mqtt_broker", help="address of mqtt broker", type=str)
    parser.add_argument("mqtt_broker_port", help="port of mqtt broker", type=str)

    broker = parser.parse_args().mqtt_broker
    port = int(parser.parse_args().mqtt_broker_port)

    pass_count = 0
    timeout_count = 0
    error_count = 0
    client = test_mqtt.client_init(broker, port, test_mqtt.on_message)
    test_mqtt.subscribing(client)
    
    res = test_mqtt.probe(client)
    if res[0] == "pass":
        pass_count += 1
    if res[0] == "timeout":
        timeout_count += 1
    error_count += res[1]
    test_mqtt.client_close(client)
    print("{} {} {}".format(pass_count, timeout_count, error_count), end="")


if __name__ == "__main__":
    main()
