import pytest

from db.models.user import UserModel

_ALERT_URL = "/alert"
_ADMIN_SETTINGS_URL = "/admin/settings"

# Admin user constants
UT_ADMIN_USER_NAME = "admin-username"
UT_ADMIN_USER_EMAIL = "admin-email"
UT_ADMIN_USER_PASSWORD = "admin_dummy_password"
UT_ADMIN_USER_ROLE = "ADMIN"


@pytest.fixture(scope="module")
def ut_admin_user_db(client_db):
    """Create an admin user for testing"""
    dbi = client_db

    # Create admin user
    ut_admin_user = UserModel(UT_ADMIN_USER_NAME, UT_ADMIN_USER_EMAIL, UT_ADMIN_USER_PASSWORD, UT_ADMIN_USER_ROLE)
    dbi.session.add(ut_admin_user)
    dbi.session.commit()

    yield ut_admin_user


@pytest.fixture(scope="module")
def admin_authentication(client, ut_admin_user_db):
    """Authenticate as admin user"""
    authentication = client.post(
        "/user/login", json={"email": UT_ADMIN_USER_EMAIL, "password": UT_ADMIN_USER_PASSWORD}
    )
    return authentication


def test_alert_get_empty_settings(client, admin_authentication):
    """Test GET alert with empty alert settings"""
    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": "dummy_content:dummy_content",
        },
    )
    assert response.status_code == 200

    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    assert "info" in data
    assert "danger" in data
    assert "warning" in data
    assert "success" in data
    assert data["info"] == []
    assert data["danger"] == []
    assert data["warning"] == []
    assert data["success"] == []


def test_alert_get_with_settings(client, admin_authentication):
    """Test GET alert with populated settings"""
    # Set up settings with alerts
    settings_content = """
alert:
  info:
    - "Info message 1"
    - "Info message 2"
  warning:
    - "Warning message 1"
  danger:
    - "Danger message 1"
  success:
    - "Success message 1"
"""

    # Update settings via admin endpoint
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Test GET alert
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    assert len(data["info"]) == 2
    assert len(data["warning"]) == 1
    assert len(data["danger"]) == 1
    assert len(data["success"]) == 1
    assert "Info message 1" in data["info"]
    assert "Warning message 1" in data["warning"]
    assert "Danger message 1" in data["danger"]
    assert "Success message 1" in data["success"]


def test_alert_get_with_string_alert(client, admin_authentication):
    """Test GET alert with string alert (not array)"""
    settings_content = """
alert:
  info: "Single info message"
  warning: "Single warning message"
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Test GET alert
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    assert len(data["info"]) == 1
    assert len(data["warning"]) == 1
    assert data["info"][0] == "Single info message"
    assert data["warning"][0] == "Single warning message"


def test_alert_post_all_types(client, admin_authentication):
    """Test POST alert with all alert types"""
    alert_types = ["info", "warning", "danger", "success"]

    for alert_type in alert_types:
        alert_data = {
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "message": f"Test {alert_type} message",
            "type": alert_type,
        }

        response = client.post(_ALERT_URL, json=alert_data)
        assert response.status_code == 200

        data = response.json
        assert f"Test {alert_type} message" in data[alert_type]


def test_alert_post_duplicate_message(client, admin_authentication):
    """Test POST alert with duplicate message (should not add duplicate)"""
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Duplicate message",
        "type": "info",
    }

    # Add first message
    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 200

    # Add same message again
    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 200

    data = response.json
    # Should only appear once
    assert data["info"].count("Duplicate message") == 1


def test_alert_post_missing_fields(client, admin_authentication):
    """Test POST alert with missing mandatory fields"""
    # Missing message
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "type": "info",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 400

    # Missing type
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Test message",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 400


def test_alert_post_invalid_type(client, admin_authentication):
    """Test POST alert with invalid alert type"""
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Test message",
        "type": "invalid_type",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 400


def test_alert_post_unauthorized_user(client, user_authentication):
    """Test POST alert with non-admin user (should fail)"""
    alert_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "message": "Test message",
        "type": "info",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 401


def test_alert_post_invalid_token(client, admin_authentication):
    """Test POST alert with invalid token"""
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": "invalid_token",
        "message": "Test message",
        "type": "info",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 401


def test_alert_delete_success(client, admin_authentication):
    """Test DELETE alert with valid data"""
    # First add an alert
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Message to delete",
        "type": "info",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 200

    # Now delete it
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Message to delete",
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 200

    # Verify it's gone
    response = client.get(_ALERT_URL)
    assert response.status_code == 200
    data = response.json
    assert "Message to delete" not in data["info"]


def test_alert_delete_nonexistent_message(client, admin_authentication):
    """Test DELETE alert with message that doesn't exist"""
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Nonexistent message",
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 200


def test_alert_delete_missing_fields(client, admin_authentication):
    """Test DELETE alert with missing mandatory fields"""
    # Missing message
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 400

    # Missing type
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Test message",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 400


def test_alert_delete_invalid_type(client, admin_authentication):
    """Test DELETE alert with invalid alert type"""
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Test message",
        "type": "invalid_type",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 400


