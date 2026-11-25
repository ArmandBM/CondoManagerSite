from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import User, Apartment, Complains, Package

@login_required(login_url="login")
def index(request):
    return render(request, "apartments/index.html", {
        "title": "Home"
    })

def login_view(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse("index"))
            else:
                return render(request, "apartments/login.html", {
                    "title": "Login",
                    "error": "Invalid username or password."
                })
        else:
            return render(request, "apartments/login.html", {
                "title": "Login"
            })
    #TODO: Treat case when the user is already logged in. Rare, but possible.

def logout_redirect(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))

def packages(request):
    apartament = getUserApartment(request.user)
    if apartament is None:
        return render(request, "apartments/packages.html", {
            "title": "Packages",
            "error": "You are not associated with any apartment."
        })
    else:

        packages = Package.objects.filter(apartament=apartament)
        return render(request, "apartments/packages.html", {
        "title": "Packages",
        "packages": packages
        })

def complains(request):
    complains = Complains.objects.filter(user=request.user)
    print('Complains for user ' + str(request.user) + ': ' + str(complains))
    if request.method =="POST":
        complain_text = request.POST.get("complain")
        if complain_text:
            Complains.objects.create(user=request.user, complain_text=complain_text)
            return HttpResponseRedirect(reverse("complains"))

        return render(request, "apartments/complain.html", {
            "title": "Complains",
            "error": "Please enter a complaint before submitting.",
            "complains": complains
        })
        
    return render(request, "apartments/complain.html", {
        "title": "Complains",
        "complains": complains
    })

def getUserApartment(user):
    user = User.objects.get(id=user.id)
    print('The user is ' + str(user))
    return user.apartament
