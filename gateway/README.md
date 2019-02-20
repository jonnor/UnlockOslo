
# [Code](./gateway.py)

# [Tests](./gateway/test_gateway.py)

# HTTP API

## Authentication

HTTP Basic Auth with server-side TLS encryption.

## Unlock door

```
    POST /doors/$door_id/unlock?duration=NN

Response status

    200: Door is now unlocked.
        Will automatically lock again after $duration seconds

    503: Unlock failed, device or message broker responded with error
    504: Unlock failed, device communication timed out

    404: Unknown door ID
    422: Invalid or out-of-range value for `duration` parameter
    403: Wrong or missing auth
```


## Healthcheck

```
    GET /status

Response status

    200: No errors detected.
        Received heartbeat from all locks within last monitoring period

    503: Missing heartbeat from one or more doorlocks

    403: Wrong or missing auth

Response format

    text/json

Reponse data example

    {
      "doors": {
        "erroring-1": {
          "last_seen": 1512057658.2107704,
          "status": 200
        },
        "virtual-1": {
          "last_seen": 1512057658.2107704,
          "status": 200,
          "bolt": {
            "last_updated": 1550678903.1224298,
            "present": false
          }
        },
        "virtual-2": {
          "last_seen": 1512057658.2107704,
          "status": 200,
          "bolt": {
            "last_updated": null,
            "present": null
          },
        }
      }
    }

Response data details

    /doors/{door}/last_seen

        null|Number

        Unix timestamp for when we last got a heartbeat message from this door/device.

    /doors/{door}/status

        null/Integer

        200: Heartbeat has been received recently
        503: Missing heartbeat within healthcheck period
        null: Status is unknown. Server has not running longer than healthcheck period

        HTTP style status code for device/door status

    /doors/{door}/bolt

      Available *if* door has a bolt sensor installed and enabled.

    /doors/{door}/bolt/present

        null|true|false

        null: Status is unknown
        true: Door is present and bolted.
        false: Door is either open, or the locking bolt has been withdrawn or blocked.

    /doors/{door}/bolt/last_updated

        null|Number

        null: Status is unknown
        Unix timestamp for when bolt @present last changed


```




