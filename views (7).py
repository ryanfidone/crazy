from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from .forms import RegisterForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            group, _ = Group.objects.get_or_create(name="LibraryMember")
            user.groups.add(group)
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "register/register.html", {"form": form})
