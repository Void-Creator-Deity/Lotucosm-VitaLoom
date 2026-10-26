# -*- coding: utf-8 -*-
"""Qt-free E262 exact-current component-identity-matrix portable witness attestation audit."""
from __future__ import annotations
import ast, copy, hashlib, json
from collections.abc import Mapping, Sequence
from typing import Any
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit_contract as build_e256_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit_contract as build_e257_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit_contract as build_e258_contract, build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_policy as build_e258_policy
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_audit_contract as build_e259_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract as build_e260_contract
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit import (
 SCOPE as E261_SCOPE, STATUS as E261_STATUS, STATIC_POLICIES,
 build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract as build_e261_contract,
 decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as decode_e261_audit,
 validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit as validate_e261_audit,
 validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract as validate_e261_contract,
)
SCHEMA_VERSION=1
STATUS="worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit"
SCOPE="e261_ordered_component_identity_matrix_portable_witness_attestation_read_only_audit"
MEDIA_TYPE="application/vnd.lotucosm.worldbridge-quarantine-operator-presentation-status-projection-boundary-attestation-receipt-shape-contract-evolution-portable-corpus-witness-provenance-envelope-component-identity-matrix-portable-witness-attestation-audit+json"
ENCODING="utf-8"; MAX_AUDIT_BYTES=24*1024; MAX_RECORD_BYTES=20*1024; MAX_CONTRACT_BYTES=12*1024; MAX_POLICY_BYTES=12*1024; MAX_RECORDS=16; MAX_SOURCE_BYTES=2*1024*1024
E261_MODULE="core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit"; STATUS_MODULE="core.VitaLoom.simulation.runtime_worldbridge_status"; REQUIRED_SOURCE_UNITS=tuple(sorted((E261_MODULE,STATUS_MODULE)))
CONTRACT_KEY="failure_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract"; MODULE_ID="quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_module"; CONTRACT_BUILDER="build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract"
DO_NOT_CLAIM=("portable_witness_attestation_audit_is_not_migration_or_execution","portable_witness_attestation_audit_is_not_process_or_ipc_execution","portable_witness_attestation_audit_is_not_command_mcp_or_runtime_authority","portable_witness_attestation_audit_is_not_receipt_consumption_or_ui_authority","portable_witness_attestation_audit_is_not_replay_restore_recovery_or_retry","portable_witness_attestation_audit_is_not_persistence_or_file_network_output","portable_witness_attestation_audit_is_not_runtime_reconstruction_or_admission","unified_pond_default_ready")
REQUIRED_AUDIT_KEYS={"schema_version","status","scope","media_type","encoding","canonical_json","boundary_input_kind","e261_status","e261_scope","e261_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","corpus_size","corpus_order","corpus_order_digest","corpus_record_digest","e261_source_unit_digests","e261_source_provenance_digest","provenance_envelope_digests","provenance_envelope_provenance_digest","component_identity_matrix","component_identity_matrix_digest","receipt_shape_digest","contract_evolution_policy_digest","unique_corpus_valid","version_compatibility_valid","receipt_shape_closure_valid","policy_closure_valid","provenance_envelope_closure_valid","component_identity_matrix_valid","portable_witness_attestation","portable_witness_attestation_digest","portable_witness_attestation_valid","contract_evolution_valid","source_order","source_order_digest","source_unit_digest","source_topology_valid","deterministic_corpus_valid","audit_digest","do_not_claim",*STATIC_POLICIES}

def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_policy()->dict[str,Any]:
 return {"schema_version":1,"accepted_e261_schema_version":1,"accepted_e261_status":E261_STATUS,"accepted_e261_scope":E261_SCOPE,"accepted_e261_contract_digest":_digest(build_e261_contract()),"accepted_e260_contract_digest":_digest(build_e260_contract()),"accepted_e259_contract_digest":_digest(build_e259_contract()),"accepted_e258_contract_digest":_digest(build_e258_contract()),"accepted_e257_contract_digest":_digest(build_e257_contract()),"accepted_e256_contract_digest":_digest(build_e256_contract()),"contract_evolution_mode":"exact_current_portable_witness_attestation_only","migration_admitted":False,"mixed_version_admitted":False,"unknown_contract_admitted":False,"execution_admitted":False,"operational_compatibility_authority":False,"corpus_min_records":2,"corpus_max_records":MAX_RECORDS}
