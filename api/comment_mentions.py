import logging
import re
from typing import List, Optional, Set, Tuple

from db.models.api import ApiModel
from db.models.api_document import ApiDocumentModel
from db.models.api_justification import ApiJustificationModel
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.api_test_case import ApiTestCaseModel
from db.models.api_test_specification import ApiTestSpecificationModel
from db.models.comment import CommentModel
from db.models.comment_mention import CommentMentionModel
from db.models.document_document import DocumentDocumentModel
from db.models.notification import NotificationModel
from db.models.sw_requirement_sw_requirement import SwRequirementSwRequirementModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.sw_requirement_test_specification import SwRequirementTestSpecificationModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.user import UserModel
from sqlalchemy.orm.exc import NoResultFound

from api_utils import get_configuration, load_settings
from notifier import EmailNotifier

logger = logging.getLogger(__name__)

MENTION_USER_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(basil-user:(\d+)\)")
MENTION_SCHEME = "basil-user:"

WORK_ITEM_LABELS = {
    "sw_requirement": "Software Requirement",
    "test_specification": "Test Specification",
    "test_case": "Test Case",
    "justification": "Justification",
    "document": "Document",
}


def parse_mention_user_ids(comment_text: str) -> List[int]:
    if not comment_text:
        return []
    ids = []
    seen = set()
    for match in MENTION_USER_LINK_PATTERN.finditer(comment_text):
        uid = int(match.group(1))
        if uid not in seen:
            seen.add(uid)
            ids.append(uid)
    return ids


def format_mention_markdown(username: str, user_id: int) -> str:
    return f"[@{username}]({MENTION_SCHEME}{user_id})"


def parse_parent_table(parent_table: str) -> Optional[Tuple[str, str]]:
    if "_mapping_" not in parent_table:
        return None
    work_item, parent = parent_table.split("_mapping_", 1)
    return work_item.replace("_", "-"), parent.replace("_", "-")


def _truncate_title(title: str, max_len: int = 100) -> str:
    if not title:
        return ""
    title = title.strip()
    if len(title) <= max_len:
        return title
    return title[: max_len - 3] + "..."


def _work_item_label(work_item_key: str) -> str:
    return WORK_ITEM_LABELS.get(work_item_key, work_item_key.replace("-", " ").title())


def resolve_comment_context(dbi_session, parent_table: str, parent_id: int, api: ApiModel):
    """
    Return (work_item_label, work_item_title) for notifications and UI.
    """
    parsed = parse_parent_table(parent_table)
    if not parsed:
        return None, None
    work_item_key, _parent_key = parsed
    work_item_label = _work_item_label(work_item_key.replace("-", "_"))

    try:
        if parent_table == ApiSwRequirementModel.__tablename__:
            row = dbi_session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.id == parent_id).one()
            return work_item_label, _truncate_title(row.sw_requirement.title)
        if parent_table == ApiTestSpecificationModel.__tablename__:
            row = dbi_session.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.id == parent_id).one()
            return work_item_label, _truncate_title(row.test_specification.title)
        if parent_table == ApiTestCaseModel.__tablename__:
            row = dbi_session.query(ApiTestCaseModel).filter(ApiTestCaseModel.id == parent_id).one()
            return work_item_label, _truncate_title(row.test_case.title)
        if parent_table == ApiJustificationModel.__tablename__:
            row = dbi_session.query(ApiJustificationModel).filter(ApiJustificationModel.id == parent_id).one()
            return work_item_label, _truncate_title(row.justification.description)
        if parent_table == ApiDocumentModel.__tablename__:
            row = dbi_session.query(ApiDocumentModel).filter(ApiDocumentModel.id == parent_id).one()
            title = row.document.title or row.document.description or ""
            return work_item_label, _truncate_title(title)
        if parent_table == SwRequirementSwRequirementModel.__tablename__:
            row = (
                dbi_session.query(SwRequirementSwRequirementModel)
                .filter(SwRequirementSwRequirementModel.id == parent_id)
                .one()
            )
            return work_item_label, _truncate_title(row.sw_requirement.title)
        if parent_table == SwRequirementTestSpecificationModel.__tablename__:
            row = (
                dbi_session.query(SwRequirementTestSpecificationModel)
                .filter(SwRequirementTestSpecificationModel.id == parent_id)
                .one()
            )
            return work_item_label, _truncate_title(row.test_specification.title)
        if parent_table == SwRequirementTestCaseModel.__tablename__:
            row = (
                dbi_session.query(SwRequirementTestCaseModel)
                .filter(SwRequirementTestCaseModel.id == parent_id)
                .one()
            )
            return work_item_label, _truncate_title(row.test_case.title)
        if parent_table == TestSpecificationTestCaseModel.__tablename__:
            row = (
                dbi_session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.id == parent_id)
                .one()
            )
            return work_item_label, _truncate_title(row.test_case.title)
        if parent_table == DocumentDocumentModel.__tablename__:
            row = dbi_session.query(DocumentDocumentModel).filter(DocumentDocumentModel.id == parent_id).one()
            title = row.document.title or row.document.description or ""
            return work_item_label, _truncate_title(title)
    except NoResultFound:
        return work_item_label, ""

    return work_item_label, ""


