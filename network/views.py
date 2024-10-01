from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import  json
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .models import User, Post

def index(request):
    posts = Post.objects.all().order_by('-timestamp')

    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'network/index.html', {
        'page_obj': page_obj
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def new_post(request):
    if request.method == "POST":
        content = request.POST["content"]
        post = Post(
            user=request.user,
            content=content,
            timestamp=datetime.now(),

        )
        post.save()
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/new_post.html")


def profile(request, username):
    profile_user = User.objects.get(username=username)
    posts = Post.objects.filter(user=profile_user).order_by('-timestamp')

    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'network/profile.html', {
        "profile_user": profile_user,
        'page_obj': page_obj,
        "actual_user": request.user
    })

@login_required
def follow(request, user_id):
    user_to_follow = User.objects.get(id=user_id)
    request.user.following.add(user_to_follow)
    return redirect('profile', username=user_to_follow.username)

@login_required
def unfollow(request, user_id):
    user_to_unfollow = User.objects.get(id=user_id)
    request.user.following.remove(user_to_unfollow)
    return redirect('profile', username=user_to_unfollow.username)

@login_required
def following(request):
    user = request.user
    following = user.following.all()
    posts = Post.objects.filter(user__in=following).order_by('-timestamp')

    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'network/following.html', {
        'page_obj': page_obj
    })

@login_required
@require_http_methods(["PUT"])
def edit_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id, user=request.user)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found or you do not have permission to edit this post."}, status=404)

    data = json.loads(request.body)
    content = data.get("content", "")
    if content.strip() == "":
        return JsonResponse({"error": "Content cannot be empty."}, status=400)

    post.content = content
    post.save()

    return JsonResponse({"success": True, "content": post.content})


@login_required
@require_POST
def toggle_like(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found."}, status=404)

    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({"likes_count": post.likes.count(), "liked": liked})

def delete_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        if post.user == request.user:
            post.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def search(request):
    query = request.GET.get('q')
    if query:
        try:
            user = User.objects.get(username__iexact=query)
            return redirect(reverse('profile', kwargs={'username': user.username}))
        except User.DoesNotExist:
            return render(request, 'network/search_results.html')
