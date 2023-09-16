from __future__ import unicode_literals
import time

import os
from luma.core import cmdline
from luma.core.render import canvas
from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from pathlib import Path
from PIL import ImageFont
from PIL import Image, ImageDraw
from luma.core.framebuffer import full_frame
from luma.core.virtual import terminal
import RPi.GPIO as GPIO
from dotenv import load_dotenv
load_dotenv()

DISABLE_LCD = os.getenv("DISABLE_LCD", 'False').lower() in ('true', '1', 't')

class LCDServiceColor:
    ICON_TALK = "\uf599"
    ICON_SAD_FACE = "\uf119"
    ICON_WIFI = "\uf1eb"
    ICON_MIC = "\uf2a2"
    ICON_MIC_OFF = "\uf2a4"
    ICON_SPEAKER = "\uf028"
    ICON_ERROR = "\uf071"    
    ICON_LOAD = "\uf110"    
    
    FACE_TALK = "bunny_talk.png"
    FACE_THINK = "bunny_think.png"
    FACE_LISTEN = "bunny_listen.png"
    FACE_SILENT = "bunny_silent.png"
    
    @classmethod
    def make_font(self, name, size):
        font_path = str(Path(__file__).resolve().parent.joinpath('fonts', name))
        return ImageFont.truetype(font_path, size)
        
    def cleanup():
        GPIO.cleanup()
        
    def __init__(self):

        if DISABLE_LCD:
            return

        parser = cmdline.create_parser(description='')
        conf_path = str(Path(__file__).resolve().parent.joinpath('', 'ili9341n.conf'))
        config = cmdline.load_config(conf_path)
        args = parser.parse_args(config)
        self.device = cmdline.create_device(args)
        
        self.font_icon = LCDServiceColor.make_font("fa-solid-900.ttf", round(self.device.height / 5))
        self.font_icon_large = LCDServiceColor.make_font("fa-solid-900.ttf", self.device.height - 100)
        self.font_text = LCDServiceColor.make_font("code2000.ttf", round(self.device.height / 14))
        self.font_text_sm = LCDServiceColor.make_font("code2000.ttf", 8)       
    
    def clear_screen(self):
        if DISABLE_LCD:
            return

        self.device.clear()

    def draw_face(self, face, icon="", additional_text = "", top_small_text = ""):
        if DISABLE_LCD:
            return
        
        face_path = str(Path(__file__).resolve().parent.joinpath('face_images', face))
        face_image=Image.open(face_path)

        with canvas(self.device, background=face_image) as draw:  
            if icon != "": 
                w, h = draw.textsize(text=icon, font=self.font_icon)
                left = self.device.width - w - 10
                top = self.device.height - h - 10
                draw.text((left, top), text=icon, font=self.font_icon, fill="white")  
            if additional_text != "": 
                w2, h2 = draw.textsize(text=additional_text, font=self.font_text)
                left2 = 10
                top2 = self.device.height - h2 - 10
                draw.text((left2, top2), text=additional_text, font=self.font_text, fill="white")    
            if top_small_text != "": 
                w3, h3 = draw.textsize(text=top_small_text, font=self.font_text_sm)
                left3 = 5
                top3 = 5
                draw.text((left3, top3), text=top_small_text, font=self.font_text_sm, fill="black")                  

    def draw_large_icon(self, icon, additional_text = ""):
        if DISABLE_LCD:
            return
        with canvas(self.device) as draw:
            w, h = draw.textsize(text=icon, font=self.font_icon_large)
            left = self.device.width / 2  - w / 2
            top = self.device.height / 2  - h / 2
            draw.text((left, top), text=icon, font=self.font_icon_large, fill="white")
            
            if additional_text != "": 
                w2, h2 = draw.textsize(text=additional_text, font=self.font_text)
                left2 = (self.device.width - w2) - 5
                top2 = 5
                draw.text((left2, top2), text=additional_text, font=self.font_text, fill="white")