def mapping_belongs_to_api(dbi_session, parent_table: str, parent_id: int, api: ApiModel) -> bool:
    try:
        if parent_table == ApiSwRequirementModel.__tablename__:
            row = dbi_session.query(ApiSwRequirementModel).filter(ApiSwRequirementModel.id == parent_id).one()
            return row.api_id == api.id
        if parent_table == ApiTestSpecificationModel.__tablename__:
            row = dbi_session.query(ApiTestSpecificationModel).filter(ApiTestSpecificationModel.id == parent_id).one()
            return row.api_id == api.id
        if parent_table == ApiTestCaseModel.__tablename__:
            row = dbi_session.query(ApiTestCaseModel).filter(ApiTestCaseModel.id == parent_id).one()
            return row.api_id == api.id
        if parent_table == ApiJustificationModel.__tablename__:
            row = dbi_session.query(ApiJustificationModel).filter(ApiJustificationModel.id == parent_id).one()
            return row.api_id == api.id
        if parent_table == ApiDocumentModel.__tablename__:
            row = dbi_session.query(ApiDocumentModel).filter(ApiDocumentModel.id == parent_id).one()
            return row.api_id == api.id
        if parent_table == SwRequirementSwRequirementModel.__tablename__:
            row = (
                dbi_session.query(SwRequirementSwRequirementModel)
                .filter(SwRequirementSwRequirementModel.id == parent_id)
                .one()
            )
            if row.sw_requirement_mapping_api_id:
                return row.sw_requirement_mapping_api.api_id == api.id
            return False
        if parent_table == SwRequirementTestSpecificationModel.__tablename__:
            row = (
                dbi_session.query(SwRequirementTestSpecificationModel)
                .filter(SwRequirementTestSpecificationModel.id == parent_id)
                .one()
            )
            if row.sw_requirement_mapping_api_id:
                return row.sw_requirement_mapping_api.api_id == api.id
            if row.sw_requirement_mapping_sw_requirement_id:
                parent = row.sw_requirement_mapping_sw_requirement
                if parent.sw_requirement_mapping_api_id:
                    return parent.sw_requirement_mapping_api.api_id == api.id
            return False
        if parent_table == SwRequirementTestCaseModel.__tablename__:
            row = (
                dbi_session.query(SwRequirementTestCaseModel)
                .filter(SwRequirementTestCaseModel.id == parent_id)
                .one()
            )
            if row.sw_requirement_mapping_api_id:
                return row.sw_requirement_mapping_api.api_id == api.id
            if row.sw_requirement_mapping_sw_requirement_id:
                parent = row.sw_requirement_mapping_sw_requirement
                if parent.sw_requirement_mapping_api_id:
                    return parent.sw_requirement_mapping_api.api_id == api.id
            return False
        if parent_table == TestSpecificationTestCaseModel.__tablename__:
            row = (
                dbi_session.query(TestSpecificationTestCaseModel)
                .filter(TestSpecificationTestCaseModel.id == parent_id)
                .one()
            )
            if row.test_specification_mapping_api_id:
                return row.test_specification_mapping_api.api_id == api.id
            if row.test_specification_mapping_sw_requirement_id:
                ts_parent = row.test_specification_mapping_sw_requirement
                if ts_parent.sw_requirement_mapping_api_id:
                    return ts_parent.sw_requirement_mapping_api.api_id == api.id
                if ts_parent.sw_requirement_mapping_sw_requirement_id:
                    sr_parent = ts_parent.sw_requirement_mapping_sw_requirement
                    if sr_parent.sw_requirement_mapping_api_id:
                        return sr_parent.sw_requirement_mapping_api.api_id == api.id
            return False
        if parent_table == DocumentDocumentModel.__tablename__:
            row = dbi_session.query(DocumentDocumentModel).filter(DocumentDocumentModel.id == parent_id).one()
            if row.document_mapping_api_id:
                return row.document_mapping_api.api_id == api.id
            if row.document_mapping_document_id:
                parent = row.document_mapping_document
                if parent.document_mapping_api_id:
                    return parent.document_mapping_api.api_id == api.id
            return False
    except NoResultFound:
        return False
    return False


