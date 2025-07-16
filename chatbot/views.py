from django.http import JsonResponse
import json
import os
import google.generativeai as genai

GEMINI_MODEL = "gemini-2.5-flash"


def chat(request):
    try:
        user_message = request.GET.get("query")

        if not user_message:
            return JsonResponse({"error": "Message not provided"}, status=400)

        # Configure the Generative AI model
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return JsonResponse(
                {"error": "GOOGLE_API_KEY environment variable not set"}, status=500
            )

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Send message to the Generative AI model
        response = model.generate_content(user_message)

        ai_message = response.text
        return JsonResponse({"message": ai_message})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
