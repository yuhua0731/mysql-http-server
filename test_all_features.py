#!/usr/bin/env python3
import requests
import json

def main():
    url = 'http://10.0.20.50:8000'

    print("==============================\nsimple GET:")
    resp = requests.get(url=url).json()
    print(json.dumps(resp, indent=4, sort_keys=False))

    print("==============================\nrf_get:")
    rf_get = {
        "operation": "rf_get",
        "st_uid": 0x11ff112aa222333333444444,
        "operator": "yu"
    }
    resp = requests.get(url=url, params=rf_get).json()
    print(json.dumps(resp, indent=4, sort_keys=False))

    print("==============================\nrf_confirm:")
    rf_confirm = {
        "operation": "rf_confirm",
        "rf_addr": int(resp['rf'][2:], 16),
        "st_uid": 0x11ff112aa222333333444444,
        "operator": "yu"
    }
    resp = requests.get(url=url, params=rf_confirm).json()
    print(json.dumps(resp, indent=4, sort_keys=False))


if __name__ == "__main__":
    main()