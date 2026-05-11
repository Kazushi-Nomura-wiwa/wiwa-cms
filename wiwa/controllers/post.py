# パスとファイル名: wiwa/controllers/post.py
# Path and filename: wiwa/controllers/post.py

# 投稿コントローラ
# Post controller
#
# URL
# URL
#   /post
#   /post/<slug>
#
# 処理の流れ（一覧ページ）
# Flow (list page)
#   1. ページ番号取得
#      Get page number
#   2. 投稿取得
#      Fetch posts
#   3. 表示用変換
#      Build view data
#   4. ページネーション計算
#      Calculate pagination
#   5. テンプレート描画
#      Render template
#
# 処理の流れ（詳細ページ）
# Flow (detail page)
#   1. slugから投稿取得
#      Fetch post by slug
#   2. 存在チェック
#      Check existence
#   3. 表示用変換
#      Build view data
#   4. テンプレート描画
#      Render template

from wiwa.config import POSTS_PER_PAGE
from wiwa.core.i18n import t
from wiwa.core.renderer import TemplateRenderer
from wiwa.core.response import Response, not_found
from wiwa.db.post_repository import PostRepository
from wiwa.services.editorjs_service import EditorJSService
from wiwa.services.post_view_service import PostViewService


# テンプレートレンダラー
# Template renderer
renderer = TemplateRenderer()

# 投稿リポジトリ
# Post repository
post_repo = PostRepository()

# 投稿表示サービス
# Post view service
post_view_service = PostViewService()

# Editor.js変換サービス
# Editor.js conversion service
editorjs_service = EditorJSService()


def index(request, route=None):
    """
    投稿一覧ページ
    Render post list page
    """

    try:
        page = int(request.query.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    if page < 1:
        page = 1

    per_page = POSTS_PER_PAGE
    skip = (page - 1) * per_page

    posts = post_repo.list_published(limit=per_page, skip=skip)
    posts = post_view_service.build_post_list(posts)

    total = post_repo.count_published()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    body = renderer.render_route(
        route,
        "html/post/index.html",
        {
            "title": t("post_list_title"),
            "posts": posts,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
        request=request,
    )

    return Response(body=body)


def slug(request, route=None, slug=None):
    """
    投稿詳細ページ
    Render post detail page
    """

    post = post_repo.find_published_by_slug(slug)

    if not post:
        return not_found()

    post["body_html"] = editorjs_service.build_html(
        post.get("body_json", "")
    )
  
    body = renderer.render_route(
        route,
        "html/post/slug.html",
        {
            "title": post.get("title", ""),
            "post": post,
        },
        request=request,
    )

    return Response(body=body)