import os
import logging
import backoff
import time
import re

from botconfig import BotConfig
bot_config = BotConfig()

from gptwrapper import GPTWrapper

class GPTChatService:
    
    log = logging.getLogger("bot_log")
    logging.basicConfig(filename='gpt_service.log', level=logging.DEBUG, filemode='w')
    
    def __init__(self, default_language="English", keep_history=True):

        self.gpt_wrapper = GPTWrapper(openai_model="gpt-35-turbo")
        self.gpt_wrapper.set_model_params(openai_model="gpt-35-turbo", max_tokens=bot_config.max_tokens, temperature=bot_config.temperature)           

        self.default_language = default_language        

        default_lang_prompt = f" Respond in {self.default_language} by default."
        
        self.initial_prompt = [{"role": "user", "content":bot_config.initial_prompt + default_lang_prompt }]

        self.chat_messages = self.initial_prompt
                
        self.log.debug(f"Initial ChatGPT prompt:  {self.chat_messages}")

        self.keep_history = keep_history

        # Statistics
        self.total_ai_tokens = 0        
    
    def change_language(self, language):
        self.default_language = language
        
    def ask(self, question):

        if (self.keep_history == False):
            self.chat_messages = self.initial_prompt        
    
        self.append_text_to_chat_log(question, True)
                   
        start = time.time()

        try:
            assistant_response = self.gpt_wrapper.gpt_call(self.chat_messages)
        except Exception as e:
            print(f"OpenAI API returned an Error")
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)          
            return ""    
         
        # print(f'OpenAI API call ended: {time.time() - start} ms')

        response_text = assistant_response['response_text']
        response_text.isalnum();

        self.update_stats(self.chat_messages, response_text)
        
        response_text = self.adjust_response(response_text)
        
        if (self.keep_history):        
            self.append_text_to_chat_log(response_text, False)
        else:
            self.chat_messages = self.initial_prompt
        
        self.log.info(f"OpenAI ChatGPT response:  {response_text}")

        return response_text     
    
    def update_stats(self, chat_messages, response):
        pass

    def get_stats(self):
        return self.total_ai_tokens
 
    def append_text_to_chat_log(self, text, is_user = True):
        role = "assistant"
        if (is_user):
            role = "user"
        self.chat_messages.append({"role": role, "content": text })
        self.log.info(f"Chat buffer:  {self.chat_messages}")
        
    def adjust_response(self, response_text):
        adjusted_response_text = response_text
        if response_text.endswith('.'): 
            word_before_last_dot = re.findall(r'\b\d+\b(?=[^\W_]*\.[^\W_]*$)', response_text)
            if word_before_last_dot:
                number_str = word_before_last_dot[0]
                sentence_without_dot = response_text[:-1] if response_text[-2] == ' ' else response_text[:-1] + ' '
                if number_str in sentence_without_dot:
                    adjusted_response_text = sentence_without_dot.replace(number_str + ".", number_str)
        return adjusted_response_text