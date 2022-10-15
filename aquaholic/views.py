from django.http import HttpResponse


# Create your views here.
def homepage(request):
    return HttpResponse("Welcome to Aquaholic🎉")