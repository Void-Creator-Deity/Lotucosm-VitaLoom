# -*- coding: utf-8 -*-
"""Qt-free E263 exact-current portable-witness-attestation aggregate-provenance audit."""
from __future__ import annotations
import ast, copy, hashlib, json
from collections.abc import Mapping, Sequence
from typing import Any
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract as build_e256_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract as build_e257_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract as build_e258_contract, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy as build_e258_policy
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract as build_e259_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract as build_e260_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit import (
 SCOPE as E262_SCOPE, STATUS as E262_STATUS, STATIC_POLICIES,
 build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract as build_e262_contract,
 decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit as decode_e262_audit,
 validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit as validate_e262_audit,
 validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract as validate_e262_contract,
)
SCHEMA_VERSION=1
STATUS="worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit"
SCOPE="e262_ordered_portable_witness_attestation_aggregate_provenance_read_only_audit"
MEDIA_TYPE="application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-attestation-receipt-shape-contract-evolution-portable-corpus-witness-provenance-envelope-component-identity-matrix-portable-witness-attestation-audit+json"
ENCODING="utf-8"; MAX_AUDIT_BYTES=24*1024; MAX_RECORD_BYTES=20*1024; MAX_CONTRACT_BYTES=12*1024; MAX_POLICY_BYTES=12*1024; MAX_RECORDS=16; MAX_SOURCE_BYTES=2*1024*1024
E262_MODULE="core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit"; STATUS_MODULE="core.VitaLoom.simulation.runtime_worldbridge_status"; REQUIRED_SOURCE_UNITS=tuple(sorted((E262_MODULE,STATUS_MODULE)))
CONTRACT_KEY="failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract"; MODULE_ID="quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_module"; CONTRACT_BUILDER="build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract"
DO_NOT_CLAIM=("portable_witness_attestation_audit_is_not_migration_or_execution","portable_witness_attestation_audit_is_not_process_or_ipc_execution","portable_witness_attestation_audit_is_not_command_mcp_or_runtime_authority","portable_witness_attestation_audit_is_not_receipt_consumption_or_ui_authority","portable_witness_attestation_audit_is_not_replay_restore_recovery_or_retry","portable_witness_attestation_audit_is_not_persistence_or_file_network_output","portable_witness_attestation_audit_is_not_runtime_reconstruction_or_admission","unified_pond_default_ready")
REQUIRED_AUDIT_KEYS={"schema_version","status","scope","media_type","encoding","canonical_json","boundary_input_kind","e262_status","e262_scope","e262_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","corpus_size","corpus_order","corpus_order_digest","corpus_record_digests","corpus_record_digest","e262_source_unit_digests","e262_source_provenance_digest","provenance_envelope_digests","provenance_envelope_provenance_digest","component_identity_matrix","component_identity_matrix_digest","receipt_shape_digest","contract_evolution_policy_digest","unique_corpus_valid","version_compatibility_valid","receipt_shape_closure_valid","policy_closure_valid","provenance_envelope_closure_valid","component_identity_matrix_valid","portable_witness_attestation","portable_witness_attestation_digest","portable_witness_attestation_valid","aggregate_provenance","aggregate_provenance_digest","aggregate_provenance_valid","contract_evolution_valid","source_order","source_order_digest","source_unit_digest","source_topology_valid","deterministic_corpus_valid","audit_digest","do_not_claim",*STATIC_POLICIES}

AGGREGATE_PROVENANCE_KEYS={"e262_audit_digests","e262_source_unit_digests","provenance_envelope_digests","component_identity_matrix_digests","corpus_record_digests","e262_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","receipt_shape_digest","contract_evolution_policy_digest","corpus_order_digest","corpus_record_digest","e262_source_provenance_digest","provenance_envelope_provenance_digest","component_identity_matrix_digest","source_order","source_order_digest","source_unit_digest"}

