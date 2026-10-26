# -*- coding: utf-8 -*-
"""Standalone E260 provenance-envelope boundary guard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
TESTS=ROOT/"tests"
sys.path[:0]=[str(RUNTIME),str(TESTS)]
from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import (
 CONTRACT_KEY,E259_MODULE,MODULE_ID,REQUIRED_SOURCE_UNITS,
 audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope,
 build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract,
 decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit,
 encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit,
 validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status
from test_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit import AUTHORITY,_canonical,_e260_inputs

def _must_reject(*args:object)->None:
 try: audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope(*args)
 except (TypeError,ValueError): return
 raise SystemExit("E260 guard accepted invalid input")

def main()->int:
 records,contract,policy,sources=_e260_inputs()
 first=audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope(records,contract,policy,sources,REQUIRED_SOURCE_UNITS)
 second=audit_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope(records,contract,policy,sources,REQUIRED_SOURCE_UNITS)
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit(first)!={"valid":True,"errors":[]}: raise SystemExit("E260 audit invalid")
 encoded=encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit(first)
 if encoded!=encode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit(second) or decode_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit(encoded)!=first: raise SystemExit("E260 deterministic round-trip invalid")
 if first.get("corpus_size")!=2 or first.get("provenance_envelope_valid") is not True or len(first.get("provenance_envelope",()))!=2: raise SystemExit("E260 envelope closure invalid")
 _must_reject(list(reversed(records)),contract,policy,sources,REQUIRED_SOURCE_UNITS); _must_reject([records[0],records[0]],contract,policy,sources,REQUIRED_SOURCE_UNITS); _must_reject(records[:1],contract,policy,sources,REQUIRED_SOURCE_UNITS)
 drift=json.loads(contract); drift["schema_version"]=2; _must_reject(records,_canonical(drift),policy,sources,REQUIRED_SOURCE_UNITS)
 drift=json.loads(policy); drift["migration_admitted"]=True; _must_reject(records,contract,_canonical(drift),sources,REQUIRED_SOURCE_UNITS)
 forbidden=dict(sources); forbidden[E259_MODULE]+="\nimport subprocess\n"; _must_reject(records,contract,policy,forbidden,REQUIRED_SOURCE_UNITS)
 tampered=dict(first); tampered["provenance_envelope_digest"]="0"*64
 if validate_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit(tampered)["valid"] is not False: raise SystemExit("E260 accepted tampered result")
 source=AUTHORITY.read_text(encoding="utf-8-sig")
 for token in ("PyQt6","QWidget","QPainter","Pond(","GameViewport","open(","Path(","requests","urllib","socket","threading","asyncio","pickle","subprocess","multiprocessing"):
  if token in source: raise SystemExit(f"E260 crossed boundary: {token}")
 status=build_runtime_worldbridge_status()
 if status.get(CONTRACT_KEY)!=build_worldbridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit_contract() or MODULE_ID not in status.get("pilot_modules",[]): raise SystemExit("E260 status registration missing")
 if status.get("runtime_mode")!="dual" or status.get("unified_pond_enabled") is not False or status.get("default_ready") is not False: raise SystemExit("E260 changed default boundary")
 print(json.dumps({"status":"ok","provenance_envelope_valid":True,"actual_fresh_process_started":False,"ipc_transport_created":False,"default_ready":False},ensure_ascii=False,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
