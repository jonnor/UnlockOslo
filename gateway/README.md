
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

Reponse data

    {
      "doors": {
        "erroring-1": {
          "last_seen": 1512057658.2107704,
          "status": 200
        },
        "virtual-1": {
          "last_seen": 1512057658.2107704,
          "status": 200
        },
        "virtual-2": {
          "last_seen": 1512057658.2107704,
          "status": 200
        }
      }
    }
```