def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_policy()->dict[str,Any]:
 return {"schema_version":1,"accepted_e262_schema_version":1,"accepted_e262_status":E262_STATUS,"accepted_e262_scope":E262_SCOPE,"accepted_e262_contract_digest":_digest(build_e262_contract()),"accepted_e260_contract_digest":_digest(build_e260_contract()),"accepted_e259_contract_digest":_digest(build_e259_contract()),"accepted_e258_contract_digest":_digest(build_e258_contract()),"accepted_e257_contract_digest":_digest(build_e257_contract()),"accepted_e256_contract_digest":_digest(build_e256_contract()),"contract_evolution_mode":"exact_current_portable_witness_attestation_only","migration_admitted":False,"mixed_version_admitted":False,"unknown_contract_admitted":False,"execution_admitted":False,"operational_compatibility_authority":False,"corpus_min_records":2,"corpus_max_records":MAX_RECORDS}
def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_policy(policy:object)->dict[str,Any]:
 if not isinstance(policy,Mapping): return {"valid":False,"errors":["policy_not_mapping"]}
 expected=build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_policy(); return {"valid":dict(policy)==expected,"errors":[] if dict(policy)==expected else ["policy_drift"]}
def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance(e262_audit_corpus_bytes:Sequence[bytes|bytearray|memoryview],e262_contract_bytes:bytes|bytearray|memoryview,portable_witness_attestation_policy_bytes:bytes|bytearray|memoryview,source_units:Mapping[str,str],source_order:Sequence[str])->dict[str,Any]:
 e262_contract=_exact_e262_contract(e262_contract_bytes); policy=_exact_policy(portable_witness_attestation_policy_bytes); records=_decode_corpus(e262_audit_corpus_bytes)
 if len(records)<2: raise ValueError("aggregate provenance requires at least two records")
 if records!=sorted(records,key=lambda record:record["audit_digest"]): raise ValueError("aggregate provenance corpus order drift detected")
 digests=[record["audit_digest"] for record in records]
 if len(set(digests))!=len(digests): raise ValueError("duplicate aggregate provenance record")
 e262,e260,e259,e258,e257,e256=map(_digest,(e262_contract,build_e260_contract(),build_e259_contract(),build_e258_contract(),build_e257_contract(),build_e256_contract())); policy_digest=_digest(build_e258_policy()); shape=records[0]["receipt_shape_digest"]
 for record in records:
  if validate_e262_audit(record)["valid"] is not True: raise ValueError("invalid E262 corpus record")
  if (record.get("schema_version"),record.get("status"),record.get("scope"))!=(1,E262_STATUS,E262_SCOPE): raise ValueError("mixed E262 version or identity")
  if (record.get("e260_contract_digest"),record.get("e259_contract_digest"),record.get("e258_contract_digest"),record.get("e257_contract_digest"),record.get("e256_contract_digest"))!=(e260,e259,e258,e257,e256): raise ValueError("stale upstream contract identity")
  if record.get("receipt_shape_digest")!=shape: raise ValueError("receipt-shape closure drift detected")
  if record.get("contract_evolution_policy_digest")!=policy_digest: raise ValueError("policy closure drift detected")
  if record.get("provenance_envelope_closure_valid") is not True or not _is_sha256(record.get("provenance_envelope_provenance_digest")): raise ValueError("provenance-envelope closure drift detected")
  if record.get("component_identity_matrix_valid") is not True or not _is_sha256(record.get("component_identity_matrix_digest")): raise ValueError("component-identity-matrix closure drift detected")
 if any(policy.get(key)!=value for key,value in (("accepted_e262_contract_digest",e262),("accepted_e260_contract_digest",e260),("accepted_e259_contract_digest",e259),("accepted_e258_contract_digest",e258),("accepted_e257_contract_digest",e257),("accepted_e256_contract_digest",e256))): raise ValueError("aggregate provenance policy contract identity drift detected")
 order=_validated_source_order(source_order); source_summary=_audit_source_topology(source_units)
 if source_summary["source_topology_valid"] is not True: raise ValueError("aggregate provenance source topology invalid: "+",".join(source_summary["forbidden_edges"]))
 e262_sources=[r["source_unit_digest"] for r in records]; envelopes=[r["provenance_envelope_provenance_digest"] for r in records]
 matrix=[{"audit_digest":r["audit_digest"],"e262_source_unit_digest":r["source_unit_digest"],"provenance_envelope_digest":r["provenance_envelope_provenance_digest"],"e260_contract_digest":r["e260_contract_digest"],"e259_contract_digest":r["e259_contract_digest"],"e258_contract_digest":r["e258_contract_digest"],"e257_contract_digest":r["e257_contract_digest"],"e256_contract_digest":r["e256_contract_digest"],"receipt_shape_digest":r["receipt_shape_digest"],"contract_evolution_policy_digest":r["contract_evolution_policy_digest"]} for r in records]
 component_digests=[r["component_identity_matrix_digest"] for r in records]; corpus_record_digests=[_digest(r) for r in records]
 attestation={"e262_audit_digests":digests,"e262_contract_digest":e262,"e260_contract_digest":e260,"e259_contract_digest":e259,"e258_contract_digest":e258,"e257_contract_digest":e257,"e256_contract_digest":e256,"component_identity_matrix_digests":component_digests,"provenance_envelope_provenance_digests":envelopes,"source_unit_digests":e262_sources,"receipt_shape_digest":shape,"contract_evolution_policy_digest":policy_digest}
 aggregate_provenance={"e262_audit_digests":digests,"e262_source_unit_digests":e262_sources,"provenance_envelope_digests":envelopes,"component_identity_matrix_digests":component_digests,"corpus_record_digests":corpus_record_digests,"e262_contract_digest":e262,"e260_contract_digest":e260,"e259_contract_digest":e259,"e258_contract_digest":e258,"e257_contract_digest":e257,"e256_contract_digest":e256,"receipt_shape_digest":shape,"contract_evolution_policy_digest":policy_digest,"corpus_order_digest":_digest(digests),"corpus_record_digest":_digest(corpus_record_digests),"e262_source_provenance_digest":_digest(e262_sources),"provenance_envelope_provenance_digest":_digest(envelopes),"component_identity_matrix_digest":_digest(matrix),"source_order":list(order),"source_order_digest":_digest(list(order)),"source_unit_digest":source_summary["source_unit_digest"]}
 result={"schema_version":1,"status":STATUS,"scope":SCOPE,"media_type":MEDIA_TYPE,"encoding":ENCODING,"canonical_json":True,"boundary_input_kind":"caller_supplied_canonical_e262_component_identity_matrix_portable_witness_attestation_bytes","e262_status":E262_STATUS,"e262_scope":E262_SCOPE,"e262_contract_digest":e262,"e260_contract_digest":e260,"e259_contract_digest":e259,"e258_contract_digest":e258,"e257_contract_digest":e257,"e256_contract_digest":e256,"corpus_size":len(records),"corpus_order":digests,"corpus_order_digest":_digest(digests),"corpus_record_digests":corpus_record_digests,"corpus_record_digest":_digest(corpus_record_digests),"e262_source_unit_digests":e262_sources,"e262_source_provenance_digest":_digest(e262_sources),"provenance_envelope_digests":envelopes,"provenance_envelope_provenance_digest":_digest(envelopes),"component_identity_matrix":matrix,"component_identity_matrix_digest":_digest(matrix),"portable_witness_attestation":attestation,"portable_witness_attestation_digest":_digest(attestation),"aggregate_provenance":aggregate_provenance,"aggregate_provenance_digest":_digest(aggregate_provenance),"receipt_shape_digest":shape,"contract_evolution_policy_digest":policy_digest,"unique_corpus_valid":True,"version_compatibility_valid":True,"receipt_shape_closure_valid":True,"policy_closure_valid":True,"provenance_envelope_closure_valid":True,"component_identity_matrix_valid":True,"portable_witness_attestation_valid":True,"aggregate_provenance_valid":True,"contract_evolution_valid":True,"source_order":list(order),"source_order_digest":_digest(list(order)),"source_unit_digest":source_summary["source_unit_digest"],"source_topology_valid":True,"deterministic_corpus_valid":True,"do_not_claim":list(DO_NOT_CLAIM),**copy.deepcopy(STATIC_POLICIES)}; result["audit_digest"]=_audit_digest(result)
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit(result)["valid"] is not True: raise RuntimeError("constructed invalid aggregate provenance audit")
 return copy.deepcopy(result)
