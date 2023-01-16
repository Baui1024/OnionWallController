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

print("""
gif.py - Display a gif on the LCD.
If you're using Breakout Garden, plug the 0.96" LCD (SPI)
breakout into the front slot.
""")

if len(sys.argv) > 1:
    image_file = sys.argv[1]
else:
    print("Usage: {} <filename.gif>".format(sys.argv[0]))
    sys.exit(0)

# Create TFT LCD display class.
disp = ST7735(
    port=0,
    cs=1,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=17,
    #backlight=11,               # 18 for back BG slot, 19 for front BG slot.
    rst=16,
    rotation = 0,
    spi_speed_hz=40000000,
    invert = True,
    offset_left = 24,
    offset_top = 0
)


WIDTH = disp.width
HEIGHT = disp.height
MESSAGE = "Hello World! How are you today?"
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))

draw = ImageDraw.Draw(img)

font = ImageFont.truetype("/root/font.tff", 30)

size_x, size_y = draw.textsize(MESSAGE, font)

text_x = 160
text_y = (80 - size_y) // 2

t_start = time.time()

img = Image.open("/root/test3.png")
disp.display(img)

exit()
while True:
    x = (time.time() - t_start) * 100
    x %= (size_x + 160)
    draw.rectangle((0, 0, 160, 80), (0, 0, 0))
    draw.text((int(text_x - x), text_y), MESSAGE, font=font, fill=(255, 255, 255))
    #img = img.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
    disp.display(img)










from adafruit_rgb_display import color565
from adafruit_st7735 import ST7735


MESSAGE = "Hello World! How are you today?"
WIDTH = 160
HEIGHT = 80

#disp = ST7735(0,1,17,backlight=11,rst=16)


#img = Image.new("RGB", (160, 80), (255, 255, 255))
#disp.display(img)

#spi = spidev.SpiDev()
#spi.open(0,1)
#spi.max_speed_hz = 10000000
#spi.mode = 0b00
#to_send = (0x01, 0x02, 0x03)
#spi.writebytes([0x01, 0x02, 0x03])
#spi.writebytes(to_send)

#display = ST7735(spi, dc=17, rst=16)
#display.fill(0x7521)



