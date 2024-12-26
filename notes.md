Source: https://codepr.github.io/posts/sol-mqtt-broker/

### MQTT client

MqttX client: https://mqttx.app/docs/cli/get-started

```
$ mqttx conn --mqtt-version 3.1.1 -h localhost -p 1883
```

Mqtt client: https://github.com/hivemq/mqtt-cli
- The client uses V5 by default. Provide `--mqttVersion 3` to use 3.1.1.
- V5 introduces "problem infomation". Pass in `--no-reqProblemInfo` to skip requesting it from server.

## Progress
- [x] Handles connection. 

```
$ mqttx conn  --mqtt-version 3.1.1 -h localhost -p 1883
✔ Connected
```

- [x] Handle publish

```
$ mqttx pub -t 'topic' -h localhost -p 1883 -m 'Test' --mqtt-version 3.1.1
✔ Connected
✔ Message published
```