def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit(audit:object)->dict[str,Any]:
 if not isinstance(audit,Mapping): return {"valid":False,"errors":["audit_not_mapping"]}
 value,errors=dict(audit),[]
 if set(value)!=REQUIRED_AUDIT_KEYS: errors.append("audit_shape_invalid")
 if (value.get("schema_version"),value.get("status"),value.get("scope"))!=(1,STATUS,SCOPE): errors.append("audit_identity_mismatch")
 if value.get("media_type")!=MEDIA_TYPE or value.get("encoding")!=ENCODING or value.get("canonical_json") is not True: errors.append("audit_encoding_mismatch")
 if value.get("boundary_input_kind")!="caller_supplied_canonical_e262_component_identity_matrix_portable_witness_attestation_bytes": errors.append("boundary_input_kind_mismatch")
 if (value.get("e262_status"),value.get("e262_scope"))!=(E262_STATUS,E262_SCOPE): errors.append("e262_identity_mismatch")
 size,order=value.get("corpus_size"),value.get("corpus_order")
 size_valid=isinstance(size,int) and not isinstance(size,bool) and 2<=size<=MAX_RECORDS
 order_valid=size_valid and isinstance(order,list) and len(order)==size and order==sorted(order) and len(set(order))==len(order) and all(_is_sha256(item) for item in order)
 if not size_valid: errors.append("corpus_size_invalid")
 if not order_valid: errors.append("corpus_order_invalid")
 record_digests=value.get("corpus_record_digests")
 record_digests_valid=size_valid and isinstance(record_digests,list) and len(record_digests)==size and all(_is_sha256(item) for item in record_digests)
 if not record_digests_valid: errors.append("corpus_record_digests_invalid")
 if record_digests_valid and value.get("corpus_record_digest")!=_digest(record_digests): errors.append("corpus_record_digest_mismatch")
 for plural,aggregate in (("e262_source_unit_digests","e262_source_provenance_digest"),("provenance_envelope_digests","provenance_envelope_provenance_digest")):
  items=value.get(plural); valid=size_valid and isinstance(items,list) and len(items)==size and all(_is_sha256(item) for item in items)
  if not valid or value.get(aggregate)!=_digest(items): errors.append(f"{plural}_invalid")
 matrix=value.get("component_identity_matrix"); matrix_keys={"audit_digest","e262_source_unit_digest","provenance_envelope_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","receipt_shape_digest","contract_evolution_policy_digest"}
 expected_matrix=[]
 if order_valid and isinstance(value.get("e262_source_unit_digests"),list) and isinstance(value.get("provenance_envelope_digests"),list):
  expected_matrix=[{"audit_digest":digest,"e262_source_unit_digest":value["e262_source_unit_digests"][index],"provenance_envelope_digest":value["provenance_envelope_digests"][index],"e260_contract_digest":value.get("e260_contract_digest"),"e259_contract_digest":value.get("e259_contract_digest"),"e258_contract_digest":value.get("e258_contract_digest"),"e257_contract_digest":value.get("e257_contract_digest"),"e256_contract_digest":value.get("e256_contract_digest"),"receipt_shape_digest":value.get("receipt_shape_digest"),"contract_evolution_policy_digest":value.get("contract_evolution_policy_digest")} for index,digest in enumerate(order)]
 if not isinstance(matrix,list) or not size_valid or len(matrix)!=size or any(not isinstance(item,Mapping) or set(item)!=matrix_keys or not all(_is_sha256(item.get(key)) for key in matrix_keys) for item in matrix) or matrix!=expected_matrix or value.get("component_identity_matrix_digest")!=_digest(matrix): errors.append("component_identity_matrix_invalid")
 attestation=value.get("portable_witness_attestation"); attestation_keys={"e262_audit_digests","e262_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","component_identity_matrix_digests","provenance_envelope_provenance_digests","source_unit_digests","receipt_shape_digest","contract_evolution_policy_digest"}
 attestation_valid=isinstance(attestation,Mapping) and set(attestation)==attestation_keys and attestation.get("e262_audit_digests")==order and all(attestation.get(key)==value.get(key) for key in ("e262_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","receipt_shape_digest","contract_evolution_policy_digest")) and attestation.get("source_unit_digests")==value.get("e262_source_unit_digests") and attestation.get("provenance_envelope_provenance_digests")==value.get("provenance_envelope_digests") and isinstance(attestation.get("component_identity_matrix_digests"),list) and len(attestation["component_identity_matrix_digests"])==size and all(_is_sha256(item) for item in attestation["component_identity_matrix_digests"]) and value.get("portable_witness_attestation_digest")==_digest(attestation)
 if not attestation_valid: errors.append("portable_witness_attestation_invalid")
 for key in ("e262_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","corpus_order_digest","corpus_record_digest","receipt_shape_digest","contract_evolution_policy_digest","source_order_digest","source_unit_digest","component_identity_matrix_digest","portable_witness_attestation_digest","aggregate_provenance_digest"):
  if not _is_sha256(value.get(key)): errors.append(f"{key}_invalid")
 if order_valid and value.get("corpus_order_digest")!=_digest(order): errors.append("corpus_order_digest_mismatch")
 for key,expected in (("e262_contract_digest",_digest(build_e262_contract())),("e260_contract_digest",_digest(build_e260_contract())),("e259_contract_digest",_digest(build_e259_contract())),("e258_contract_digest",_digest(build_e258_contract())),("e257_contract_digest",_digest(build_e257_contract())),("e256_contract_digest",_digest(build_e256_contract())),("contract_evolution_policy_digest",_digest(build_e258_policy()))):
  if value.get(key)!=expected: errors.append(f"{key}_mismatch")
 expected_aggregate={"e262_audit_digests":value.get("corpus_order"),"e262_source_unit_digests":value.get("e262_source_unit_digests"),"provenance_envelope_digests":value.get("provenance_envelope_digests"),"component_identity_matrix_digests":attestation.get("component_identity_matrix_digests") if isinstance(attestation,Mapping) else None,"corpus_record_digests":value.get("corpus_record_digests"),"e262_contract_digest":value.get("e262_contract_digest"),"e260_contract_digest":value.get("e260_contract_digest"),"e259_contract_digest":value.get("e259_contract_digest"),"e258_contract_digest":value.get("e258_contract_digest"),"e257_contract_digest":value.get("e257_contract_digest"),"e256_contract_digest":value.get("e256_contract_digest"),"receipt_shape_digest":value.get("receipt_shape_digest"),"contract_evolution_policy_digest":value.get("contract_evolution_policy_digest"),"corpus_order_digest":value.get("corpus_order_digest"),"corpus_record_digest":value.get("corpus_record_digest"),"e262_source_provenance_digest":value.get("e262_source_provenance_digest"),"provenance_envelope_provenance_digest":value.get("provenance_envelope_provenance_digest"),"component_identity_matrix_digest":value.get("component_identity_matrix_digest"),"source_order":value.get("source_order"),"source_order_digest":value.get("source_order_digest"),"source_unit_digest":value.get("source_unit_digest")}
 aggregate=value.get("aggregate_provenance")
 if not isinstance(aggregate,Mapping) or set(aggregate)!=AGGREGATE_PROVENANCE_KEYS or dict(aggregate)!=expected_aggregate or value.get("aggregate_provenance_digest")!=_digest(expected_aggregate): errors.append("aggregate_provenance_invalid")
 for key in ("unique_corpus_valid","version_compatibility_valid","receipt_shape_closure_valid","policy_closure_valid","provenance_envelope_closure_valid","component_identity_matrix_valid","portable_witness_attestation_valid","aggregate_provenance_valid","contract_evolution_valid","source_topology_valid","deterministic_corpus_valid"):
  if value.get(key) is not True: errors.append(f"{key}_mismatch")
 if value.get("source_order")!=list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest")!=_digest(list(REQUIRED_SOURCE_UNITS)): errors.append("source_order_mismatch")
 for key,expected in STATIC_POLICIES.items():
  if value.get(key) is not expected: errors.append(f"policy_{key}_mismatch")
 if value.get("do_not_claim")!=list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
 if value.get("audit_digest")!=_audit_digest(value): errors.append("audit_digest_mismatch")
 return {"valid":not errors,"errors":errors}
