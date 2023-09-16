import json
import requests
import openai
openai.api_key = ""
from pathlib import Path

class GPTWrapper:
    
    def __init__(self, openai_model="gpt-4-32k"):
        self.service_token = self.get_service_token()
        self.openai_model = openai_model
        self.max_tokens = 600
        self.temperature = 0.0        
        
        return
    
    def get_openai_model(self):
        return self.openai_model
    
    def set_model_params(self, openai_model, max_tokens, temperature):
        self.openai_model = openai_model
        self.max_tokens = max_tokens
        self.temperature = temperature       
    
    def get_service_token(self):
        json_path = str(Path(__file__).resolve().parent.joinpath('', '1d4ef6fb-2077-4dd7-9567-9bcebe839ec3.json'))
        with open(json_path, "r") as key_file:
            svc_key = json.load(key_file)
            
        self.svc_url = svc_key["url"]
        client_id = svc_key["uaa"]["clientid"]
        client_secret = svc_key["uaa"]["clientsecret"]
        uaa_url = svc_key["uaa"]["url"]

        params = {"grant_type": "client_credentials" }
        resp = requests.post(f"{uaa_url}/oauth/token",
                            auth=(client_id, client_secret),
                            params=params)
        return resp.json()["access_token"]    
    
    def get_file_contents(self, file_name):
        file_open = open(file_name, "r", encoding='utf8')
        file_content = file_open.read()
        return file_content

    def get_model_config_guide_content(self):
        return self.get_file_contents("ibp_model.txt")    
    
    def gpt_call(self, chat_messages):
        
        completion_tokens = 0
        prompt_tokens = 0
        
        headers = { "Authorization":  f"Bearer {self.service_token}", "Content-Type": "application/json" }

        data = {
            "deployment_id": self.openai_model,
            "messages": chat_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "frequency_penalty": 0, "presence_penalty": 0,
            "top_p": 0.95
        }            

        response = requests.post(f"{self.svc_url}/api/v1/completions", headers=headers, json=data)
        response_data = response.json()
        #print(response_data)
        
        if ("status" in response_data):
            if (response_data['status'] == 500):
                raise Exception("Azure OpenAI service error")
               
        response_text = response_data['choices'][0]['message']['content'];

        completion_tokens = response_data['usage']['completion_tokens']
        prompt_tokens = response_data['usage']['prompt_tokens']
            
        return { "response_text": response_text, "completion_tokens": completion_tokens, "prompt_tokens": prompt_tokens}
