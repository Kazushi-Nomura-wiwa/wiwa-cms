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
from wiwa.core.response import html, not_found
from wiwa.db.post_repository import PostRepository
from wiwa.services.editorjs_service import EditorJSService
from wiwa.services.post_view_service import PostViewService


# テンプレートレンダラー
# Template renderer
renderer = TemplateRenderer()

# 投稿リポジトリ
# Post repository
post_repo = PostRepository()

# Editor.js変換サービス
# Editor.js conversion service
editorjs_service = EditorJSService()

def index(request, route=None):
    """
    投稿一覧ページ
    Render post list page
    """

    # ページ番号取得
    # Get page number
    try:
        page = int(request.query.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    if page < 1:
        page = 1

    # ページネーション計算
    # Pagination calculation
    per_page = POSTS_PER_PAGE
    skip = (page - 1) * per_page

    # 投稿取得
    # Fetch posts
    posts = post_repo.list_published(limit=per_page, skip=skip)

    # 表示用変換
    # Convert posts into template-friendly data
    posts = post_view_service.build_post_list(posts)

    # 総件数取得
    # Get total count
    total = post_repo.count_published()

    # 総ページ数計算
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    # テンプレート描画
    # Render template
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

    # HTMLレスポンス返却
    # Return HTML response
    return html(body)


def slug(request, route=None, slug=None):
    """
    投稿詳細ページ
    Render post detail page
    """

    # slugから投稿取得
    # Fetch post by slug
    post = post_repo.find_published_by_slug(slug)

    # 投稿が存在しない場合
    # If post not found
    if not post:
        return not_found()

    # 表示用変換
    # Convert post into template-friendly data
    # Editor.js JSONをHTMLへ変換
    # Convert Editor.js JSON to HTML
    post["body_html"] = editorjs_service.build_html(
        post.get("body_json", "")
    )

    # テンプレート描画
    # Render template
    body = renderer.render_route(
        route,
        "html/post/slug.html",
        {
            "title": post.get("title", ""),
            "post": post,
        },
        request=request,
    )

    # HTMLレスポンス返却
    # Return HTML response
    return html(body)