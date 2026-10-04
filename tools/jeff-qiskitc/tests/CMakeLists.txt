include(GoogleTest)

set(test_name "jeff_qiskitc_tests")

# Links GTest::gtest_main, so none of the test sources define main() themselves.
add_executable(
    ${test_name} gate_conversion_test.cpp circuit_conversion_test.cpp file_conversion_test.cpp
)
target_link_libraries(${test_name} PRIVATE jeff_qiskitc GTest::gtest_main)
gtest_discover_tests(${test_name} DISCOVERY_TIMEOUT 60)