def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit(audit:Mapping[str,Any])->bytes:
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit(audit)["valid"] is not True: raise ValueError("invalid aggregate provenance audit")
 return _canonical_json_bytes(dict(audit))
def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit(data:bytes|bytearray|memoryview)->dict[str,Any]:
 value=_decode_canonical_object(_bounded(data,MAX_AUDIT_BYTES,"aggregate provenance audit"),"aggregate provenance audit")
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit(value)["valid"] is not True: raise ValueError("invalid aggregate provenance audit")
 return copy.deepcopy(value)
def _contract_template()->dict[str,Any]: return {"schema_version":1,"status":STATUS,"scope":SCOPE,"accepted_e262_status":E262_STATUS,"accepted_e262_scope":E262_SCOPE,"accepted_e262_contract_digest":_digest(build_e262_contract()),"accepted_e260_contract_digest":_digest(build_e260_contract()),"accepted_e259_contract_digest":_digest(build_e259_contract()),"accepted_e258_contract_digest":_digest(build_e258_contract()),"accepted_e257_contract_digest":_digest(build_e257_contract()),"accepted_e256_contract_digest":_digest(build_e256_contract()),"required_source_units":list(REQUIRED_SOURCE_UNITS),"source_order":list(REQUIRED_SOURCE_UNITS),"corpus_min_records":2,"corpus_max_records":MAX_RECORDS,"contract_evolution_mode":"exact_current_portable_witness_attestation_only","explicit_input_dependency_closure_only":True,"static_policies":copy.deepcopy(STATIC_POLICIES),"aggregate_provenance_keys":sorted(AGGREGATE_PROVENANCE_KEYS),"do_not_claim":list(DO_NOT_CLAIM),"actual_fresh_process_started":False,"ipc_transport_created":False,"contract_valid":True}
def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract()->dict[str,Any]: return _contract_template()
def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_audit_contract(contract:object)->dict[str,Any]:
 if not isinstance(contract,Mapping): return {"valid":False,"errors":["contract_not_mapping"]}
 value,expected=dict(contract),_contract_template(); errors=[f"contract_{key}_mismatch" for key in expected if value.get(key)!=expected[key]]
 if set(value)!=set(expected): errors.append("contract_shape_invalid")
 return {"valid":not errors,"errors":errors}
