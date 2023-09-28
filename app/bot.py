import os
import azure.cognitiveservices.speech as speechsdk
import time
import logging
import argparse
import RPi.GPIO as GPIO
import textwrap
import re
import sys
from pathlib import Path
#log_file_path = str(Path(__file__).resolve().parent.joinpath('', 'bot_log.txt'))
#sys.stdout = open(log_file_path, 'w')

from dotenv import load_dotenv
load_dotenv()

# Translations
trans_hu = {"listening" : "FÜLEL", "thinking" : "GONDOL", "speaking" : "BESZÉL", "silent":"CSENDBEN", "lang": "Hungarian"}
trans_en = {"listening" : "LISTENING", "thinking" : "THINKING", "speaking" : "SPEAKING", "silent":"SILENT", "lang": "English"}
trans_de = {"listening" : "HÖREN", "thinking" : "DENKEN", "speaking" : "SPRECHEN", "silent":"STILL", "lang": "German"}
translation = {}
translation["hu"] = trans_hu
translation["en"] = trans_en
translation["de"] = trans_de

lang_switch_phrases = [
    {"language": "English", 
        "voice": "en-GB-HollieNeural", 
        "phrases": ["válts angolra", "beszélj angolul", "válaszolj angolul", "angolul válaszolj", "angolul beszélj"]},
    {"language": "Hungarian", 
        "voice": "hu-HU-NoemiNeural", 
        "phrases": ["switch to hungarian", "respond in hungarian", "use hungarian", "talk in hungarian", "talk hungarian", "speak in hungarian", "speak hungarian"]},
    {"language": "German", 
        "voice": "de-DE-KatjaNeural", 
        "phrases": ["válts németre", "beszélj németül", "válaszolj németül", "németül válaszolj", "németül beszélj", "switch to german", "respond in german", "use german", "talk in german", "talk german", "speak in german", "speak german"]  }
]

# Local classes
from utils import Utils
utils = Utils()

from botconfig import BotConfig
bot_config = BotConfig()

from gptchatservice import GPTChatService

from lcdservice import LCDServiceColor
lcd_service = LCDServiceColor()

# Set API keys and API settings
speech_key, service_region = os.getenv('SPEECH_KEY'), os.getenv('SPEECH_REGION'), 
speech_lang, speech_voice = "hu-HU", "hu-HU-NoemiNeural"

# Audio HW settings
output_device_name="sysdefault:CARD=UACDemoV10"
input_device_name="hw:CARD=WEBCAM"
mute_mic_during_tts = True

# Global variable for stopping execution
done = False 
listening = True
thinking = False
speaking = False

# Statistics
total_tts_duration = 0
total_stt_chars = 0
program_start_time = 0

# Method to call once recognition ends
def stop_cb(evt):
    speech_recognizer.stop_continuous_recognition()
    global done
    done= True

def check_single_char_dot(string):
    pattern = r'^[a-zA-Z0-9]\.'
    match = re.search(pattern, string)
    if match:
        return True
    else:
        return False
    
# Speech to Text utterance / command recognition finished event    
def recognized(evt: speechsdk.SpeechRecognitionEventArgs):

    try:

        global thinking
        global speaking
        global total_stt_chars

        if (speaking == True or thinking == True):
            return;
        
        stt_text = evt.result.text
        
        if stt_text == "" or check_single_char_dot(stt_text): return
 
        recognized_text_log = f"Recognized speech: {stt_text}"
        print(recognized_text_log, flush=True)
        log.info(recognized_text_log)

        total_stt_chars += len(stt_text)

        if (mute_mic_during_tts): utils.mute_mic(device_name=input_device_name)
        
        if (bot_config.change_face == True):
            change_mood_thinking(stt_text)
           
        thinking = True
        start = time.time()

        if (bot_config.exp_lang_autoswitch == True):
            lang_switcher = check_lang_switch_phrases(stt_text)
            if (lang_switcher != None):
                change_language(lang_switcher)
                print(f"Language switched to {lang_switcher['language']}")
                self.log.info(f"Language switched to {lang_switcher['language']}")
                stt_text = f" From now on, you will have to respond in {lang_switcher['language']}! So please respond in {lang_switcher['language']}. Acknowledge this by saying that you will speak now in {lang_switcher['language']}"

        response_text = gpt_service.ask(stt_text)
        openai_call_duration = f'OpenAI API call ended: {time.time() - start} ms'
        print(openai_call_duration, flush=True)
        self.log.debug(openai_call_duration)
        thinking = False
        
        if (bot_config.change_face == True):
            change_mood_talking(response_text)
            time.sleep(0.5) 
        
        start = time.time()
        speak_text(response_text)

        if (listening == False):
            return
        
        print("Speak!")
        if (bot_config.auto_mute_mic == True): 
            toggle_mute(False)
        else:
            toggle_mute(True)
            
        
    except Exception as e:
        self.log.error(e)
        if hasattr(e, 'message'):
            print(e.message)
            self.log.error(e.message)
        else:
            print(e)          
        return "" 

