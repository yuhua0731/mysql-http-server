#!/usr/bin/env python3
import json
import argparse
import sys
import subprocess
import csv
import os

try:
    import paho.mqtt.client as paho
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", 'paho-mqtt'])
finally:
    import paho.mqtt.client as paho

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", 'requests'])
finally:
    import requests

test_mode = True

def main():
    python_command = "python3" if sys.platform == "darwin" else "python"
    # specify arguments
    parser = argparse.ArgumentParser(description="Run a simple HTTP client")
    parser.add_argument(
        "-l",
        "--url",
        default="http://10.0.20.50:8000",
        help="Specify the url of http server",
    )
    parser.add_argument(
        "-u",
        "--user",
        default="yu",
        help="Specify the operator's name",
    )
    parser.add_argument(
        "-m",
        "--mqtt",
        default="sort-controller.local",
        help="address of mqtt broker",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=1883,
        help="port of mqtt broker",
    )
    parser.add_argument(
        "-a",
        "--addr",
        default="",
        help="Specify the shuttle's mac address",
    )
    args = parser.parse_args()

    # read st_uid
    if test_mode:
        st_uid = [77777, 88888, 99999]
    else:
        res = subprocess.check_output(
            [
                "{}".format(python_command),
                "mqtt_get_uid.py",
                "{}".format(args.mqtt),
                "{}".format(args.port),
                "{}".format(args.addr),
            ]
        )
        res = list(map(int, str(res, "utf-8").split(" ")))
        if res[0] != 1:
            sys.exit(f"request st_uid timeout, please retry: {res}")
        st_uid = [res[3], res[4], res[5]]
    print(f"st_uid0: {st_uid[0]}\nst_uid1: {st_uid[1]}\nst_uid2: {st_uid[2]}")

    # request rf address
    rf_get_request = {
        "operation": "get_rf_address",
        "st_uid0": st_uid[0],
        "st_uid1": st_uid[1],
        "st_uid2": st_uid[2],
        "operator": args.user
    }
    print("====================================\nget_rf_address request")
    print(json.dumps(rf_get_request, indent=4, sort_keys=False))
    rf_get_respond = requests.get(args.url, params=rf_get_request).json()
    print("====================================\nget_rf_address reply")
    print(json.dumps(rf_get_respond, indent=4, sort_keys=False))
    # if "result" in rf_get_respond:
    #     if rf_get_respond["result"] == "OK":
    #         rf_confirm_request = {
    #             "operation": "confirm_rf_address",
    #             "rf_address": rf_get_respond["rf_address"],
    #             "st_uid0": st_uid[0],
    #             "st_uid1": st_uid[1],
    #             "st_uid2": st_uid[2],
    #             "flash_result": "ERROR",
    #             "operator": args.user
    #         }
    #         # write rf address
    #         rf_write = "23003000"
    #         rf_write += rf_get_respond["rf_address"] + "00"
    #         with open('rf_addr_temp.csv', 'w', newline='') as file:
    #             writer = csv.writer(file)
    #             writer.writerow([rf_write])
    #         res = subprocess.check_output(
    #             [
    #                 "{}".format(python_command),
    #                 "mqtt_set_config.py",
    #                 "{}".format(args.mqtt),
    #                 "{}".format(args.port),
    #                 "{}".format(args.addr),
    #                 "rf_addr_temp.csv",
    #                 "1",
    #             ]
    #         )
    #         if(os.path.exists("rf_addr_temp.csv") and os.path.isfile("rf_addr_temp.csv")):
    #             os.remove("rf_addr_temp.csv")
    #         res = list(map(int, str(res, "utf-8").split(" ")))
    #         if res[1] != 0 or res[2] != 0:
    #             print(f"write rf_addr error, please retry: {res}")
    #         else:
    #             rf_confirm_request["flash_result"] = "OK"

    #         # request rf confirm
    #         print("====================================\nconfirm_rf_address request")
    #         print(json.dumps(rf_confirm_request, indent=4, sort_keys=False))
    #         rf_confirm_respond = requests.get(
    #             args.url, params=rf_confirm_request).json()
    #         print("====================================\nconfirm_rf_address reply")
    #         print(json.dumps(rf_confirm_respond, indent=4, sort_keys=False))
    #         if "result" in rf_confirm_respond:
    #             print(f"rf confirm: {rf_confirm_respond['result']}")
    #         else:
    #             print("rf confirm failed")
    #     else:
    #         print(rf_get_respond["result"])
    # else:
    #     print("request rf address failed")


if __name__ == '__main__':
    main()
