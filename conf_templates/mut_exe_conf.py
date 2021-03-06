import sys, os

sys.path.insert(0, "__TG_CONF_DIR__")
from __TG_CONF_MODULE__ import *
sys.path.pop(0)

# override
OUTPUT_ROOT_DIR="__MUTERIA_OUTPUT__"

# put back all criteria
ENABLED_CRITERIA = [
        TestCriteria.STATEMENT_COVERAGE, 
        TestCriteria.BRANCH_COVERAGE,
        TestCriteria.FUNCTION_COVERAGE,
        TestCriteria.WEAK_MUTATION,
        TestCriteria.MUTANT_COVERAGE,
        TestCriteria.STRONG_MUTATION,
]

# Select tests and mutants
import json
def test_selector (testlist, maxselcount):
    with open('__AVOID_META_TESTS_LIST_FILE__') as f:
        avoid = set(json.load(f))
    cand = set(testlist) - avoid
    # remove dev_tests
    return [mt for mt in cand if (mt.startswith('semu') or mt.startswith('shadow_se'))]
TESTCASES_SELECTION = test_selector
    
def mutant_selector(testobjectivelist, maxselcount):
    with open('__AVOID_META_TESTS_LIST_FILE__') as f:
        avoid = set(json.load(f))
    return list(set(testobjectivelist) - avoid)
CRITERIA_ELEM_SELECTIONS = {TestCriteria.STRONG_MUTATION: mutant_selector}
    
# Set the execution to start directly from criteria execution
if __FIRST_TIME_MUTANT_EXECUTION__:
    RE_EXECUTE_FROM_CHECKPOINT_META_TASKS = ['TESTS_EXECUTION_SELECTION_PRIORITIZATION', \
                                             'CRITERIA_EXECUTION_SELECTION_PRIORITIZATION']

import muteria.drivers.testgeneration as tc_driver

try:
    tts = TEST_TOOL_TYPES_SCHEDULING
except NameError:
    tts = tc_driver.TEST_TOOL_TYPES_SCHEDULING

TEST_TOOL_TYPES_SCHEDULING = []
for tt in tts:
    TEST_TOOL_TYPES_SCHEDULING += list(tt)
TEST_TOOL_TYPES_SCHEDULING = [tuple(TEST_TOOL_TYPES_SCHEDULING)]
