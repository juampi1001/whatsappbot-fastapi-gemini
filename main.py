from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import sett

app = FastAPI()

class WhatsAppEvent(BaseModel):
    message: dict

@app.post("/")
async def handle_post_request(request: Request):
    data = await request.json()
    print("POST request data recibido :", data)
    return {"status": "success", "message": "POST request recibido"}

@app.get("/")
def verify(request: Request):
    mode = request.query_params.get('hub.mode')
    challenge = request.query_params.get('hub.challenge')
    token = request.query_params.get('hub.verify_token')

    if mode and token:
        if mode == 'subscribe' and token == sett.verify_token:
            print("WEBHOOK_VERIFIED")
            return JSONResponse(content=int(challenge), status_code=200)
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    return {"code": 200, 'message': 'test'}

@app.post("/webhook")
def receive_message(event: WhatsAppEvent):
    try:
        user_message = event.message['text']
        sender_id = event.message['sender']['id']
        bot_response = f'You said: {user_message}' #sending an echo message

        # Prepare response for WhatsApp
        response_data = {
            'recipient': {'id': sender_id},
            'message': {'text': bot_response}
        }

        send_whatsapp_message(sender_id, bot_response)

        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

def send_whatsapp_message(recipient_id, message_body):
    headers = {
        'Authorization': f'Bearer {sett.whatsapp_api_token}',
        'Content-Type': 'application/json'
    }

    data = {
        'phone': recipient_id,
        'message': {
            'text': message_body
        }
    }

    try:
        response = requests.post(sett.whatsapp_url, headers=headers, json=data)
        response.raise_for_status()  # Raises HTTPError for bad responses

        print("WhatsApp API response:", response.text)  # Add this line for debugging

        return response.json()  # If you want to return the API response data
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
        raise HTTPException(status_code=500, detail=f"HTTP Error: {errh}")
    except requests.exceptions.RequestException as err:
        print("Request Error:", err)
        raise HTTPException(status_code=500, detail=f"Request Error: {err}")
