# alerts.py
# Tools for monitoring MQTT traffic and sending email alerts.

import datetime as dt
import json
import logging
import re

# from mqttemail.mqtt import MqttMessage, Mqtt
# from mqttemail.gmail import Gmail
from mqtt import MqttMessage, Mqtt
from gmail import Gmail

# TODO: Load config from file.

# These two need a separte time thread to check.
# TODO: Heartbeat check (hours) - Send if message not received within time.
# TODO: System heartbeat (days) - Send message confirming system up.


class Alert:
    """
    Alert class.
    """

    def __init__(
        self,
        topic: str = None,
        condition: str = None,
        email: str = None,
        period_minimum: dt.timedelta = None,
        period_maximum: dt.timedelta = None,
    ) -> None:
        # Logging config
        self.logger = logging.getLogger(__name__)

        self._topic = None
        if topic is not None:
            self.topic = topic

        self._condition = None
        self._variable = None
        self._expr = None
        if condition is not None:
            self.condition = condition

        self._period_minimum = None
        if period_minimum is not None:
            self.period_minimum = period_minimum
        else:
            self.period_minimum = dt.timedelta(minutes=60)

        self._period_maximum = None
        if period_maximum is not None:
            self.period_maximum = period_maximum
        else:
            self.period_maximum = dt.timedelta(days=1)

        self._email = None
        if email is not None:
            self.email = email

        self._message_last_received = dt.datetime.now()
        self._message_last_check = dt.datetime.now()

    def __repr__(self) -> str:
        return "Alert(" + self.__str__() + ")"

    def __str__(self) -> str:
        return f"'{self.topic}','{self.condition}'"

    @property
    def period_minimum(self) -> dt.timedelta:
        """
        Minimum period between checking messages.

        Returns:
            dt.timedelta: Minimum period.
        """
        return self._period_minimum

    @period_minimum.setter
    def period_minimum(self, value: dt.timedelta) -> None:
        # Error checks
        if not isinstance(value, dt.timedelta):
            raise TypeError("Period minimum must be a timedelta.")

        self._period_minimum = value

    @property
    def period_maximum(self) -> dt.timedelta:
        """
        Maximum expected period between messages.

        Returns:
            dt.timedelta: Maximum period.
        """
        return self._period_maximum

    @period_maximum.setter
    def period_maximum(self, value: dt.timedelta) -> None:
        # Error checks
        if not isinstance(value, dt.timedelta):
            raise TypeError("Period maximum must be a timedelta.")

        self._period_maximum = value

    @property
    def message_last_check(self) -> dt.datetime:
        """
        Time stamp of last time an MQTT message was checked.
        Messages are not checked within the minimum period.

        Returns:
            dt.datetime: Last message timestamp.
        """
        return self._message_last_check

    @property
    def message_last_received(self) -> dt.datetime:
        """
        Time stamp of last time an MQTT message was received.

        Returns:
            dt.datetime: Last message timestamp.
        """
        return self._message_last_received

    @property
    def topic(self) -> str:
        """
        MQTT topic.

        Returns:
            str: MQTT topic.
        """
        return self._topic

    @topic.setter
    def topic(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("MQTT topic must be a string.")

        self._topic = value

    @property
    def condition(self) -> str:
        """
        Condition.

        Returns:
            str: Condition.
        """
        return self._condition

    @condition.setter
    def condition(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("Condition must be a string.")

        idx = re.search(r"[^_a-zA-Z0-9]", value).start()
        if idx < 1:
            raise ValueError("Condition must be in the form 'variable test value'")

        self._condition = value
        self._variable = value[:idx]
        self._expr = value[idx:]

    @property
    def condition_variable(self) -> str:
        """
        Condition variable.

        Returns:
            str: Condition variable.
        """
        return self._variable

    @property
    def condition_expr(self) -> str:
        """
        Condition expression.

        Returns:
            str: Condition expression.
        """
        return self._expr

    @property
    def email(self) -> str:
        """
        Email address.

        Returns:
            str: Email address.
        """
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("Email address must be a string.")

        self._email = value

    def check(self, message: MqttMessage, gmail: Gmail = None) -> None:
        """
        Checks MQTT message data to see if alert should be fired.

        Args:
            message (MqttMessage): MQTT message.

        Returns:
            bool: True if message matches alert.
        """

        # Check topic
        if self.topic is not None:
            if message.topic != self.topic:
                return

        # Got a message on our topic
        now = dt.datetime.now()
        self._message_last_received = now

        # Check period min to see if we can ignore
        if now - self.message_last_check < self.period_minimum:
            return

        # Check condition
        self._message_last_check = now
        if self.condition is None:
            return

        if self.condition_variable not in message.data:
            raise ValueError(
                f"Condition variable '{self.condition_variable}' not in message data: {message.data}"
            )

        val = message.data[self.condition_variable]
        if not isinstance(val, str):
            val = str(val)

        if not eval(f"{val}{self.condition_expr}"):
            return False

        # Condition was met, send email
        subject = f"Alert: '{self.topic}', '{self.condition}'"
        self.logger.info(subject)

        # Send email
        if not gmail:
            return
        if not self.email:
            return

        # Use message here uncase subscribed to wildcard.
        body = f"Alert on: {message.topic}.\n"
        body += f"Variable: {self.condition_variable} = {val}.\n"
        body += (
            f"Satifies alert condition: {self.condition_variable} {self.condition_expr}"
        )
        gmail.email_send(self.email, body, subject=subject)

    def to_dict(self) -> dict:
        """
        Converts Alert object to dictionary representation.

        Returns:
            dict: Dictionary representation of Alert object.
        """

        dict = {}
        dict["topic"] = self.topic
        dict["condition"] = self.condition
        dict["email"] = self.email
        dict["period_minimum"] = self.period_minimum
        dict["period_maximum"] = self.period_maximum

        return dict

    def from_dict(self, data) -> None:
        """
        Converts dictionary representation to Alert object.

        Args:
            dict (dict): Dictionary representation of Alert object.
        """

        # Error checks
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")

        self.topic = data["topic"]
        self.condition = data["condition"]
        self.email = data["email"]
        self.period_minimum = data["period_minimum"]
        self.period_maximum = data["period_maximum"]

    def to_json(self) -> str:
        """
        Converts Alert object to JSON string representation.

        Returns:
            str: JSON representation
        """

        data = self.to_dict()
        data["period_minimum"] = str(data["period_minimum"].total_seconds())
        data["period_maximum"] = str(data["period_maximum"].total_seconds())

        jsonstr = json.dumps(data)
        return jsonstr

    def from_json(self, jsonstr: str) -> None:
        """
        Converts JSON string representation to Alert object.

        Args:
            json (str): JSON representation
        """

        # Error checks
        if not isinstance(jsonstr, str):
            raise TypeError("JSON must be a string.")

        data = json.loads(jsonstr)
        data["period_minimum"] = dt.timedelta(seconds=float(data["period_minimum"]))
        data["period_maximum"] = dt.timedelta(seconds=float(data["period_maximum"]))

        return self.from_dict(data)


class AlertManager:
    """
    Alert manager class.
    """

    def __init__(self, mqtt: Mqtt = None, gmail: Gmail = None) -> None:
        # Logging config
        self.logger = logging.getLogger(__name__)

        self._alerts = []

        self._mqtt = None
        if mqtt is not None:
            self.mqtt = mqtt

        self._gmail = None
        if gmail is not None:
            self.gmail = gmail

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Alerts: {len(self._alerts)}"

    @property
    def mqtt(self) -> Mqtt:
        """
        MQTT client.

        Returns:
            Mqtt: MQTT client.
        """
        return self._mqtt

    @mqtt.setter
    def mqtt(self, value: Mqtt) -> None:
        # Error checks
        if not isinstance(value, Mqtt):
            raise TypeError("MQTT client must be a Mqtt object.")

        self._mqtt = value

    @property
    def gmail(self) -> Gmail:
        """
        Gmail client.

        Returns:
            Gmail: Gmail client.
        """
        return self._gmail

    @gmail.setter
    def gmail(self, value: Gmail) -> None:
        # Error checks
        if not isinstance(value, Gmail):
            raise TypeError("Gmail client must be a Gmail object.")

        self._gmail = value

    def add(self, alert: Alert) -> None:
        """
        Add alert.

        Args:
            alert (Alert): Alert to add.
        """

        self.logger.info(f"Adding alert: {alert}")

        self._alerts.append(alert)

    def remove(self, alert: Alert) -> None:
        """
        Remove alert.

        Args:
            alert (Alert): Alert to remove.
        """
        self._alerts.remove(alert)

    def run(self) -> None:
        """
        Run alert manager.
        """
        if self.mqtt is None:
            raise ValueError("MQTT client must be set.")

        self.mqtt.callback = self._mqtt_message_handler
        self.mqtt.connect()

    def _mqtt_message_handler(self, message: MqttMessage) -> None:
        """
        MQTT message handler.

        Args:
            message (MqttMessage): MQTT message.
        """
        self.logger.info(f"Message received: {message}")
        for alert in self._alerts:
            alert.check(message, self.gmail)

    def to_dict(self) -> dict:
        """
        Converts AlertManager object to dictionary representation.

        Returns:
            dict: Dictionary representation of AlertManager object.
        """

        dict = {}
        dict["alerts"] = [alert.to_dict() for alert in self._alerts]

        return dict

    def from_dict(self, data) -> None:
        """
        Converts dictionary representation to AlertManager object.

        Args:
            dict (dict): Dictionary representation of AlertManager object.
        """

        # Error checks
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")

        for alert in data["alerts"]:
            self.add(Alert().from_dict(alert))

    def to_json(self) -> str:
        """
        Converts AlertManager object to JSON string representation.

        Returns:
            str: JSON representation
        """

        data = {}
        data["alerts"] = [alert.to_json() for alert in self._alerts]

        jsonstr = json.dumps(data)

        return jsonstr

    def from_json(self, jsonstr: str) -> None:
        """
        Converts JSON string representation to AlertManager object.

        Args:
            json (str): JSON representation
        """

        # Error checks
        if not isinstance(jsonstr, str):
            raise TypeError("JSON must be a string.")

        data = json.loads(jsonstr)
        self.from_dict(data)

    def save(self, filename: str) -> None:
        """
        Saves AlertManager object to file as JSON.

        Args:
            filename (str): Filename.
        """

        jsonstr = self.to_json()
        with open(filename, "w") as f:
            f.write(jsonstr)

    def load(self, filename: str):
        """
        Loads AlertManager object from JSON file.

        Args:
            filename (str): File to load.
        """


if __name__ == "__main__":
    # Logging config
    logging.basicConfig(
        filename="alerts.log",
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create MQTT client
    mqtt = Mqtt(ipaddr="192.168.0.120", port=1885)

    # Create Gmail client
    gmail = Gmail()

    # Create alert manager
    alert_manager = AlertManager(mqtt=mqtt, gmail=gmail)

    # Add alert to manager
    alert_manager.add(
        Alert(
            topic="device/#",
            email="5034490111@mms.att.net",
            condition="temperature < 33",
            period_minimum=dt.timedelta(hours=1),
            period_maximum=dt.timedelta(days=1),
        )
    )

    alert_manager.add(
        Alert(
            topic="device/#",
            email="5034490111@mms.att.net",
            condition="temperature < 40",
            period_minimum=dt.timedelta(hours=4),
            period_maximum=dt.timedelta(days=1),
        )
    )

    # Run alert manager
    alert_manager.run()
