from pennmobile.settings.base import *  # noqa: F401, F403


# Override default Django Test Runner to include test suite-wide Mock Patch
TEST_RUNNER = "pennmobile.test_runner.MobileTestCIRunner"

TEST_OUTPUT_VERBOSE = 2
TEST_OUTPUT_DIR = "test-results"
