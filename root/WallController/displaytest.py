from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import sys
import time
import gpiod
import spidev
#from upm.pyupm_st7735 import ST7735
#from st7735 import ST7735

#display = ST7735(12,5,10,5)

from PIL import Image
from st7735 import ST7735
import time
import sys

# Create TFT LCD display class.
disp = ST7735(
    port=0,
    cs=1,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=17,
    backlight=11,               # 18 for back BG slot, 19 for front BG slot.
    rst=16,
    rotation = 270,
    spi_speed_hz=220000000,
    invert = False,
    offset_left = 24,
    offset_top = 0
)


WIDTH = disp.height
HEIGHT = disp.width
MESSAGE = "Hello World! How are you today?"
start = time.time()
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 255))
print("generate image: ",time.time()-start)

print("generate draw: ",time.time()-start)
font = ImageFont.truetype("/root/WallController/Roboto-Light.ttf", 15)








#t_start = time.time()
#img = Image.open("/root/WallController/blackgreenblack.png")
#print("open testimage: ",time.time()-start)
disp.display(img)
print("display testiamge: ",time.time()-start)
testframes = 60
while True:
    start = time.time()
    
    ip,subnet,gateway = "192.168.178.99","255.255.255.0","192.168.178.1"
    for x in range(testframes):
        img = Image.new('RGB', (160, 80), color=(0, 0, 255))
        draw = ImageDraw.Draw(img)
        # get a drawing context
        # draw multiline text
        draw.multiline_text((10, 10), f"{x}", font=font, fill=(0, 0, 0))
        draw.multiline_text((10, 10), f"IP:\t{ip}\nSN:\t{subnet}\nGW:\t{gateway}\n", font=font, fill=(255, 255, 255))
        disp.display(img)
        
    end = time.time()-start
    print("display testiamge: ",end,"FPS: ",testframes/end)






