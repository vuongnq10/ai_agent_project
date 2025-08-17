import time
import json
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse

from master_agent.agents.master import MasterAgent

master_agent = MasterAgent()


def chat(request):
    user_message = request.GET.get("query")

    print("User message:", user_message)

    def event_stream():
        try:
            for chunk in master_agent(user_message):
                for line in chunk.splitlines(keepends=True):
                    for char in line:
                        payload = {"character": char}
                        yield f"data: {json.dumps(payload)}\n\n"
                        time.sleep(0.01)

            yield f"event: end\ndata: END\n\n"

        except Exception as e:
            print(f"Error in streaming: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