def _exact_e262_contract(raw:bytes|bytearray|memoryview)->dict[str,Any]:
 value=_decode_canonical_object(_bounded(raw,MAX_CONTRACT_BYTES,"E262 contract"),"E262 contract")
 if validate_e262_contract(value)["valid"] is not True or value!=build_e262_contract(): raise ValueError("E262 contract drift detected")
 return value
def _exact_policy(raw:bytes|bytearray|memoryview)->dict[str,Any]:
 value=_decode_canonical_object(_bounded(raw,MAX_POLICY_BYTES,"aggregate provenance policy"),"aggregate provenance policy")
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_aggregate_provenance_policy(value)["valid"] is not True: raise ValueError("aggregate provenance policy drift detected")
 return value
def _decode_corpus(corpus:Sequence[bytes|bytearray|memoryview])->list[dict[str,Any]]:
 if isinstance(corpus,(str,bytes,bytearray,memoryview)) or not isinstance(corpus,Sequence): raise ValueError("aggregate provenance corpus must be a byte sequence")
 if len(corpus)>MAX_RECORDS: raise ValueError("aggregate provenance exceeds bounded record count")
 return [decode_e262_audit(_bounded(i,MAX_RECORD_BYTES,"E262 corpus record")) for i in corpus]
def _validated_source_order(source_order:Sequence[str])->tuple[str,...]:
 if isinstance(source_order,(str,bytes,bytearray)) or not isinstance(source_order,Sequence) or any(not isinstance(i,str) for i in source_order): raise ValueError("source order must be a string sequence")
 order=tuple(source_order)
 if order!=REQUIRED_SOURCE_UNITS: raise ValueError("source order drift detected")
 return order
