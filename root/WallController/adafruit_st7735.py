# SPDX-FileCopyrightText: 2017 Radomir Dopieralski for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rgb_display.st7735`
====================================================

A simple driver for the ST7735-based displays.

* Author(s): Radomir Dopieralski, Michael McWethy
"""
import struct
import gpiod

from adafruit_rgb_display import DisplaySPI

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RGB_Display.git"

_NOP = 0x00
_SWRESET = 0x01
_RDDID = 0x04
_RDDST = 0x09

_SLPIN = 0x10
_SLPOUT = 0x11
_PTLON = 0x12
_NORON = 0x13

_INVOFF = 0x20
_INVON = 0x21
_DISPOFF = 0x28
_DISPON = 0x29
_CASET = 0x2A
_RASET = 0x2B
_RAMWR = 0x2C
_RAMRD = 0x2E

_PTLAR = 0x30
_COLMOD = 0x3A
_MADCTL = 0x36

_FRMCTR1 = 0xB1
_FRMCTR2 = 0xB2
_FRMCTR3 = 0xB3
_INVCTR = 0xB4
_DISSET5 = 0xB6

_PWCTR1 = 0xC0
_PWCTR2 = 0xC1
_PWCTR3 = 0xC2
_PWCTR4 = 0xC3
_PWCTR5 = 0xC4
_VMCTR1 = 0xC5

_RDID1 = 0xDA
_RDID2 = 0xDB
_RDID3 = 0xDC
_RDID4 = 0xDD

_PWCTR6 = 0xFC

_GMCTRP1 = 0xE0
_GMCTRN1 = 0xE1


class ST7735(DisplaySPI):
    """
    A simple driver for the ST7735-based displays.

    >>> import busio
    >>> import digitalio
    >>> import board
    >>> from adafruit_rgb_display import color565
    >>> import adafruit_rgb_display.st7735 as st7735
    >>> spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    >>> display = st7735.ST7735(spi, cs=digitalio.DigitalInOut(board.GPIO0),
    ...    dc=digitalio.DigitalInOut(board.GPIO15), rst=digitalio.DigitalInOut(board.GPIO16))
    >>> display.fill(0x7521)
    >>> display.pixel(64, 64, 0)
    """

    _COLUMN_SET = _CASET
    _PAGE_SET = _RASET
    _RAM_WRITE = _RAMWR
    _RAM_READ = _RAMRD
    _INIT = (
        #(_SWRESET, None),
        #(_SLPOUT, None),
        #(_COLMOD, b"\x05"),  # 16bit color
        (_SWRESET, None),
        (_SLPOUT, None),
        (_COLMOD, (0x05,)),  # 16bit color

        # fastest refresh, 6 lines front porch, 3 line back porch
        #(_FRMCTR1, b"\x00\x06\x03"),
        #(_MADCTL, b"\x08"),  # bottom to top refresh
        (_FRMCTR1, (0x00,0x06,0x03)),
        (_MADCTL, (0x08,)),  # bottom to top refresh
        # 1 clk cycle nonoverlap, 2 cycle gate rise, 3 sycle osc equalie,
        # fix on VTL
        #(_DISSET5, b"\x15\x02"),
        #(_INVCTR, b"0x00"),  # line inversion
        #(_PWCTR1, b"\x02\x70"),  # GVDD = 4.7V, 1.0uA
        #(_PWCTR2, b"\x05"),  # VGH=14.7V, VGL=-7.35V
        #(_PWCTR3, b"\x01\x02"),  # Opamp current small, Boost frequency
        #(_VMCTR1, b"\x3c\x38"),  # VCOMH = 4V, VOML = -1.1V
        #(_PWCTR6, b"\x11\x15"),

        (_DISSET5, (0x15,0x02)),
        (_INVCTR, (0x00,)),  # line inversion
        (_PWCTR1, (0x02,0x70)),  # GVDD = 4.7V, 1.0uA
        (_PWCTR2, (0x05,)),  # VGH=14.7V, VGL=-7.35V
        (_PWCTR3, (0x01,0x02)),  # Opamp current small, Boost frequency
        (_VMCTR1, (0x3c,0x38)),  # VCOMH = 4V, VOML = -1.1V
        (_PWCTR6, (0x11,0x15)),

        (
            _GMCTRP1,
            #b"\x09\x16\x09\x20\x21\x1b\x13\x19" b"\x17\x15\x1e\x2b\x04\x05\x02\x0e",
            (0x09,0x16,0x09,0x20,0x21,0x1b,0x13,0x19,0x17,0x15,0x1e,0x2b,0x04,0x05,0x02,0x0e),
        ),  # Gamma
        (
            _GMCTRN1,
            #b"\x08\x14\x08\x1e\x22\x1d\x18\x1e" b"\x18\x1a\x24\x2b\x06\x06\x02\x0f",
            (0x08,0x14,0x08,0x1e,0x22,0x1d,0x18,0x1e,0x18,0x1a,0x24,0x2b,0x06,0x06,0x02,0x0f),
        ),
        #(_CASET, b"\x00\x02\x00\x81"),  # XSTART = 2, XEND = 129
        #(_RASET, b"\x00\x02\x00\x81"),  # XSTART = 2, XEND = 129
        (_CASET, (0x00,0x02,0x00,0x81)),  # XSTART = 2, XEND = 129
        (_RASET, (0x00,0x02,0x00,0x81)),  # XSTART = 2, XEND = 129
        (_NORON, None),
        (_DISPON, None),
    )
    _ENCODE_PIXEL = ">H"
    _ENCODE_POS = ">HH"

    # pylint: disable-msg=useless-super-delegation, too-many-arguments
    def __init__(
        self,
        spi,
        dc,
        rst=None,
        width=160,
        height=80,
        baudrate=16000000,
        polarity=0,
        phase=0,
        *,
        x_offset=0,
        y_offset=0,
        rotation=0,
        chip = gpiod.Chip('gpiochip0')
    ):
        #spi.writebytes([0x01, 0x02, 0x03])
        super().__init__(
            spi,
            dc,
            rst,
            width,
            height,
            baudrate=baudrate,
            polarity=polarity,
            phase=phase,
            x_offset=x_offset,
            y_offset=y_offset,
            rotation=rotation,
            chip = chip
        )



class ST7735R(ST7735):
    """A simple driver for the ST7735R-based displays."""

    _INIT = (
        (_SWRESET, None),
        (_SLPOUT, None),
        (_MADCTL, b"\xc8"),
        (_COLMOD, b"\x05"),  # 16bit color
        (_INVCTR, b"\x07"),
        (_FRMCTR1, b"\x01\x2c\x2d"),
        (_FRMCTR2, b"\x01\x2c\x2d"),
        (_FRMCTR3, b"\x01\x2c\x2d\x01\x2c\x2d"),
        (_PWCTR1, b"\x02\x02\x84"),
        (_PWCTR2, b"\xc5"),
        (_PWCTR3, b"\x0a\x00"),
        (_PWCTR4, b"\x8a\x2a"),
        (_PWCTR5, b"\x8a\xee"),
        (_VMCTR1, b"\x0e"),
        (_INVOFF, None),
        (
            _GMCTRP1,
            b"\x02\x1c\x07\x12\x37\x32\x29\x2d" b"\x29\x25\x2B\x39\x00\x01\x03\x10",
        ),  # Gamma
        (
            _GMCTRN1,
            b"\x03\x1d\x07\x06\x2E\x2C\x29\x2D" b"\x2E\x2E\x37\x3F\x00\x00\x02\x10",
        ),
    )

    # pylint: disable-msg=useless-super-delegation, too-many-arguments
    def __init__(
        self,
        spi,
        dc,
        cs,
        rst=None,
        width=128,
        height=160,
        baudrate=16000000,
        polarity=0,
        phase=0,
        *,
        x_offset=0,
        y_offset=0,
        rotation=0,
        bgr=False
    ):
        self._bgr = bgr
        super().__init__(
            spi,
            dc,
            cs,
            rst,
            width,
            height,
            baudrate=baudrate,
            polarity=polarity,
            phase=phase,
            x_offset=x_offset,
            y_offset=y_offset,
            rotation=rotation,
        )


    def init(self):
        super().init()
        cols = struct.pack(">HH", 0, self.width - 1)
        rows = struct.pack(">HH", 0, self.height - 1)

        for command, data in (
            (_CASET, cols),
            (_RASET, rows),
            (_NORON, None),
            (_DISPON, None),
        ):
            self.write(command, data)
        if self._bgr:
            self.write(_MADCTL, b"\xc0")


class ST7735S(ST7735):
    """A simple driver for the ST7735S-based displays."""

    _INIT = (
        # Frame Rate
        #(_FRMCTR1, b"\x01\x2c\x2d"),
        #(_FRMCTR2, b"\x01\x2c\x2d"),
        #(_FRMCTR3, b"\x01\x2c\x2d\x01\x2c\x2d"),
        (_FRMCTR1, (0x01,0x2c,0x2d)),
        (_FRMCTR2, (0x01,0x2c,0x2d)),
        (_FRMCTR3, (0x01,0x2c,0x2d,0x01,0x2c,0x2d)),
        
        # Column inversion
        #(_INVCTR, b"\x07"),
        (_INVCTR, (0x07,)),

        # Power Sequence
        #(_PWCTR1, b"\xa2\x02\x84"),
        #(_PWCTR2, b"\xc5"),
        #(_PWCTR3, b"\x0a\x00"),
        #(_PWCTR4, b"\x8a\x2a"),
        #(_PWCTR5, b"\x8a\xee"),

        (_PWCTR1, (0xa2,0x02,0x84)),
        (_PWCTR2, (0xc5,)),
        (_PWCTR3, (0x0a,0x00)),
        (_PWCTR4, (0x8a,0x2a)),
        (_PWCTR5, (0x8a,0xee)),
        # VCOM
        #(_VMCTR1, b"\x0e"),
        (_VMCTR1, (0x0e,)),

        # Gamma
        (
            _GMCTRP1,
            #b"\x0f\x1a\x0f\x18\x2f\x28\x20\x22" b"\x1f\x1b\x23\x37\x00\x07\x02\x10",
            (0x0f,0x1a,0x0f,0x18,0x2f,0x28,0x20,0x22,0x1f,0x1b,0x23,0x37,0x00,0x07,0x02,0x10),
        ),
        (
            _GMCTRN1,
            #b"\x0f\x1b\x0f\x17\x33\x2c\x29\x2e" b"\x30\x30\x39\x3f\x00\x07\x03\x10",
            (0x0f,0x1b,0x0f,0x17,0x33,0x2c,0x29,0x2e,0x30,0x30,0x39,0x3f,0x00,0x07,0x03,0x10),
        ),
        # 65k mode
        #(_COLMOD, b"\x05"),
        (_COLMOD, (0x05,)),
        # set scan direction: up to down, right to left
        #(_MADCTL, b"\x60"),
        #(_SLPOUT, None),
        #(_DISPON, None),

        (_MADCTL, (0x60,)),
        (_SLPOUT, (None,)),
        (_DISPON, (None,)),
  
    )

    # pylint: disable-msg=useless-super-delegation, too-many-arguments
    def __init__(
        self,
        spi,
        dc,
        cs,
        bl,
        rst=None,
        width=128,
        height=160,
        baudrate=16000000,
        polarity=0,
        phase=0,
        *,
        x_offset=2,
        y_offset=1,
        rotation=0
    ):
        self._bl = bl
        # Turn on backlight
        self._bl.switch_to_output(value=1)
        super().__init__(
            spi,
            dc,
            cs,
            rst,
            width,
            height,
            baudrate=baudrate,
            polarity=polarity,
            phase=phase,
            x_offset=x_offset,
            y_offset=y_offset,
            rotation=rotation,
        )