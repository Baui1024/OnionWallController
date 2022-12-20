from dbus_next.aio import MessageBus
from dbus_next import Variant, DBusError
import os
import asyncio
import re


class Bluetooth():
    def __init__(self,MessageBus):
        self.bus = MessageBus
        self.paired_devices = []
        self.paired_devices_name = []
        self.discovering = False
        self.name = ""
        self.mac = ""
        self.connected_device_name = ""
        self.connected_device_mac = ""
        self.current_artist = ""
        self.current_song = ""
        self.current_album = ""
        self.current_song_duration = 0
        self.current_song_position = 0

##############################################
#
#   Global Proxy & Interface Creation     
#
##############################################
    async def get_adapter_proxy(self):
        dongle_introspection = await self.bus.introspect("org.bluez", "/org/bluez/hci0")
        return self.bus.get_proxy_object("org.bluez", "/org/bluez/hci0", dongle_introspection)

    async def get_adapter_interface(self):
        proxy = await self.get_adapter_proxy()
        return proxy.get_interface("org.bluez.Adapter1")
    
    async def get_properties_interface(self):
        proxy = await self.get_adapter_proxy()
        return proxy.get_interface('org.freedesktop.DBus.Properties')

    async def get_device_interface(self,device_mac):
        device_introspection = await self.bus.introspect("org.bluez", "/org/bluez/hci0/dev_"+device_mac)
        device_proxy = self.bus.get_proxy_object("org.bluez","/org/bluez/hci0/dev_"+device_mac,device_introspection)
        device_interface = device_proxy.get_interface("org.bluez.Device1")
        return device_interface

    async def get_player_proxy(self,mac):
        path = f"/org/bluez/hci0/dev_{mac}/player0"
        device_introspection = await self.bus.introspect("org.bluez", path)
        return self.bus.get_proxy_object("org.bluez",path,device_introspection)

    async def get_player_interface(self,mac):
        try:
            player_proxy = await self.get_player_proxy(mac)
            return player_proxy.get_interface("org.bluez.MediaPlayer1")
        except DBusError:
            raise

##############################################
#
#   Properties & Signal Listener Functions     
#
##############################################

    def listen_to_adapter_properties(self,interface_name, changed_properties, invalidated_properties):
        for changed, variant in changed_properties.items():
            print(f'property changed: {changed} - {variant.value}')

    def listen_to_device_properties(self,interface_name, changed_properties, invalidated_properties):
        for changed, variant in changed_properties.items():
            pass
            #print(f'property changed: {changed} - {variant.value}')

    def listen_to_media_properties(self,interface_name, changed_properties, invalidated_properties):
        for changed, variant in changed_properties.items():
            print(f'property changed: {changed} - {variant.value}')
            if changed == "Track":
                for key, value in variant.value.items():
                    #print(key,str(value.value)) 
                    if key == "Artist":
                        self.current_artist = str(value.value)
                    elif key == "Album":
                        self.current_album = str(value.value)
                    elif key == "Title":
                        self.current_song = str(value.value)
                    elif key == "Duration":
                        time = int(value.value/1000)
                        self.current_song_duration = time 
            elif changed == "Position":
                time = int(variant.value/1000)
                self.current_song_position = time

##############################################
#
#   Event Loop Functions      
#
##############################################


    async def get_metadata(self):
        while True:
            try:
                if self.connected_device_mac != "":
                    try:
                        player_proxy = await self.get_player_proxy(self.connected_device_mac)
                        #player_properies_interface = player_proxy.get_interface("org.freedesktop.DBus.Properties")
                        #player_properies_interface.on_properties_changed(self.listen_to_media_properties)
                        #all = await player_properies_interface.call_get_all("org.bluez.MediaPlayer1")
                        #self.listen_to_media_properties("org.bluez.MediaPlayer1",all,"nothing")
                        player_interface = player_proxy.get_interface("org.bluez.MediaPlayer1")
                        position = await player_interface.get_position()
                        track = await player_interface.get_track()
                        for changed, variant in track.items():
                            if changed == "Artist":
                                self.current_artist = str(variant.value)
                            elif changed == "Album":
                                self.current_album = str(variant.value)
                            elif changed == "Title":
                                self.current_song = str(variant.value)
                            elif changed == "Duration":
                                time = variant.value
                                self.current_song_duration = time
                        #print(os.times(),position)
                        self.current_song_position = position
                        #self.listen_to_media_properties("org.bluez.MediaPlayer1",position,"nothing")
                    except DBusError:
                        #print(err)
                        self.metadata_reset()   
                await asyncio.sleep(1)
            except DBusError as err:
                print(err)

    async def keep_devices_updated(self):
        try:
            while True:
                await self.get_devices()
                await asyncio.sleep(6)
        except DBusError:
            raise

