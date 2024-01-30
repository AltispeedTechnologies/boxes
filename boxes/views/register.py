from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from boxes.forms import RegisterForm

def register(request):
    if request.method == "GET":
        form = RegisterForm()
        return render(request, "register.html", { "form": form}) 

    if request.method == "POST":
        form = RegisterForm(request.POST) 
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            messages.success(request, "User successfully registered.")
            login(request, user)
            success = reverse_lazy("home")
            return redirect(success)
        else:
            return render(request, "register.html", {"form": form})
