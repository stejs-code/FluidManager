from machine import Pin
from FluidManager import FluidManager
from hx711_pio import HX711

pump = Pin(18, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_DOWN)

pin_OUT = Pin(12, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(13, Pin.OUT)

hx711 = HX711(pin_SCK, pin_OUT)

manager = FluidManager(pump, button, hx711)
manager.start()