##############################################
#
#   Utils functions & API      
#
##############################################

    async def get_devices(self):
        try:          
            adapter_proxy = await self.get_adapter_proxy()
            device_connected = False
            for components in adapter_proxy.introspection.nodes:
                device_mac = components.name[4:]
                device_interface = await self.get_device_interface(device_mac)
                if await device_interface.get_paired() and device_mac not in self.paired_devices:
                    print(device_mac)
                    self.paired_devices.append(device_mac)
                    self.paired_devices_name.append(await device_interface.get_name())
                    await device_interface.set_trusted(True)
                    
                if await device_interface.get_connected():
                    #to do - request UUID maybe but maybe trust does the trick 
                    self.connected_device_name = await device_interface.get_name()
                    self.connected_device_mac = device_mac 
                    device_connected = True
                    #device_properties_interface = device_proxy.get_interface("org.freedesktop.DBus.Properties")
                    #device_properties_interface.on_properties_changed(self.listen_to_device_properties)
                    #metadata listener
                    #
                                       
            if not device_connected:
                self.metadata_reset()
                #await self.try_connect()
                for components in adapter_proxy.introspection.nodes:
                    device_mac = components.name[4:]
                    device_interface = await self.get_device_interface(device_mac)    
                    if await device_interface.get_paired():
                        try:
                            await device_interface.call_connect()                
                            print("actively connected to: "+device_mac)
                            player_proxy = await self.get_player_proxy(device_mac)
                            player_properies_interface = player_proxy.get_interface("org.freedesktop.DBus.Properties")
                            player_properies_interface.on_properties_changed(self.listen_to_media_properties)
                        except:
                            print("device not ready:"+device_mac)

        except DBusError:
            raise

    async def try_connect(self):
        try:
            adapter_interface = await self.get_adapter_interface()
            self.discovering = True
            await adapter_interface.call_start_discovery()
            await asyncio.sleep(10)
            result = await adapter_interface.call_stop_discovery()
            self.discovering = False
            print(result)
            
        except DBusError:
            raise
            


    def metadata_reset(self):
        self.connected_device_name = ""
        self.connected_device_mac = "" 
        self.current_song = ""
        self.current_album = ""
        self.current_artist = ""
        self.current_song_duration = 0
        self.current_song_position = 0   

    async def get_mac(self):
        try:
            adapter = await self.get_adapter_interface()
            mac = await adapter.get_address()
            self.mac = mac
            return self.mac
        except DBusError:
            raise

    async def get_name(self):
        try:
            adapter = await self.get_adapter_interface()
            name = await adapter.get_alias()
            self.name = name
            return self.name
        except DBusError:
            raise

    async def set_name(self,name):
        try:
            adapter = await self.get_adapter_interface()
            await adapter.set_alias(name)
        except DBusError:
            raise

    async def disconnect_device(self,device_mac):
        device = await self.get_device_interface(device_mac)
        await device.call_disconnect()

    async def remove_device_name(self,name):
        try:
            await self.remove_device(self.paired_devices[self.paired_devices_name.index(name)])
        except:
            print("Device can't be removed. Not in List")

    async def remove_device(self,mac):
        try: 
            #await self.get_devices()
            await self.disconnect_device(mac)
            self.paired_devices.clear()
            self.paired_devices_name.clear()
            adapter = await self.get_adapter_interface()
            await adapter.call_remove_device("/org/bluez/hci0/dev_"+mac)
            await self.get_devices()
        except DBusError:
            raise
    
    async def remove_all_devices(self):
        try:
            await self.get_devices()
            for mac in self.paired_devices:
                await self.remove_device(mac)
                print("deleted:", mac)
        except DBusError:
            raise

    async def start_pairing(self):
        try:
            adapter = await self.get_adapter_interface()
            if not await adapter.get_powered():
                await self.power_on()
            await adapter.set_pairable(True)
            await adapter.set_discoverable(True)
        except DBusError:
            raise
    
    async def change_pairing_timeout(self,timeout):
        try:
            adapter = await self.get_adapter_interface()
            if not await adapter.get_powered():
                await self.power_on()
            await adapter.set_discoverable_timeout(timeout)
            await adapter.set_pairable_timeout(timeout)
        except DBusError:
            raise

    async def stop_pairing(self):
        try:
            adapter = await self.get_adapter_interface()
            await adapter.set_discoverable(False)
            await adapter.set_pairable(False)
        except DBusError:
            raise
    
    async def get_pairing_state(self):
        adapter = await self.get_adapter_interface()
        return await adapter.get_pairable()
        
    async def get_paired_devices(self):
        #await self.get_devices()
        return self.paired_devices_name

    async def get_connected_device_mac(self):
        #await self.get_devices()
        return self.connected_device_mac

    async def get_connected_device_name(self):
        await self.get_devices()
        return self.connected_device_name

    async def power_on(self):
        try:
            adapter = await self.get_adapter_interface()
            await adapter.set_powered(True)
        except DBusError:
            raise
                
    async def media_control(self,cmd):
        try:
            mac = await self.get_connected_device_mac()
            if mac == "":
                return
            player = await self.get_player_interface(mac)
            if cmd == "play":
                await player.call_play()
            elif cmd == "stop":
                await player.call_stop()
            elif cmd == "pause":
                await player.call_pause()
            elif cmd ==  "prev":
                await player.call_previous()
            elif cmd ==  "next":
                await player.call_next()
        except DBusError:
            raise