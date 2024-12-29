A toy MQTT broker implementation supporting [version 3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html). 

[TOC]

### MQTT client

MqttX client: https://mqttx.app/docs/cli/get-started

```
$ mqttx conn --mqtt-version 3.1.1 -h localhost -p 1883
```

Note: I believe [HiveMQ's client](https://github.com/hivemq/mqtt-cli) is flawed for 3.1.1. In QoS 2, when the broker relays a message to the subscriber, the message exchange should look like
```
Broker -> Subscriber: PUBLISH
Subscriber -> Broker: PUBREC
Broker -> Subscriber: PUBREL
Subscriber -> Broker: PUBCOMP
```
However, after receiving PUBREL, the client disconnected immedaitely without sending a PUBCOMP.

### Progress

```
$ mqtt test -h localhost -p 1883 --mqttVersion=3
MQTT 3: OK
	- Maximum topic length: 510 bytes
	- QoS 0: Received 10/10 publishes in 4.18ms
	- QoS 1: Received 10/10 publishes in 7.08ms
	- QoS 2: Received 1/10 publishes in 10012.45ms
	- Retain: TIME_OUT
	- Wildcard subscriptions: NO
		> '+' Wildcard: TIME_OUT
		> '#' Wildcard: TIME_OUT
	- Shared subscriptions: TIME_OUT
	- Payload size: 986 bytes
	- Maximum client id length: 65535 bytes
	- Unsupported Ascii Chars: ALL SUPPORTED
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

- [x] Message forwarding, at least once
```
$ mqttx sub -t my_topic --mqtt-version 3.1.1 -h 127.0.0.1 -p 1883  --qos 1
✔ Connected
✔ Subscribed to my_topic
topic: my_topic, qos: 1
hi

$ mqttx pub -t my_topic --mqtt-version 3.1.1 -h 127.0.0.1 -p 1883 --qos 1 -m hi
✔ Connected
✔ Message published
```

- [x] Message forwarding, exactly once
```
$ mqttx sub -t my_topic --mqtt-version 3.1.1 -h 127.0.0.1 -p 1883  --qos 2
✔ Connected
✔ Subscribed to my_topic

topic: my_topic, qos: 2
hi

$ mqttx pub -t my_topic --mqtt-version 3.1.1 -h 127.0.0
.1 -p 1883 --qos 2 -m hi
✔ Connected
✔ Message published
```
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



### Digging into the test of HiveMQ's client

> Note: this section is no longer useful. Because I believe the client's test is flawed for 3.1.1.

Build https://hivemq.github.io/mqtt-cli/ from source locally.

Update build.gradle.tks (there's another one in `./mqtt-cli-plugins`) to use the jdk you have. The following diff is for JDK23.

```
diff --git a/build.gradle.kts b/build.gradle.kts
index 118e0aa8..8a572770 100644
--- a/build.gradle.kts
+++ b/build.gradle.kts
@@ -50,13 +50,13 @@ application {

 java {
     toolchain {
-        languageVersion = JavaLanguageVersion.of(21)
+        languageVersion = JavaLanguageVersion.of(23)
     }
 }

 tasks.compileJava {
     javaCompiler = javaToolchains.compilerFor {
-        languageVersion = JavaLanguageVersion.of(11)
+        languageVersion = JavaLanguageVersion.of(23)
     }
 }

@@ -546,7 +546,7 @@ tasks.buildDeb {

 tasks.buildRpm {
     release = "1"
-    requires("jre", "1.8.0", Flags.GREATER or Flags.EQUAL)
+    requires("jre", "1.23.0", Flags.GREATER or Flags.EQUAL)
 }

 val buildDebianPackage by tasks.registering {
diff --git a/mqtt-cli-plugins/build.gradle.kts b/mqtt-cli-plugins/build.gradle.kts
index 94e92779..7a248dee 100644
--- a/mqtt-cli-plugins/build.gradle.kts
+++ b/mqtt-cli-plugins/build.gradle.kts
@@ -6,7 +6,7 @@ group = "com.hivemq"

 java {
     toolchain {
-        languageVersion = JavaLanguageVersion.of(8)
+        languageVersion = JavaLanguageVersion.of(23)
     }
 }
```

Find out java home
```
$ brew install openjdk
$ java --version
$ /usr/libexec/java_home
/opt/homebrew/Cellar/openjdk/23.0.1/libexec/openjdk.jdk/Contents/Home
```

In vscode settings, add the line blow s.t. the extention knows about this jre.

```
    "java.import.gradle.java.home": "/opt/homebrew/Cellar/openjdk/23.0.1/libexec/openjdk.jdk/Contents/Home",
```

Build with gradlew: `./gradlew build -x check`. Use `-x check` to skip the task named "check" in build.gradle.tks.

Run `java -jar build/libs/mqtt-cli-4.35.0.jar`.