#include "kernel.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <map>
#include <limits>
#include <set>
#include <stdexcept>

namespace vitalloom::sr2d {
namespace {

struct Body {
    double x = 0.0;
    double y = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double radius = 18.0;
    std::string entity_type;
    bool pinned = false;
    bool membrane_locked = false;
};

struct Hit {
    double nx = 1.0;
    double ny = 0.0;
    double penetration = 0.0;
};

double clamp(double value, double low, double high) {
    return std::max(low, std::min(high, value));
}

bool is_kinematic_integrable(const Body& body) {
    return !body.pinned && !body.membrane_locked;
}

bool is_dynamic(const Body& body) {
    return is_kinematic_integrable(body) &&
           (body.entity_type == "organism" || body.entity_type == "central_brain");
}

bool is_static_disk(const Body& body) {
    return body.entity_type == "nutrient" || body.entity_type == "environment_well";
}

double inv_mass(const Body& body) {
    if (!is_dynamic(body)) {
        return 0.0;
    }
    const double radius = std::max(8.0, body.radius);
    return 1.0 / (radius * radius);
}

void integrate(Body& body, double dt, double width, double height, const StepConfig& config) {
    if (!is_kinematic_integrable(body)) {
        body.vx = 0.0;
        body.vy = 0.0;
        return;
    }

    const double damp = clamp(config.linear_damping, 0.0, 1.0);
    body.vx *= damp;
    body.vy *= damp;

    const double max_speed = std::max(1.0, config.max_speed);
    const double speed = std::sqrt(body.vx * body.vx + body.vy * body.vy);
    if (speed > max_speed) {
        const double scale = max_speed / speed;
        body.vx *= scale;
        body.vy *= scale;
    }

    body.x += body.vx * dt;
    body.y += body.vy * dt;

    const double bounce = clamp(config.boundary_bounce, 0.0, 1.0);
    const double radius = body.radius;
    if (body.x < radius) {
        body.x = radius;
        body.vx = std::abs(body.vx) * bounce;
    } else if (body.x > width - radius) {
        body.x = width - radius;
        body.vx = -std::abs(body.vx) * bounce;
    }
    if (body.y < radius) {
        body.y = radius;
        body.vy = std::abs(body.vy) * bounce;
    } else if (body.y > height - radius) {
        body.y = height - radius;
        body.vy = -std::abs(body.vy) * bounce;
    }
}

bool circle_hit(const Body& a, const Body& b, Hit& out) {
    const double dx = a.x - b.x;
    const double dy = a.y - b.y;
    const double dist = std::sqrt(dx * dx + dy * dy);
    const double min_dist = a.radius + b.radius;
    if (dist >= min_dist) {
        return false;
    }
    if (dist > 1e-8) {
        out.nx = dx / dist;
        out.ny = dy / dist;
        out.penetration = min_dist - dist;
        return true;
    }
    out.nx = 1.0;
    out.ny = 0.0;
    out.penetration = min_dist;
    return true;
}

void resolve_pair(std::vector<Body>& bodies, std::size_t ia, std::size_t ib, const StepConfig& config) {
    Hit hit;
    if (!circle_hit(bodies[ia], bodies[ib], hit)) {
        return;
    }

    const double im_a = inv_mass(bodies[ia]);
    const double im_b = inv_mass(bodies[ib]);
    const double inv_sum = im_a + im_b;
    if (im_a <= 0.0 && im_b <= 0.0) {
        return;
    }

    const double rvx = bodies[ia].vx - bodies[ib].vx;
    const double rvy = bodies[ia].vy - bodies[ib].vy;
    const double vn = rvx * hit.nx + rvy * hit.ny;
    if (vn <= 0.0 && inv_sum > 1e-12) {
        const double j = -(1.0 + config.restitution) * vn / inv_sum;
        const double ix = j * hit.nx;
        const double iy = j * hit.ny;
        if (im_a > 0.0) {
            bodies[ia].vx += ix * im_a;
            bodies[ia].vy += iy * im_a;
        }
        if (im_b > 0.0) {
            bodies[ib].vx -= ix * im_b;
            bodies[ib].vy -= iy * im_b;
        }

        const double post_rvx = bodies[ia].vx - bodies[ib].vx;
        const double post_rvy = bodies[ia].vy - bodies[ib].vy;
        const double vt = post_rvx * -hit.ny + post_rvy * hit.nx;
        const double friction_limit = std::abs(j * config.friction);
        const double jt = clamp(-vt / inv_sum, -friction_limit, friction_limit);
        const double tx = -hit.ny;
        const double ty = hit.nx;
        if (im_a > 0.0) {
            bodies[ia].vx += tx * jt * im_a;
            bodies[ia].vy += ty * jt * im_a;
        }
        if (im_b > 0.0) {
            bodies[ib].vx -= tx * jt * im_b;
            bodies[ib].vy -= ty * jt * im_b;
        }
    }

    if (inv_sum <= 1e-12) {
        return;
    }

    if (im_a > 0.0) {
        const double share = im_a / inv_sum;
        bodies[ia].x += hit.nx * hit.penetration * share;
        bodies[ia].y += hit.ny * hit.penetration * share;
    }
    if (im_b > 0.0) {
        const double share = im_b / inv_sum;
        bodies[ib].x -= hit.nx * hit.penetration * share;
        bodies[ib].y -= hit.ny * hit.penetration * share;
    }

    const double correction = std::max(hit.penetration - config.contact_slop, 0.0) *
                              config.contact_correction;
    if (correction <= 0.0) {
        return;
    }
    if (im_a > 0.0) {
        const double share = im_a / inv_sum;
        bodies[ia].x += hit.nx * correction * share;
        bodies[ia].y += hit.ny * correction * share;
    }
    if (im_b > 0.0) {
        const double share = im_b / inv_sum;
        bodies[ib].x -= hit.nx * correction * share;
        bodies[ib].y -= hit.ny * correction * share;
    }
}

void clamp_dynamic_bodies(std::vector<Body>& bodies, double width, double height, double boundary_bounce) {
    for (Body& body : bodies) {
        if (!is_dynamic(body)) {
            continue;
        }
        const double radius = body.radius;
        if (body.x < radius) {
            body.x = radius;
            body.vx = std::abs(body.vx) * boundary_bounce;
        } else if (body.x > width - radius) {
            body.x = width - radius;
            body.vx = -std::abs(body.vx) * boundary_bounce;
        }
        if (body.y < radius) {
            body.y = radius;
            body.vy = std::abs(body.vy) * boundary_bounce;
        } else if (body.y > height - radius) {
            body.y = height - radius;
            body.vy = -std::abs(body.vy) * boundary_bounce;
        }
    }
}

using Cell = std::pair<long long, long long>;

long long floor_cell_coordinate(double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(
            "SR2D spatial-hash coordinates must be finite");
    }

