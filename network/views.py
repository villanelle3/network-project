from django.contrib.auth import authenticate, login, logout
from django import forms
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import User, Posts, Likes, Followers
from django.template.loader import render_to_string
from django.core.paginator import Paginator


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

@login_required(login_url="/login")  # redirect when user is not logged in
def index(request):
    if request.method == "GET":
        current_user = request.user
        seguindo = Followers.objects.filter(conta=current_user.id).values(
            "seguindo_id",
        )
        lista_de_ids = []
        for i in range(len(seguindo)):
            lista_de_ids.append(seguindo[i]["seguindo_id"])
        contents = Posts.objects.all()
        already_liked = []
        id = request.user.id
        for content in contents:
            if content.likes.filter(id=id).exists():
                already_liked.append(content.id)
        data = (
            Posts.objects.filter(dono__in=lista_de_ids)
            .order_by("-data")
            .values("texto", "data", "dono_id__username", "dono", "like_count", "id")
        )
        p = Paginator(data, 8)
        page = request.GET.get("page")
        todas = p.get_page(page)
        nums = " " * todas.paginator.num_pages
        return render(
            request,
            "network/timeline.html",
            {
                "usuario": current_user,
                "data": data,
                "already_liked": already_liked,
                "todas": todas,
                "nums": nums,
            },
        )


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
            return render(
                request,
                "network/login.html",
                {"message": "Invalid username and/or password.", "tipo": "danger"},
            )
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
            return render(
                request,
                "network/register.html",
                {"message": "Passwords must match.", "tipo": "danger"},
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "network/register.html",
                {"message": "Username already taken.", "tipo": "danger"},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def profile(request, pk):
    current_user = request.user
    if pk == current_user.id:
        dono = True
        dono_da_pag = current_user
    else:
        dono = False
        try:
            dono_da_pag = User.objects.filter(id=pk).values("username")[0]["username"]
        except Exception:
            dono_da_pag = False
            return render(request, "network/profile.html", {"dono_da_pag": dono_da_pag})

    posts = Posts.objects.filter(dono=pk).order_by("-data").values()
    seguidores = len(Followers.objects.filter(seguindo=pk).values())
    seguindo = len(Followers.objects.filter(conta=pk).values())

    lista_seguidores = Followers.objects.filter(seguindo=pk).values(
        "conta_id"
    )  # Lista de todo mundo que segue pk
    # Se current_user.id esta na lista, vai aparecer unfollow
    lista_de_seguidores = []
    for i in range(seguidores):
        lista_de_seguidores.append(lista_seguidores[i]["conta_id"])
    if current_user.id in lista_de_seguidores:
        Follow = "Unfollow"
    else:
        Follow = "Follow"

    if request.method == "POST":
        if Follow == "Unfollow":
            Followers.objects.filter(conta_id=current_user.id, seguindo_id=pk).delete()
        else:
            Followers.objects.create(conta_id=current_user.id, seguindo_id=pk).save()
        return HttpResponseRedirect(reverse("profile", args=[pk]))

    contents = Posts.objects.all()
    already_liked = []
    id = request.user.id
    for content in contents:
        if content.likes.filter(id=id).exists():
            already_liked.append(content.id)

    p = Paginator(posts, 5)
    page = request.GET.get("page")
    todas = p.get_page(page)
    nums = " " * todas.paginator.num_pages

    return render(
        request,
        "network/profile.html",
        {
            "user": current_user,
            "dono": dono,
            "dono_da_pag": dono_da_pag,
            "posts": posts,
            "seguidores": seguidores,
            "seguindo": seguindo,
            "Follow": Follow,
            "already_liked": already_liked,
            "todas": todas,
            "nums": nums,
        },
    )

@login_required(login_url="/login")  # redirect when user is not logged in
def all(request):
    if request.method == "POST" and not is_ajax(request=request):
        print(request.POST["postar"])
        Posts.objects.create(texto=request.POST["postar"], dono=request.user).save()
        # Remove the duplicate post
        ids = Posts.objects.filter(
            texto=request.POST["postar"], dono_id__username=request.user
        ).values("id")
        lista_de_ids = []
        for i in range(len(ids)):
            lista_de_ids.append(ids[i]["id"])
        Posts.objects.filter(
            texto=request.POST["postar"],
            dono_id__username=request.user,
            id=lista_de_ids[1],
        ).delete()

    contents = Posts.objects.all()
    already_liked = []
    id = request.user.id
    for content in contents:
        if content.likes.filter(id=id).exists():
            already_liked.append(content.id)
    data = (
        Posts.objects.values(
            "texto", "data", "dono_id__username", "dono__id", "like_count", "id"
        )
        .order_by("-data")
        .distinct()
    )

    p = Paginator(data, 10)
    page = request.GET.get("page")
    todas = p.get_page(page)
    nums = " " * todas.paginator.num_pages
    return render(
        request,
        "network/index.html",
        {"posts": data, "already_liked": already_liked, "todas": todas, "nums": nums, "title":"All posts"},
    )

@login_required(login_url="/login")  # redirect when user is not logged in
def following(request):
    if request.method == "GET":
        current_user = request.user
        seguindo = Followers.objects.filter(conta=current_user.id).values(
            "seguindo_id",
        )
        lista_de_ids = []
        for i in range(len(seguindo)):
            lista_de_ids.append(seguindo[i]["seguindo_id"])
        contents = Posts.objects.all()
        already_liked = []
        id = request.user.id
        for content in contents:
            if content.likes.filter(id=id).exists():
                already_liked.append(content.id)
        data = (
            Posts.objects.filter(dono__in=lista_de_ids)
            .order_by("-data")
            .values("texto", "data", "dono_id__username", "dono", "like_count", "id")
        )
        p = Paginator(data, 8)
        page = request.GET.get("page")
        todas = p.get_page(page)
        nums = " " * todas.paginator.num_pages
        return render(
            request,
            "network/timeline.html",
            {
                "usuario": current_user,
                "data": data,
                "already_liked": already_liked,
                "todas": todas,
                "nums": nums,
            },
        )


@login_required(login_url="/login")  # redirect when user is not logged in
def like(request):
    if request.POST.get("action") == "post":
        result = ""
        id = request.POST.get("postid")
        post = get_object_or_404(Posts, id=id)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            post.like_count -= 1
            result = post.like_count
            jadeulike = False
            post.save()
        else:
            post.likes.add(request.user)
            post.like_count += 1
            result = post.like_count
            jadeulike = True
            post.save()

        return JsonResponse(
            {
                "result": result,
                "jadeulike": jadeulike,
                "postid": id,
                "numlikes": post.like_count,
            }
        )


@login_required(login_url="/login")  # redirect when user is not logged in
def edit(request, pk):
    post = Posts.objects.filter(id=pk).values()
    dono = post[0]["dono_id"]
    length = int(len(post[0]["texto"]))

    class EditPost(forms.Form):
        Post = forms.CharField(
            widget=forms.Textarea(
                attrs={
                    "autocomplete": "off",
                    "class": "form-control",
                    "autofocus": "on",
                }
            )
        )

        def __init__(self, *args, **kwargs):
            super(EditPost, self).__init__(*args, **kwargs)
            self.fields["Post"].initial = post[0]["texto"]
            self.fields["Post"].widget.attrs[
                "onfocus"
            ] = f"this.setSelectionRange({length}, {length})"  # autofocus no fim

    if request.method == "POST":
        p = Posts.objects.get(id=pk)
        att = request.POST["Post"]
        p.texto = att  # change field
        p.save()  # this will update only
        return HttpResponseRedirect(reverse("index"))

    return render(
        request,
        "network/edit.html",
        {"usuario": dono, "form": EditPost(request.POST or None)},
    )


"""

def post_update(request, pk):
    post = get_object_or_404(Posts, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
    else:
        form = PostForm(instance=post)
    return save_post_form(request, form, 'network/includes/partial_post_update.html') #####


def save_post_form(request, form, template_name):
    data = dict()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
            posts = Posts.objects.all()
            data['html_product_list'] = render_to_string('network/includes/partial_post_list.html', { ###
                'posts': posts
            })
        else:
            data['form_is_valid'] = False
    context = {'form': form}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)
"""
