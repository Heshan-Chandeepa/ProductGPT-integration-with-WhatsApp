from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Load credentials from Render Environment Variables.
# IMPORTANT: Ensure these are set correctly in your Render dashboard.
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# HARDCODED JWT directly from your browser's dev tools as per Covergo support.
# IMPORTANT: This token will expire. For production, you'd need a refresh mechanism.
COVERGO_JWT = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJEWUdiM1g3dkNRc0U1ZkIzQzFyaTljcDZHWnRZVXFBdDVDVlZjOFRucjY4In0.eyJleHAiOjE3NTUzNDEwMjAsImlhdCI6MTc1NTMyNjYyMCwiYXV0aF90aW1lIjoxNzU1MzI2NjIwLCJqdGkiOiJlMzY0YWU3Ni1mYjE0LTRjOTQtOGZmYi0xMDY0ZDRhYTgxYTAiLCJpc3MiOiJodHRwczovL2tleWNsb2FrLmRldi5jb3ZlcmdvLmNsb3VkL3JlYWxtcy9haV9hcGVpcm9uX2RldiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI1NDE2MWVmNC0zZjNkLTQ2YTMtOGFmNi1hZjY2NjlhYmJkYTciLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhZG1pbl9wb3J0YWwiLCJzaWQiOiJhMmVhM2IzOS03NzI5LTRjNTItYmMzNi0yNDRmNzAwMjUxZTQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9sb2NhbGhvc3Q6NDIwMC8qIiwiaHR0cHM6Ly9haS13b3JrYmVuY2guZGV2LmFzaWEuY292ZXJnby5jbG91ZC8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsImRlZmF1bHQtcm9sZXMtYWlfYXBlaXJvbl9kZXYiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicm9sZV90eXBlIjoiVEVOQU5UX0FETUlOIiwibmFtZSI6IkNoYW5kZWVwYSBMYW5rYWJhbmRhbmFnZSIsInByZWZlcnJlZF91c2VybmFtZSI6ImNoYW5kZWVwYS5sYW5rYWJhbmRhbmFnZUBjb3ZlcmdvLmNvbSIsImdpdmVuX25hbWUiOiJDaGFuZGVlcGEiLCJmYW1pbHlfbmFtZSI6IkxhbmthYmFuZGFuYWdlIiwiZW1haWwiOiJjaGFuZGVlcGEubGFua2FiYW5kYW5hZ2VAY292ZXJnby5jb20ifQ.S9EyIdUaqMo20QQflCzavREtXy8WS4sMrr3dXXwgnGLoF8h3mIvttaH1pw7iiH2ue6zamvAFUg3lBGcGQWfI2hNvXI0wRlJoTPRr3PoQAlFMCUDj45mVwWIs0HTKgQYqL2u3adaD9VhUjy8VXMgfqEedyv8BAM_nh2hi7PHlRN3tRLSipt9mLJkR6ENlMHplPVbYuXLgu0ZKTMdSSyEvM7DArZLgHNJF7sVWfu2gF0_LffjP7NAeuczK31LL3WBoblbBUnPIlQnelRX44cnps4wu4gchUkmBtDMEQwUG-fJ8I5egdiawITOuJAq1_WfFCq_AJhqrIIWvJ3iFTD_8hg"

# Correct Agent ID based on the successful API call you provided
PRODUCTGPT_AGENT_ID = "32dcd1d8-d3ca-4d18-aaea-ac650a029fff" 

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
                'accept': 'text/event-stream', # As seen in your successful request
                'authorization': f'Bearer {COVERGO_JWT}', # Using the JWT now
                'content-length': '0', # As seen in your successful request
                'covergo-client-id': 'admin_portal', # As seen in your successful request
                'covergo-tenant-id': 'apeiron', # As seen in your successful request
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
                
                # Assuming the Covergo response structure is { "messages": [ { "text": "..." } ] }
                # Adjust this parsing based on actual Covergo API response
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