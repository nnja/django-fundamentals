from django.contrib.auth import get_user_model


def test_user_model_is_the_accounts_app_model():
    assert get_user_model()._meta.label == "accounts.User"