    const double floored = std::floor(value);
    const double minimum = static_cast<double>(std::numeric_limits<long long>::min());
    const double maximum = static_cast<double>(std::numeric_limits<long long>::max());
    if (floored < minimum || floored >= maximum) {
        throw std::invalid_argument(
            "SR2D spatial-hash coordinates exceed the native cell range");
    }
    return static_cast<long long>(floored);
}

double body_radius_for_broadphase(const Body& body) {
    return std::max(0.0, body.radius);
}

std::vector<Cell> covered_cells(const Body& body, double cell_size, double padding = 0.0) {
    const double radius = body_radius_for_broadphase(body) + std::max(0.0, padding);
    const long long min_x = floor_cell_coordinate((body.x - radius) / cell_size);
    const long long max_x = floor_cell_coordinate((body.x + radius) / cell_size);
    const long long min_y = floor_cell_coordinate((body.y - radius) / cell_size);
    const long long max_y = floor_cell_coordinate((body.y + radius) / cell_size);
    std::vector<Cell> cells;
    for (long long cell_x = min_x; cell_x <= max_x; ++cell_x) {
        for (long long cell_y = min_y; cell_y <= max_y; ++cell_y) {
            cells.emplace_back(cell_x, cell_y);
        }
    }
    return cells;
}

std::vector<std::pair<std::size_t, std::size_t>> bruteforce_pairs(
    const std::vector<std::size_t>& dynamics,
    const std::vector<std::size_t>& statics) {
    std::vector<std::pair<std::size_t, std::size_t>> pairs;
    for (std::size_t i = 0; i < dynamics.size(); ++i) {
        for (std::size_t j = i + 1; j < dynamics.size(); ++j) {
            pairs.emplace_back(dynamics[i], dynamics[j]);
        }
        for (std::size_t static_index : statics) {
            pairs.emplace_back(dynamics[i], static_index);
        }
    }
    return pairs;
}

std::vector<std::pair<std::size_t, std::size_t>> spatial_hash_pairs(
    const std::vector<Body>& bodies,
    const std::vector<std::size_t>& dynamics,
    const std::vector<std::size_t>& statics,
    int contact_iterations) {
    std::vector<std::size_t> active = dynamics;
    active.insert(active.end(), statics.begin(), statics.end());
    if (active.empty()) {
        return {};
    }

    double max_radius = 0.0;
    for (std::size_t index : active) {
        max_radius = std::max(max_radius, body_radius_for_broadphase(bodies[index]));
    }
    const double cell_size = std::max(1.0, max_radius * 2.0);
    std::map<Cell, std::vector<std::size_t>> cells;
    for (std::size_t index : active) {
        for (const Cell& cell : covered_cells(bodies[index], cell_size)) {
            cells[cell].push_back(index);
        }
    }

    const double query_padding =
        max_radius * static_cast<double>(std::max(0, contact_iterations)) * 4.0;
    std::vector<std::pair<std::size_t, std::size_t>> pairs;
    for (std::size_t dynamic_order = 0; dynamic_order < dynamics.size(); ++dynamic_order) {
        const std::size_t dynamic_index = dynamics[dynamic_order];
        std::set<std::size_t> nearby;
        for (const Cell& cell : covered_cells(
                 bodies[dynamic_index],
                 cell_size,
                 query_padding)) {
            const auto found = cells.find(cell);
            if (found == cells.end()) {
                continue;
            }
            nearby.insert(found->second.begin(), found->second.end());
        }

        for (std::size_t other_order = dynamic_order + 1;
             other_order < dynamics.size();
             ++other_order) {
            if (nearby.count(dynamics[other_order]) != 0U) {
                pairs.emplace_back(dynamic_index, dynamics[other_order]);
            }
        }
        for (std::size_t static_index : statics) {
            if (nearby.count(static_index) != 0U) {
                pairs.emplace_back(dynamic_index, static_index);
            }
        }
    }
    return pairs;
}

std::vector<std::pair<std::size_t, std::size_t>> build_contact_pairs(
    const std::vector<Body>& bodies,
    const std::vector<std::size_t>& dynamics,
    const std::vector<std::size_t>& statics,
    const StepConfig& config) {
    if (config.pvaec_broadphase == "bruteforce") {
        return bruteforce_pairs(dynamics, statics);
    }
    if (config.pvaec_broadphase == "spatial_hash") {
        return spatial_hash_pairs(
            bodies,
            dynamics,
            statics,
            config.contact_iterations);
    }
    throw std::invalid_argument(
        "unsupported PVAEC broadphase: " + config.pvaec_broadphase);
}

}  // namespace

