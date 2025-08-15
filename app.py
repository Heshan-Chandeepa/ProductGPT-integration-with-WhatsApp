from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Load credentials from Render Environment Variables.
# IMPORTANT: Ensure these are set correctly in your Render dashboard.
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
COVERGO_API_KEY = os.environ.get("COVERGO_API_KEY")

# Hardcoded Agent ID based on your provided information
PRODUCTGPT_AGENT_ID = "c378fdd7-0028-4309-9df8-236fcdd0432d" 

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN") # e.g., "my-secret-token-for-render"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Handles Meta's webhook verification GET request."""
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
    """Handles incoming POST requests from Meta (WhatsApp messages)."""
    data = request.get_json()
    
    if 'entry' in data and data['entry'][0]['changes'][0]['value'].get('messages'):
        message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
        from_number = message_info['from']
        
        if 'text' in message_info:
            message_body = message_info['text']['body']
            print(f"Received text message from {from_number}: {message_body}")

            # 1. Send the message to your Covergo ProductGPT agent using the correct URL format
            covergo_headers = {
                'Authorization': f'Bearer {COVERGO_API_KEY}',
            }
            # The URL from your successful request uses a session ID and query parameters.
            # We use the user's phone number as the session ID for a simple prototype.
            covergo_url = f"https://ai-workbench-api.dev.asia.covergo.cloud/api/v1/ai-agents/{PRODUCTGPT_AGENT_ID}/chat/{from_number}/send?message={message_body}&isFollowUpQuestion=false"
            
            response_text = "Sorry, my AI backend is unavailable or responded unexpectedly."
            try:
                # Send the POST request to the corrected URL.
                covergo_response = requests.post(covergo_url, headers=covergo_headers)
                covergo_response.raise_for_status() 
                
                covergo_data = covergo_response.json()
                if covergo_data.get('messages') and covergo_data['messages'][0].get('text'):
                    response_text = covergo_data['messages'][0]['text']
                else:
                    response_text = "Covergo responded, but the message format was unexpected."

            except requests.exceptions.RequestException as e:
                print(f"Error calling Covergo API: {e}")
                response_text = "Sorry, my AI backend encountered an error. Please try again later."
            except KeyError as e:
                print(f"Covergo response missing expected key: {e}")
                response_text = "An error occurred while parsing the AI's response."
            
            # 2. Send the response back to WhatsApp
            send_whatsapp_message(from_number, response_text)

        else:
            send_whatsapp_message(from_number, "Sorry, I can only process text messages at the moment. Please try typing your question.")
    
    return 'OK', 200

def send_whatsapp_message(to_number, text):
    """Sends a text message back to the specified WhatsApp number."""
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