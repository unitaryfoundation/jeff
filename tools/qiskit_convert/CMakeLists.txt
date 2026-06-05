cmake_minimum_required(VERSION 3.20)
project(jeff-qiskit-convert LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(CAPNP REQUIRED capnp)

set(JEFF_SRC_DIR /tmp/jeff/impl/cpp/src)
set(QISKIT_CAPI_DIR /private/tmp/braket-venv2/lib/python3.12/site-packages/qiskit/capi)

add_executable(jeff-qiskit-convert
    main.cpp
    ${JEFF_SRC_DIR}/capnp/jeff.capnp.c++
)

target_include_directories(jeff-qiskit-convert PRIVATE
    ${JEFF_SRC_DIR}
    ${QISKIT_CAPI_DIR}/include
    ${CAPNP_INCLUDE_DIRS}
)

target_link_directories(jeff-qiskit-convert PRIVATE
    ${CAPNP_LIBRARY_DIRS}
)

target_link_libraries(jeff-qiskit-convert PRIVATE
    ${CAPNP_LIBRARIES}
    ${CMAKE_DL_LIBS}
)
