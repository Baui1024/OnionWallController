from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time
import spidev
#from upm.pyupm_st7735 import ST7735
from st7735 import ST7735

MESSAGE = "Hello World! How are you today?"
WIDTH = 160
HEIGHT = 80


display = ST7735(0,1,8,rst=16)

#spi = spidev.SpiDev()
#spi.open(0,1)
#spi.max_speed_hz = 1000000




# Create ST7735 LCD display class.
#disp = ST7735(6,15,8,16)

# Initialize display.
#disp.begin()

#WIDTH = disp.width
#HEIGHT = disp.height


#img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))

#draw = ImageDraw.Draw(img)

#font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

#size_x, size_y = draw.textsize(MESSAGE, font)

#text_x = 160
#text_y = (80 - size_y) // 2

#t_start = time.time()

#while True:
#    x = (time.time() - t_start) * 100
#    x %= (size_x + 160)
#    draw.rectangle((0, 0, 160, 80), (0, 0, 0))
#    draw.text((int(text_x - x), text_y), MESSAGE, font=font, fill=(255, 255, 255))
#    disp.display(img)