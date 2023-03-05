import select
from threading import Timer,Thread
import asyncio
import json
import time

class Encoder():
    def __init__(self,apisocket):
        self.gpio_id = 480
        self.offset_left = self.gpio_id+22
        self.offset_right = self.gpio_id+21
        self.offset_pairing = self.gpio_id + 24
        self.offset_encoder = self.gpio_id + 23
        self.encoderModifierLeft = 0
        self.encoderModifierRight = 0
        self.value_file_left = None
        self.value_file_right = None
        self.value_file_pairing = None
        self.value_file_encoder = None
        self.left_lock = False
        self.right_lock = False
        self.timer = None
        self.timeout = 0.3
        self.encoder_timer = None
        self.encoder_timeout = 0.05
        self.encoderModifierIncrease = 0.01
        self.encoderModifierLimit = 0.05
        self.apisocket = apisocket
        self.epoll = select.epoll()
        self.init()
        self.thread_main = Thread(target=self.main)
        self.thread_main.start()
        self.right_counter = 0
        self.left_counter = 0
        #self.main()

    def start_lock_timer(self):
        try: 
            self.timer.cancel()
        except AttributeError:
            pass
        self.timer = Timer(self.timeout, self.unlock)
        self.timer.start()

    
    def start_encoder_timer(self):
        try: 
            self.encoder_timer.cancel()
        except AttributeError:
            pass
        self.encoder_timer = Timer(self.encoder_timeout, self.reset_encoder_speed)
        self.encoder_timer.start()

    def reset_encoder_speed(self):
        self.encoderModifierLeft = 0
        self.encoderModifierRight = 0


    def unlock(self):
        self.left_lock = False
        self.right_lock = False
        self.encoderModifierLeft = 0
        self.encoderModifierRight = 0

    def handle_left(self):
        try:
            with open(f"/sys/class/gpio/gpio{self.offset_left}/value", "r") as leftval:
                l = leftval.readline()[:1]
                with open(f"/sys/class/gpio/gpio{self.offset_right}/value", "r") as rightval: 
                    r = rightval.readline()[:1]
                    print(time.time(),l,r)
                    if l == "0" and r == "1" and not self.left_lock:
                        self.start_lock_timer()
                        self.start_encoder_timer()
                        self.right_lock = True
                        self.left_counter += 1
                        print("left",self.left_counter)
                        if self.apisocket.zone_select:
                            new_zone_index = 0
                            for index,zone in enumerate(self.apisocket.available_zones):
                                if self.apisocket.current_zone == zone:
                                    if index > 0:
                                        new_zone_index = index - 1
                                    print(index,new_zone_index)
                            self.apisocket.current_zone = self.apisocket.available_zones[new_zone_index]                                            
                            self.apisocket.display.select_zone(self.apisocket.current_zone)              
                        else:
                            new_gain = 0.02+self.encoderModifierLeft
                            self.apisocket.available_gains[self.apisocket.current_zone] -= new_gain*100
                            if self.apisocket.available_gains[self.apisocket.current_zone] <= 0:
                                self.apisocket.available_gains[self.apisocket.current_zone] = 0
                            self.apisocket.encoder_queue.append(("left",new_gain))
                            if  self.encoderModifierLeft < self.encoderModifierLimit:
                                self.encoderModifierLeft += self.encoderModifierIncrease
                            return 
                            data =  {"vol_down" : new_gain}
                            self.apisocket.display.show_zone_level(
                                self.apisocket.available_gains[self.apisocket.current_zone],
                                self.apisocket.current_zone
                            )
                            
                            self.apisocket.tx_buf.append(json.dumps(data))
        except:
            pass

    def handle_right(self):
        with open(f"/sys/class/gpio/gpio{self.offset_right}/value", "r") as rightval:
            r = rightval.readline()[:1]
            with open(f"/sys/class/gpio/gpio{self.offset_left}/value", "r") as leftval: 
                l = leftval.readline()[:1]
                #print(r,l)
                if r == "0" and l == "1" and not self.right_lock:
                    self.start_lock_timer()
                    self.start_encoder_timer()
                    self.left_lock = True
                    self.right_counter += 1
                    print("right",self.right_counter) 
                    if self.apisocket.zone_select:
                        new_zone_index = len(self.apisocket.available_zones)-1
                        for index,zone in enumerate(self.apisocket.available_zones):
                            if self.apisocket.current_zone == zone:
                                if index < new_zone_index:
                                    new_zone_index = index + 1
                                print(index,new_zone_index)
                        self.apisocket.current_zone = self.apisocket.available_zones[new_zone_index]                                            
                        self.apisocket.display.select_zone(self.apisocket.current_zone)              
                    else:
                        new_gain = 0.02+self.encoderModifierRight
                        self.apisocket.available_gains[self.apisocket.current_zone] += new_gain*100
                        if self.apisocket.available_gains[self.apisocket.current_zone] >= 100:
                                self.apisocket.available_gains[self.apisocket.current_zone] = 100
                        self.apisocket.encoder_queue.append(("right",new_gain))
                        if self.encoderModifierRight < self.encoderModifierLimit:
                            self.encoderModifierRight += self.encoderModifierIncrease
                        return
                        data =  {"vol_up" : new_gain}
                        self.apisocket.display.show_zone_level(
                                self.apisocket.available_gains[self.apisocket.current_zone],
                                self.apisocket.current_zone
                            )
                        
                        self.apisocket.tx_buf.append(json.dumps(data))

    def handle_encoder(self):
        with open(f"/sys/class/gpio/gpio{self.offset_encoder}/value", "r") as encoderval:
            if encoderval.readline()[:1] == "0":
                if self.apisocket.zone_select:
                    self.apisocket.zone_select = False
                    data =  {"zone_set" : self.apisocket.current_zone}
                    self.apisocket.tx_buf.append(json.dumps(data))
                else:
                    self.apisocket.display.select_zone(self.apisocket.current_zone)
                    self.apisocket.zone_select = True
                    print("Menu")
    def main(self):
        try:
            while True:
                # Wait for the value file to change
                events = self.epoll.poll()
                for fileno, event in events:
                    if fileno == self.value_file_left.fileno():
                        self.handle_left()                                    
                    if fileno == self.value_file_right.fileno(): 
                        self.handle_right()
                    if fileno == self.value_file_pairing.fileno():
                         with open(f"/sys/class/gpio/gpio{self.offset_pairing}/value", "r") as pairingval:
                            if pairingval.readline()[:1] == "0":
                                print("pairing")
                    if fileno == self.value_file_encoder.fileno():
                        self.handle_encoder()
        except KeyboardInterrupt:
            with open("/sys/class/gpio/unexport", "w") as unexport_file:
                unexport_file.write(f"{self.offset_left}")
            with open("/sys/class/gpio/unexport", "w") as unexport_file:
                unexport_file.write(f"{self.offset_right}")
        # Unexport the GPIO pin

    def init(self):
        try:
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_left}")
        except OSError:
            with open("/sys/class/gpio/unexport", "w") as unexport_file:
                unexport_file.write(f"{self.offset_left}")
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_left}")
        
        try:    
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_right}")
        except OSError:
            with open("/sys/class/gpio/unexport", "w") as unexport_file:
                unexport_file.write(f"{self.offset_right}")
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_right}")
        
        try:    
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_pairing}")
        except OSError:
            with open("/sys/class/gpio/unexport", "w") as unexport_file:
                unexport_file.write(f"{self.offset_pairing}")
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_pairing}")
        
        try:    
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_encoder}")
        except OSError:
            with open("/sys/class/gpio/unexport", "w") as unexport_file:
                unexport_file.write(f"{self.offset_encoder}")
            with open("/sys/class/gpio/export", "w") as export_file:
                export_file.write(f"{self.offset_encoder}")

        # Set the direction of the pin to input
        with open(f"/sys/class/gpio/gpio{self.offset_left}/direction", "w") as direction_file:
            direction_file.write("in")
        with open(f"/sys/class/gpio/gpio{self.offset_right}/direction", "w") as direction_file:
            direction_file.write("in")
        with open(f"/sys/class/gpio/gpio{self.offset_pairing}/direction", "w") as direction_file:
            direction_file.write("in")
        with open(f"/sys/class/gpio/gpio{self.offset_encoder}/direction", "w") as direction_file:
            direction_file.write("in")

        # Set the edge trigger type to rising edge
        with open(f"/sys/class/gpio/gpio{self.offset_left}/edge", "w") as edge_file:
            edge_file.write("falling")
        with open(f"/sys/class/gpio/gpio{self.offset_right}/edge", "w") as edge_file:
            edge_file.write("falling")
        with open(f"/sys/class/gpio/gpio{self.offset_pairing}/edge", "w") as edge_file:
            edge_file.write("falling")
        with open(f"/sys/class/gpio/gpio{self.offset_encoder}/edge", "w") as edge_file:
            edge_file.write("falling")
        
        self.value_file_left = open(f"/sys/class/gpio/gpio{self.offset_left}/value", "r")
        self.value_file_right = open(f"/sys/class/gpio/gpio{self.offset_right}/value", "r")
        self.value_file_pairing = open(f"/sys/class/gpio/gpio{self.offset_pairing}/value", "r")
        self.value_file_encoder = open(f"/sys/class/gpio/gpio{self.offset_encoder}/value", "r")
        
        self.epoll.register(self.value_file_left, select.EPOLLIN | select.EPOLLET)
        self.epoll.register(self.value_file_right, select.EPOLLIN | select.EPOLLET)
        self.epoll.register(self.value_file_pairing, select.EPOLLIN | select.EPOLLET)
        self.epoll.register(self.value_file_encoder, select.EPOLLIN | select.EPOLLET)
# Open the value file for the GPIO pin


#test = Encoder()
#test.main()
