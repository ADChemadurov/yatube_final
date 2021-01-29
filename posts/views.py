from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse

from django.core.paginator import Paginator

from .models import Follow, Post, Group, User
from .forms import PostForm, CommentForm


def index(request):
    """
    Отображение главной страницы со всеми постами.
    Показывает 10 постов на странице. От самого свежего до самого старого.
    """
    post_list = Post.objects.select_related("group")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"page": page, "paginator": paginator}
    return render(request, "index.html", context)


def group_posts(request, slug):
    """
    Отображение страницы группы. Принцип отображения как у главной страницы.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"group": group, "page": page, "paginator": paginator}
    return render(request, "group.html", context)


@login_required
def new_post(request):
    """ Страница создания нового поста. """
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {"form": form}
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        form.save()
        return redirect("index")
    return render(request, "posts/new_post.html", context)


@login_required
def follow_index(request):
    """ Отображение всех постов авторов на которых подписан пользователь. """
    # posts = Post.objects.filter(author__following__user=request.user)
    posts = Post.objects.select_related(
        "author"
        ).filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"page": page, "paginator": paginator}
    return render(request, "posts/follow.html", context)


def profile(request, username):
    """ Страница отображения профиля автора. Показывает все посты автора. """
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    followers_qty = author.following.count()
    followed_qty = author.follower.count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
            ).exists()
    posts_number = len(post_list)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "posts_number": posts_number,
        "page": page,
        "author": author,
        "followers_qty": followers_qty,
        "followed_qty": followed_qty,
        "following": following,
        "paginatior": paginator,
    }
    return render(request, "posts/profile.html", context)


@login_required
def profile_follow(request, username):
    """ Подписывает на автора. """
    follower = get_object_or_404(User, username=request.user)
    followed_author = get_object_or_404(User, username=username)
    followed_author_profile_url = reverse(
        "profile", kwargs={"username": followed_author}
    )
    # Проверка, что не пользователь не пытается сам на себя подписаться.
    if follower == followed_author:
        return redirect(followed_author_profile_url)
    # Если проверки пройдены, создаем новую запись.
    Follow.objects.get_or_create(
        user=follower,
        author=followed_author,
    )
    return redirect(followed_author_profile_url)


@login_required
def profile_unfollow(request, username):
    """ Отписывает от автора. """
    follower = get_object_or_404(User, username=request.user)
    followed_author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=follower, author=followed_author).delete()
    return redirect(
        reverse("profile", kwargs={"username": followed_author})
    )


def post_view(request, username, post_id):
    """
    Отображение страницы конкретного поста.
    Так же отображает все комментарии к нему.
    """
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    followers_qty = author.following.count()
    followed_qty = author.follower.count()
    posts_number = author.posts.count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid() and request.user.is_authenticated:
        comment = form.save(commit=False)
        comment.post = Post.objects.get(id=post_id)
        comment.author = request.user
        form.save()
        return redirect(
            reverse("post", kwargs={"username": username, "post_id": post_id})
        )
    context = {
        "form": form,
        "posts_number": posts_number,
        "author": author,
        "post": post,
        "comments": comments,
        "followers_qty": followers_qty,
        "followed_qty": followed_qty,
    }
    return render(request, "posts/post.html", context)


@login_required
def post_edit(request, username, post_id):
    """
    Функция редактирования поста. Редактировать может только автор поста.
    Использует шаблон new_post.html.
    """
    sel_post = get_object_or_404(Post, id=post_id)
    sel_post_author = sel_post.author
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=sel_post
    )
    if request.user != sel_post_author or form.is_valid():
        if form.is_valid():
            form.save()
        return redirect(reverse(
            "post", kwargs={"username": username, "post_id": post_id}
        ))
    context = {
        "form": form,
        "sel_post": sel_post,
        "is_edit": True,
        "username": username,
        "post_id": post_id,
    }
    return render(request, "posts/new_post.html", context)


@login_required
def add_comment(request, username, post_id):
    """ Отображение страницы страницы создания комментария к посту. """
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    followers_qty = author.following.count()
    followed_qty = author.follower.count()
    posts_number = author.posts.count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid() and request.user.is_authenticated:
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        form.save()
        return redirect(
            reverse("post", kwargs={"username": username, "post_id": post_id})
        )
    context = {
        "form": form,
        "posts_number": posts_number,
        "author": author,
        "post": post,
        "comments": comments,
        "followers_qty": followers_qty,
        "followed_qty": followed_qty,
    }
    return render(request, "posts/post.html", context)


def page_not_found(request, exception):
    """ Отображение страницы, которая не была найдена. """
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    """ Отображение страницы при ошибке на сервере. """
    return render(request, "misc/500.html", status=500)
