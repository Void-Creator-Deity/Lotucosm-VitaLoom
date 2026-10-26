#include "kernel.hpp"

#include <algorithm>
#include <cctype>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

double config_float(const py::dict& config, const char* key, double fallback) {
    if (!config.contains(key)) {
        return fallback;
    }
    return py::cast<double>(config[key]);
}

int config_int(const py::dict& config, const char* key, int fallback) {
    if (!config.contains(key)) {
        return fallback;
    }
    return py::cast<int>(config[key]);
}

std::string normalize_pvaec_broadphase(
    const py::dict& config,
    const std::string& fallback) {
    constexpr const char* key = "pvaec_broadphase";
    if (!config.contains(key)) {
        return fallback;
    }

    const py::handle raw = config[key];
    const int truthy = PyObject_IsTrue(raw.ptr());
    if (truthy < 0) {
        throw py::error_already_set();
    }
    if (truthy == 0) {
        return "spatial_hash";
    }

    std::string value = py::str(raw);
    const auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), not_space));
    value.erase(
        std::find_if(value.rbegin(), value.rend(), not_space).base(),
        value.end());
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return value.empty() ? "spatial_hash" : value;
}

void require_size(const char* name, std::size_t actual, std::size_t expected) {
    if (actual != expected) {
        throw py::value_error(
            std::string(name) + " length " + std::to_string(actual) +
            " does not match positions length " + std::to_string(expected));
    }
}

py::dict step_pvaec_circles(
    const std::vector<std::pair<double, double>>& positions,
    const std::vector<std::pair<double, double>>& velocities,
    const std::vector<double>& radii,
    const std::vector<std::string>& entity_types,
    const std::vector<bool>& pinned,
    const std::vector<bool>& membrane_locked,
    double dt,
    double width,
    double height,
    const py::dict& config_raw) {
    const std::size_t entity_count = positions.size();
    require_size("velocities", velocities.size(), entity_count);
    require_size("radii", radii.size(), entity_count);
    require_size("entity_types", entity_types.size(), entity_count);
    require_size("pinned", pinned.size(), entity_count);
    require_size("membrane_locked", membrane_locked.size(), entity_count);

    vitalloom::sr2d::StepConfig config;
    config.linear_damping = config_float(config_raw, "linear_damping", config.linear_damping);
    config.boundary_bounce = config_float(config_raw, "boundary_bounce", config.boundary_bounce);
    config.restitution = config_float(config_raw, "restitution", config.restitution);
    config.friction = config_float(config_raw, "friction", config.friction);
    config.contact_slop = config_float(config_raw, "contact_slop", config.contact_slop);
    config.contact_correction = config_float(
        config_raw,
        "contact_correction",
        config.contact_correction);
    config.contact_iterations = std::max(
        1,
        config_int(config_raw, "contact_iterations", config.contact_iterations));
    config.pvaec_broadphase = normalize_pvaec_broadphase(
        config_raw,
        config.pvaec_broadphase);
    config.max_speed = config_float(config_raw, "max_speed", config.max_speed);

    const vitalloom::sr2d::StepResult result = vitalloom::sr2d::step_pvaec_circles(
        positions,
        velocities,
        radii,
        entity_types,
        pinned,
        membrane_locked,
        dt,
        width,
        height,
        config);

    py::dict output;
    output["positions"] = result.positions;
    output["velocities"] = result.velocities;
    return output;
}

}  // namespace

PYBIND11_MODULE(_vitalloom_sr2d_cpp, module) {
    module.doc() = "Optional C++ SR2D PVAEC circle kernel for VitaLoom.";
    module.attr("VITALLOOM_SR2D_ABI_VERSION") = 1;
    module.attr("VITALLOOM_SR2D_ENTROPY_CONTRACT") = "none";
    module.def(
        "step_pvaec_circles",
        &step_pvaec_circles,
        py::arg("positions"),
        py::arg("velocities"),
        py::arg("radii"),
        py::arg("entity_types"),
        py::arg("pinned"),
        py::arg("membrane_locked"),
        py::arg("dt"),
        py::arg("width"),
        py::arg("height"),
        py::arg("config"));
}
