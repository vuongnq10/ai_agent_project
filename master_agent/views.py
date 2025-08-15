from django.http import JsonResponse, StreamingHttpResponse, HttpResponse


# Create your views here.
def chat(request):

    user_message = request.GET.get("query")

    return JsonResponse({"message": user_message})
