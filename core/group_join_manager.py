
from typing import Dict, List
import json
import os



class GroupJoinData:
    def __init__(self, path: str = "group_join_data.json"):
        self.path = path
        self.accept_keywords: Dict[str, List[str]] = {}
        self.reject_keywords: Dict[str, List[str]] = {}
        self.reject_ids: Dict[str, List[str]] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            self._save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.accept_keywords = data.get("accept_keywords", {})
            self.reject_keywords = data.get("reject_keywords", {})
            self.reject_ids = data.get("reject_ids", {})
        except Exception as e:
            print(f"加载 group_join_data 失败: {e}")
            self._save()

    def _save(self):
        data = {
            "accept_keywords": self.accept_keywords,
            "reject_keywords": self.reject_keywords,
            "reject_ids": self.reject_ids,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self):
        self._save()



class GroupJoinManager:
    def __init__(self, json_path: str):
        self.data = GroupJoinData(json_path)
        self.auto_reject_without_keyword: bool = False

    def reject_reason(
        self, group_id: str, user_id: str, comment: str | None = None
    ) -> str | None:
        """返回拒绝原因标识：
        black_user: 在用户ID黑名单中
        black_keyword: 触发黑名单关键词
        no_accept_keyword: 已配置自动同意关键词但未命中且开启自动拒绝
        None: 不拒绝
        """
        # 1. 用户ID黑名单
        if (
            group_id in self.data.reject_ids
            and user_id in self.data.reject_ids[group_id]
        ):
            return "黑名单用户"

        if comment:
            lower_comment = comment.lower()
            # 2. 黑名单关键词
            if group_id in self.data.reject_keywords and any(
                rk.lower() in lower_comment for rk in self.data.reject_keywords[group_id]
            ):
                return "命中黑名单关键词"
            # 3. 未包含任何自动同意关键词（需开启开关 & 已设置白名单关键词）
            if (
                self.auto_reject_without_keyword
                and group_id in self.data.accept_keywords
                and self.data.accept_keywords[group_id]
                and not any(
                    ak.lower() in lower_comment
                    for ak in self.data.accept_keywords[group_id]
                )
            ):
                return "未包含进群关键词"
        return None

    def should_reject(
        self, group_id: str, user_id: str, comment: str | None = None
    ) -> bool:
        return self.reject_reason(group_id, user_id, comment) is not None

    def should_approve(self, group_id: str, comment: str) -> bool:
        if group_id not in self.data.accept_keywords:
            return False
        return any(
            kw.lower() in comment.lower() for kw in self.data.accept_keywords[group_id]
        )

    def add_keyword(self, group_id: str, keywords: List[str]):
        self.data.accept_keywords.setdefault(group_id, []).extend(keywords)
        self.data.accept_keywords[group_id] = list(
            set(self.data.accept_keywords[group_id])
        )
        self.data.save()

    def remove_keyword(self, group_id: str, keywords: List[str]):
        if group_id in self.data.accept_keywords:
            for k in keywords:
                if k in self.data.accept_keywords[group_id]:
                    self.data.accept_keywords[group_id].remove(k)
            self.data.save()

    def get_keywords(self, group_id: str) -> List[str]:
        return self.data.accept_keywords.get(group_id, [])

    def add_reject_keyword(self, group_id: str, keywords: List[str]):
        self.data.reject_keywords.setdefault(group_id, []).extend(keywords)
        self.data.reject_keywords[group_id] = list(
            set(self.data.reject_keywords[group_id])
        )
        self.data.save()

    def remove_reject_keyword(self, group_id: str, keywords: List[str]):
        if group_id in self.data.reject_keywords:
            for k in keywords:
                if k in self.data.reject_keywords[group_id]:
                    self.data.reject_keywords[group_id].remove(k)
            self.data.save()

    def get_reject_keywords(self, group_id: str) -> List[str]:
        return self.data.reject_keywords.get(group_id, [])

    def add_reject_id(self, group_id: str, ids: List[str]):
        self.data.reject_ids.setdefault(group_id, []).extend(ids)
        self.data.reject_ids[group_id] = list(set(self.data.reject_ids[group_id]))
        self.data.save()

    def remove_reject_id(self, group_id: str, ids: List[str]):
        if group_id in self.data.reject_ids:
            for uid in ids:
                if uid in self.data.reject_ids[group_id]:
                    self.data.reject_ids[group_id].remove(uid)
            self.data.save()

    def get_reject_ids(self, group_id: str) -> List[str]:
        return self.data.reject_ids.get(group_id, [])

    def blacklist_on_leave(self, group_id: str, user_id: str) -> None:
        self.data.reject_ids.setdefault(group_id, []).append(user_id)
        self.data.save()

