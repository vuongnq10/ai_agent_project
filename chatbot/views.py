# 1. N8N
# 2. Langchain
# 3. LLMs

from django.http import JsonResponse
import os
import requests
import json
import google.generativeai as genai
from cx_connector.tool_server import ToolServer
from tools.agent import Agent

GEMINI_MODEL = "gemini-1.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
tools = ToolServer()
agent = Agent()


def chat(request):
    user_message = request.GET.get("query")

    response = agent(user_message)  # Using the callable instance
    return JsonResponse({"success": True, "message": response})


def chat_1(request):
    try:
        user_message = request.GET.get("query")

        if not user_message:
            return JsonResponse({"error": "Message not provided"}, status=400)

        # Configure the Generative AI model

        if not API_KEY:
            return JsonResponse(
                {"error": "GOOGLE_API_KEY environment variable not set"}, status=500
            )

        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL, tools=tools.get_tools_config())

        # Send message to the Generative AI model
        response = model.generate_content(user_message)

        ai_message = response.text
        return JsonResponse({"message": ai_message})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def chat_new(request):
    try:
        user_message = request.GET.get("query")

        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        # response = model.generate_content(user_message)

        system_prompt = """You are a tool-aware assistant. 
        If the user's message requires using a tool, respond ONLY in this JSON format:
        {
            "tool": "<tool_name>",
            "parameters": {
                "param1": "value1",
                "param2": "value2"
            }
        }
        If no tool is needed, respond like:
        {
            "reply": "<your message to the user>"
        }
        """
        response = model.generate_content(
            [
                {"role": "system", "parts": [system_prompt]},
                {"role": "user", "parts": [user_message]},
            ]
        )

        print(f"AI response: {response.text}")

        parsed = response.text.strip()

        # Step 1: Parse the AI response
        try:
            parsed_json = json.loads(parsed)
        except Exception as parse_err:
            return JsonResponse({"error": f"Invalid AI response: {parsed}"}, status=500)

        print(f"Parsed response: {parsed_json}")

        # Step 2: Call tool if needed
        if "tool" in parsed_json:
            tool_name = parsed_json["tool"]
            parameters = parsed_json.get("parameters", {})
            mcp_response = requests.post(
                MCP_URL, json={"tool": tool_name, "input": parameters}
            )
            return JsonResponse({"tool": tool_name, "result": mcp_response.json()})

        print("No tool needed, returning Gemini's reply.")

        # Otherwise, return Gemini's reply
        return JsonResponse({"message": parsed_json.get("reply", "[No reply]")})

        # ai_message = response.text

        # return JsonResponse({"message": ai_message})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# def ticker_data(request):
#     result = get_data()
#     return JsonResponse(result)


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
