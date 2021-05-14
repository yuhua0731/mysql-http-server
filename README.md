RF address central manager

Run http server:
    ./mysql_http_server.py -h
    ./mysql_http_server.py -l 10.0.20.50 -p 8000

# Process:

## 1 Request RF address

### Client request body

```JSON
{
    "operation": "get_rf_address",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "operator": "yu"
}
```

### Server reply body

```JSON
{
    "result": "OK",
    "rf_address": "C32103",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "operator": "yu",
    "status": false
}
```

```JSON
{
    "result": "ERROR: access denied, need operator's name"
}
```

## 2 Comfirm RF address

### Client request body

```JSON
{
    "operation": "confirm_rf_address",
    "rf_address": "C32100",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "flash_result": "OK",
    "operator": "yu"
}
```

### Server reply body

```JSON
{
    "result": "OK",
    "rf_address": "C32100",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "operator": "yu",
    "status": true
}
```

```JSON
{
    "result": "ERROR: incorrect st_uids",
    "rf_address": "C32100",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "operator": "yu",
    "status": false
}
```

```JSON
{
    "result": "ERROR: cannot find this RF address",
    "rf_address": "C32100",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "operator": "yu",
    "status": false
}
```

```JSON
{
    "result": "ERROR: access denied, need operator's name",
    "rf_address": "C32100",
    "st_uid0": 456435,
    "st_uid1": 56431,
    "st_uid2": 654456,
    "operator": "",
    "status": false
}
```
