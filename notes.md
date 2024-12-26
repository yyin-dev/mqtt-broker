[TOC]

A toy MQTT broker implementation supporting [version 3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html). Inspired by: https://codepr.github.io/posts/sol-mqtt-broker/

### MQTT client

MqttX client: https://mqttx.app/docs/cli/get-started

```
$ mqttx conn --mqtt-version 3.1.1 -h localhost -p 1883
```

Mqtt client: https://github.com/hivemq/mqtt-cli
- The client uses V5 by default. Provide `--mqttVersion 3` to use 3.1.1.
- V5 introduces "problem infomation". Pass in `--no-reqProblemInfo` to skip requesting it from server.

### Progress
```
$ mqtt test -h localhost -p 1883 --mqttVersion=3
MQTT 3: OK
	- Maximum topic length: 510 bytes
	- QoS 0: Received 10/10 publishes in 4.36ms
	- QoS 1: Received 0/10 publishes in 10010.08ms
	- QoS 2: Received 0/10 publishes in 1.99ms
	- Retain: TIME_OUT
	- Wildcard subscriptions: NO
		> '+' Wildcard: TIME_OUT
		> '#' Wildcard: TIME_OUT
	- Shared subscriptions:
```

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
- [x] Handles subscribe

```
$ mqttx sub -t topic -h localhost --mqtt-version 3.1.1 -p 1883
✔ Connected
✔ Subscribed to topic
```

- [x] Message forwarding, at most once

```
$ mqttx pub -t my_topic --mqtt-version 3.1.1 -h localhost -p 1883 -m "Testing"
✔ Connected
✔ Message published

$ mqttx sub -t my_topic --mqtt-version 3.1.1 -h localhost -p 1883
✔ Connected
✔ Subscribed to my_topic
topic: my_topic, qos: 0
Testing
```

- [ ] Retained message
- [ ] Message forwarding, at least once
- [ ] Message forwarding, exactly once
- [ ] Topic wildcards



### Python hex notation

`\x` is used in strings, regular or byte strings, to specify a single byte using hex notation.
```
s = b"\x41\x42"
```
`0x` is a prefix to indicate that a number is in hexadecimal notation.
```
num = 0x41 
```