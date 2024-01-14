# gmail.py
# Tools for sending email via gmail account.
# This module heavily borrows from: https://medium.com/testingonprod/how-to-send-text-messages-with-python-for-free-a7c92816e1a4

# For more information see: https://support.google.com/accounts/answer/185833

import keyring
import logging
import smtplib
from typing import Union

# Mapping of carrier names to email servers.
# As of 2024-01-13, US only.
CARRIERS = {
    "ATT": "@mms.att.net",
    "TMobile": "@tmomail.net",
    "Verizon": "@vtext.com",
    "Sprint": "@messaging.sprintpcs.com",
}


def sms_address(number: Union[str, int] = None, carrier: str = None):
    """
    Returns email address for SMS number (US only) based on carrier.
    If no inputs provided, returns all possible carriers.

    Args:
        number (str,int): Phone number.
        carrier (str): Carrier name.

    Returns:
        str: Email address.
    """
    global CARRIERS
    carrier_names = ", ".join(CARRIERS.keys())

    if carrier is None:
        raise ValueError(f"No carrier specified, valid carriers are: {carrier_names}")
    if not isinstance(carrier, str):
        raise TypeError("Carrier must be a string")

    # Convert carrier name to lowercase
    CARRIERS = {k.lower(): v for k, v in CARRIERS.items()}

    if carrier.lower() not in CARRIERS.keys():
        raise ValueError(
            f"Invalid carrier: '{carrier}'. Valid carriers: {carrier_names}"
        )

    if number is None:
        raise ValueError("No phone number specified")
    if not isinstance(number, (str, int)):
        raise TypeError("Phone number must be a string or integer")
    if isinstance(number, int):
        number = str(number)

    # Clean up phone number
    if isinstance(number, str):
        number = (
            number.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
        )
        number = (
            number.replace("+", "").replace(".", "").replace(",", "").replace(";", "")
        )

    if not number.isdigit():
        raise ValueError(f"Phone number must be all digits, got: {number}")
    if len(number) != 10:
        raise ValueError(f"Phone number must be 10 digits, got: {number}")

    return number + CARRIERS[carrier.lower()]


class Gmail:
    """
    GMail email helper class.
    """

    def __init__(
        self,
        server: str = "smtp.gmail.com",
        port: int = 587,
        email: str = None,
        password: str = None,
    ) -> None:
        """
        Initialize Gmail class.
        """

        # Logging config
        self.logger = logging.getLogger(__name__)

        self._server = None
        self.server = server

        self._port = None
        self.port = port

        self._email = None
        if email is not None:
            self.email = email

        self._password = None
        if password is not None:
            self.password = password

        # Use keyring stored values if available
        if self.email is None:
            try:
                self.email = keyring.get_password("Google", "email")
            except RuntimeError:
                self.logger.debug("Keyring (Google,email) not available")
        if self.password is None:
            try:
                self.password = keyring.get_password("Google", "app_password")
            except RuntimeError:
                self.logger.debug("Keyring (Google,app_password) not available")

        # Try to create SMPT server
        self._smtp_server = None
        try:
            self.connect()
        except Exception as e:
            pass

    @property
    def server(self) -> str:
        """
        SMTP server address.

        Returns:
            str: SMTP server address.
        """
        return self._server

    @server.setter
    def server(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("SMTP server address must be a string.")

        self._server = value

    @property
    def port(self) -> int:
        """
        SMTP server port.

        Returns:
            int: SMTP server port.
        """
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        # Error checks
        if not isinstance(value, int):
            raise TypeError("SMTP server port must be an integer.")

        self._port = value

    @property
    def email(self) -> str:
        """
        GMail email address.

        Returns:
            str: GMail email address.
        """
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("GMail email address must be a string.")

        self._email = value

    @property
    def password(self) -> str:
        """
        GMail app password.

        Returns:
            str: GMail password.
        """
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        # Error checks
        if not isinstance(value, str):
            raise TypeError("GMail password must be a string.")

        self._password = value

    @property
    def is_connected(self) -> bool:
        """
        Check if connected to SMTP server.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._smtp_server is not None

    @property
    def smtp_server(self) -> smtplib.SMTP:
        """
        Get SMTP server object.

        Returns:
            _type_: _description_
        """

        return self._smtp_server

    def connect(self) -> None:
        """
        Connect to SMTP server.
        """

        self._smtp_server = None

        if self.server is None:
            raise ValueError("GMail server not specified.")
        if self.port is None:
            raise ValueError("GMail server port not specified.")
        if self.email is None:
            raise ValueError("GMail account email address not specified.")
        if self.password is None:
            raise ValueError("GMail account app password not specified.")

        self._smtp_server = smtplib.SMTP(self._server, self._port)
        self._smtp_server.starttls()
        try:
            self._smtp_server.login(self._email, self._password)
        except smtplib.SMTPAuthenticationError as e:
            self.logger.debug("GMail login failed")
            self._smtp_server = None
            raise e

    def sms_send(
        self,
        number: Union[str, int],
        message: str,
        carrier: str = "ATT",
        subject: str = None,
    ):
        """
        Send SMS message.

        Args:
            number (str,int): Recipient phone number.
            message (str): Message to send.
            carrier (str): Carrier name.
            subject (str,optional): Message subject.
        """
        email = sms_address(number, carrier)
        self.email_send(email, message, subject)

    def email_send(self, email: str, message: str, subject: str = None) -> None:
        """
        Send email message.

        Args:
            recipient (str): Recipient email address.
            message (str): Message to send.
        """
        if self._smtp_server is None:
            raise ValueError("GMail server not initialized")

        if not self.is_connected:
            self.connect()

        if subject is not None:
            message = f"Subject: {subject}\n\n{message}"

        try:
            self._smtp_server.sendmail(self._email, email, message)
        except Exception as e:
            self.logger.debug(f"GMail send failed: {e}")
            raise e
