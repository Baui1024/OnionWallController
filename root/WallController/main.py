from dbus_next.aio import MessageBus
import dbus_next
from bluetooth import Bluetooth
from apisocket import APIServer
from agent import Agent
import asyncio
import json
from display import Display
import os



class WallController:
    def __init__(self):
        pass
        self.loop = asyncio.get_event_loop()
        self.socket = APIServer()
        self.display = Display()
        self.agent = Agent()
        self.socket.passDisplay(self.display)
        self.startLoop()
        self.bluetooth = None

    async def main(self):
        bus = await MessageBus(bus_type=dbus_next.BusType(2)).connect()
        
        # the introspection xml would normally be included in your project, but
        # this is convenient for development
        #/org/bluez/hci is adapter related but /org/bluez containts the manager and profiles 
        
        
        #introspection for the different dbus paths
        bluez_introspection = await bus.introspect("org.bluez", "/org/bluez")
        dongle_introspection = await bus.introspect("org.bluez", "/org/bluez/hci0")
        myphone_introspection = await bus.introspect("org.bluez", "/org/bluez/hci0/dev_D4_3A_2C_94_FD_78")
        
        #proxy object for whole bluetooth
        bluez_proxy = bus.get_proxy_object("org.bluez", "/org/bluez",bluez_introspection)
        #proxy object for the bluetoothdongle
        dongel_proxy = bus.get_proxy_object("org.bluez", "/org/bluez/hci0",dongle_introspection)

        agent_path = "/test/adapter"
        #exporting the Agent as a service to dbus
        bus.export(agent_path, self.agent)
        #await bus.request_name('org.bluez.Agent1')
        
        #create bluetooth object with helpers and pass it to our server
        self.bluetooth = Bluetooth(bus)
        await self.bluetooth.power_on() #make sure adapter is powered on start  
        await self.bluetooth.register_player() #registering the player for UUID
        #self.loop.create_task(self.bluetooth.get_metadata())
        self.loop.create_task(self.bluetooth.keep_devices_updated())
        self.loop.create_task(self.bluetooth.testBlocking())
        self.socket.passBluetooth(self.bluetooth)
        print("passed bluetooth",self.bluetooth)
        
        #create monitor for changes on bt:
        def callback(interface_name, changed_properties, invalidated_properties):
            for changed, variant in changed_properties.items():
                print(f'property changed: {changed} - {variant.value}')

        dongle_interface = dongel_proxy.get_interface("org.freedesktop.DBus.Properties")
        dongle_interface.on_properties_changed(callback)



        #register the Agent Class to BlueZ
        bluez_agent_manager = bluez_proxy.get_interface("org.bluez.AgentManager1")
        await bluez_agent_manager.call_register_agent(agent_path,"NoInputNoOutput")
        await bluez_agent_manager.call_request_default_agent(agent_path)

        device_introspection = await bus.introspect("org.bluez", agent_path)
        #device_proxy = bus.get_proxy_object("org.bluez","/org/bluez/hci0/dev_D4_3A_2C_94_FD_78/player0",device_introspection)
        #print("agent:",device_introspection.tostring())
        await self.bluetooth.stop_pairing()


        self.loop.create_task(self.socket.sendTX())   
        self.loop.create_task(self.socket.run())
        self.loop.create_task(self.socket.handle_encoder_events())

        #register the Headset Profile to BlueZ
        #bluez_profile_manager = bluez_proxy.get_interface("org.bluez.ProfileManager1")
        #await bluez_profile_manager.call_register
        #print(agent.introsp    ect().methods)
        #await agent.call_release()

        #print(await bluetooth.get_name())
        #await bluetooth.set_name("test123")
        #print(await bluetooth.get_name())

        #print("---------------------\n",bluez_introspection.tostring())
        #print("---------------------\n",dongle_introspection.tostring())
        #print("---------------------\n",device_introspection.tostring())
        print("---------------------\n",myphone_introspection.tostring())
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
        
        
    def startLoop(self):
        os.nice(19)
        #print(f"the nicenes of main is: {os.nice(0)} ")
        #asyncio.set_event_loop_policy(TimedEventLoopPolicy())
        self.loop.create_task(self.main())
        self.loop.set_debug(False)
        self.loop.run_forever()
    
if __name__ == "__main__":
    WallController()