from __future__ import annotations

import json

try:
    from .check_worldbridge_e375_compatibility_provenance import verify_provenance
except ImportError:
    from check_worldbridge_e375_compatibility_provenance import verify_provenance


def verify_e376() -> dict[str, object]:
    result = verify_provenance()
    if result.get("canonical_roundtrip") is not True:
        raise AssertionError("E376 canonical roundtrip is not stable")
    if result.get("cross_process_stable") is not True:
        raise AssertionError("E376 cross-process provenance decode drifted")
    return {
        "status": "worldbridge_e376_provenance_canonical",
        "contract_valid": True,
        "canonical_roundtrip": True,
        "cross_process_stable": True,
        "default_ready": False,
        "replay_admitted": False,
        "lossless": False,
    }


if __name__ == "__main__":
    result = verify_e376()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if result["contract_valid"] else 1)
