use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone)]
struct Body {
    x: f64,
    y: f64,
    vx: f64,
    vy: f64,
    radius: f64,
    entity_type: String,
    pinned: bool,
    membrane_locked: bool,
}

struct Config {
    linear_damping: f64,
    boundary_bounce: f64,
    restitution: f64,
    friction: f64,
    contact_slop: f64,
    contact_correction: f64,
    contact_iterations: usize,
    max_speed: f64,
    pvaec_broadphase: String,
}

fn dict_float(config: &Bound<'_, PyDict>, key: &str, default: f64) -> PyResult<f64> {
    Ok(config
        .get_item(key)?
        .map(|v| v.extract::<f64>())
        .transpose()?
        .unwrap_or(default))
}

fn dict_usize(config: &Bound<'_, PyDict>, key: &str, default: usize) -> PyResult<usize> {
    Ok(config
        .get_item(key)?
        .map(|v| v.extract::<usize>())
        .transpose()?
        .unwrap_or(default))
}

fn dict_broadphase(config: &Bound<'_, PyDict>) -> PyResult<String> {
    let Some(value) = config.get_item("pvaec_broadphase")? else {
        return Ok("bruteforce".to_owned());
    };
    if !value.is_truthy()? {
        return Ok("spatial_hash".to_owned());
    }
    let label_value = value.str()?;
    let label = label_value.to_str()?.trim().to_ascii_lowercase();
    if label.is_empty() {
        Ok("spatial_hash".to_owned())
    } else {
        Ok(label)
    }
}

fn is_kinematic_integrable(body: &Body) -> bool {
    !body.pinned && !body.membrane_locked
}

fn is_dynamic(body: &Body) -> bool {
    is_kinematic_integrable(body)
        && (body.entity_type == "organism" || body.entity_type == "central_brain")
}

fn is_static_disk(body: &Body) -> bool {
    body.entity_type == "nutrient" || body.entity_type == "environment_well"
}

fn inv_mass(body: &Body) -> f64 {
    if !is_dynamic(body) {
        return 0.0;
    }
    let r = body.radius.max(8.0);
    1.0 / (r * r)
}

fn integrate(body: &mut Body, dt: f64, width: f64, height: f64, config: &Config) {
    if !is_kinematic_integrable(body) {
        body.vx = 0.0;
        body.vy = 0.0;
        return;
    }

    let damp = config.linear_damping.clamp(0.0, 1.0);
    body.vx *= damp;
    body.vy *= damp;

    let max_speed = config.max_speed.max(1.0);
    let speed = body.vx.hypot(body.vy);
    if speed > max_speed {
        let scale = max_speed / speed;
        body.vx *= scale;
        body.vy *= scale;
    }

    body.x += body.vx * dt;
    body.y += body.vy * dt;

    let bounce = config.boundary_bounce.clamp(0.0, 1.0);
    let r = body.radius;
    if body.x < r {
        body.x = r;
        body.vx = body.vx.abs() * bounce;
    } else if body.x > width - r {
        body.x = width - r;
        body.vx = -body.vx.abs() * bounce;
    }
    if body.y < r {
        body.y = r;
        body.vy = body.vy.abs() * bounce;
    } else if body.y > height - r {
        body.y = height - r;
        body.vy = -body.vy.abs() * bounce;
    }
}

fn circle_hit(a: &Body, b: &Body) -> Option<(f64, f64, f64)> {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    let dist = dx.hypot(dy);
    let min_dist = a.radius + b.radius;
    if dist >= min_dist {
        return None;
    }
    if dist > 1e-8 {
        return Some((dx / dist, dy / dist, min_dist - dist));
    }
    Some((1.0, 0.0, min_dist))
}