def get_mentionable_users_query(
    dbi_session, api: ApiModel, search: Optional[str] = None, exclude_user_id: Optional[int] = None
):
    # Lazy import: api.py imports this module.
    from api import get_api_user_permissions  # noqa: WPS433

    users = dbi_session.query(UserModel).filter(UserModel.enabled == 1).filter(UserModel.role != "GUEST").all()
    mentionable = []
    for u in users:
        if exclude_user_id is not None and u.id == exclude_user_id:
            continue
        perms = get_api_user_permissions(api, u, dbi_session)
        if "r" not in perms:
            continue
        if search:
            term = search.strip().lower()
            if term and term not in u.username.lower() and term not in (u.email or "").lower():
                continue
        mentionable.append(u)
    mentionable.sort(key=lambda x: x.username.lower())
    return mentionable


def validate_mention_user_ids(
    comment_text: str, api: ApiModel, author: UserModel, dbi_session
) -> Optional[str]:
    if author is None:
        return "Authentication required to post comments with mentions."
    mention_ids = set(parse_mention_user_ids(comment_text))
    if author.id in mention_ids:
        return "You cannot mention yourself."
    allowed_ids = {u.id for u in get_mentionable_users_query(dbi_session, api, exclude_user_id=author.id)}
    invalid = mention_ids - allowed_ids
    if invalid:
        return "One or more mentioned users are not allowed for this software component."
    return None


def sync_comment_mentions(dbi_session, comment: CommentModel, mention_user_ids: List[int]) -> Set[int]:
    existing = (
        dbi_session.query(CommentMentionModel.user_id)
        .filter(CommentMentionModel.comment_id == comment.id)
        .all()
    )
    existing_ids = {row[0] for row in existing}
    new_ids = set(mention_user_ids)

    for uid in existing_ids - new_ids:
        dbi_session.query(CommentMentionModel).filter(
            CommentMentionModel.comment_id == comment.id,
            CommentMentionModel.user_id == uid,
        ).delete()

    for uid in new_ids - existing_ids:
        dbi_session.add(CommentMentionModel(comment.id, uid))

    return new_ids - existing_ids


def send_email_on_tag_enabled(settings_path) -> bool:
    settings, settings_last_modified = load_settings(None, None)
    if not isinstance(settings, dict):
        return False
    enabled = get_configuration(
        setting_section="notifications",
        setting_key="send_email_on_tag",
        settings=settings,
        settings_last_modified=settings_last_modified,
    )
    if not enabled:
        return False
    notifier = EmailNotifier(settings=settings, settings_last_modified=settings_last_modified, dry_mode=True)
    return notifier.validate_settings()


def build_comment_deep_link_url(api_id: int, parent_table: str, parent_id: int, notification_id: Optional[int] = None):
    url = (
        f"/mapping/{api_id}?view=comments&parent_table={parent_table}&parent_id={parent_id}"
    )
    if notification_id:
        url += f"&notification_id={notification_id}"
    return url


def create_tag_notifications(
    dbi_session,
    api: ApiModel,
    author: UserModel,
    comment: CommentModel,
    parent_table: str,
    parent_id: int,
    new_mention_user_ids: Set[int],
    notification_category_new: str,
    settings_filepath: str,
    email_template_path: str,
    email_discord_footer: str,
    async_email_notification_fn,
):
    if not new_mention_user_ids:
        return

    work_item_label, work_item_title = resolve_comment_context(dbi_session, parent_table, parent_id, api)
    if not work_item_label:
        work_item_label = "Work item"
    title_part = f"{work_item_label} {work_item_title}".strip()

    for uid in new_mention_user_ids:
        if uid == author.id:
            continue
        try:
            tagged_user = dbi_session.query(UserModel).filter(UserModel.id == uid).one()
        except NoResultFound:
            continue

        description = (
            f"{author.username} tagged you in a comment to {title_part} "
            f"of the software component {api.api} of the library {api.library}"
        )
        notification = NotificationModel(
            api,
            notification_category_new,
            f"{author.username} mentioned you in a comment",
            description,
            f"[{author.id}]",
            "",
        )
        notification.user_ids = f"[{uid}]"
        dbi_session.add(notification)
        dbi_session.flush()
        notification.url = build_comment_deep_link_url(api.id, parent_table, parent_id, notification.id)

        if send_email_on_tag_enabled(settings_filepath) and tagged_user.email:
            email_subject = f"BASIL - {author.username} mentioned you in a comment"
            async_email_notification_fn(
                settings_filepath,
                email_template_path,
                [tagged_user.email],
                email_subject,
                description,
                email_discord_footer,
                True,
            )


def should_add_comment_broadcast_notification(parent_table: str) -> bool:
    supported = {
        ApiSwRequirementModel.__tablename__,
        ApiTestSpecificationModel.__tablename__,
        ApiTestCaseModel.__tablename__,
        ApiJustificationModel.__tablename__,
        ApiDocumentModel.__tablename__,
    }
    return parent_table in supported


def broadcast_read_by_for_tagged(tagged_user_ids: Set[int], author_id: int) -> str:
    read_by = f"[{author_id}]"
    for uid in tagged_user_ids:
        if uid != author_id:
            read_by += f"[{uid}]"
    return read_by
