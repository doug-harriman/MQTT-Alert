# Simplified MQTT interface class.
# Listens on topic "device/#"
# When MQTT message is received, call specified callback function with MqttMessage object.
# Connection call blocks indefinitely.

import ipaddress
import logging
import json
from paho.mqtt import client as mqtt_client
import datetime as dt

# logging.basicConfig(
#     level=logging.DEBUG,
#     filename="mqtt.log",
#     filemode="w",
#     format="%(asctime)s %(message)s",
# )


class MqttMessage:
    """
    MQTT message encapsulation class.
    """

    def __init__(self, topic: str, data: dict) -> None:
        if not isinstance(topic, str):
            raise TypeError("MQTT topic must be a string.")
        if not isinstance(data, dict):
            raise TypeError("MQTT data must be a dict.")

        self._topic = topic
        self._data = data
        self._timestamp = dt.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.topic}: {self.data}"

    @property
    def topic(self) -> str:
        """
        MQTT topic.

        Returns:
            str: MQTT topic.
        """
        return self._topic

    @property
    def data(self) -> dict:
        """
        MQTT data.

        Returns:
            dict: MQTT data.
        """
        return self._data

    @property
    def timestamp(self) -> str:
        """
        MQTT timestamp.

        Returns:
            str: MQTT timestamp.
        """
        return self._timestamp


class Mqtt:
    """
    Simplified MQTT interface class.
    Class expects to receive JSON formatted messages.
    """

    def __init__(
        self,
        ipaddr: str = "0.0.0.0",
        port: int = 1883,  # Default Mosquitto port
        callback=None,
    ) -> None:
        """
        Simplified MQTT interface class.

        Args:
            ipaddr (str, optional): IP address of MQTT broker. Defaults to "0.0.0.0" (localhost).
            port (int, optional): IP Port of MQTT broker . Defaults to 1883 (Mosquitto default).
        """

        self._is_connected = False
        self._mqtt_client = mqtt_client.Client()
        self._callback = None

        # Logging config
        self.logger = logging.getLogger(__name__)

        # Setters
        if ipaddr is not None:
            self.ipaddr = ipaddr
        if port is not None:
            self.port = port
        if callback is not None:
            self.callback = callback

    @property
    def ipaddr(self) -> str:
        """
        MQTT Host IP Address.

        Returns:
            str: Host IP address.
        """
        return self._ipaddr

    @ipaddr.setter
    def ipaddr(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("MQTT host IP must be a string.")

        try:
            ipaddress.ip_address(value)
        except ValueError as e:
            self.logger.debug("Invalid IP address for MQTT server: %s", value)
            raise e

        self._ipaddr = value

    @property
    def port(self) -> int:
        """
        MQTT Host IP Port.

        Returns:
            int: Port number.
        """
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        # Error checks
        if not isinstance(value, int):
            raise TypeError("MQTT host port must be an integer.")

        self._port = value

    @property
    def is_connected(self) -> bool:
        """
        Check if connected to MQTT broker.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._is_connected

    @property
    def callback(self):
        """
        MQTT subscription callback function.

        Returns:
            callable: Callback function.
        """
        return self._callback

    @callback.setter
    def callback(self, value) -> None:
        """
        Set MQTT subscription callback function.

        Args:
            value (callable): Callback function.
        """

        if not callable(value):
            raise TypeError("MQTT callback must be a callable.")

        self._callback = value

    def connect(self, blocking: bool = True) -> bool:
        """
        Connect to MQTT broker.

        Returns:
            bool: True if connection successful, False otherwise.
        """

        self._is_connected = False

        # Error checks
        if self.ipaddr is None:
            raise ValueError("MQTT host IP address is not set.")
        if self.port is None:
            raise ValueError("MQTT host port is not set.")

        # Connect to MQTT broker
        self._mqtt_client = mqtt_client.Client()
        self._mqtt_client.on_message = self._on_mqtt_message
        try:
            self._mqtt_client.connect(self.ipaddr, self.port)
            self.logger.debug(f"Connected to MQTT broker: {self.ipaddr}:{self.port}")

            topic = "device/#"
            self._mqtt_client.subscribe(topic)
            self.logger.debug(f"Subscribed to topic: {topic}")

        except Exception as e:
            self.logger.debug(f"Failed to connect to MQTT broker: {e}")

            if blocking:
                raise e
            else:
                return False

        self._is_connected = True

        if self.callback is None:
            self.logger.debug("Using default message handler")

        if blocking:
            self.logger.debug("Blocking: awaiting messages from MQTT broker")
            self._mqtt_client.loop_forever()
        else:
            # TOOD: Start thread
            raise NotImplementedError("Non-blocking connect not implemented.")

        return True

    def disconnect(self) -> None:
        """
        Disconnect from MQTT broker.
        """
        self.logger.debug("Disconnecting from MQTT broker")
        self._is_connected = False

        if self._mqtt_client is not None:
            self._mqtt_client.disconnect()

    def _on_mqtt_message(self, client, userdata, message, tmp=None) -> None:
        """
        MQTT subscription message handler.

        Args:
            client (_type_): _description_
            userdata (_type_): _description_
            message (_type_): _description_
            tmp (_type_, optional): _description_. Defaults to None.
        """

        self.logger.debug(f"MQTT message received on topic: {message.topic}")

        # Message payload is assumed to be JSON, convert to dict
        if not isinstance(message.payload, bytes):
            self.logger.debug(f"MQTT message payload is not bytes: {message.payload}")
            return

        try:
            data = json.loads(message.payload.decode("utf-8"))
        except Exception as e:
            self.logger.debug(f"Failed to decode MQTT message payload: {e}")
            return

        # Create message object
        msg = MqttMessage(message.topic, data)
        if self.callback is not None:
            try:
                self.callback(msg)
            except Exception as e:
                self.logger.debug(f"Callback failed: '{str(self.callback)}': {e}")
        else:
            print(msg)


if __name__ == "__main__":
    mqtt = Mqtt(ipaddr="192.168.0.120", port=1885)
    mqtt.connect(blocking=True)
