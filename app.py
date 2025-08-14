from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Replace with your actual credentials.
# These will be loaded from your Render Environment Variables.
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
COVERGO_API_KEY = os.environ.get("COVERGO_API_KEY")
PRODUCTGPT_AGENT_ID = os.environ.get("PRODUCTGPT_AGENT_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    # Webhook verification request from Meta
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return 'Verification token mismatch', 403

@app.route('/webhook', methods=['POST'])
def handle_message():
    # Handle incoming messages from WhatsApp
    data = request.get_json()
    if 'entry' in data and data['entry'][0]['changes'][0]['value']['messages']:
        message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
        from_number = message_info['from']
        message_body = message_info['text']['body']

        print(f"Received message from {from_number}: {message_body}")

        # 1. Send the message to your Covergo ProductGPT agent
        covergo_headers = {
            'Authorization': f'Bearer {COVERGO_API_KEY}',
            'Content-Type': 'application/json'
        }
        covergo_payload = {
            'agent_id': PRODUCTGPT_AGENT_ID,
            'text': message_body,
            'user_id': from_number
        }
        
        try:
            covergo_response = requests.post("https://ai-workbench.dev.asia.covergo.cloud/api/v1/chat", headers=covergo_headers, json=covergo_payload)
            response_text = covergo_response.json()['response_text']
        except Exception as e:
            print(f"Error calling Covergo: {e}")
            response_text = "Sorry, my AI backend is unavailable."

        # 2. Send the response back to WhatsApp
        send_whatsapp_message(from_number, response_text)

    return 'OK', 200

def send_whatsapp_message(to_number, text):
    headers = {
        'Authorization': f'Bearer {META_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": text
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"WhatsApp message sent. Status code: {response.status_code}")

if __name__ == '__main__':
    app.run()