def change_mood_thinking(top_text):
    wrapper = textwrap.TextWrapper(width=70)
    text_wrapped = wrapper.fill(text=top_text)
    if (bot_config.show_recognized == False): 
        text_wrapped = ''
    lcd_service.draw_face(face=LCDServiceColor.FACE_THINK, icon=LCDServiceColor.ICON_LOAD, additional_text=translation[ui_lang]['thinking'], top_small_text=text_wrapped)

def change_mood_talking(top_text):
    wrapper = textwrap.TextWrapper(width=70)
    text_wrapped = wrapper.fill(text=top_text)
    if (bot_config.show_gpt_response == False):
        text_wrapped = ''    
    lcd_service.draw_face(face=LCDServiceColor.FACE_TALK, icon=LCDServiceColor.ICON_SPEAKER, additional_text=translation[ui_lang]['speaking'], top_small_text=text_wrapped)

def escape( str_xml: str ):
    str_xml = str_xml.replace("&", "&amp;")
    str_xml = str_xml.replace("<", "&lt;")
    str_xml = str_xml.replace(">", "&gt;")
    str_xml = str_xml.replace("\"", "&quot;")
    str_xml = str_xml.replace("'", "&apos;")
    return str_xml       
        
def speak_text(text):
    global speaking
    global total_tts_duration
    
    # Finally, start the Azure TTS synthesis 
    # Use SSML to set speaking rate and pitch
    text_escaped = escape(text)
    text_ssml = f"<speak version='1.0' xml:lang='{speech_lang}'><voice xml:lang='{speech_lang}' xml:gender='Female' name='{speech_voice}'><prosody volume='+30%' rate='{speech_rate}%' pitch='{speech_pitch}%'>{text_escaped}</prosody></voice></speak>"
            
    speaking = True    
    result = speech_synthesizer.speak_ssml_async(text_ssml).get()
    sleep_duration = result.audio_duration.microseconds / 1000000
    time.sleep(sleep_duration)
    print(f"AI response ({result.audio_duration.seconds} sec): {text}")
    total_tts_duration += result.audio_duration.seconds
    speaking = False
    

# Unregister speech recognizer events
def unset_speech_recognizer_events():
    speech_recognizer.stop_continuous_recognition()
    speech_recognizer.recognized.disconnect_all()
    speech_recognizer.session_started.disconnect_all()
    speech_recognizer.session_stopped.disconnect_all()
    speech_recognizer.canceled.disconnect_all()

# Register speech recognizer events, e.g. when an utterance is recognized
def set_speech_recognizer_events():
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_started.connect(lambda evt: print('RECOGNIZE STARTED {}'.format(evt)))    
    speech_recognizer.session_stopped.connect(lambda evt: print('RECOGNIZE STOPPED {}'.format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print('RECOGNIZE CANCELED {}'.format(evt)))
    speech_recognizer.start_continuous_recognition()

def run_ai():

    global program_start_time

    # Start continous speech recognition
    if (mute_mic_during_tts): utils.unmute_mic(device_name=input_device_name)

    program_start_time = time.time()
  
    if (bot_config.auto_mute_mic == True): 
        toggle_mute(False)
    else:
        print("Speak!")
        lcd_service.draw_face(face=LCDServiceColor.FACE_LISTEN, icon=LCDServiceColor.ICON_MIC, additional_text=translation[ui_lang]['listening'])

    while not done:
        time.sleep(.5)

def init_logging():
    global log
    log = logging.getLogger("bot_log")
    logging.basicConfig(filename='gpt_service.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def check_internet():
        
    log.info("Checking internet connection")
    if (utils.has_internet() == True):
        return
        
    time.sleep(1)

    while not utils.has_internet():
        lcd_service.draw_large_icon(LCDServiceColor.ICON_ERROR, "Waiting for internet connect...")
        time.sleep(1)
    
    lcd_service.draw_large_icon(LCDServiceColor.ICON_WIFI, "Internet connection found!")
    time.sleep(1)
    lcd_service.clear_screen()    

def check_lang_switch_phrases(input_text):
    for phrase_item in lang_switch_phrases:
        for phrase_text in phrase_item["phrases"]:
            if re.search(phrase_text, input_text, re.IGNORECASE):
                lang_switcher = {"language": phrase_item["language"], "voice": phrase_item["voice"]}
                return lang_switcher
    return None

def change_language(lang_switcher):
    change_azure_voice(lang_switcher["voice"])
    gpt_service.change_language(lang_switcher["language"])


def change_azure_voice(voice_name):

    unset_speech_recognizer_events()

    global speech_voice
    global speech_lang
    global ui_lang
    
    speech_voice = voice_name
    speech_lang = speech_voice[0:5]
    ui_lang = speech_voice[0:2]

    global speech_config
    speech_config.speech_recognition_language = speech_lang
    speech_config.speech_synthesis_language = speech_lang
    
    global speech_recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)   

    set_speech_recognizer_events()  
    
def init_azure(voice_name):

    global speech_voice
    global speech_lang
    global ui_lang
    
    speech_voice = voice_name
    speech_lang = speech_voice[0:5]
    ui_lang = speech_voice[0:2]
   
    global speech_rate
    global speech_pitch
    
    speech_rate = bot_config.rate
    speech_pitch = bot_config.pitch

    # Init Azure Text to Speech & Speech to Text configuration
    global speech_config
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.set_property(speechsdk.enums.PropertyId.SpeechServiceConnection_SynthLanguage, speech_voice)
    speech_config.set_property(speechsdk.enums.PropertyId.SpeechServiceConnection_RecoLanguage, speech_lang)

    # Create input and output config for speech recognizer
    global audio_config_output
    audio_config_output = speechsdk.audio.AudioOutputConfig(device_name=output_device_name)

    global audio_config_input
    #audio_config_input = speechsdk.audio.AudioConfig(device_name=input_device_name)
    #audio_config_input = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Create speech recognizer
    global speech_recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    # Create speech synthesizer
    global speech_synthesizer
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config_output)

    # Set to reuse speech synthesizer HTTP connection 
    connection = speechsdk.Connection.from_speech_synthesizer(speech_synthesizer)
    connection.open(True)

    set_speech_recognizer_events()
    
