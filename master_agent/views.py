import time
import json
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse

from master_agent.agents_gemini.agentic_agent import MasterGemini
from master_agent.agents_openai.master import MasterOpenAI

master_gemini = MasterGemini()
master_openai = MasterOpenAI()


def chat_gemini(request):
    user_message = request.GET.get("query")

    print("User message:", user_message)

    def event_stream():
        try:
            for chunk in master_gemini(user_message):
                for line in chunk.splitlines(keepends=True):
                    for char in line:
                        payload = {"character": char}
                        yield f"data: {json.dumps(payload)}\n\n"
                        time.sleep(0.005)

            yield f"event: end\ndata: END\n\n"

        except Exception as e:
            print(f"Error in streaming: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


def chat_openai(request):
    user_message = request.GET.get("query")

    def event_stream():
        try:
            for chunk in master_openai(user_message):
                for line in chunk.splitlines(keepends=True):
                    for char in line:
                        payload = {"character": char}
                        yield f"data: {json.dumps(payload)}\n\n"
                        time.sleep(0.005)

            yield f"event: end\ndata: END\n\n"

        except Exception as e:
            print(f"Error in streaming: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
