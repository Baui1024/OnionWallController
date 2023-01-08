import asyncio
import json
#from main import WallController
import re
import subprocess
import array
import gc

#from heartbeat import heartbeat  # Optional LED flash

class APIServer():
    
    def __init__(self,host='0.0.0.0', port=1666, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout
        self.version = 0.1
        self.bluetooth = None
		#self.i2c = SoftI2C(sda=Pin(15),scl=Pin(14))
		#self.display = Display(self.i2c,self.nic)
        self.encoderModifierLeft = 0
        self.encoderModifierRight = 0
		#self.interuptPin = Pin(35,Pin.IN,Pin.PULL_UP)
		#self.interuptPin.irq(handler=self.safeInterupt, trigger=Pin.IRQ_FALLING)
        self.rxBuf = []
        self.txBuf = []
        self.activeLED = 1
        self.connections = {}
        self.availableZones = []
        self.availableGains = []
        self.currentZone = ""
        self.blinkingDisplay = False
	
    def getVersion(self):
        return self.version

    def passBluetooth(self,bt):
        self.bluetooth = bt

    async def sendTX(self):
        while True:
            try:
                for x in self.txBuf:
                    await self.sendData(x)
                self.txBuf.clear()
            except:
                raise
            #heavily influences cpu load
            await asyncio.sleep(0.005)

    async def send_whole_state(self):
        data = {"devices" : self.bluetooth.paired_devices_name}
        data["connected_device"] = self.bluetooth.connected_device_name
        data["pairing_state"] = await self.bluetooth.get_pairing_state()
        data["mac"] = self.bluetooth.mac
        data2 = {"all" : data}
        data2 = json.dumps(data2)
        self.txBuf.append(data2)

    async def run(self):
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
                    data = await asyncio.wait_for(sreader.read(5000), self.timeout)
                    length = int.from_bytes(data[:1], "big")   
                    position = 0
                    while position < len(data):
                        cmd = data[position+1:position+length+1]
                        if self.bluetooth != None:
                            await self.parseData(cmd)
                        #print(cmd)
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
            pass
            #self.display.showIP()
		
    async def sendData(self,data):
        if len(self.connections) == 0:
            self.txBuf.clear()
        for connection in self.connections:
            try:
                print(data)
                self.connections[connection].write((data+"\r").encode('utf_8'))
                await self.connections[connection].drain()
            except asyncio.TimeoutError:
                raise OSError
            
    async def parseData(self,data):
        try:
            data = data.decode("UTF-8")
            data = json.loads(data)
            #print(data)
            for key in data:
                if key == "keepAlive":
                    pass 
                elif key == "get":
                    if data[key] == "all":
                        await self.send_whole_state()
                elif key == "pairing":
                    if data[key]:
                        await self.bluetooth.start_pairing()
                    else:
                        await self.bluetooth.stop_pairing()
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
                    self.currentZone = data[key]["zone"]
                    #self.display.showVolume(data[key]["Gain"],data[key]["Zone"]) 
                #elif key == "availableZones":
                 #   if self.blinkingDisplay:
                  #      self.blinkingDisplay = False
                   #     self.display.stopBlink()
                    #    self.availableZones.clear()
                     #   self.availableGains.clear()
                      #  cmd = {"Zone set" : self.currentZone}
                       # self.txBuf.append(json.dumps(cmd))
                    #else:
                     #   self.blinkingDisplay = True
                      #  self.display.startBlink()
                       # index = 0
                        #for x in data[key]:
                         #   for zone in x:
                          #      self.availableZones.append(zone)
                           #     self.availableGains.append(x[zone])
        except Exception as error:
            raise
            print("parsingerror: " + str(error))

    async def close(self):
        print('Closing server')
        self.server.close()
        #await self.server.wait_closed()
        print('Server closed.')

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