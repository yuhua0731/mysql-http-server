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
    parser.add_argument("config_array", help="file name which contains configurations", type=str)
    parser.add_argument("test_times", help="how many times to test", type=str)

    mac_addr = parser.parse_args().mac_address
    config = parser.parse_args().config_array
    broker = parser.parse_args().mqtt_broker
    port = int(parser.parse_args().mqtt_broker_port)
    test = int(parser.parse_args().test_times)

    test_mqtt.mac = mac_addr.upper()
    test_mqtt.error_count = 0
    pass_count = 0
    timeout_count = 0
    error_count = 0
    client = test_mqtt.client_init(broker, port, test_mqtt.on_message)
    test_mqtt.subscribing(client)
    for x in range(test):
        with open(config, "r") as csvfile:
            config_plots = csv.reader(csvfile)
            for config_row in config_plots:
                set_config_msg = bytearray.fromhex(config_row[0])
                if len(set_config_msg) < 8:
                    set_config_msg += bytearray.fromhex(mac_addr)
                    set_config_msg += b"\x00"
                test_mqtt.config_reply = bytearray(b"\x60") + set_config_msg[1:]
                test_mqtt.flag_config = True
                res = test_mqtt.request_config(client, set_config_msg)
                if res[0] == "pass":
                    pass_count += 1
                if res[0] == "timeout":
                    timeout_count += 1
                error_count += res[1]
            reboot = bytearray(b"\x23\x00\x20\x00\xFF\xFF\xFF\xFF")
            test_mqtt.reboot(client, reboot)
    print("{} {} {}".format(pass_count, timeout_count, error_count), end="")
    test_mqtt.client_close(client)


if __name__ == "__main__":
    main()
