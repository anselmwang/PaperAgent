import requests
import json

def send_chat_message(model, messages, stream):
    url = 'http://localhost:11434/api/chat'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'model': model,
        'messages': messages,
        'stream': stream
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

# Example usage:
# response = send_chat_message(
#     "mistral",
#     [{"role": "user", "content": "why is the sky blue?"}],
#     False
# )
# print(response)
