from django.shortcuts import render
from django.http import JsonResponse
import json
from google import genai
from django.conf import settings

# Create your views here.
def chat(request):
  if request.method == "POST":
    #access the request body and decode the raw bytes to be left with json string
    json_msg = request.body.decode("utf-8")
    #coverting json string to python dictionary
    user_msg = json.loads(json_msg)
    #now i can get the message's value using user_msg[]"message"] but its better to use:
    msg_to_send = user_msg.get("message")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    #Google SDK already converts the response to a Python object hence response.text is just a Python string  but Javascript expects a JSON resonse  
    response = client.models.generate_content(
      model = "gemini-2.5-flash",
      contents = msg_to_send
    )

    #first create a python dictionary then convert to a json respon
    return JsonResponse({
      "reply": response.text
    })

   