StepResult step_pvaec_circles(
    const std::vector<std::pair<double, double>>& positions,
    const std::vector<std::pair<double, double>>& velocities,
    const std::vector<double>& radii,
    const std::vector<std::string>& entity_types,
    const std::vector<bool>& pinned,
    const std::vector<bool>& membrane_locked,
    double dt,
    double width,
    double height,
    const StepConfig& config) {
    const std::size_t entity_count = positions.size();
    if (velocities.size() != entity_count || radii.size() != entity_count ||
        entity_types.size() != entity_count || pinned.size() != entity_count ||
        membrane_locked.size() != entity_count) {
        throw std::invalid_argument("SR2D native input arrays must have identical lengths");
    }

    std::vector<Body> bodies;
    bodies.reserve(entity_count);
    for (std::size_t i = 0; i < entity_count; ++i) {
        Body body;
        body.x = positions[i].first;
        body.y = positions[i].second;
        body.vx = velocities[i].first;
        body.vy = velocities[i].second;
        body.radius = radii[i];
        body.entity_type = entity_types[i];
        body.pinned = pinned[i];
        body.membrane_locked = membrane_locked[i];
        bodies.push_back(body);
    }

    if (entity_count == 0 || dt <= 0.0) {
        StepResult unchanged;
        unchanged.positions = positions;
        unchanged.velocities = velocities;
        return unchanged;
    }

    for (Body& body : bodies) {
        integrate(body, dt, width, height, config);
    }

    std::vector<std::size_t> dynamics;
    std::vector<std::size_t> statics;
    for (std::size_t i = 0; i < bodies.size(); ++i) {
        if (is_dynamic(bodies[i])) {
            dynamics.push_back(i);
        } else if (is_static_disk(bodies[i])) {
            statics.push_back(i);
        }
    }

    const std::vector<std::pair<std::size_t, std::size_t>> pairs =
        build_contact_pairs(bodies, dynamics, statics, config);

    const int iterations = std::max(1, config.contact_iterations);
    for (int iter = 0; iter < iterations; ++iter) {
        for (const auto& pair : pairs) {
            resolve_pair(bodies, pair.first, pair.second, config);
        }
    }
    clamp_dynamic_bodies(bodies, width, height, config.boundary_bounce);

    StepResult result;
    result.positions.reserve(bodies.size());
    result.velocities.reserve(bodies.size());
    for (const Body& body : bodies) {
        result.positions.emplace_back(body.x, body.y);
        result.velocities.emplace_back(body.vx, body.vy);
    }
    return result;
}

}  // namespace vitalloom::sr2d