def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_policy(policy:object)->dict[str,Any]:
 if not isinstance(policy,Mapping): return {"valid":False,"errors":["policy_not_mapping"]}
 expected=build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_policy(); return {"valid":dict(policy)==expected,"errors":[] if dict(policy)==expected else ["policy_drift"]}
def audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation(e261_audit_corpus_bytes:Sequence[bytes|bytearray|memoryview],e261_contract_bytes:bytes|bytearray|memoryview,portable_witness_attestation_policy_bytes:bytes|bytearray|memoryview,source_units:Mapping[str,str],source_order:Sequence[str])->dict[str,Any]:
 e261_contract=_exact_e261_contract(e261_contract_bytes); policy=_exact_policy(portable_witness_attestation_policy_bytes); records=_decode_corpus(e261_audit_corpus_bytes)
 if len(records)<2: raise ValueError("portable witness attestation requires at least two records")
 if records!=sorted(records,key=lambda record:record["audit_digest"]): raise ValueError("portable witness attestation corpus order drift detected")
 digests=[record["audit_digest"] for record in records]
 if len(set(digests))!=len(digests): raise ValueError("duplicate portable witness attestation record")
 e261,e260,e259,e258,e257,e256=map(_digest,(e261_contract,build_e260_contract(),build_e259_contract(),build_e258_contract(),build_e257_contract(),build_e256_contract())); policy_digest=_digest(build_e258_policy()); shape=records[0]["receipt_shape_digest"]
 for record in records:
  if validate_e261_audit(record)["valid"] is not True: raise ValueError("invalid E261 corpus record")
  if (record.get("schema_version"),record.get("status"),record.get("scope"))!=(1,E261_STATUS,E261_SCOPE): raise ValueError("mixed E261 version or identity")
  if (record.get("e260_contract_digest"),record.get("e259_contract_digest"),record.get("e258_contract_digest"),record.get("e257_contract_digest"),record.get("e256_contract_digest"))!=(e260,e259,e258,e257,e256): raise ValueError("stale upstream contract identity")
  if record.get("receipt_shape_digest")!=shape: raise ValueError("receipt-shape closure drift detected")
  if record.get("contract_evolution_policy_digest")!=policy_digest: raise ValueError("policy closure drift detected")
  if record.get("provenance_envelope_closure_valid") is not True or not _is_sha256(record.get("provenance_envelope_provenance_digest")): raise ValueError("provenance-envelope closure drift detected")
  if record.get("component_identity_matrix_valid") is not True or not _is_sha256(record.get("component_identity_matrix_digest")): raise ValueError("component-identity-matrix closure drift detected")
 if any(policy.get(key)!=value for key,value in (("accepted_e261_contract_digest",e261),("accepted_e260_contract_digest",e260),("accepted_e259_contract_digest",e259),("accepted_e258_contract_digest",e258),("accepted_e257_contract_digest",e257),("accepted_e256_contract_digest",e256))): raise ValueError("portable witness attestation policy contract identity drift detected")
 order=_validated_source_order(source_order); source_summary=_audit_source_topology(source_units)
 if source_summary["source_topology_valid"] is not True: raise ValueError("portable witness attestation source topology invalid: "+",".join(source_summary["forbidden_edges"]))
 e261_sources=[r["source_unit_digest"] for r in records]; envelopes=[r["provenance_envelope_provenance_digest"] for r in records]
 matrix=[{"audit_digest":r["audit_digest"],"e261_source_unit_digest":r["source_unit_digest"],"provenance_envelope_digest":r["provenance_envelope_provenance_digest"],"e260_contract_digest":r["e260_contract_digest"],"e259_contract_digest":r["e259_contract_digest"],"e258_contract_digest":r["e258_contract_digest"],"e257_contract_digest":r["e257_contract_digest"],"e256_contract_digest":r["e256_contract_digest"],"receipt_shape_digest":r["receipt_shape_digest"],"contract_evolution_policy_digest":r["contract_evolution_policy_digest"]} for r in records]
 attestation={"e261_audit_digests":digests,"e261_contract_digest":e261,"e260_contract_digest":e260,"e259_contract_digest":e259,"e258_contract_digest":e258,"e257_contract_digest":e257,"e256_contract_digest":e256,"component_identity_matrix_digests":[r["component_identity_matrix_digest"] for r in records],"provenance_envelope_provenance_digests":[r["provenance_envelope_provenance_digest"] for r in records],"source_unit_digests":e261_sources,"receipt_shape_digest":shape,"contract_evolution_policy_digest":policy_digest}
 result={"schema_version":1,"status":STATUS,"scope":SCOPE,"media_type":MEDIA_TYPE,"encoding":ENCODING,"canonical_json":True,"boundary_input_kind":"caller_supplied_canonical_e261_component_identity_matrix_portable_witness_attestation_bytes","e261_status":E261_STATUS,"e261_scope":E261_SCOPE,"e261_contract_digest":e261,"e260_contract_digest":e260,"e259_contract_digest":e259,"e258_contract_digest":e258,"e257_contract_digest":e257,"e256_contract_digest":e256,"corpus_size":len(records),"corpus_order":digests,"corpus_order_digest":_digest(digests),"corpus_record_digest":_digest([_digest(r) for r in records]),"e261_source_unit_digests":e261_sources,"e261_source_provenance_digest":_digest(e261_sources),"provenance_envelope_digests":envelopes,"provenance_envelope_provenance_digest":_digest(envelopes),"component_identity_matrix":matrix,"component_identity_matrix_digest":_digest(matrix),"portable_witness_attestation":attestation,"portable_witness_attestation_digest":_digest(attestation),"receipt_shape_digest":shape,"contract_evolution_policy_digest":policy_digest,"unique_corpus_valid":True,"version_compatibility_valid":True,"receipt_shape_closure_valid":True,"policy_closure_valid":True,"provenance_envelope_closure_valid":True,"component_identity_matrix_valid":True,"portable_witness_attestation_valid":True,"contract_evolution_valid":True,"source_order":list(order),"source_order_digest":_digest(list(order)),"source_unit_digest":source_summary["source_unit_digest"],"source_topology_valid":True,"deterministic_corpus_valid":True,"do_not_claim":list(DO_NOT_CLAIM),**copy.deepcopy(STATIC_POLICIES)}; result["audit_digest"]=_audit_digest(result)
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit(result)["valid"] is not True: raise RuntimeError("constructed invalid portable witness attestation audit")
 return copy.deepcopy(result)
