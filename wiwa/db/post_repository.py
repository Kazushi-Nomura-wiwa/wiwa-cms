# パスとファイル名: wiwa/db/post_repository.py
# Path and filename: wiwa/db/post_repository.py

# 投稿リポジトリ
# Post repository
#
# 概要
# Summary
#   投稿のCRUDおよび公開・ゴミ箱管理を行う
#   Provide CRUD operations and manage published/trash states
#
# 処理の流れ
# Flow
#   1. 投稿作成
#      Insert post
#   2. 投稿取得
#      Fetch posts
#   3. 投稿更新
#      Update post
#   4. 論理削除（ゴミ箱）
#      Soft delete (trash)
#   5. 復元・物理削除
#      Restore or permanently delete

import re
import unicodedata
from datetime import UTC, datetime, timedelta

from bson import ObjectId

from wiwa.db.mongo import get_collection
from wiwa.config import TRASH_RETENTION_DAYS


class PostRepository:
    def __init__(self):
        """
        リポジトリ初期化
        Initialize repository
        """
        self.collection = get_collection("posts")

    def insert_post(self, post: dict) -> str:
        """
        投稿を作成
        Insert a new post
        """
        result = self.collection.insert_one(post)
        return str(result.inserted_id)

    def list_all(self) -> list[dict]:
        """
        全投稿一覧（ゴミ箱除外）
        List all posts (excluding trashed)
        """
        posts = list(
            self.collection
            .find({"status": {"$ne": "trash"}})
            .sort("created_at", -1)
        )

        for post in posts:
            post["_id"] = str(post["_id"])

        return posts

    def list_by_author_id(self, author_id: str) -> list[dict]:
        """
        投稿一覧（著者別）
        List posts by author
        """
        posts = list(
            self.collection
            .find({
                "author_id": author_id,
                "status": {"$ne": "trash"},
            })
            .sort("created_at", -1)
        )

        for post in posts:
            post["_id"] = str(post["_id"])

        return posts

    def list_trashed_all(self) -> list[dict]:
        """
        ゴミ箱一覧
        List trashed posts
        """
        posts = list(
            self.collection
            .find({"status": "trash"})
            .sort("deleted_at", -1)
        )

        for post in posts:
            post["_id"] = str(post["_id"])

        return posts

    def list_trashed_by_author_id(self, author_id: str) -> list[dict]:
        """
        ゴミ箱一覧（著者別）
        List trashed posts by author
        """
        posts = list(
            self.collection
            .find({
                "author_id": author_id,
                "status": "trash",
            })
            .sort("deleted_at", -1)
        )

        for post in posts:
            post["_id"] = str(post["_id"])

        return posts

    def list_published(self, limit: int | None = None, skip: int = 0) -> list[dict]:
        """
        公開済み投稿一覧
        List published posts

        Args:
            limit (int | None): 最大取得件数 / Max number of posts
            skip (int): スキップ件数（ページネーション用） / Number of documents to skip
        """

        cursor = (
            self.collection
            .find({"status": "published"})
            .sort("published_at", -1)
            .skip(skip)
        )

        if limit is not None:
            cursor = cursor.limit(limit)

        posts = list(cursor)

        for post in posts:
            post["_id"] = str(post["_id"])

        return posts

    def count_published(self) -> int:
        """
        公開済み投稿数
        Count published posts
        """
        return self.collection.count_documents({"status": "published"})

    def find_by_id(self, post_id: str) -> dict | None:
        """
        投稿取得（ID）
        Find post by ID
        """
        if not ObjectId.is_valid(post_id):
            return None

        post = self.collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            return None

        post["_id"] = str(post["_id"])
        return post

    def find_active_by_id(self, post_id: str) -> dict | None:
        """
        投稿取得（ゴミ箱除外）
        Find active post by ID
        """
        if not ObjectId.is_valid(post_id):
            return None

        post = self.collection.find_one({
            "_id": ObjectId(post_id),
            "status": {"$ne": "trash"},
        })
        if not post:
            return None

        post["_id"] = str(post["_id"])
        return post

    def find_published_by_slug(self, slug: str) -> dict | None:
        """
        投稿取得（slug・公開済み）
        Find published post by slug
        """
        post = self.collection.find_one({
            "slug": slug,
            "status": "published",
        })

        if not post:
            return None

        post["_id"] = str(post["_id"])
        return post

    def update_post_by_id(self, post_id: str, post: dict) -> bool:
        """
        投稿更新
        Update post
        """
        if not ObjectId.is_valid(post_id):
            return False

        post["updated_at"] = datetime.now(UTC)

        result = self.collection.update_one(
            {
                "_id": ObjectId(post_id),
                "status": {"$ne": "trash"},
            },
            {"$set": post},
        )
        return result.modified_count > 0

    def delete_post_by_id(self, post_id: str) -> bool:
        """
        論理削除（ゴミ箱へ移動）
        Soft delete (move to trash)
        """
        if not ObjectId.is_valid(post_id):
            return False

        now = datetime.now(UTC)
        purge_at = now + timedelta(days=TRASH_RETENTION_DAYS)

        result = self.collection.update_one(
            {
                "_id": ObjectId(post_id),
                "status": {"$ne": "trash"},
            },
            {
                "$set": {
                    "status": "trash",
                    "deleted_at": now,
                    "purge_at": purge_at,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count > 0

    def restore_post_by_id(self, post_id: str, status: str = "draft") -> bool:
        """
        投稿復元
        Restore post from trash
        """
        if not ObjectId.is_valid(post_id):
            return False

        now = datetime.now(UTC)

        result = self.collection.update_one(
            {
                "_id": ObjectId(post_id),
                "status": "trash",
            },
            {
                "$set": {
                    "status": status,
                    "updated_at": now,
                },
                "$unset": {
                    "deleted_at": "",
                    "purge_at": "",
                },
            },
        )
        return result.modified_count > 0

    def delete_post_permanently_by_id(self, post_id: str) -> bool:
        """
        物理削除
        Permanently delete post
        """
        if not ObjectId.is_valid(post_id):
            return False

        result = self.collection.delete_one({"_id": ObjectId(post_id)})
        return result.deleted_count > 0
    
    def normalize_slug(self, value: str) -> str:
        """
        スラッグ正規化
        Normalize slug
        """

        value = unicodedata.normalize("NFKC", value or "")
        value = value.strip().lower()

        # 空白 → ハイフン
        # Spaces to hyphen
        value = re.sub(r"\s+", "-", value)

        # スラッシュ除去
        # Remove slashes
        value = re.sub(r"/+", "-", value)

        # 使用可能文字だけ許可
        # Keep allowed characters
        value = re.sub(
            r"[^a-z0-9\-_ぁ-んァ-ヶ一-龠々ー]",
            "",
            value,
        )

        # ハイフン連続除去
        # Collapse multiple hyphens
        value = re.sub(r"-+", "-", value)

        return value.strip("-")
    
    def slug_exists(
        self,
        slug: str,
        exclude_post_id: str | None = None,
    ) -> bool:
        """
        スラッグ存在確認
        Check whether slug already exists
        """

        query = {
            "slug": slug,
            "status": {
                "$ne": "trash"
            },
        }

        # 自分自身は除外
        # Exclude current post
        if exclude_post_id and ObjectId.is_valid(exclude_post_id):
            query["_id"] = {
                "$ne": ObjectId(exclude_post_id)
            }

        return self.collection.count_documents(query) > 0