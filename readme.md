# PI GPTBot

![The voice assistant](https://github.com/bbence84/pi_gptbot/assets/1684946/c894caae-cafa-4d47-bd74-944e8edb3ff3)

This is a relatively simple Python based implementation of a Raspberry Pi based voice assistant that has the following features:
- Leverages the OpenAI APIs (Azure or regular OpenAI endpoints) to act the main conversational "engine"
- Uses Azure Cognitive Services for Text to Speech and Speech to Text (voice recognition)
- Has a config UI where it's possible to configure many aspects of the voice assistant:
    - Used GPT model, max. token count use
    - Various prompt templates (bot "personalities" as initial system prompts)
    - Used TTS voice, volume, pitch, rate, etc.
- Shows simple facial expressions (bunny, showing states like listening, speaking, thinking) and recognized voice on an LCD

## Prerequisites

- This description assumes that you are using a Raspberry Pi 4, with Raspberry Pi OS Lite installed. But it should work with other Rpi4 distros, e.g. DietPi. YMMW, though.
- I am using the following USB speaker and webcam:
    - USB speaker: Mini USB stereo speaker (like this: https://aliexpress.com/item/1005004417967899.html)
    - Webcam: Logitech HD Webcam C270 (others will likely due, but this one has a quite sensitive mic.)
- And the following LCD screen: ILI9341 320x240 LCD screen (like this: https://www.aliexpress.com/item/1005003120684423.html)
    - Connecting the wires: https://luma-lcd.readthedocs.io/en/latest/hardware.html#ili9341 (please see ili9341n.conf in the app folder, some pins are not using the default config)
- Besides the above, you also need to have the following accounts and API keys:
    - OpenAI API key (or Azure based OpenAI): https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/
    - Azure Cognitive Services API key: https://azure.microsoft.com/en-us/products/ai-services/ai-speech 

## Installation

There are multiple steps required to get the voice assistant up and running, which are described below. I hope I have not missed anything, but feel free to reach out to me if something is not working.

### Create 'bot' user

We will create all the things under the bot user and the scripts and references in this setup guide use this user, so it's highly recommended to create it unless you know how to adapt these things to another user.
```
sudo adduser bot
sudo adduser bot sudo
```
Then answer the question, e.g. for the password.
From now on, use this created user for logging in, as we will be creating things under this user.

### Set USB audio as default and enable the SPI interface

1. Start the setup program of the Raspberry OS: `sudo raspi-config`
2. Go to: System options -> Audio and select the USB Audio device
3. Go to: Interface options -> SPI and enable the SPI interface

### Disable built in audio

The built in audio devices (line out and HDMI) can cause a problem for the bot script to properly identify the USB speaker as an output. You can disable these other audio devices like so:

```sudo nano /boot/config.txt```
In this config.txt, do the following:
1. Comment out the following line (put a \# mark in front of the line): #dtparam=audio=on
2. Add the following line after the commented out line:
dtoverlay=vc4-kms-v3d,noaudio
Save the text file and restart your Raspberry Pi.

### Install required Linux packages
```
sudo apt-get update -y && \
 sudo    apt-get install python3 -y && \
 sudo    apt-get install python3-pip -y && \
  sudo   apt-get install -y --no-install-recommends \
        libasound2-dev \
        alsa-base \
        alsa-utils \
        libsndfile1-dev && \
   sudo  apt-get clean
```

### Clone repo

```
cd /home/bot/
sudo apt install git
git clone https://github.com/bbence84/pi_gptbot.git
```
### Install required Python packages

```
cd /home/bot/pi_gptbot
python3 -m pip install -r requirements.txt
```

### Set required environment variables

There are couple of things, e.g. API keys that need to be set for the bot to work. Create and edit .env file in the root of the repository (NOT the app subfolder, but the folder where e.g. the requirements.txt can be found)

```
nano .env
```

then set the following

```
OPENAI_API_KEY=<YOUR_API_KEY>
OPENAI_API_TYPE=openai
#AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
#AZURE_OPENAI_VERSION=2023-03-15-preview
#AZURE_OPENAI_ENGINE=xxx
SPEECH_KEY=<YOUR_API_KEY>
SPEECH_REGION=westeurope
DISABLE_LCD=False
GMAIL_USERNAME=xxx@gmail.com
GMAIL_PASSWORD=
SEND_URL_TO_EMAIL=xxx@xxx.com
```

In case you would like to use Azure OpenaAI services, uncomment the 3 lines and also set those variables. Then change the OPENAI_API_TYPE variable to "azure" (without quotes)

The bot configuration UI (see later for details) can send an email (announcing the temporary url) upon booting the voice assistant. This leverages a beta feature from one of the underlying Python packages (nicegui). This temporary URL will be available for about 10 minutes after booting. Later versions of this python package might provide stable urls... To configure the email sending, set the below .env paramaters. You will want to create a new gmail email address and set an app password (see here for details: https://www.sitepoint.com/quick-tip-sending-email-via-gmail-with-python/). (SEND_URL_TO_EMAIL is the recipient email address to which you want to send the temporary url.)
```
GMAIL_USERNAME=xxx@gmail.com
GMAIL_PASSWORD=
SEND_URL_TO_EMAIL=xxx@xxx.com
```

### Setup autostart for the config UI and the bot (optional)

You can configure the bot and the config UI to start automatically when the Raspberry starts.

1. Change the permission of the start bot bash script to be executable:
```
chmod +x scripts/start_bot.sh
```
2. Create a new service definition file: 
```
sudo nano /etc/systemd/system/start_bot.service
```
3. Then add the following contents:
```
[Unit]
Description=Start Bot Script

[Service]
User=bot
WorkingDirectory=/home/bot/pi_gptbot/app
ExecStart=/home/bot/pi_gptbot/scripts/start_bot.sh
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```

4. Finally enable the autostart:
```
sudo systemctl enable start_bot
```

And if you want to start the config UI as well automatically:

1. Change the permission of the start bot bash script to be executable:
```
chmod +x scripts/start_config_ui.sh
```
2. Create a new service definition file: 
```
sudo nano /etc/systemd/system/start_config_ui.service
```
3. Then add the following contents:
```
[Unit]
Description=Start Config UI Web Server Script

[Service]
User=bot
WorkingDirectory=/home/bot/pi_gptbot/app
ExecStart=/home/bot/pi_gptbot/scripts/start_config_ui.sh
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```
4. Finally enable the autostart:
```
sudo systemctl enable start_config_ui
```
5. You can check the exposed http tunnel url if you run the following command after a system start:
```
sudo systemctl status start_config_ui
```
You will see a line similar to:  `NiceGUI is on air at http://on-air.nicegui.io/devices/xxxxxx/`
The generated URL works only for 1 hour.

## Usage

To start the app without the autostart scripts, you can just run it with python (if you are in the pi_gptbot folder):
```
python3 app/config_ui.py
```

And to start the config UI:
```
python3 app/config_ui.py
``` 
The web app starts to listen on port 8080 and you can open it up on your computer or mobile phone that is on the same network as the voice assistant (using the IP of the voice assistant).
NiceGUI also creates a publicly accessible URL (via http tunnel). You will see a line similar to:  `NiceGUI is on air at http://on-air.nicegui.io/devices/xxxxxx/`. This can be opened anywhere.
If you want to disable it, open config_ui.py and remove the on_air=True part at the end. The generated URL works only for 1 hour.

## Adding new personalities to the voice assistant

You can add / edit system prompts that you can pick on the config UI. These system prompts influence how the voice assistant "behaves", what personality it will have.
Create a new file with name ai_personalities_user.yaml in the app folder:
`nano ai_personalities_user.yaml`

## Wifi config

https://medium.com/swlh/raspberry-pi-3-connect-to-multiple-wifis-set-multiple-static-ips-52f8a80d2ee1
You need to access the device first e.g. on a wired network connection, then ssh into the machine and edit the wpa_supplicant file:

`sudo nano /etc/wpa_supplicant/wpa_supplicant.conf`

Then add the entry:
```
network={‎
‎    ssid="NETWORK_SSID"‎
‎    psk="NETWORK_PASSPHRASE"‎‎}‎ 
```

Save and restart (double check the above settings if they are correct)

## Config UI

If you are running the voice assistant on a local network, it will be available on the following URL: http://pi-gptbot:8080/
If you need to access the config UI, e.g. to reload the assistant or change parameters, an automatic email can be configured via the environment variables (see chapter "Set required environment variables") that will announce a temporarily generated URL, that is made available using a tunnel.

On the config UI, you can configure the following settings:
- Max tokens and temperature for the OpenAI APIs (the GPT model name does not have an effect for Azure)
- Max token count for the whole conversation (ChatGPT 3.5 can support about 4K tokens). Handy to improve the response time. After this amount of tokens are reached, the conversation history resets
- Prompt presets: you can use the preconfigured "personalities" or use your own (see previous chapter)
- Azure TTS voice name
- Volume, pitch, speaking rate
- Set if after each speaking "round", the voice assistant should mute the mic, which gets enabled on a button press (this can be handy in a noisy environment, where otherwise you would have no influence which commands the assitant picks up)
- To speed up the response time a bit, you can disable face redraws on the LCD
- There's an experimental language switch feature where you could use a voice command to change languages (see source code)

![Config UI 1](https://github.com/bbence84/pi_gptbot/assets/1684946/fa944103-e188-493d-afe4-55d5709c2f65)

## Contributing

I am open for contributions and pull request to further improve the project :)

## Possible future features and open issues

- [ ] When the device hasn't booted for a longer time (~10 hours or more), then the speech is not recognized. You need to restart the Raspberry or the app to make it work
- [X] Create config for "headless" assistant (make the bot work without an LCD screen)
- [ ] Improve the performance of the facial expression redraw
- [ ] Dockerize the whole thing (help would be appreciated, as I am stuck with exposing the audio and low level GPIO access that is required by the LCD display library)