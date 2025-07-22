# 1. N8N
# 2. Langchain
# 3. LLMs

from django.http import JsonResponse
import os
from .agent import Agent

GEMINI_MODEL = "gemini-1.5-flash"
API_KEY = os.getenv("GOOGLE_API_KEY")
agent = Agent()


def chat(request):
    user_message = request.GET.get("query")

    response = agent(user_message)  # Using the callable instance
    return JsonResponse({"success": True, "message": response})


# def call_agent(self, prompt: str) -> str:
#     chat = self.model.start_chat(enable_automatic_function_calling=True)
#     response = chat.send_message(prompt)

#     print("Initial response:", response.text)

#     while True:
#         # Check if we have function calls
#         function_calls = []
#         for candidate in response.candidates:
#             if candidate.content.parts:
#                 for part in candidate.content.parts:
#                     if hasattr(part, "function_call") and part.function_call:
#                         function_calls.append(part.function_call)

#         if not function_calls:
#             print("✅ Final result:", response.text)
#             return response.text

#         # Process all function calls in this response
#         tool_responses = []
#         for func_call in function_calls:
#             tool_name = func_call.name
#             args = dict(func_call.args)

#             print(f"Calling tool: {tool_name}({args})")

#             try:
#                 result = self.execute_tool(tool_name, **args)
#                 tool_responses.append(
#                     genai.types.Part(
#                         function_response={"name": tool_name, "response": result}
#                     )
#                 )
#                 print(f"↳ Result: {result}")
#             except Exception as e:
#                 tool_responses.append(
#                     genai.types.Part(
#                         function_response={
#                             "name": tool_name,
#                             "response": f"Error: {str(e)}",
#                         }
#                     )
#                 )

#         # Send tool responses back to Gemini
#         response = chat.send_message(
#             content=genai.types.Content(role="tool", parts=tool_responses)
#         )

#         print("Updated response:", response.text)
