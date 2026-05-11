# パスとファイル名: wiwa/controllers/admin/post.py
# Path and filename: wiwa/controllers/admin/post.py

# 投稿管理コントローラ
# Admin post management controller

from wiwa.config import TRASH_RETENTION_DAYS
from wiwa.core.i18n import t
from wiwa.core.renderer import TemplateRenderer
from wiwa.core.response import Response, not_found, redirect
from wiwa.services.editorjs_service import EditorJSService
from wiwa.services.post_form_service import (
    current_user_info,
    empty_post_form,
    post_to_form,
    split_tags,
    submitted_post_form,
    validate_post_form,
)
from wiwa.services.post_service import PostService


# テンプレートレンダラー
# Template renderer
renderer = TemplateRenderer()

# Editor.js変換サービス
# Editor.js conversion service
editorjs_service = EditorJSService()


def list(request, route=None, **params):
    """
    投稿一覧
    Render post list
    """

    service = PostService()

    body = renderer.render_route(
        route,
        "html/admin/post/list.html",
        {
            "title": t("admin_post_list_title"),
            "posts": service.list_posts(),
            "retention_days": TRASH_RETENTION_DAYS,
        },
        request=request,
    )

    return Response(body=body)


def trash(request, route=None, **params):
    """
    ゴミ箱の投稿一覧
    Render trashed post list
    """

    service = PostService()

    body = renderer.render_route(
        route,
        "html/admin/post/trash.html",
        {
            "title": t("admin_post_trash_title"),
            "posts": service.list_posts(include_trashed=True),
            "retention_days": TRASH_RETENTION_DAYS,
        },
        request=request,
    )

    return Response(body=body)


def new(request, route=None, **params):
    """
    投稿作成
    Create post
    """

    service = PostService()

    # フォーム初期化
    # Initialize form data
    form = empty_post_form()
    form["body_json"] = editorjs_service.empty()

    # POST処理
    # Handle POST
    if request.method == "POST":
        form = submitted_post_form(request)
        error = validate_post_form(form)

        print("POST FORM:", form)
        print("POST ERROR:", error)

        if error:
            body = renderer.render_route(
                route,
                "html/admin/post/new.html",
                {
                    "title": t("admin_post_new_title"),
                    "error": error,
                    "action": "/admin/post/new",
                    "submit_label": t("submit_create_post"),
                    "form": form,
                },
                request=request,
            )
            #return Response(body=body, status="400 Bad Request")
            return Response(
                body=f"<pre>POST FORM: {form}\nPOST ERROR: {error}</pre>",
                status="400 Bad Request",
            )

        author_id, author_name = current_user_info(request)

        service.create_post(
            title=form["title"],
            body_json=form["body_json"],
            author_id=author_id,
            author_name=author_name,
            status=form["status"],
            tags=split_tags(form["tags"]),
        )

        return redirect("/admin/post/list")

    body = renderer.render_route(
        route,
        "html/admin/post/new.html",
        {
            "title": t("admin_post_new_title"),
            "error": "",
            "action": "/admin/post/new",
            "submit_label": t("submit_create_post"),
            "form": form,
        },
        request=request,
    )

    return Response(body=body)


def edit(request, route=None, id=None, **params):
    """
    投稿編集
    Edit post
    """

    service = PostService()

    # 投稿取得
    # Fetch post
    post = service.find_post(id)
    if not post:
        return not_found()

    form = post_to_form(post)
    form["body_json"] = editorjs_service.normalize(form.get("body_json"))

    body = renderer.render_route(
        route,
        "html/admin/post/edit.html",
        {
            "title": t("admin_post_edit_title"),
            "error": "",
            "action": f"/admin/post/update/{id}",
            "submit_label": t("submit_update"),
            "form": form,
        },
        request=request,
    )

    return Response(body=body)


def update(request, route=None, id=None, **params):
    """
    投稿更新
    Update post
    """

    service = PostService()

    # POST以外は一覧へ戻す
    # Redirect non-POST requests to list
    if request.method != "POST":
        return redirect("/admin/post/list")

    # 投稿取得
    # Fetch post
    post = service.find_post(id)
    if not post:
        return not_found()

    form = submitted_post_form(request)
    error = validate_post_form(form)

    if error:
        form["_id"] = str(post.get("_id", ""))
        form["body_json"] = editorjs_service.normalize(form.get("body_json"))

        body = renderer.render_route(
            route,
            "html/admin/post/edit.html",
            {
                "title": t("admin_post_edit_title"),
                "error": error,
                "action": f"/admin/post/update/{id}",
                "submit_label": t("submit_update"),
                "form": form,
            },
            request=request,
        )
        return Response(body=body, status="400 Bad Request")

    # 元の著者情報を維持
    # Keep original author information
    author_id = str(post.get("author_id", "") or "")
    author_name = post.get("author_name", "") or ""

    # 更新者情報を取得
    # Get updater information
    updated_by_id, updated_by_name = current_user_info(request)

    ok = service.update_post(
        post_id=str(post.get("_id")),
        title=form["title"],
        body_json=form["body_json"],
        slug=post.get("slug", "") or "",
        author_id=author_id,
        author_name=author_name,
        status=form["status"],
        updated_by_id=updated_by_id,
        updated_by_name=updated_by_name,
        tags=split_tags(form["tags"]),
    )

    if not ok:
        return not_found()

    return redirect("/admin/post/list")


def delete(request, route=None, id=None, **params):
    """
    投稿削除
    Delete post
    """

    service = PostService()

    post = service.find_post(id)
    if not post:
        return not_found()

    if request.method == "POST":
        ok = service.delete_post(id)
        if not ok:
            return not_found()

        return redirect("/admin/post/list")

    body = renderer.render_route(
        route,
        "html/admin/post/delete.html",
        {
            "title": t("admin_post_delete_title"),
            "post": post,
            "retention_days": TRASH_RETENTION_DAYS,
        },
        request=request,
    )

    return Response(body=body)


def restore(request, route=None, id=None, **params):
    """
    ゴミ箱の投稿を復元する
    Restore post from trash
    """

    service = PostService()

    if request.method != "POST":
        return redirect("/admin/post/trash")

    ok = service.restore_post(id, status="draft")
    if not ok:
        return not_found()

    return redirect("/admin/post/trash")