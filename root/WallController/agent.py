from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next import Variant, DBusError


class Agent(ServiceInterface):
    def __init__(self):
        super().__init__('org.bluez.Agent1')
        self._bar = 105
        print("agent created")

    @method()
    def Release(self):
        try:
            print("agent has been released")
        except DBusError:
            raise

    @method()
    def RequestPinCode(self, device: 'o'):
        self._bar += 1
        try:
            print("PinCode Requested")
        except DBusError:
            raise

    @method()
    def RequestConfirmation(self, device: 'o', passkey: 'u'):
        self._bar += 1
        try: 
            print("requested confirmation")
            print("passkey: ", passkey)
            return 
        except DBusError:
            raise
    
    @method()
    def RequestAuthorization(self, device: 'o'):
        self._bar += 1
        try: 
            print("requested Authorization")
            #return 
        except DBusError:
            raise

    @method()
    def AuthorizeService(self, device: 'o', uuid: 's'):
        self._bar += 1
        try:
            print("UUID requested: ", uuid)
            return
        except DBusError:
            raise

    @dbus_property()
    def Bar(self) -> 'y':
        return self._bar
    
    @Bar.setter
    def Bar(self, val: 'y'):
        if self._bar == val:
            return

        self._bar = val

        self.emit_properties_changed({'Bar': self._bar})
    

    @method()
    def Cancel():
        print("something failed in agent")

    #@dbus.service.method(AGENT_INTERFACE,
    #                in_signature="os", out_signature="")
    #def AuthorizeService(self, device, uuid):
    #  print("Some stuff and things")
