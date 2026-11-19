from pathlib import Path

import pytest

from workload_generator import WorkloadGenerator, WorkloadSpec, WorkloadValidationError


@pytest.mark.parametrize("stage", ["dev", "staging"])
def test_nonprod_namespace_mapping(stage):
    generator = WorkloadGenerator(Path("."))
    spec = WorkloadSpec(
        name="example-api", domain="commerce", environment=stage,
        size="small", namespace_mode="domain",
        image="example.azurecr.io/example-api:v1", port=8080,
    )
    assert generator.resolve_namespace(spec) == "sog-nonprod-commerce"


def test_dedicated_namespace_mapping():
    generator = WorkloadGenerator(Path("."))
    spec = WorkloadSpec(
        name="example-api", domain="commerce", environment="dev",
        size="small", namespace_mode="dedicated",
        image="example.azurecr.io/example-api:v1", port=8080,
    )
    assert generator.resolve_namespace(spec) == "sog-nonprod-commerce-example-api"


def test_prod_onboarding_is_rejected_until_supported():
    generator = WorkloadGenerator(Path("."))
    spec = WorkloadSpec(
        name="example-api", domain="commerce", environment="prod",
        size="small", namespace_mode="domain",
        image="example.azurecr.io/example-api:v1", port=8080,
    )
    with pytest.raises(WorkloadValidationError, match="Production onboarding"):
        generator.resolve_namespace(spec)
