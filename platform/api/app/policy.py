import os

import httpx

OPA_URL =os.getenv("OPA_URL", "http://127.0.0.1:8181/v1/data/sog/workload/decision")

class PolicyEngineUnavailableError(Exception):
    """Raised when the policy engine is unavailable."""
    pass

def evaluate_policy(workload: dict, identity: dict) -> str:
    payload = {
        "input": {
            "identity": identity,
            "workload": workload,
        }
    }
    try:
        response = httpx.post(
            OPA_URL,
            json=payload,
            timeout=5.0,
        )
        response.raise_for_status()

        decision = response.json().get("result")

        if decision not in {
            "allow",
            "deny",
            "requires_approval",
        }:
            raise PolicyEngineUnavailableError(
                "OPA returned an invalid policy decision"
            )
        
        return decision
    
    except httpx.RequestError as exc:
        raise PolicyEngineUnavailableError(
            "OPA policy evaluation failed"
        ) from exc