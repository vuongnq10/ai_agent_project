from django.http import JsonResponse
from tech_implement.tools.agent import LangGraphAgent

agent = LangGraphAgent()


def chat(request):
    user_message = request.GET.get("query")

    print("User message:", user_message)

    response = agent(user_message)

    return JsonResponse({"success": True, "message": response})
