from django.contrib import admin

from .models import Post, Group, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title",)
    empty_value_display = "-пусто-"
    prepopulated_fields = {"slug": ("title",), }


class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "post", "created", "author", "text",)
    search_fields = ("post",)
    list_filter = ("created",)
    empty_value_display = "-пусто-"


class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "author",)
    search_fields = ("user",)
    list_filter = ("user",)
    empty_value_display = "-пусто-"


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)