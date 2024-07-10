# This is a dummy version of gpiozero so I can use it while testing and developing

class DigitalInputDevice:
    
    def __init__ ( self, pin ):
        self.pin = pin
        self.is_active = False

class DigitalOutputDevice:
    
    def __init__ ( self, pin ):
        self.pin = pin
        self.is_active = False

    def on ( self ):
        self.is_active = True

    def off ( self ):
        self.is_active = False