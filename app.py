from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Load credentials from Render Environment Variables.
# IMPORTANT: Ensure these are set correctly in your Render dashboard.
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
COVERGO_API_KEY = os.environ.get("COVERGO_API_KEY")

# Directly use the provided Agent ID
PRODUCTGPT_AGENT_ID = "4b490482-d481-4850-b0d7-116b0a9a6d87" 

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN") # e.g., "my-secret-token-for-render"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Handles Meta's webhook verification GET request.
    Meta sends a GET request to your webhook URL with hub.mode, hub.verify_token, and hub.challenge.
    Your server must respond with the hub.challenge if the tokens match.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    else:
        print("Webhook verification failed: Token mismatch or invalid mode.")
        return 'Verification token mismatch', 403

@app.route('/webhook', methods=['POST'])
def handle_message():
    """
    Handles incoming POST requests from Meta (WhatsApp messages and other events).
    Parses the incoming payload, calls the Covergo ProductGPT API, and sends a response back to WhatsApp.
    """
    data = request.get_json()
    print("Received webhook data:", data) # Log the full incoming payload for debugging

    # Check if the payload contains messages (to avoid KeyError for non-message events)
    # The structure can be complex, so we safely navigate through it.
    if 'entry' in data and data['entry']:
        for entry in data['entry']:
            if 'changes' in entry and entry['changes']:
                for change in entry['changes']:
                    if 'value' in change and change['value'].get('messages'):
                        # Process only messages (ignore status updates, etc.)
                        message_info = change['value']['messages'][0]
                        from_number = message_info['from'] # User's WhatsApp number

                        # Check for text messages specifically
                        if 'text' in message_info:
                            message_body = message_info['text']['body']
                            print(f"Received text message from {from_number}: {message_body}")

                            # 1. Send the message to your Covergo ProductGPT agent
                            covergo_headers = {
                                'Authorization': f'Bearer {COVERGO_API_KEY}',
                                'Content-Type': 'application/json'
                            }
                            # For a prototype, you can use a fixed session ID.
                            # In a production app, you'd manage unique session IDs per user.
                            session_id = from_number # Using from_number as session_id for simplicity
                            covergo_url = f"https://ai-workbench.dev.asia.covergo.cloud/api/v1/agents/{PRODUCTGPT_AGENT_ID}/chat/session/{session_id}/message"

                            covergo_payload = {
                                'agentId': PRODUCTGPT_AGENT_ID, # Ensure agentId is in payload if required by Covergo
                                'text': message_body,
                                'userId': from_number # Ensure userId is in payload if required by Covergo
                            }
                            
                            response_text = "Sorry, my AI backend is unavailable or responded unexpectedly."
                            try:
                                covergo_response = requests.post(covergo_url, headers=covergo_headers, json=covergo_payload)
                                covergo_response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
                                
                                # Assuming the Covergo response structure is { "messages": [ { "text": "..." } ] }
                                # Adjust this parsing based on actual Covergo API response
                                covergo_data = covergo_response.json()
                                if covergo_data.get('messages') and covergo_data['messages'][0].get('text'):
                                    response_text = covergo_data['messages'][0]['text']
                                else:
                                    print("Covergo response missing 'messages' or 'text' key.")
                                    response_text = "Covergo responded, but I couldn't understand its message."

                            except requests.exceptions.RequestException as e:
                                print(f"Error calling Covergo API: {e}")
                                response_text = "Sorry, my AI backend encountered an error. Please try again later."
                            except KeyError as e:
                                print(f"Covergo response missing expected key: {e}")
                                response_text = "An error occurred while parsing the AI's response."
                            
                            # 2. Send the response back to WhatsApp
                            send_whatsapp_message(from_number, response_text)

                        else:
                            # Handle other message types (e.g., image, video, audio)
                            print(f"Received non-text message from {from_number}. Ignoring for now.")
                            send_whatsapp_message(from_number, "Sorry, I can only process text messages at the moment. Please try typing your question.")
    
    return 'OK', 200 # Always return 200 OK to Meta

def send_whatsapp_message(to_number, text):
    """
    Sends a text message back to the specified WhatsApp number using Meta's API.
    """
    headers = {
        'Authorization': f'Bearer {META_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    # Meta's API version is v19.0 as seen in your earlier screenshots
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
        print(f"WhatsApp API error response: {response.text}") # Log error details

if __name__ == '__main__':
    # When running on Render, it will automatically handle the port.
    # For local testing, you might use app.run(port=5000, debug=True)
    app.run()