cmake_minimum_required(VERSION 3.18)

project(vitalloom_sr2d_cpp LANGUAGES CXX)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG QUIET)

set(
    VITALLOOM_SR2D_CPP_SOURCES
    src/bindings.cpp
    src/kernel.cpp
)

if(pybind11_FOUND)
    pybind11_add_module(
        _vitalloom_sr2d_cpp
        MODULE
        ${VITALLOOM_SR2D_CPP_SOURCES}
    )
else()
    set(
        PYBIND11_INCLUDE_DIR
        ""
        CACHE PATH
        "Directory containing pybind11/pybind11.h when a pybind11 CMake package is unavailable"
    )
    if(NOT PYBIND11_INCLUDE_DIR)
        message(
            FATAL_ERROR
            "pybind11 was not found. Install its CMake package or configure "
            "-DPYBIND11_INCLUDE_DIR=<directory-containing-pybind11/pybind11.h>."
        )
    endif()
    if(NOT EXISTS "${PYBIND11_INCLUDE_DIR}/pybind11/pybind11.h")
        message(
            FATAL_ERROR
            "PYBIND11_INCLUDE_DIR does not contain pybind11/pybind11.h: "
            "${PYBIND11_INCLUDE_DIR}"
        )
    endif()

    Python_add_library(
        _vitalloom_sr2d_cpp
        MODULE
        WITH_SOABI
        ${VITALLOOM_SR2D_CPP_SOURCES}
    )
    target_include_directories(
        _vitalloom_sr2d_cpp
        PRIVATE
        "${PYBIND11_INCLUDE_DIR}"
    )
    target_link_libraries(_vitalloom_sr2d_cpp PRIVATE Python::Module)
endif()

target_compile_features(_vitalloom_sr2d_cpp PRIVATE cxx_std_17)

install(
    TARGETS _vitalloom_sr2d_cpp
    LIBRARY DESTINATION .
    RUNTIME DESTINATION .
)
