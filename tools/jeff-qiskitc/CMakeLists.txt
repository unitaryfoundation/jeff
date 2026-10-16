cmake_minimum_required(VERSION 3.21...4.2)
project(
    jeff_qiskitc
    VERSION 0.1.0
    LANGUAGES CXX
)

set(JEFF_QISKITC_TOOL_NAME "jeff-qiskitc")

option(BUILD_JEFF_QISKITC_TESTS "Build tests for the jeff-qiskitc project" ${PROJECT_IS_TOP_LEVEL})

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

set(FETCH_PACKAGES capnproto)
FetchContent_Declare(
    capnproto
    GIT_REPOSITORY https://github.com/capnproto/capnproto.git
    GIT_TAG v1.5.0
)

if(BUILD_JEFF_QISKITC_TESTS)
    set(GTEST_VERSION
        1.17.0
        CACHE STRING "Google Test version"
    )
    set(INSTALL_GTEST
        OFF
        CACHE BOOL "" FORCE
    )
    FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/refs/tags/v${GTEST_VERSION}.tar.gz
    )
    list(APPEND FETCH_PACKAGES googletest)
endif()

FetchContent_MakeAvailable(${FETCH_PACKAGES})

# The Qiskit C API isn't part of this repo and isn't find_package()-able; point QISKIT_C_DIR at a
# directory containing include/qiskit.h and lib/libqiskit.so, either as a CMake cache variable
# (-DQISKIT_C_DIR=/path/to/qiskit/dist/c) or the QISKIT_C_DIR environment variable.
if(NOT QISKIT_C_DIR AND DEFINED ENV{QISKIT_C_DIR})
    set(QISKIT_C_DIR "$ENV{QISKIT_C_DIR}")
endif()
if(NOT QISKIT_C_DIR)
    message(
        FATAL_ERROR
            "QISKIT_C_DIR is not set. Point it at a Qiskit C API install "
            "(a directory containing include/qiskit.h and lib/libqiskit.so), "
            "e.g. -DQISKIT_C_DIR=/path/to/qiskit/dist/c, or set the "
            "QISKIT_C_DIR environment variable."
    )
endif()

add_library(qiskit_c SHARED IMPORTED)
set_target_properties(
    qiskit_c PROPERTIES IMPORTED_LOCATION "${QISKIT_C_DIR}/lib/libqiskit.so"
                        INTERFACE_INCLUDE_DIRECTORIES "${QISKIT_C_DIR}/include"
)

# jeff.capnp's generated C++ bindings, regenerated from impl/capnp/jeff.capnp by `just
# update-capnp`.
set(JEFF_CAPNP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../impl/cpp/src")

# NOTE: file(GLOB) is evaluated at configure time, so adding a new .cpp under lib/ won't be picked
# up until CMake is re-run (e.g. touch this file, or re-run `cmake ..`).
file(GLOB JEFF_QISKITC_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/lib/*.cpp")

add_library(jeff_qiskitc ${JEFF_QISKITC_SOURCES} "${JEFF_CAPNP_DIR}/capnp/jeff.capnp.c++")
target_include_directories(jeff_qiskitc PUBLIC include lib "${JEFF_CAPNP_DIR}")
target_link_libraries(jeff_qiskitc PUBLIC CapnProto::capnp qiskit_c)

configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/include/jeff_qiskitc_version.h.in"
    "${CMAKE_CURRENT_BINARY_DIR}/include/jeff_qiskitc_version.h" @ONLY
)
target_include_directories(jeff_qiskitc PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/include")

if(BUILD_JEFF_QISKITC_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