def _audit_source_topology(source_units:Mapping[str,str])->dict[str,Any]:
 if not isinstance(source_units,Mapping) or set(source_units)!=set(REQUIRED_SOURCE_UNITS): raise ValueError("source units must be exactly E262 and status")
 units={}
 for name in REQUIRED_SOURCE_UNITS:
  text=source_units.get(name)
  if not isinstance(text,str) or not text.strip() or len(text.encode(ENCODING))>MAX_SOURCE_BYTES: raise ValueError("invalid bounded source unit")
  units[name]=text
 trees={name:ast.parse(text,filename=name) for name,text in units.items()}; edges=[]; e262=trees[E262_MODULE]
 for seam in ("decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit","validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit","build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract","validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract"):
  if sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==seam for n in e262.body)!=1: edges.append(f"e262_seam_missing:{seam}")
 status=_named_function(trees[STATUS_MODULE],"build_runtime_worldbridge_status",STATUS_MODULE)
 if not _imports_symbol(trees[STATUS_MODULE],__name__,CONTRACT_BUILDER): edges.append("status_contract_import_missing")
 if CONTRACT_KEY not in _string_constants(status) or MODULE_ID not in _string_constants(status) or CONTRACT_BUILDER not in _called_names(status): edges.append("status_contract_registration_missing")
 roots={"sub"+"process","multi"+"processing","sock"+"et","request"+"s","url"+"lib","import"+"lib"}; calls={"op"+"en","P"+"ath","Pond","Game"+"Viewport","consume_worldbridge_quarantine_operator_presentation_receipt"}
 for module,tree in trees.items():
  for n in ast.walk(tree):
   if isinstance(n,ast.Import) and any(a.name.split(".")[0] in roots for a in n.names): edges.append(f"{module}:forbidden_import")
   elif isinstance(n,ast.ImportFrom) and n.module and n.module.split(".")[0] in roots: edges.append(f"{module}:forbidden_import")
   elif isinstance(n,ast.Call):
    name=_qualified_name(n.func)
    if name and name.rsplit(".",1)[-1] in calls: edges.append(f"{module}:forbidden_call")
 return {"source_unit_digest":_digest({n:units[n] for n in REQUIRED_SOURCE_UNITS}),"source_topology_valid":not edges,"forbidden_edges":sorted(set(edges))}