def init_gpio():
    GPIO.setmode(GPIO.BCM) # Use physical pin numbering
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
    GPIO.add_event_detect(15,GPIO.RISING,callback=button_pushed, bouncetime=500) # Setup event on pin 10 rising edge
    

def button_pushed(channel):

    global thinking
    if (thinking == True):
        return
    
    global listening
    listening = not listening
    toggle_mute(listening)

def toggle_mute(listening_local):
    global speech_recognizer
    global speech_synthesizer
    global listening
    if (listening_local == True):
        listening = True
        if (bot_config.change_face == True):
            lcd_service.draw_face(face=LCDServiceColor.FACE_LISTEN, icon=LCDServiceColor.ICON_MIC, additional_text=translation[ui_lang]['listening'])
        if (mute_mic_during_tts): utils.unmute_mic(device_name=input_device_name)
        #speech_recognizer.start_continuous_recognition()   
    if (listening_local == False):
        listening = False
        if (bot_config.change_face == True):
            lcd_service.draw_face(face=LCDServiceColor.FACE_SILENT, icon=LCDServiceColor.ICON_MIC_OFF, additional_text=translation[ui_lang]['silent'])  
        #speech_recognizer.stop_continuous_recognition() 
        if (mute_mic_during_tts): utils.mute_mic(device_name=input_device_name)
        speech_synthesizer.stop_speaking()
        speech_synthesizer.stop_speaking_async()


def init_ai():
    global gpt_service
    gpt_service = GPTChatService(translation[ui_lang]['lang'])
    print(translation[ui_lang]['lang'])

def end_program(write_stats = True):

    lcd_service.clear_screen()
    GPIO.cleanup()     

    if (write_stats):
        global gpt_service
        global program_start_time
        global total_stt_chars
        global total_tts_duration

        program_end_time = time.time()
        program_run_duration = program_end_time - program_start_time
        print(f'STATS: program duration: {program_run_duration} seconds')
        print(f'STATS: total TTS duration: {total_tts_duration} sec')
        print(f'STATS: total STT characters: {total_stt_chars} chars')    
        print(f'STATS: total OpenAI API tokens: {gpt_service.get_stats()}')        
    


def main():
    try:
        init_gpio()
        init_logging()
        check_internet()
        init_azure(bot_config.voice_name)        
        init_ai()        
        run_ai() 
    except KeyboardInterrupt:
        end_program()   
    finally:
        end_program()       
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--audio_input", help='Audio input device')
    parser.add_argument("-o", "--audio_output", help='Audio output device')
    parser.add_argument("-r", "--record_card", help='Audio record card')
    args = parser.parse_args()
    if (args.audio_input is not None):
        input_device_name=args.audio_input
        print(f"Audio input override: {input_device_name}")
    if (args.audio_output is not None):
        output_device_name=args.audio_output  
        print(f"Audio output override: {output_device_name}")  
        
    main()
