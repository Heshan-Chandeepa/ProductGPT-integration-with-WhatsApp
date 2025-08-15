from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Load credentials from Render Environment Variables.
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
COVERGO_API_KEY = os.environ.get("COVERGO_API_KEY")

# The Agent ID from the successful API call you provided.
PRODUCTGPT_AGENT_ID = "32dcd1d8-d3ca-4d18-aaea-ac650a029fff" 

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    else:
        print("Webhook verification failed.")
        return 'Verification token mismatch', 403

@app.route('/webhook', methods=['POST'])
def handle_message():
    data = request.get_json()
    if 'entry' in data and data['entry'][0]['changes'][0]['value'].get('messages'):
        message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
        from_number = message_info['from']

        if 'text' in message_info:
            message_body = message_info['text']['body']
            print(f"Received text message from {from_number}: {message_body}")

            # 1. Send the message to your Covergo ProductGPT agent using the correct URL and headers
            covergo_headers = {
                'accept': 'text/event-stream',
                'authorization': f'Bearer {COVERGO_API_KEY}',
                'content-length': '0',
                'covergo-client-id': 'admin_portal',
                'covergo-tenant-id': 'apeiron',
            }

            # Use the user's phone number as the session ID for a simple prototype.
            session_id = from_number
            # Construct the URL with query parameters exactly as shown in the successful request.
            covergo_url = f"https://ai-workbench-api.dev.asia.covergo.cloud/api/v1/ai-agents/{PRODUCTGPT_AGENT_ID}/chat/{session_id}/send?message={message_body}&isFollowUpQuestion=false"
            
            response_text = "Sorry, my AI backend is unavailable or responded unexpectedly."
            try:
                # Send the POST request with the corrected headers and no JSON payload.
                covergo_response = requests.request("POST", covergo_url, headers=covergo_headers)
                covergo_response.raise_for_status() 
                
                # Check for a streaming response and parse as needed, or assume a JSON response.
                if 'application/json' in covergo_response.headers.get('Content-Type', ''):
                    covergo_data = covergo_response.json()
                    if covergo_data.get('messages') and covergo_data['messages'][0].get('text'):
                        response_text = covergo_data['messages'][0]['text']
                    else:
                        response_text = "Covergo responded, but the message format was unexpected."
                else:
                    response_text = covergo_response.text  # Use the raw text if not JSON

            except requests.exceptions.RequestException as e:
                print(f"Error calling Covergo API: {e}")
            
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
    if response.status_code != 200:
        print(f"WhatsApp API error response: {response.text}")

if __name__ == '__main__':
    app.run()