def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit(audit:object)->dict[str,Any]:
 if not isinstance(audit,Mapping): return {"valid":False,"errors":["audit_not_mapping"]}
 value,errors=dict(audit),[]
 if set(value)!=REQUIRED_AUDIT_KEYS: errors.append("audit_shape_invalid")
 if (value.get("schema_version"),value.get("status"),value.get("scope"))!=(1,STATUS,SCOPE): errors.append("audit_identity_mismatch")
 if value.get("media_type")!=MEDIA_TYPE or value.get("encoding")!=ENCODING or value.get("canonical_json") is not True: errors.append("audit_encoding_mismatch")
 if value.get("boundary_input_kind")!="caller_supplied_canonical_e261_component_identity_matrix_portable_witness_attestation_bytes": errors.append("boundary_input_kind_mismatch")
 if (value.get("e261_status"),value.get("e261_scope"))!=(E261_STATUS,E261_SCOPE): errors.append("e261_identity_mismatch")
 size,order=value.get("corpus_size"),value.get("corpus_order")
 if not isinstance(size,int) or not 2<=size<=MAX_RECORDS: errors.append("corpus_size_invalid")
 if not isinstance(order,list) or len(order)!=size or order!=sorted(order) or len(set(order))!=len(order) or not all(_is_sha256(i) for i in order): errors.append("corpus_order_invalid")
 for plural,aggregate in (("e261_source_unit_digests","e261_source_provenance_digest"),("provenance_envelope_digests","provenance_envelope_provenance_digest")):
  items=value.get(plural)
  if not isinstance(items,list) or len(items)!=size or not all(_is_sha256(i) for i in items) or value.get(aggregate)!=_digest(items): errors.append(f"{plural}_invalid")
 matrix=value.get("component_identity_matrix")
 matrix_keys={"audit_digest","e261_source_unit_digest","provenance_envelope_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","receipt_shape_digest","contract_evolution_policy_digest"}
 if not isinstance(matrix,list) or len(matrix)!=size or [i.get("audit_digest") for i in matrix if isinstance(i,Mapping)]!=order or any(not isinstance(i,Mapping) or set(i)!=matrix_keys or not all(_is_sha256(i.get(k)) for k in matrix_keys) for i in matrix) or value.get("component_identity_matrix_digest")!=_digest(matrix): errors.append("component_identity_matrix_invalid")
 attestation=value.get("portable_witness_attestation"); attestation_keys={"e261_audit_digests","e261_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","component_identity_matrix_digests","provenance_envelope_provenance_digests","source_unit_digests","receipt_shape_digest","contract_evolution_policy_digest"}
 if not isinstance(attestation,Mapping) or set(attestation)!=attestation_keys or attestation.get("e261_audit_digests")!=order or attestation.get("e261_contract_digest")!=value.get("e261_contract_digest") or attestation.get("e260_contract_digest")!=value.get("e260_contract_digest") or attestation.get("e259_contract_digest")!=value.get("e259_contract_digest") or attestation.get("e258_contract_digest")!=value.get("e258_contract_digest") or attestation.get("e257_contract_digest")!=value.get("e257_contract_digest") or attestation.get("e256_contract_digest")!=value.get("e256_contract_digest") or attestation.get("receipt_shape_digest")!=value.get("receipt_shape_digest") or attestation.get("contract_evolution_policy_digest")!=value.get("contract_evolution_policy_digest") or attestation.get("source_unit_digests")!=value.get("e261_source_unit_digests") or not all(isinstance(attestation.get(key),list) and len(attestation[key])==size and all(_is_sha256(item) for item in attestation[key]) for key in ("component_identity_matrix_digests","provenance_envelope_provenance_digests","source_unit_digests")) or value.get("portable_witness_attestation_digest")!=_digest(attestation): errors.append("portable_witness_attestation_invalid")
 for key in ("e261_contract_digest","e260_contract_digest","e259_contract_digest","e258_contract_digest","e257_contract_digest","e256_contract_digest","corpus_order_digest","corpus_record_digest","receipt_shape_digest","contract_evolution_policy_digest","source_order_digest","source_unit_digest","component_identity_matrix_digest","portable_witness_attestation_digest"):
  if not _is_sha256(value.get(key)): errors.append(f"{key}_invalid")
 if value.get("corpus_order_digest")!=_digest(order): errors.append("corpus_order_digest_mismatch")
 for key,expected in (("e261_contract_digest",_digest(build_e261_contract())),("e260_contract_digest",_digest(build_e260_contract())),("e259_contract_digest",_digest(build_e259_contract())),("e258_contract_digest",_digest(build_e258_contract())),("e257_contract_digest",_digest(build_e257_contract())),("e256_contract_digest",_digest(build_e256_contract())),("contract_evolution_policy_digest",_digest(build_e258_policy()))):
  if value.get(key)!=expected: errors.append(f"{key}_mismatch")
 for key in ("unique_corpus_valid","version_compatibility_valid","receipt_shape_closure_valid","policy_closure_valid","provenance_envelope_closure_valid","component_identity_matrix_valid","portable_witness_attestation_valid","contract_evolution_valid","source_topology_valid","deterministic_corpus_valid"):
  if value.get(key) is not True: errors.append(f"{key}_mismatch")
 if value.get("source_order")!=list(REQUIRED_SOURCE_UNITS) or value.get("source_order_digest")!=_digest(list(REQUIRED_SOURCE_UNITS)): errors.append("source_order_mismatch")
 for key,expected in STATIC_POLICIES.items():
  if value.get(key) is not expected: errors.append(f"policy_{key}_mismatch")
 if value.get("do_not_claim")!=list(DO_NOT_CLAIM): errors.append("do_not_claim_mismatch")
 if value.get("audit_digest")!=_audit_digest(value): errors.append("audit_digest_mismatch")
 return {"valid":not errors,"errors":errors}
def encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit(audit:Mapping[str,Any])->bytes:
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit(audit)["valid"] is not True: raise ValueError("invalid portable witness attestation audit")
 return _canonical_json_bytes(dict(audit))
def decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit(data:bytes|bytearray|memoryview)->dict[str,Any]:
 value=_decode_canonical_object(_bounded(data,MAX_AUDIT_BYTES,"portable witness attestation audit"),"portable witness attestation audit")
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit(value)["valid"] is not True: raise ValueError("invalid portable witness attestation audit")
 return copy.deepcopy(value)
def _contract_template()->dict[str,Any]: return {"schema_version":1,"status":STATUS,"scope":SCOPE,"accepted_e261_status":E261_STATUS,"accepted_e261_scope":E261_SCOPE,"accepted_e261_contract_digest":_digest(build_e261_contract()),"accepted_e260_contract_digest":_digest(build_e260_contract()),"accepted_e259_contract_digest":_digest(build_e259_contract()),"accepted_e258_contract_digest":_digest(build_e258_contract()),"accepted_e257_contract_digest":_digest(build_e257_contract()),"accepted_e256_contract_digest":_digest(build_e256_contract()),"required_source_units":list(REQUIRED_SOURCE_UNITS),"source_order":list(REQUIRED_SOURCE_UNITS),"corpus_min_records":2,"corpus_max_records":MAX_RECORDS,"contract_evolution_mode":"exact_current_portable_witness_attestation_only","explicit_input_dependency_closure_only":True,"static_policies":copy.deepcopy(STATIC_POLICIES),"do_not_claim":list(DO_NOT_CLAIM),"actual_fresh_process_started":False,"ipc_transport_created":False,"contract_valid":True}
def build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract()->dict[str,Any]: return _contract_template()
def validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit_contract(contract:object)->dict[str,Any]:
 if not isinstance(contract,Mapping): return {"valid":False,"errors":["contract_not_mapping"]}
 value,expected=dict(contract),_contract_template(); errors=[f"contract_{key}_mismatch" for key in expected if value.get(key)!=expected[key]]
 if set(value)!=set(expected): errors.append("contract_shape_invalid")
 return {"valid":not errors,"errors":errors}
