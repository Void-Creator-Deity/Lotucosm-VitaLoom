#pragma once

#include <string>
#include <utility>
#include <vector>

namespace vitalloom::sr2d {

struct StepConfig {
    double linear_damping = 0.98;
    double boundary_bounce = 0.85;
    double restitution = 0.34;
    double friction = 0.18;
    double contact_slop = 0.85;
    double contact_correction = 0.42;
    int contact_iterations = 4;
    std::string pvaec_broadphase = "bruteforce";
    double max_speed = 420.0;
};

struct StepResult {
    std::vector<std::pair<double, double>> positions;
    std::vector<std::pair<double, double>> velocities;
};

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
    const StepConfig& config);

}  // namespace vitalloom::sr2d
