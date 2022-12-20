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
    async def Release(self):
        try:
            print("agent has been released")
        except DBusError:
            raise

    @method()
    async def RequestPinCode(self, device: 'o'):
        try:
            print("PinCode Requested")
        except DBusError:
            raise

    @method()
    async def RequestConfirmation(self, device: 'o', passkey: 'u'):
        try: 
            print("requested confirmation")
            print("passkey: ", passkey)
            return 
        except DBusError:
            raise

    @method()
    async def AuthorizeService(self, device: 'o', uuid: 's'):
        try:
            print("UUID requested: ", uuid)
        except DBusError:
            raise

    @method()
    async def Cancel():
        print("something failed in agent")

    #@dbus.service.method(AGENT_INTERFACE,
    #                in_signature="os", out_signature="")
    #def AuthorizeService(self, device, uuid):
    #  print("Some stuff and things")
