# -*- coding: utf-8
"""兼容层：请改用 ``core.Lotucosm.sr_physics2d``。"""

from __future__ import annotations

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.pvaec_contacts import (
    clamp_pvaec_bodies as clamp_dynamic_bodies,
    inv_mass,
    is_pvaec_dynamic_body as is_sr_dynamic_body,
    is_pvaec_static_disk as is_sr_static_disk,
    resolve_pvaec_contacts,
)


def resolve_sr_body_contacts(entities, *, width, height, iterations=3, slop=0.85, correction_percent=0.42, restitution=0.34, friction=0.18):
    cfg = SrPhysics2DConfig(
        contact_iterations=int(iterations),
        contact_slop=float(slop),
        contact_correction=float(correction_percent),
        restitution=float(restitution),
        friction=float(friction),
    )
    resolve_pvaec_contacts(entities, width=width, height=height, config=cfg)
