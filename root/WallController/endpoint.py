from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next import Variant, DBusError

SBC_CONFIGURATION = [b'0x21', b'0x15', b'2', b'32']

class Endpoint(ServiceInterface):
    def __init__(self):
        super().__init__('org.bluez.MediaEndpoint1')
        self.configuration = SBC_CONFIGURATION
        print("Endpoint created")

    @method()
    def Release(self):
        try:
            print("endpoint has been released")
        except DBusError:
            raise

    @method()
    def ClearConfiguration(self):
        print("clear configuration")

    @method()
    def SetConfiguration(self, transport: 's', config: 's'):
        try: 
            print("SetConfiguration (%s, %s)" % (transport, config))
            return 
        except DBusError:
            raise
    
    @method()
    def SelectConfiguration(self, caps: 's'):
        try: 
            print("SelectConfiguration (%s)" % (caps))
            return self.configuration
        except DBusError:
            raise


    #@dbus.service.method(AGENT_INTERFACE,
    #                in_signature="os", out_signature="")
    #def AuthorizeService(self, device, uuid):
    #  print("Some stuff and things")