def _exact_e261_contract(raw:bytes|bytearray|memoryview)->dict[str,Any]:
 value=_decode_canonical_object(_bounded(raw,MAX_CONTRACT_BYTES,"E261 contract"),"E261 contract")
 if validate_e261_contract(value)["valid"] is not True or value!=build_e261_contract(): raise ValueError("E261 contract drift detected")
 return value
def _exact_policy(raw:bytes|bytearray|memoryview)->dict[str,Any]:
 value=_decode_canonical_object(_bounded(raw,MAX_POLICY_BYTES,"portable witness attestation policy"),"portable witness attestation policy")
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_policy(value)["valid"] is not True: raise ValueError("portable witness attestation policy drift detected")
 return value
def _decode_corpus(corpus:Sequence[bytes|bytearray|memoryview])->list[dict[str,Any]]:
 if isinstance(corpus,(str,bytes,bytearray,memoryview)) or not isinstance(corpus,Sequence): raise ValueError("portable witness attestation corpus must be a byte sequence")
 if len(corpus)>MAX_RECORDS: raise ValueError("portable witness attestation exceeds bounded record count")
 return [decode_e261_audit(_bounded(i,MAX_RECORD_BYTES,"E261 corpus record")) for i in corpus]
def _validated_source_order(source_order:Sequence[str])->tuple[str,...]:
 if isinstance(source_order,(str,bytes,bytearray)) or not isinstance(source_order,Sequence) or any(not isinstance(i,str) for i in source_order): raise ValueError("source order must be a string sequence")
 order=tuple(source_order)
 if order!=REQUIRED_SOURCE_UNITS: raise ValueError("source order drift detected")
 return order
def _audit_source_topology(source_units:Mapping[str,str])->dict[str,Any]:
 if not isinstance(source_units,Mapping) or set(source_units)!=set(REQUIRED_SOURCE_UNITS): raise ValueError("source units must be exactly E261 and status")
 units={}
 for name in REQUIRED_SOURCE_UNITS:
  text=source_units.get(name)
  if not isinstance(text,str) or not text.strip() or len(text.encode(ENCODING))>MAX_SOURCE_BYTES: raise ValueError("invalid bounded source unit")
  units[name]=text
 trees={name:ast.parse(text,filename=name) for name,text in units.items()}; edges=[]; e261=trees[E261_MODULE]
 for seam in ("decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit","validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit","build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract","validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit_contract"):
  if sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==seam for n in e261.body)!=1: edges.append(f"e261_seam_missing:{seam}")
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