fn resolve_pair(bodies: &mut [Body], ia: usize, ib: usize, config: &Config) {
    let Some((nx, ny, pen)) = circle_hit(&bodies[ia], &bodies[ib]) else {
        return;
    };

    let im_a = inv_mass(&bodies[ia]);
    let im_b = inv_mass(&bodies[ib]);
    if im_a <= 0.0 && im_b <= 0.0 {
        return;
    }

    let rvx = bodies[ia].vx - bodies[ib].vx;
    let rvy = bodies[ia].vy - bodies[ib].vy;
    let vn = rvx * nx + rvy * ny;
    let inv_sum = im_a + im_b;
    if vn <= 0.0 && inv_sum > 1e-12 {
        let j = -(1.0 + config.restitution) * vn / inv_sum;
        let ix = j * nx;
        let iy = j * ny;
        bodies[ia].vx += ix * im_a;
        bodies[ia].vy += iy * im_a;
        bodies[ib].vx -= ix * im_b;
        bodies[ib].vy -= iy * im_b;

        let rvx = bodies[ia].vx - bodies[ib].vx;
        let rvy = bodies[ia].vy - bodies[ib].vy;
        let vt = rvx * -ny + rvy * nx;
        let jt = (-vt / inv_sum).clamp(-(j * config.friction).abs(), (j * config.friction).abs());
        bodies[ia].vx += -ny * jt * im_a;
        bodies[ia].vy += nx * jt * im_a;
        bodies[ib].vx -= -ny * jt * im_b;
        bodies[ib].vy -= nx * jt * im_b;
    }

    if inv_sum <= 1e-12 {
        return;
    }

    bodies[ia].x += nx * pen * (im_a / inv_sum);
    bodies[ia].y += ny * pen * (im_a / inv_sum);
    bodies[ib].x -= nx * pen * (im_b / inv_sum);
    bodies[ib].y -= ny * pen * (im_b / inv_sum);

    let corr = (pen - config.contact_slop).max(0.0) * config.contact_correction;
    if corr > 0.0 {
        bodies[ia].x += nx * corr * (im_a / inv_sum);
        bodies[ia].y += ny * corr * (im_a / inv_sum);
        bodies[ib].x -= nx * corr * (im_b / inv_sum);
        bodies[ib].y -= ny * corr * (im_b / inv_sum);
    }
}

fn clamp_dynamic_bodies(bodies: &mut [Body], width: f64, height: f64, bounce: f64) {
    for body in bodies.iter_mut().filter(|b| is_dynamic(b)) {
        let r = body.radius;
        if body.x < r {
            body.x = r;
            body.vx = body.vx.abs() * bounce;
        } else if body.x > width - r {
            body.x = width - r;
            body.vx = -body.vx.abs() * bounce;
        }
        if body.y < r {
            body.y = r;
            body.vy = body.vy.abs() * bounce;
        } else if body.y > height - r {
            body.y = height - r;
            body.vy = -body.vy.abs() * bounce;
        }
    }
}

fn floor_cell_coordinate(value: f64) -> PyResult<i64> {
    if !value.is_finite() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "SR2D spatial-hash coordinates must be finite",
        ));
    }
    let floored = value.floor();
    if floored < i64::MIN as f64 || floored >= i64::MAX as f64 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "SR2D spatial-hash coordinates exceed the native cell range",
        ));
    }
    Ok(floored as i64)
}

fn covered_cells(body: &Body, cell_size: f64, padding: f64) -> PyResult<Vec<(i64, i64)>> {
    let radius = body.radius.max(0.0) + padding.max(0.0);
    let min_x = floor_cell_coordinate((body.x - radius) / cell_size)?;
    let max_x = floor_cell_coordinate((body.x + radius) / cell_size)?;
    let min_y = floor_cell_coordinate((body.y - radius) / cell_size)?;
    let max_y = floor_cell_coordinate((body.y + radius) / cell_size)?;
    let mut cells = Vec::new();
    let mut x = min_x;
    loop {
        let mut y = min_y;
        loop {
            cells.push((x, y));
            if y == max_y { break; }
            y += 1;
        }
        if x == max_x { break; }
        x += 1;
    }
    Ok(cells)
}

fn build_contact_pairs(
    bodies: &[Body],
    dynamics: &[usize],
    statics: &[usize],
    config: &Config,
) -> PyResult<Vec<(usize, usize)>> {
    if config.pvaec_broadphase == "bruteforce" {
        let mut pairs = Vec::new();
        for (offset, &a) in dynamics.iter().enumerate() {
            for &b in dynamics.iter().skip(offset + 1) { pairs.push((a, b)); }
            for &s in statics { pairs.push((a, s)); }
        }
        return Ok(pairs);
    }
    if config.pvaec_broadphase != "spatial_hash" {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "unsupported PVAEC broadphase: {}", config.pvaec_broadphase
        )));
    }

    let mut active = dynamics.to_vec();
    active.extend_from_slice(statics);
    if active.is_empty() { return Ok(Vec::new()); }
    let max_radius = active.iter().map(|&index| bodies[index].radius.max(0.0)).fold(0.0, f64::max);
    let cell_size = (max_radius * 2.0).max(1.0);
    let mut cells: BTreeMap<(i64, i64), Vec<usize>> = BTreeMap::new();
    for &index in &active {
        for cell in covered_cells(&bodies[index], cell_size, 0.0)? {
            cells.entry(cell).or_default().push(index);
        }
    }
    let query_padding = max_radius * config.contact_iterations as f64 * 4.0;
    let mut pairs = Vec::new();
    for (dynamic_order, &dynamic_index) in dynamics.iter().enumerate() {
        let mut nearby = BTreeSet::new();
        for cell in covered_cells(&bodies[dynamic_index], cell_size, query_padding)? {
            if let Some(found) = cells.get(&cell) { nearby.extend(found.iter().copied()); }
        }
        for &other in dynamics.iter().skip(dynamic_order + 1) {
            if nearby.contains(&other) { pairs.push((dynamic_index, other)); }
        }
        for &static_index in statics {
            if nearby.contains(&static_index) { pairs.push((dynamic_index, static_index)); }
        }
    }
    Ok(pairs)
}

