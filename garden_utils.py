# Choose to use dummy
DUMMY = True

if DUMMY:
    from dummy_gpiozero import DigitalOutputDevice, DigitalInputDevice
else:
    from gpiozero import DigitalOutputDevice, DigitalInputDevice

# GPIO DEVICE ALLOCATION
ACT_VALVE = DigitalOutputDevice(17)
ACT_PUMP = DigitalOutputDevice(25)
SNS_TANK_FULL = DigitalInputDevice(21)
SNS_TANK_EMPTY = DigitalInputDevice(20)
SNS_WELL_EMPTY = DigitalInputDevice(16)
SNS_RAIN = DigitalInputDevice(12)

# Gets the status of the pump
def get_pump_status ():
    status = False
    status = ACT_PUMP.is_active
    return status

# Sets and returns status of the pump
def set_pump_status ( status ):
    if status:
        ACT_PUMP.on()
    else:
        ACT_PUMP.off()
    status = ACT_PUMP.is_active
    return status

# Gets the status of the valve
def get_valve_status ():
    status = False
    status = ACT_VALVE.is_active
    return status

# Sets and returns status of the valve
def set_valve_status ( status ):
    if status:
        ACT_VALVE.on()
    else:
        ACT_VALVE.off()
    status = ACT_VALVE.is_active
    return status

# Gets the status of the tank full sensor
def get_tank_full_status ():
    status = False
    status = SNS_TANK_FULL.is_active
    return status

# Gets the status of the tank empty sensor
def get_tank_empty_status ():
    status = False
    status = SNS_TANK_EMPTY.is_active
    return status

# Gets the status of the well empty sensor
def get_well_empty_status ():
    status = False
    status = SNS_WELL_EMPTY.is_active
    return status

# Gets the status of the rain sensor
def get_rain_status ():
    status = False
    status = SNS_RAIN.is_active
    return status
