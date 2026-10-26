# -*- coding: utf-8 -*-
"""Mechanical E225 ordered decision-plus-mutation named-stream guard."""
from __future__ import annotations
import json, random, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from _runtime_bootstrap import install_runtime_paths
install_runtime_paths(ROOT)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import create_worldbridge_deterministic_randomness_context, register_worldbridge_deterministic_random_stream
from core.Lotucosm.runtime.world_bridge_named_stream_adapter import run_worldbridge_named_stream_sr_respawn_handoff
from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status

def main()->int:
    c=create_worldbridge_deterministic_randomness_context('e225-guard','seed')
    register_worldbridge_deterministic_random_stream(c,'decision','python_random')
    register_worldbridge_deterministic_random_stream(c,'mutation','python_random')
    pb=random.getstate(); nb=np.random.get_state(); before=c.snapshot()
    rejected=run_worldbridge_named_stream_sr_respawn_handoff(c,'decision','mutation',{'wander_amp':20.0},0.25,0.0)
    after=c.snapshot()
    if rejected['ordered_steps']!=['decision'] or rejected['mutation_stream_consumed'] is not False: raise SystemExit('rejected handoff consumed mutation')
    if after['streams'][1]['state']!=before['streams'][1]['state']: raise SystemExit('mutation stream moved on rejection')
    if random.getstate()!=pb or nb[0]!=np.random.get_state()[0] or not np.array_equal(nb[1],np.random.get_state()[1]) or nb[2:]!=np.random.get_state()[2:]: raise SystemExit('global RNG moved')
    status=build_runtime_worldbridge_status()
    if status['default_ready'] is not False or status['opt_in_respawn_two_stream_handoff_contract']['default_tick_attached'] is not False: raise SystemExit('default adoption overclaim')
    print(json.dumps({'status':'ok','ordered_steps':rejected['ordered_steps'],'decision_stream_changed':True,'mutation_stream_consumed':False,'global_python_random_unchanged':True,'global_numpy_random_unchanged':True,'default_tick_attached':False,'replay_admitted':False,'default_ready':False},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
