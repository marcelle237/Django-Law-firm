import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # make sure your key is set

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")

        # You can prompt the model to focus on Cameroonian law:
        prompt = f"You are a legal assistant specializing in Cameroon law. Answer concisely and accurately.\n\nUser: {user_message}"

        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # or gpt-4-turbo
            messages=[{"role": "user", "content": prompt}],
        )

        reply = completion.choices[0].message.content
        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "Invalid request"}, status=400)
from django.shortcuts import render

# Create your views here.
