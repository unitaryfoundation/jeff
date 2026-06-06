cmake_minimum_required(VERSION 3.20)
project(jeff-qiskit-convert LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(CapnProto REQUIRED)

# Generate Cap'n Proto bindings from schema at build time
set(CAPNPC_SRC_PREFIX ${CMAKE_CURRENT_SOURCE_DIR}/../../impl)
set(CAPNPC_OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
set(CAPNPC_IMPORT_DIRS ${CAPNP_INCLUDE_DIRECTORY})
capnp_generate_cpp(CAPNP_SRCS CAPNP_HDRS
    ${CAPNPC_SRC_PREFIX}/capnp/jeff.capnp
)

# Find Python (needed for Qiskit's C API path discovery)
find_package(Python3 COMPONENTS Interpreter Development QUIET)

# Locate Qiskit C API
if(Python3_FOUND)
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c
            "import importlib, os; m=importlib.import_module('qiskit._accelerate'); print(os.path.dirname(m.__file__))"
        OUTPUT_VARIABLE QISKIT_API_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
endif()

if(NOT QISKIT_API_DIR)
    set(QISKIT_API_DIR "$ENV{QISKIT_ROOT}" CACHE PATH "Qiskit C API directory")
endif()

# Qiskit C API header (in capi/include/ relative to the Qiskit package)
find_path(QISKIT_INCLUDE_DIR qiskit.h
    PATHS ${QISKIT_API_DIR}/capi/include
    ${QISKIT_API_DIR}/include
    /usr/local/include/qiskit
)

# Qiskit C API shared library
find_library(QISKIT_LIBRARY
    NAMES _accelerate.abi3 _accelerate
    PATHS ${QISKIT_API_DIR}
)

add_executable(jeff-qiskit-convert
    main.cpp
    ${CAPNP_SRCS}
)

target_include_directories(jeff-qiskit-convert PRIVATE
    ${CMAKE_CURRENT_BINARY_DIR}
    ${QISKIT_INCLUDE_DIR}
)

target_link_libraries(jeff-qiskit-convert PRIVATE
    CapnProto::capnp
)

if(QISKIT_LIBRARY AND Python3_FOUND)
    target_link_libraries(jeff-qiskit-convert PRIVATE
        ${QISKIT_LIBRARY}
        Python3::Python
    )
    target_compile_definitions(jeff-qiskit-convert PRIVATE HAVE_QISKIT=1)
    message(STATUS "Qiskit C API: ${QISKIT_INCLUDE_DIR}")
else()
    message(STATUS "Qiskit C API not found — building without Qiskit support (set QISKIT_ROOT if needed)")
endif()