#[pyfunction]
fn step_pvaec_circles(
    py: Python<'_>,
    positions: Vec<(f64, f64)>,
    velocities: Vec<(f64, f64)>,
    radii: Vec<f64>,
    entity_types: Vec<String>,
    pinned: Vec<bool>,
    membrane_locked: Vec<bool>,
    dt: f64,
    width: f64,
    height: f64,
    config_raw: Bound<'_, PyDict>,
) -> PyResult<PyObject> {
    let config = Config {
        linear_damping: dict_float(&config_raw, "linear_damping", 0.98)?,
        boundary_bounce: dict_float(&config_raw, "boundary_bounce", 0.85)?,
        restitution: dict_float(&config_raw, "restitution", 0.34)?,
        friction: dict_float(&config_raw, "friction", 0.18)?,
        contact_slop: dict_float(&config_raw, "contact_slop", 0.85)?,
        contact_correction: dict_float(&config_raw, "contact_correction", 0.42)?,
        contact_iterations: dict_usize(&config_raw, "contact_iterations", 4)?.max(1),
        max_speed: dict_float(&config_raw, "max_speed", 420.0)?,
        pvaec_broadphase: dict_broadphase(&config_raw)?,
    };

    let entity_count = positions.len();
    for (name, actual) in [
        ("velocities", velocities.len()),
        ("radii", radii.len()),
        ("entity_types", entity_types.len()),
        ("pinned", pinned.len()),
        ("membrane_locked", membrane_locked.len()),
    ] {
        if actual != entity_count {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "{} length {} does not match positions length {}", name, actual, entity_count
            )));
        }
    }

    if entity_count == 0 || dt <= 0.0 {
        let out = PyDict::new_bound(py);
        out.set_item("positions", positions)?;
        out.set_item("velocities", velocities)?;
        return Ok(out.into());
    }

    let mut bodies = Vec::with_capacity(positions.len());
    for i in 0..positions.len() {
        let (x, y) = positions[i];
        let (vx, vy) = velocities[i];
        bodies.push(Body {
            x,
            y,
            vx,
            vy,
            radius: radii[i],
            entity_type: entity_types[i].clone(),
            pinned: pinned[i],
            membrane_locked: membrane_locked[i],
        });
    }

    for body in bodies.iter_mut() {
        integrate(body, dt, width, height, &config);
    }

    let dynamics: Vec<usize> = bodies
        .iter()
        .enumerate()
        .filter(|(_, b)| is_dynamic(b))
        .map(|(i, _)| i)
        .collect();
    let statics: Vec<usize> = bodies
        .iter()
        .enumerate()
        .filter(|(_, b)| is_static_disk(b))
        .map(|(i, _)| i)
        .collect();
    let pairs = build_contact_pairs(&bodies, &dynamics, &statics, &config)?;
    for _ in 0..config.contact_iterations {
        for &(a, b) in &pairs {
            resolve_pair(&mut bodies, a, b, &config);
        }
    }
    clamp_dynamic_bodies(&mut bodies, width, height, config.boundary_bounce);

    let out = PyDict::new_bound(py);
    out.set_item(
        "positions",
        bodies.iter().map(|b| (b.x, b.y)).collect::<Vec<_>>(),
    )?;
    out.set_item(
        "velocities",
        bodies.iter().map(|b| (b.vx, b.vy)).collect::<Vec<_>>(),
    )?;
    Ok(out.into())
}

#[pymodule]
fn _vitalloom_sr2d_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("VITALLOOM_SR2D_ABI_VERSION", 1)?;
    m.add("VITALLOOM_SR2D_ENTROPY_CONTRACT", "none")?;
    m.add_function(wrap_pyfunction!(step_pvaec_circles, m)?)?;
    Ok(())
}
