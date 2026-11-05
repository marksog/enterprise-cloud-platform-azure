from app.auth import DeveloperIdentity
from app.entra_config import COMMERCE_DEVELOPERS_GROUP_ID
from app.identity_mapping import map_developer_identity


def test_commerce_developer_mapping():
    developer = DeveloperIdentity(
        user_id="test-developer",
        groups=(COMMERCE_DEVELOPERS_GROUP_ID,),
    )

    identity = map_developer_identity(developer)

    assert identity == {
        "id": "test-developer",
        "groups": ["commerce-developers"],
    }


def test_unknown_group_grants_no_permissions():
    developer = DeveloperIdentity(
        user_id="unauthorized-developer",
        groups=("unknown-group-id",),
    )

    identity = map_developer_identity(developer)

    assert identity == {
        "id": "unauthorized-developer",
        "groups": [],
    }