#!/usr/bin/env python3
import requests
import json

def main():
    url = 'http://10.0.1.251:8000'

    # response = requests.get(url)
    # print(response.status_code)
    # print(print(json.dumps(response.json(), indent=4, sort_keys=False)))

    # print("==============================\nsimple GET:")
    # resp = requests.get(url=url).json()
    # print(json.dumps(resp, indent=4, sort_keys=False))

    # print("==============================\nrf_get:")
    # rf_get = {
    #     "operation": "rf_get",
    #     "st_uid": 0x11ff112aa222333333444444,
    #     "operator": "yu"
    # }
    # resp = requests.get(url=url, params=rf_get).json()
    # print(json.dumps(resp, indent=4, sort_keys=False))

    # print("==============================\nrf_confirm:")
    # rf_confirm = {
    #     "operation": "rf_confirm",
    #     "rf_addr": int(resp['rf'][2:], 16),
    #     "st_uid": 0x11ff112aa222333333444444,
    #     "operator": "yu"
    # }
    # resp = requests.get(url=url, params=rf_confirm).json()
    # print(json.dumps(resp, indent=4, sort_keys=False))



    # request rf address
    rf_get_request = {
        "operation": "get_rf_address",
        "st_uid0": 77777,
        "st_uid1": 88888,
        "st_uid2": 99999,
        "operator": "test"
    }
    print("====================================\nget_rf_address request")
    print(json.dumps(rf_get_request, indent=4, sort_keys=False))
    rf_get_respond = requests.get(url, params=rf_get_request).json()
    # print("====================================\nget_rf_address reply")
    # print(json.dumps(rf_get_respond, indent=4, sort_keys=False))

if __name__ == "__main__":
    main()