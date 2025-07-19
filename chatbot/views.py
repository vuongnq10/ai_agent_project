# 1. N8N
# 2. Langchain
# 3. LLMs

from django.http import JsonResponse
import os
import google.generativeai as genai

GEMINI_MODEL = "gemini-1.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")


def chat(request):
    try:
        user_message = request.GET.get("query")
        print(f"Received user message: {user_message}")

        if not user_message:
            return JsonResponse({"error": "Message not provided"}, status=400)

        # Configure the Generative AI model

        if not API_KEY:
            return JsonResponse(
                {"error": "GOOGLE_API_KEY environment variable not set"}, status=500
            )

        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Send message to the Generative AI model
        response = model.generate_content(user_message)

        ai_message = response.text
        return JsonResponse({"message": ai_message})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# def chat(request):
#     try:
#         user_message = request.GET.get("query")
#         print(f"Received user message: {user_message}")

#         if not user_message:
#             return JsonResponse({"error": "Message not provided"}, status=400)

#         # Configure the Generative AI model

#         if not API_KEY:
#             return JsonResponse(
#                 {"error": "GOOGLE_API_KEY environment variable not set"}, status=500
#             )

#         llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=API_KEY)

#         # Send message to the Generative AI model
#         response = llm.invoke([HumanMessage(content=user_message)])

#         ai_message = response.content
#         return JsonResponse({"message": ai_message})

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
