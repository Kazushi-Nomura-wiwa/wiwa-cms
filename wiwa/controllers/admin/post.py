# パスとファイル名: wiwa/controllers/admin/post.py
# Path and filename: wiwa/controllers/admin/post.py

# 投稿管理コントローラ
# Admin post management controller
#
# URL
# URL
#   /admin/post/list
#   /admin/post/trash
#   /admin/post/new
#   /admin/post/edit/<id>
#   /admin/post/update/<id>
#   /admin/post/delete/<id>
#   /admin/post/restore/<id>
#
# 処理の流れ（一覧）
# Flow (list)
#   1. 投稿一覧取得
#      Fetch posts
#   2. テンプレート描画
#      Render template
#
# 処理の流れ（ゴミ箱）
# Flow (trash)
#   1. ゴミ箱投稿取得
#      Fetch trashed posts
#   2. テンプレート描画
#      Render template
#
# 処理の流れ（作成）
# Flow (create)
#   1. GET時はフォーム表示
#      Render form on GET
#   2. POST時は入力取得
#      Get submitted form
#   3. 入力検証
#      Validate form
#   4. 投稿作成
#      Create post
#
# 処理の流れ（編集）
# Flow (edit)
#   1. 投稿取得
#      Fetch post
#   2. テンプレート描画
#      Render template
#
# 処理の流れ（更新）
# Flow (update)
#   1. 投稿取得
#      Fetch post
#   2. 入力取得
#      Get submitted form
#   3. 入力検証
#      Validate form
#   4. 投稿更新
#      Update post
#
# 処理の流れ（削除）
# Flow (delete)
#   1. 投稿取得
#      Fetch post
#   2. POST時は削除実行
#      Execute delete
#   3. 確認画面描画
#      Render confirmation
#
# 処理の流れ（復元）
# Flow (restore)
#   1. POST時は復元実行
#      Execute restore
#   2. リダイレクト
#      Redirect

from wiwa.config import TRASH_RETENTION_DAYS
from wiwa.core.i18n import t
from wiwa.core.renderer import TemplateRenderer
from wiwa.core.response import html, not_found, redirect
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

# 投稿サービス
# Post service
post_service = PostService()


def list(request, route=None, **params):
    """
    投稿一覧を表示する
    Render post list
    """

    # 投稿一覧を取得
    # Fetch posts
    posts = post_service.list_posts()

    # 投稿一覧テンプレートを描画
    # Render post list template
    body = renderer.render_route(
        route,
        "html/admin/post/list.html",
        {
            "title": t("admin_post_list_title"),
            "posts": posts,
            "retention_days": TRASH_RETENTION_DAYS,
        },
        request=request,
    )
    return html(body)


def trash(request, route=None, **params):
    """
    ゴミ箱の投稿一覧を表示する
    Render trashed post list
    """

    # ゴミ箱の投稿を取得
    # Fetch trashed posts
    posts = post_service.list_posts(include_trashed=True)

    # ゴミ箱テンプレートを描画
    # Render trash template
    body = renderer.render_route(
        route,
        "html/admin/post/trash.html",
        {
            "title": t("admin_post_trash_title"),
            "posts": posts,
            "retention_days": TRASH_RETENTION_DAYS,
        },
        request=request,
    )
    return html(body)


def new(request, route=None, **params):
    """
    投稿作成画面および投稿作成処理
    Render new post form and create post
    """

    # GET時は新規作成フォームを表示
    # On GET, render new post form
    if request.method == "GET":
        body = renderer.render_route(
            route,
            "html/admin/post/new.html",
            {
                "title": t("admin_post_new_title"),
                "error": "",
                "action": "/admin/post/new",
                "submit_label": t("submit_create_post"),
                "form": empty_post_form(),
            },
            request=request,
        )
        return html(body)

    # 送信フォームを取得
    # Get submitted form
    form = submitted_post_form(request)

    # 入力値を検証
    # Validate form
    error = validate_post_form(form)

    # エラー時は入力内容を保持して再表示
    # If invalid, re-render form with submitted data
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
        return html(body, status="400 Bad Request")

    # 現在のユーザー情報を取得
    # Get current user information
    author_id, author_name = current_user_info(request)

    # 投稿を作成
    # Create post
    post_service.create_post(
        title=form["title"],
        body_json=form["body_json"],
        author_id=author_id,
        author_name=author_name,
        status=form["status"],
        tags=split_tags(form["tags"]),
    )

    return redirect("/admin/post/list")


def edit(request, route=None, id=None, **params):
    """
    投稿編集画面を表示する
    Render post edit form
    """

    # 投稿を取得
    # Fetch post
    post = post_service.find_post(id)
    if not post:
        return not_found()

    # 編集フォームを描画
    # Render edit form
    body = renderer.render_route(
        route,
        "html/admin/post/edit.html",
        {
            "title": t("admin_post_edit_title"),
            "error": "",
            "action": f"/admin/post/update/{id}",
            "submit_label": t("submit_update"),
            "form": post_to_form(post),
        },
        request=request,
    )
    return html(body)


def update(request, route=None, id=None, **params):
    """
    投稿更新処理
    Update post
    """

    # POST以外は一覧へ戻す
    # Redirect non-POST requests to list
    if request.method != "POST":
        return redirect("/admin/post/list")

    # 投稿を取得
    # Fetch post
    post = post_service.find_post(id)
    if not post:
        return not_found()

    # 送信フォームを取得
    # Get submitted form
    form = submitted_post_form(request)

    # 入力値を検証
    # Validate form
    error = validate_post_form(form)

    # エラー時は入力内容を保持して編集画面を再表示
    # If invalid, re-render edit form with submitted data
    if error:
        form["_id"] = str(post.get("_id", ""))
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
        return html(body, status="400 Bad Request")

    # 元の著者情報を維持
    # Keep original author information
    author_id = str(post.get("author_id", "") or "")
    author_name = post.get("author_name", "") or ""

    # 更新者情報を取得
    # Get updater information
    updated_by_id, updated_by_name = current_user_info(request)

    # 投稿を更新
    # Update post
    ok = post_service.update_post(
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
    投稿削除画面および削除処理
    Render delete confirmation and move post to trash
    """

    # 投稿を取得
    # Fetch post
    post = post_service.find_post(id)
    if not post:
        return not_found()

    # POST時は削除実行
    # Execute delete on POST
    if request.method == "POST":
        ok = post_service.delete_post(id)
        if not ok:
            return not_found()

        return redirect("/admin/post/list")

    # 削除確認画面を描画
    # Render delete confirmation
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
    return html(body)


def restore(request, route=None, id=None, **params):
    """
    ゴミ箱の投稿を復元する
    Restore post from trash
    """

    # POST以外はゴミ箱へ戻す
    # Redirect non-POST requests to trash
    if request.method != "POST":
        return redirect("/admin/post/trash")

    # 下書きとして復元
    # Restore as draft
    ok = post_service.restore_post(id, status="draft")
    if not ok:
        return not_found()

    return redirect("/admin/post/trash")