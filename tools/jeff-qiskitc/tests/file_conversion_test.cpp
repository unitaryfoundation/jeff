// Round-trip tests for the .jeff-file wrapper functions:
// QkCircuit -> qiskitc_to_jeff_file -> (real file on disk) ->
// jeff_file_to_qiskitc -> QkCircuit, checked instruction-by-instruction
// against the original.
//
// Unlike circuit_conversion_test.cpp (which round-trips through the
// in-memory Reader/Array<word> API), this exercises the actual file I/O
// path: open/write/close then open/read/close via real file descriptors.
//
//   cmake --build build --target file_conversion_test
//   ./build/tests/file_conversion_test

#include "jeff_qiskitc.h"
#include "test_utils.h"

#include <gtest/gtest.h>
#include <qiskit.h>
#include <unistd.h>

#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <string>

namespace jeff_qiskitc_test {

class FileRoundTripTest : public ::testing::TestWithParam<CircuitCase> {
  protected:
    void SetUp() override {
        char path_template[] = "/tmp/jeff_qiskitc_test_XXXXXX";
        const int fd = mkstemp(path_template);
        ASSERT_GE(fd, 0) << "failed to create temp file: " << std::strerror(errno);
        close(fd);
        path_ = path_template;
    }

    // Runs even when the test body returns early from a failed assertion.
    void TearDown() override {
        if (!path_.empty())
            unlink(path_.c_str());
    }

    std::string path_;
};

TEST_P(FileRoundTripTest, RoundTripsThroughAFile) {
    const CircuitPtr original = GetParam().build();

    qiskitc_to_jeff_file(original.get(), path_);

    const CircuitPtr roundtripped(jeff_file_to_qiskitc(path_));

    expect_same_circuit(original.get(), roundtripped.get());
}

INSTANTIATE_TEST_SUITE_P(Circuits, FileRoundTripTest, ::testing::ValuesIn(circuit_cases()),
                         circuit_case_name);

} // namespace jeff_qiskitc_test
