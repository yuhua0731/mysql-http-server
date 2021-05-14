#!/usr/bin/env python3
import json
import argparse
import sys
import subprocess

try:
    import serial
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", 'pyserial'])
finally:
    import serial

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip",
                           "install", 'requests'])
finally:
    import requests

SERIAL_MSG_SIZE = 8
INDEX_BASE = 3000
test_mode = False

class SerialPort:
    def __init__(self, port, buand):
        self.port = serial.Serial(port, buand)
        if not self.port.isOpen():
            self.port.open()

    def port_open(self):
        if not self.port.isOpen():
            self.port.open()

    def port_close(self):
        self.port.close()

    def serial_read_configuration(self, index):
        tx_array = b'\x40'
        tx_array += int(str(index), 16).to_bytes(2,
                                                 byteorder='little', signed=False)
        tx_array += b'\x00\x00\x00\x00\x00'
        if SERIAL_MSG_SIZE != self.port.write(tx_array):
            sys.exit(f"serial read error: {tx_array.hex()}")
        return self.port.read(SERIAL_MSG_SIZE)

    def serial_write_configuration(self, index, data):
        tx_array = b'\x23'
        tx_array += int(str(index), 16).to_bytes(2,
                                                 byteorder='little', signed=False) + b'\x00'
        tx_array += int(data, 16).to_bytes(3, byteorder='big',
                                           signed=False) + b'\x00'
        if SERIAL_MSG_SIZE != self.port.write(tx_array):
            sys.exit(f"serial write error: {tx_array.hex()}")
        return self.port.read(SERIAL_MSG_SIZE)

    def serial_read_uid(self):
        uid = [0] * 3
        for index in range(1, 4):
            temp = self.serial_read_configuration(index + INDEX_BASE)
            if(temp[0] == 0x43):
                uid[index - 1] = int.from_bytes(temp[4:8],
                                                byteorder='little', signed=False)
                print(f"UID{index} is {uid[index - 1]}")
            else:
                sys.exit(f"read the UID{index} failed")
        return uid

    def serial_rf_addr_config(self, rf_addr):
        ret = self.serial_write_configuration(INDEX_BASE, rf_addr)
        if ret[0] == 0x60:
            temp_check = self.serial_read_configuration(INDEX_BASE)
            rf_addr_check = int.from_bytes(
                temp_check[4:7], byteorder='big', signed=False)
            if rf_addr_check == int(rf_addr, 16):
                return True
            else:
                print("rf address check failed")
        else:
            print("serial write failed")
        return False


def main():
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
        "-p",
        "--port",
        default="",
        help="Specify the serial port to use",
    )
    args = parser.parse_args()

    # open serial port
    if not test_mode:
        myserial = SerialPort(args.port, 115200)
        myserial.port_open()

    # # read st_uid
    st_uid = myserial.serial_read_uid() if not test_mode else [77777, 77777, 77777]

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
    if "result" in rf_get_respond:
        if rf_get_respond["result"] == "OK":
            rf_confirm_request = {
                "operation": "confirm_rf_address",
                "rf_address": rf_get_respond["rf_address"],
                "st_uid0": st_uid[0],
                "st_uid1": st_uid[1],
                "st_uid2": st_uid[2],
                "flash_result": "ERROR",
                "operator": args.user
            }
            # write rf address
            if test_mode or myserial.serial_rf_addr_config(rf_get_respond["rf_address"]):
                rf_confirm_request["flash_result"] = "OK"

            # request rf confirm
            print("====================================\nconfirm_rf_address request")
            print(json.dumps(rf_confirm_request, indent=4, sort_keys=False))
            rf_confirm_respond = requests.get(
                args.url, params=rf_confirm_request).json()
            print("====================================\nconfirm_rf_address reply")
            print(json.dumps(rf_confirm_respond, indent=4, sort_keys=False))
            if "result" in rf_confirm_respond:
                print(f"rf confirm: {rf_confirm_respond['result']}")
            else:
                print("rf confirm failed")
        else:
            print(rf_get_respond["result"])
    else:
        print("request rf address failed")

    if not test_mode:
        myserial.port_close()


if __name__ == '__main__':
    main()
