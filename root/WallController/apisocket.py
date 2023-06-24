import asyncio
import json
#from main import WallController
import re
import subprocess
import gpiod
import array
import gc
import queue
from encoder2 import Encoder

#from heartbeat import heartbeat  # Optional LED flash

class APIServer():
    
    def __init__(self,host='0.0.0.0', port=1666, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout
        self.bluetooth = None
        self.display = None
        self.tx_buf = []
        self.connections = {}
        self.available_zones = []
        self.available_gains = {}
        self.current_zone = ""
        self.zone_select = False
        self.encoder = Encoder(self)
        self.encoder_queue = []
        self.encoderModifierIncrease = 0.01
        self.encoderModifierLimit = 0.05
        self.encoderModifierLeft = 0
        self.encoderModifierRight = 0

    def passBluetooth(self,bt):
        self.bluetooth = bt
    
    def passDisplay(self,display):
        self.display = display

    def showIP(self):
        NIC = "eth0"
        output = subprocess.run('ifconfig '+ NIC, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
        #output = process.stdout
        IP = re.search("addr:\d*.\d*.\d*.\d*",output).group(0)[5:]
        SN = re.search("Mask:\d*.\d*.\d*.\d*",output).group(0)[5:]
        output = subprocess.run('ip r', shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
        #output = process.stdout
        GW = re.search("via \d*.\d*.\d*.\d*",output).group(0)[4:]
        self.display.show_network_settings(IP,SN,GW)

    async def sendTX(self):
        while True:
            try:
                for x in self.tx_buf:
                    #print(x)
                    await self.sendData(x)
                self.tx_buf.clear()
            except:
                raise
            #heavily influences cpu load
            await asyncio.sleep(0.01)

    async def send_whole_state(self):
        data = {"devices" : self.bluetooth.paired_devices_name}
        data["connected_device"] = self.bluetooth.connected_device_name
        data["pairing_state"] = await self.bluetooth.get_pairing_state()
        data["mac"] = self.bluetooth.mac
        data2 = {"all" : data}
        data2 = json.dumps(data2)
        self.tx_buf.append(data2)

    async def run(self):
        self.showIP()
        self.cid = 0
        self.server = await asyncio.start_server(self.run_client, self.host, self.port)
        while True: 
            await asyncio.sleep(100)

    async def run_client(self, sreader, swriter):
        self.cid += 1
        localID = self.cid
        self.connections[str(self.cid)] = swriter
        print('Got connection from client', self.cid, swriter.get_extra_info('peername'))
        self.config_pulseaudio(swriter.get_extra_info('peername')[0])
        if self.bluetooth != None:
            await self.send_whole_state()
        try:
            while True:
                try:
                    data = await asyncio.wait_for(sreader.read(10000), self.timeout)
                    length = int.from_bytes(data[:1], "big")   
                    position = 0
                    while position < len(data):
                        cmd = data[position+1:position+length+1]
                        if self.bluetooth != None:
                            await self.parseData(cmd)
                        #print(cmd,self.bluetooth)
                        position = position + length +1 
                        length = int.from_bytes(data[position:position+1], "big") 
                except asyncio.TimeoutError:
                    data = b''
                if data == b'':
                    raise OSError
        except OSError:
            pass
        print('Client {} disconnect.'.format(self.cid))
        self.connections.pop(str(localID))
        print('Client {} socket closed.'.format(self.cid))
        if len(self.connections) == 0:
            self.showIP()
		
    async def sendData(self,data):
        if len(self.connections) == 0:
            self.tx_buf.clear()
        for connection in self.connections:
            try:
                #print(data)
                self.connections[connection].write((data+"\r").encode('utf_8'))
                await self.connections[connection].drain()
            except asyncio.TimeoutError:
                raise OSError
            
    async def parseData(self,data):
        try:
            data = data.decode("UTF-8")
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                print("couldn't parse data, possible buffer overflow")
            print(data)
            for key in data:
                if key == "keepAlive":
                    pass 
                elif key == "get":
                    if data[key] == "all":
                        await self.send_whole_state()
                elif key == "pairing":
                    print("pairing:",data[key])
                    if data[key]:
                        await self.bluetooth.start_pairing()
                        self.display.show_pairing_state(await self.bluetooth.get_name())
                    else:
                        await self.bluetooth.stop_pairing()
                        self.display.show_pairing_result("Pairing Stopped")
                elif key == "remove_all_devices":
                    await self.bluetooth.remove_all_devices()
                elif key == "remove_device":
                    await self.bluetooth.remove_device_name(data[key])
                elif key == "set_name":
                    await self.bluetooth.set_name(data[key])
                elif key == "media_control":
                    await self.bluetooth.media_control(data[key])
                elif key == "get_metadata":
                    #await self.bluetooth.get_metadata()
                    if self.bluetooth.current_song != data[key]["song"] or self.bluetooth.current_album != data[key]["album"] or self.bluetooth.current_artist != data[key]["artist"]:
                        await self.sendData(json.dumps({"metadata":{"song" : self.bluetooth.current_song,
                                                            "album" : self.bluetooth.current_album,
                                                            "artist" : self.bluetooth.current_artist
                                                            }}))
                    await self.sendData(json.dumps({"song_progress":{"duration" : self.bluetooth.current_song_duration,
                                                    "position" : self.bluetooth.current_song_position}}))
                elif key == "gain":
                    self.current_zone = data[key]["zone"]
                    self.available_gains[self.current_zone] = data[key]["gain"]
                    if not self.zone_select:
                        self.display.show_zone_level(data[key]["gain"],data[key]["zone"]) 
                elif key == "zone_names":
                    self.available_zones.clear()
                    self.available_gains.clear()
                    for zonedata in data[key]:
                        #print(zonedata)
                        self.available_gains.update(zonedata)
                        for zonename in zonedata.keys():
                            self.available_zones.append(zonename)
                    self.display.create_zones(self.available_zones)
                    print(self.available_gains)
        except Exception as error:
            raise
            print("parsingerror: " + str(error))

    async def close(self):
        print('Closing server')
        self.server.close()
        #await self.server.wait_closed()
        print('Server closed.')

    async def handle_encoder_events(self):
        while True:
            #print(self.encoder_queue)
            if self.encoder_queue:
                event = self.encoder_queue.pop()
                if event[0] == "left":
                    new_gain = event[1]
                    data =  {"vol_down" : new_gain}
                    self.display.show_zone_level(
                        self.available_gains[self.current_zone],
                        self.current_zone
                    )
                    self.tx_buf.append(json.dumps(data))
                elif event[0] == "right":
                    new_gain = event[1]
                    data =  {"vol_up" : new_gain}
                    self.display.show_zone_level(
                        self.available_gains[self.current_zone],
                        self.current_zone
                    )
                    self.tx_buf.append(json.dumps(data))

            await asyncio.sleep(0.01)

    def config_pulseaudio(self,ip):
        pulseconfig = open("/etc/pulse/system.pa")
        output_file = ""
        for line in pulseconfig:
            
            if re.search("load-module module-rtp-send source=rtp.monitor destination=",line):
                try:
                    if ip == re.search("\d+.\d+.\d+.\d+",line).group(0):
                        print("same ip")
                        return
                except:
                    raise
                output_file += f"load-module module-rtp-send source=rtp.monitor destination={ip} port=46998\n"
            else:
                output_file += line
            pass
        pulseconfig.close()
        new_pulseconfig = open("/etc/pulse/system.pa","w")
        new_pulseconfig.write(output_file)
        new_pulseconfig.close()
        subprocess.run(["killall", "pulseaudio"])
        subprocess.run(["/etc/init.d/pulseaudio","start"])