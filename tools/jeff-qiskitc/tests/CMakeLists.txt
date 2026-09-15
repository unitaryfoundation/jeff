include(GoogleTest)

# Each test links GTest::gtest_main, so none of them define main() themselves.
foreach(test_name gate_conversion_test circuit_conversion_test file_conversion_test)
    add_executable(${test_name} ${test_name}.cpp)
    target_link_libraries(${test_name} PRIVATE jeff_qiskitc GTest::gtest_main)
    gtest_discover_tests(${test_name} DISCOVERY_TIMEOUT 60)
endforeach()