def test_alert_delete_unauthorized_user(client, user_authentication):
    """Test DELETE alert with non-admin user (should fail)"""
    delete_data = {
        "user-id": user_authentication.json["id"],
        "token": user_authentication.json["token"],
        "message": "Test message",
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 401


def test_alert_delete_invalid_token(client, admin_authentication):
    """Test DELETE alert with invalid token"""
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": "invalid_token",
        "message": "Test message",
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 401


def test_alert_get_with_integer_values(client, admin_authentication):
    """Test GET alert when alert values are integers"""
    settings_content = """
alert:
  info: 123
  warning: 456
  danger: 789
  success: 0
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Test GET alert
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    # Should convert integers to empty arrays since they're not lists
    assert data["info"] == []
    assert data["warning"] == []
    assert data["danger"] == []
    assert data["success"] == []


def test_alert_get_with_dictionary_values(client, admin_authentication):
    """Test GET alert when alert values are dictionaries"""
    settings_content = """
alert:
  info:
    key1: "value1"
    key2: "value2"
  warning:
    nested:
      data: "test"
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Test GET alert
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    # Should convert dictionaries to empty arrays since they're not lists
    assert data["info"] == []
    assert data["warning"] == []
    assert data["danger"] == []
    assert data["success"] == []


def test_alert_get_with_null_values(client, admin_authentication):
    """Test GET alert when alert values are null"""
    settings_content = """
alert:
  info: null
  warning: null
  danger: null
  success: null
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Test GET alert
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    # Should handle null values gracefully
    assert data["info"] == []
    assert data["warning"] == []
    assert data["danger"] == []
    assert data["success"] == []


def test_alert_get_with_mixed_types(client, admin_authentication):
    """Test GET alert with mixed data types"""
    settings_content = """
alert:
  info:
    - "Valid list item 1"
    - "Valid list item 2"
  warning: "Single string warning"
  danger: 42
  success:
    nested: "dictionary"
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Test GET alert
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    # Only valid list should be preserved
    assert len(data["info"]) == 2
    assert "Valid list item 1" in data["info"]
    assert "Valid list item 2" in data["info"]

    # Non-list types should be converted to empty arrays
    assert data["warning"] == ["Single string warning"]
    assert data["danger"] == []
    assert data["success"] == []


def test_alert_post_with_non_list_existing_data(client, admin_authentication):
    """Test POST alert when existing data is not a list"""
    # Set up settings with non-list values
    settings_content = """
alert:
  info: "This is a string, not a list"
  warning: 123
  danger:
    key: "value"
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Try to add an alert
    alert_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "New info message",
        "type": "info",
    }

    response = client.post(_ALERT_URL, json=alert_data)
    assert response.status_code == 200

    # Verify the alert was added and old non-list data was converted
    data = response.json
    assert len(data["info"]) == 1
    assert "New info message" in data["info"]
    # The old string value should be gone
    assert "This is a string, not a list" not in data["info"]


def test_alert_delete_with_non_list_existing_data(client, admin_authentication):
    """Test DELETE alert when existing data is not a list"""
    # Set up settings with non-list values
    settings_content = """
alert:
  info: "This is a string, not a list"
  warning: 123
"""

    # Update settings
    response = client.put(
        _ADMIN_SETTINGS_URL,
        json={
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "content": settings_content,
        },
    )
    assert response.status_code == 200

    # Try to delete a message
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "Some message",
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 200

    # Verify the non-list data was converted to empty array
    data = response.json
    assert data["info"] == []
    assert data["warning"] == []


def test_alert_complex_scenario(client, admin_authentication):
    """Test complex scenario with multiple alerts of different types"""
    # Add multiple alerts
    alerts_to_add = [
        {"message": "System maintenance scheduled", "type": "info"},
        {"message": "Database backup in progress", "type": "warning"},
        {"message": "Security vulnerability detected", "type": "danger"},
        {"message": "System update completed", "type": "success"},
        {"message": "Another info message", "type": "info"},
    ]

    for alert in alerts_to_add:
        alert_data = {
            "user-id": admin_authentication.json["id"],
            "token": admin_authentication.json["token"],
            "message": alert["message"],
            "type": alert["type"],
        }

        response = client.post(_ALERT_URL, json=alert_data)
        assert response.status_code == 200

    # Verify all alerts are present
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    assert len(data["info"]) == 2
    assert len(data["warning"]) == 1
    assert len(data["danger"]) == 1
    assert len(data["success"]) == 1

    assert "System maintenance scheduled" in data["info"]
    assert "Another info message" in data["info"]
    assert "Database backup in progress" in data["warning"]
    assert "Security vulnerability detected" in data["danger"]
    assert "System update completed" in data["success"]

    # Delete one alert
    delete_data = {
        "user-id": admin_authentication.json["id"],
        "token": admin_authentication.json["token"],
        "message": "System maintenance scheduled",
        "type": "info",
    }

    response = client.delete(_ALERT_URL, json=delete_data)
    assert response.status_code == 200

    # Verify it's gone
    response = client.get(_ALERT_URL)
    assert response.status_code == 200

    data = response.json
    assert len(data["info"]) == 1
    assert "System maintenance scheduled" not in data["info"]
    assert "Another info message" in data["info"]
