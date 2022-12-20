from dbus_next.aio import MessageBus
import dbus_next
from bluetooth import Bluetooth
from apisocket import APIServer
from agent import Agent
import asyncio
import json



class WallController:
    def __init__(self):
        pass
        self.loop = asyncio.get_event_loop()
        self.socket = APIServer()
        self.startLoop()
        self.bluetooth = None

    async def main(self):
        bus = await MessageBus(bus_type=dbus_next.BusType(2)).connect()
        
        # the introspection xml would normally be included in your project, but
        # this is convenient for development
        #/org/bluez/hci is adapter related but /org/bluez containts the manager and profiles 
        
        #creating Agent that handles pairing
        agent = Agent()
        
        #introspection for the different dbus paths
        bluez_introspection = await bus.introspect("org.bluez", "/org/bluez")
        dongle_introspection = await bus.introspect("org.bluez", "/org/bluez/hci0")
        
        #proxy object for whole bluetooth
        bluez_proxy = bus.get_proxy_object("org.bluez", "/org/bluez",bluez_introspection)
        
        #exporting the Agent as a service to dbus
        bus.export('/org/bluez/Agent1', agent)

        #create bluetooth object with helpers and pass it to our server
        self.bluetooth = Bluetooth(bus)
        await self.bluetooth.power_on() #make sure adapter is powered on start  
        await self.bluetooth.get_devices()
        self.loop.create_task(self.bluetooth.get_metadata())
        self.loop.create_task(self.bluetooth.keep_devices_updated())
        self.socket.passBluetooth(self.bluetooth)

        #register the Agent Class to BlueZ
        bluez_agent_manager = bluez_proxy.get_interface("org.bluez.AgentManager1")
        await bluez_agent_manager.call_register_agent("/org/bluez/Agent1","NoInputNoOutput")
        await bluez_agent_manager.call_request_default_agent("/org/bluez/Agent1")

        device_introspection = await bus.introspect("org.bluez", "/org/bluez/hci0/dev_8C_7A_AA_55_44_26/player0")
        device_proxy = bus.get_proxy_object("org.bluez","/org/bluez/hci0/dev_8C_7A_AA_55_44_26/player0",device_introspection)
        print(device_introspection.tostring())
        #register the Headset Profile to BlueZ
        #bluez_profile_manager = bluez_proxy.get_interface("org.bluez.ProfileManager1")
        #await bluez_profile_manager.call_register
        #print(agent.introspect().methods)
        #await agent.call_release()

        #print(await bluetooth.get_name())
        #await bluetooth.set_name("test123")
        #print(await bluetooth.get_name())

        #print("---------------------\n",bluez_introspection.tostring())
        #print("---------------------\n",dongle_introspection.tostring())
        #print("---------------------\n",device_introspection.tostring())
        #print("---------------------\n",agent_introspection.tostring())
        #await bluez_agent_manager.call_unregister_agent("/org/bluez/superagent")
        #dongle_proxy = bus.get_proxy_object("org.bluez", "/org/bluez/hci0", dongle_introspection)
        #player = dongle_proxy.get_interface("org.bluez.Adapter1")
        #for method in agent.introspect().methods:
        #    print(method.name)        
        
        #await bluetooth.get_devices()
        #await bluetooth.remove_all_devices()
        #await self.bluetooth.stop_pairing()
        #await bluetooth.start_pairing(timeout=120)
        # call methods on the interface (this causes the media player to play)
        #await player.RegisterProfile("0000110b-0000-1000-8000-00805F9B34FB")
        #result = await player.get_address()
        #await player.set_powered(True)
        #print(result)
        #await player.call_start_discovery()
        
        await self.bluetooth.stop_pairing()
    def startLoop(self):
        #await Bluetooth.start()
        self.loop.create_task(self.main())
        self.loop.create_task(self.socket.sendTX())   
        self.loop.create_task(self.socket.run())
        self.loop.run_forever()
    
if __name__ == "__main__":
    WallController()