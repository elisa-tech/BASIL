from http import HTTPStatus

import pytest
from db.models.api_sw_requirement import ApiSwRequirementModel
from db.models.comment_mention import CommentMentionModel
from db.models.notification import NotificationModel
from db.models.user import UserModel

from comment_mentions import format_mention_markdown, parse_mention_user_ids

_MAPPING_COMMENT_URL = '/comments'
_MENTIONABLE_USERS_URL = '/comments/mentionable-users'


def test_parse_mention_user_ids_dedupes():
    text = (
        f"Hi {format_mention_markdown('alice', 2)} and "
        f"again {format_mention_markdown('alice', 2)}"
    )
    assert parse_mention_user_ids(text) == [2]


def test_comment_post_with_mention_notifies_tagged_user(client, user_authentication, api_sr_db, client_db):
    api_sr = api_sr_db
    tagged = client_db.session.query(UserModel).filter(UserModel.email == 'dummy_user').one()
    author_id = user_authentication.json['id']
    mention = format_mention_markdown(tagged.username, tagged.id)

    mapping_data = {
        'api-id': api_sr.api_id,
        'user-id': author_id,
        'token': user_authentication.json['token'],
        'comment': f'Please review {mention}',
        'parent_table': ApiSwRequirementModel.__tablename__,
        'parent_id': api_sr.id,
        'todo': False,
    }

    response = client.post(_MAPPING_COMMENT_URL, json=mapping_data)
    assert response.status_code == HTTPStatus.CREATED
    comment_id = response.json['id']

    mentions = (
        client_db.session.query(CommentMentionModel)
        .filter(CommentMentionModel.comment_id == comment_id)
        .all()
    )
    assert len(mentions) == 1
    assert mentions[0].user_id == tagged.id

    tag_notifications = (
        client_db.session.query(NotificationModel)
        .filter(NotificationModel.user_ids.contains(f'[{tagged.id}]'))
        .filter(NotificationModel.description.contains('tagged you'))
        .all()
    )
    assert len(tag_notifications) >= 1

    broadcast = (
        client_db.session.query(NotificationModel)
        .filter(NotificationModel.user_ids == '')
        .filter(NotificationModel.description.contains('added a Comment'))
        .order_by(NotificationModel.id.desc())
        .first()
    )
    assert broadcast is not None
    assert f'[{tagged.id}]' in broadcast.read_by


def test_mentionable_users_requires_api_access(client, user_authentication, api_sr_db):
    api_sr = api_sr_db
    url = (
        f'{_MENTIONABLE_USERS_URL}?api-id={api_sr.api_id}'
        f'&user-id={user_authentication.json["id"]}'
        f'&token={user_authentication.json["token"]}'
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json, list)


@pytest.mark.parametrize('mandatory_field', ['api-id', 'user-id', 'token'])
def test_mentionable_users_bad_payload(client, user_authentication, api_sr_db, mandatory_field):
    api_sr = api_sr_db
    url = (
        f'{_MENTIONABLE_USERS_URL}?api-id={api_sr.api_id}'
        f'&user-id={user_authentication.json["id"]}'
        f'&token={user_authentication.json["token"]}'
    )
    if mandatory_field == 'api-id':
        url = url.replace(f'api-id={api_sr.api_id}', 'api-id=')
    elif mandatory_field == 'user-id':
        url = url.replace(f'user-id={user_authentication.json["id"]}', 'user-id=')
    else:
        url = url.replace(f'token={user_authentication.json["token"]}', 'token=')
    response = client.get(url)
    assert response.status_code == HTTPStatus.BAD_REQUEST
