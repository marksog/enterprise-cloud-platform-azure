"""
SOG Platform API — Identity Mapping.

Maps verified Microsoft Entra security groups
to platform authorization groups.
"""

from app.auth import DeveloperIdentity
from app.entra_config import COMMERCE_DEVELOPERS_GROUP_ID


GROUP_MAPPING = {
    COMMERCE_DEVELOPERS_GROUP_ID: "commerce-developers",
}


def map_developer_identity(
    developer: DeveloperIdentity,
) -> dict:
    """
    Convert an authenticated developer into an
    OPA-compatible authorization identity.
    """

    platform_groups = sorted({
        GROUP_MAPPING[group_id]
        for group_id in developer.groups
        if group_id in GROUP_MAPPING
    })

    return {
        "id": developer.user_id,
        "groups": platform_groups,
    }