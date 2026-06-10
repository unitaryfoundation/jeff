cmake_minimum_required(VERSION 3.14)
project(jeff-qiskit-convert LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ─── Python ──────────────────────────────────────────────────────
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# ─── Cap'n Proto ─────────────────────────────────────────────────
find_package(CapnProto REQUIRED)

# ─── Qiskit C API paths (via the Python package) ────────────────
execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import qiskit.capi; print(qiskit.capi.get_include())"
  OUTPUT_VARIABLE QISKIT_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE QISKIT_INCLUDE_RESULT
)
execute_process(
  COMMAND ${Python3_EXECUTABLE} -c "import qiskit.capi; print(qiskit.capi.get_lib())"
  OUTPUT_VARIABLE QISKIT_LIB_PATH
  OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE QISKIT_LIB_RESULT
)

if(NOT QISKIT_INCLUDE_RESULT EQUAL 0 OR NOT QISKIT_LIB_RESULT EQUAL 0)
  message(FATAL_ERROR "Could not find Qiskit C API. Install qiskit: pip install qiskit")
endif()

message(STATUS "Qiskit include: ${QISKIT_INCLUDE_DIR}")
message(STATUS "Qiskit lib:     ${QISKIT_LIB_PATH}")

# ─── jeff capnp sources (already generated) ─────────────────────
set(JEFF_CAPNP_DIR "${CMAKE_SOURCE_DIR}/../../impl/cpp/src/capnp")

# ─── Converter library ──────────────────────────────────────────
add_library(jeff_qiskit_convert STATIC
  qiskit_jeff.cpp
  ${JEFF_CAPNP_DIR}/jeff.capnp.c++
)
target_include_directories(jeff_qiskit_convert PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${JEFF_CAPNP_DIR}
  ${QISKIT_INCLUDE_DIR}
)
target_link_libraries(jeff_qiskit_convert PUBLIC
  CapnProto::capnp
  ${QISKIT_LIB_PATH}
)

# ─── CLI tool ────────────────────────────────────────────────────
add_executable(jeff-qiskit-convert main.cpp)
target_link_libraries(jeff-qiskit-convert PRIVATE jeff_qiskit_convert Python3::Python)

# ─── Python C Extension ──────────────────────────────────────────
Python3_add_library(qiskit_jeff_py MODULE qiskit_jeff_pyext.cpp)
target_link_libraries(qiskit_jeff_py PRIVATE jeff_qiskit_convert CapnProto::capnp)
set_target_properties(qiskit_jeff_py PROPERTIES PREFIX "")
