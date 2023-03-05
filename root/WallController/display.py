from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from st7735 import ST7735
from copy import copy
from threading import Timer

class Display():
    def __init__(self):
        self.WIDTH = 160
        self.HEIGHT = 80
        self.display = ST7735(
            port = 0,
            cs = 1,
            dc = 17,
            backlight = 11,
            rst = 16,
            rotation = 90,
            spi_speed_hz = 220000000,
            invert = False,
            offset_left = 24,
            offset_top = 0
        ) 
        self.fontsize = 15
        self.fontsize_big = 20
        self.font = "/root/WallController/Roboto-Light.ttf"
        self.images = {}
        self.main_color = (255,255,255)
        self.background_color = (0,0,0)
        self.upper_line = 30
        self.lower_line = 60
        self.x_offset = 2 
        self.timeout = 30
        self.timer = None

    def start_timer(self):
        try: 
            self.timer.cancel()
        except AttributeError:
            pass
        self.timer = Timer(self.timeout, self.show_blank_screen)
        self.timer.start()

    def show_network_settings(self,ip,subnet,gateway):
        font = ImageFont.truetype(self.font, self.fontsize)
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color = self.background_color)
        draw = ImageDraw.Draw(img)
        draw.multiline_text((7, 15), f"IP:\nSN:\nGW:\n", font = font, fill = self.main_color)
        draw.multiline_text((40, 15), f"{ip}\n{subnet}\n{gateway}\n", font = font, fill = self.main_color)
        self.display.display(img)
        self.start_timer()

    def show_zone_level(self,level,zone):
        if zone in self.images:
            image = copy(self.images[zone])
            draw = ImageDraw.Draw(image)
            y_offset = 5
            x_start = self.x_offset+4
            x_end = self.WIDTH-self.x_offset-x_start-5
            draw.rectangle([(x_start,self.upper_line+y_offset),(x_end*(0.01*level)+x_start+1,self.lower_line-y_offset)], fill = self.main_color)
            self.display.display(image)
            self.start_timer()

    def create_zones(self,zones):
        self.images.clear()
        for zone in zones:
            img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color = self.background_color)
            font = ImageFont.truetype(self.font, self.fontsize_big)
            draw = ImageDraw.Draw(img)
            draw.text((self.WIDTH/2, 7), f"{zone}", font=font, anchor = "mt", fill = self.main_color)
            draw.line([(self.x_offset,self.upper_line),(self.x_offset+10,self.upper_line)], fill = self.main_color)
            draw.line([(self.x_offset,self.upper_line),(self.x_offset,self.lower_line)], self.main_color)
            draw.line([(self.x_offset,self.lower_line),(self.x_offset+10,self.lower_line)], self.main_color)
            draw.line([(self.WIDTH-self.x_offset,self.upper_line),(self.WIDTH-self.x_offset-10,self.upper_line)], fill = self.main_color)
            draw.line([(self.WIDTH-self.x_offset,self.upper_line),(self.WIDTH-self.x_offset,self.lower_line)], self.main_color)
            draw.line([(self.WIDTH-self.x_offset,self.lower_line),(self.WIDTH-self.x_offset-10,self.lower_line)], self.main_color)
            self.images[zone] = img

    def select_zone(self,zone):
        font = ImageFont.truetype(self.font, self.fontsize)
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color = self.background_color)
        draw = ImageDraw.Draw(img)
        draw.text((self.WIDTH/2, 7), f"Select Zone", font = font, anchor = "mt", fill = self.main_color)
        draw.text((self.WIDTH/2, 38), f"<  {zone}  >", font = font, anchor = "mt", fill = self.main_color)
        self.display.display(img)
        self.start_timer()


    def show_blank_screen(self):
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color = (0,0,0))
        self.display.display(img)

import time
    
"""start = time.time()
test = Display()
end = time.time()-start
print("init class: ",end,"FPS: ",1/end)
test.create_zones(["test1","apfel","test2"])
testframes=100
start = time.time()
for x in range(testframes):
    test.select_zone("apfel")
    #test.show_network_settings("255.255.255.255","255.255.255.255","255.255.255.255")
end = time.time()-start
print("display ip: ",end,"FPS: ",testframes/end)"""
