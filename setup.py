from setuptools import setup, find_packages

VERSION = "0.0.1"
DESCRIPTION = "MQTT monitoring and email alert system."
LONG_DESCRIPTION = (
    "Monitors MQTT topics and sends email alerts when conditions are met."
)

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="mqttalert",
    version=VERSION,
    author="Doug Harriman",
    author_email="doug.harriman@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        "keyring",
        "keyrings.alt",
        "ipaddress",
        "paho-mqtt",
        "invoke",
    ],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'
    keywords=["python", "mqtt", "email", "alert"],
    classifiers=[],
)
