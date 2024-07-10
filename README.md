garden.proto:
  - Holds the message definitions specified in a Google protocol buffer 3 standard.
  - They are currently compiled using version 5.27.2 of protobuf, if you are using a different version you should recompile them.

garden_pb2.py:
  - The compiled python version of the garden.proto. Will be generated when running the protoc compiler on garden.proto: 'protoc --python_out=./ garden.proto' or something along those lines.

garden_utils.py:
  - Contains the interface to my dad's Raspberry Pi's GPIO. He has 2 digital output devices configured to control the pump relay and valve solenoid. There are also 4 digital input devices to read the tank full, tank empty, well empty, and rain sensors.
  - If running on desktop you should probably leave DUMMY = True to use the duped versions of the gpiozero classes. Otherwise I imagine you would have to deal with actual gpiozero.

dummy_gpiozero.py:
  - Contains the duped versions of the digital output device and digital input device, to be used during development absent a Raspberry Pi.

garden_daemon.py:
  - This is the server meant to be run on my dad's Raspberry Pi Zero configured with the GPIO specified in garden_utils.py. If you're running this not on an RPi then you should leave DUMMY = True.
  - The main process is in charge of sending and receiving messages specified in garden.proto.
  - The gardener process is in charge of handling requests and running routine garden tasks (checking sensors and toggling the pump/valve as needed, etc).

remote_gardener_cmd.py:
  - A terminal version of the client. Has secret options -1 and -2. -1 allows you to toggle the state of a sensor when using the dummy_gpiozero classes. -2 allows you to shutdown the garden_daemon.py server.

remote_gardener_gui.py:
  - A GUI client built using PyQt6. During development on desktop, leave DEMO_MODE = True, this will allow you to toggle the state of sensors for testing while using dummy_gpiozero by clicking on the state of a sensor. Similar to -1 secret option while running remote_gardener_cmd.py.