def _bounded(data:bytes|bytearray|memoryview,limit:int,label:str)->bytes:
 if not isinstance(data,(bytes,bytearray,memoryview)): raise TypeError(f"{label} must be bytes-like")
 raw=bytes(data)
 if len(raw)>limit: raise ValueError(f"{label} exceeds bounded size")
 return raw
def _decode_canonical_object(raw:bytes,label:str)->dict[str,Any]:
 try: value=json.loads(raw.decode(ENCODING),object_pairs_hook=_reject_duplicate_keys,parse_constant=_reject_constant)
 except (UnicodeDecodeError,json.JSONDecodeError,TypeError,ValueError) as exc: raise ValueError(f"invalid canonical {label}") from exc
 if not isinstance(value,dict) or _canonical_json_bytes(value)!=raw: raise ValueError(f"{label} is non-canonical")
 return value
def _named_function(tree:ast.Module,name:str,module:str)->ast.FunctionDef|ast.AsyncFunctionDef:
 matches=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 if len(matches)!=1: raise ValueError(f"{module} must define exactly one {name}")
 return matches[0]
def _imports_symbol(tree:ast.AST,module:str,symbol:str)->bool: return any(isinstance(n,ast.ImportFrom) and n.module==module and any(a.name==symbol for a in n.names) for n in ast.walk(tree))
def _called_names(tree:ast.AST)->set[str]: return {name for n in ast.walk(tree) if isinstance(n,ast.Call) if (name:=_qualified_name(n.func))}
def _string_constants(tree:ast.AST)->set[str]: return {n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
def _qualified_name(n:ast.AST)->str|None:
 if isinstance(n,ast.Name): return n.id
 if isinstance(n,ast.Attribute):
  base=_qualified_name(n.value); return f"{base}.{n.attr}" if base else n.attr
 return None
def _canonical_json_bytes(value:object)->bytes: return json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(",",":")).encode(ENCODING)
def _digest(value:object)->str: return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()
def _audit_digest(value:Mapping[str,Any])->str:
 copied=dict(value); copied.pop("audit_digest",None); return _digest(copied)
def _is_sha256(value:object)->bool: return isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value)
def _reject_duplicate_keys(pairs:list[tuple[str,Any]])->dict[str,Any]:
 value={}
 for k,i in pairs:
  if k in value: raise ValueError("duplicate JSON object key")
  value[k]=i
 return value
def _reject_constant(value:str)->None: raise ValueError(f"non-finite JSON constant: {value}")






