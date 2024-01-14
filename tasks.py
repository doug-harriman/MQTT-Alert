from invoke import task


@task
def mqtt(ctx, ipaddr: str = "192.168.0.120", port: int = 1885):
    """
    Blocking task to monitor MQTT traffic on subject "device/#".

    Args:
        ipadd (str, optional): IP address of MQTT broker. Defaults to 192.168.0.120
        port (int, optional): IP Port of MQTT broker . Defaults to 1885.
    """

    from mqttalert import Mqtt

    print(f"Monitoring MQTT traffic on {ipaddr}:{port}", flush=True)
    m = Mqtt(ipaddr=ipaddr, port=port)
    m.connect()


@task
def email(
    ctx,
    email: str,
    message: str,
    subject: str = None,
    server: str = "smtp.gmail.com",
    port: int = 587,
):
    """
    Send email message via GMail SMTP server.

    Args:
        email (str): Recipient email address.
        message (str): Message to send.
        subject (str,optional): Message subject.
        server (str, optional): Server name. Defaults to "smtp.gmail.com".
        port (int, optional): Server port. Defaults to 587.
    """

    from mqttalert import Gmail

    print(f"Sending email to {email}", flush=True)
    g = Gmail(server=server, port=port)
    g.email_send(email, message, subject)


@task
def sms(
    ctx,
    number: str,
    message: str,
    subject: str = None,
    carrier: str = "ATT",
    server: str = "smtp.gmail.com",
    port: int = 587,
):
    """
    Send SMS message via GMail SMTP server.

    Args:
        number (str): Recipient phone number.
        message (str): Message to send.
        subject (str,optional): Message subject.  Defaults to empty.
        carrier (str, optional): Carrier name. Defaults to "ATT".
        server (str, optional): Server name. Defaults to "smtp.gmail.com".
        port (int, optional): Server port. Defaults to 587.

    """

    from mqttalert import Gmail

    print(f"Sending SMS to {number}", flush=True)
    g = Gmail(server=server, port=port)
    g.sms_send(number, message, carrier, subject=subject)


@task
def carriers(cxt):
    """
    Lists supported SMS carriers (US only).
    """

    from mqttalert import CARRIERS

    print("Supported SMS carrier names:")
    for carrier in CARRIERS:
        print(f"  {carrier}")
