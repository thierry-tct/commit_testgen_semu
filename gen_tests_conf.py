import sys, os

sys.path.insert(0, os.path.dirname("__ORIGINAL_CONF_DIR__"))
from __ORIGINAL_CONF_DIR__ import *
sys.path.pop(0)

# override
OUTPUT_ROOT_DIR="__MUTERIA_OUTPUT__"

# remove all criteria
ENABLED_CRITERIA = []

# remove all test tools and create a shadow tool to collect tests
from muteria.drivers.testgeneration.tools_by_languages.c.shadow_se.\
                                        driver_config import DriverConfigShadow
from muteria.drivers.testgeneration.tools_by_languages.c.semu.\
                                        driver_config import DriverConfigSemu

t_exec_timeout = 10

shadow_for_cmp = TestcaseToolsConfig(tooltype=TestToolType.USE_CODE_AND_TESTS,\
                        toolname='shadow_se', \
                        config_id='cmp', \
                        tool_user_custom=ToolUserCustom(\
                            PATH_TO_TOOL_BINARY_DIR='/home/shadowvm/shadow/klee-change/Release+Asserts/bin/',
                            DRIVER_CONFIG=DriverConfigShadow(keep_first_test=False),
                            PRE_TARGET_CMD_ORDERED_FLAGS_LIST=[
                                ('--search', 'bfs'),
                                ('-max-memory', '150000')
                            ]
                        ))

shadow_for_cmp.set_one_test_execution_timeout(t_exec_timeout)

semu_cmp_list = []
for distance in range(10):
    semu_test_cmp = TestcaseToolsConfig(tooltype=TestToolType.USE_CODE_AND_TESTS, \
                        toolname='semu', \
                        config_id='cmp'+str(distance), \
                        tool_user_custom=ToolUserCustom(
                            PRE_TARGET_CMD_ORDERED_FLAGS_LIST=[
                                #('-semu-disable-statediff-in-testgen',),
                                #('-semu-continue-mindist-out-heuristic',),
                                #('-semu-use-basicblock-for-distance',),
                                ('-semu-forkprocessfor-segv-externalcalls',),
                                #('-semu-testsgen-only-for-critical-diffs',),
                                ('-semu-consider-outenv-for-diffs',),

                                ('-semu-mutant-max-fork', str(distance)),
                                ('-semu-checknum-before-testgen-for-discarded', '0'),
                                ('-semu-mutant-state-continue-proba', '0.0'),
                                ('-semu-precondition-length', '-2'), # start from top
                                #('-semu-max-total-tests-gen', '1000')
                                ('-semu-max-tests-gen-per-mutant', '500000'),
                                ('-solver-backend', 'z3'),
                                ('-max-memory', '150000')
                            ],
                            POST_TARGET_CMD_ORDERED_FLAGS_LIST=semu_sym_args)
                            )
    semu_test_cmp.set_one_test_execution_timeout(semu_cmp_list)
    semu_cmp_list.append(semu_test_cmp)

TESTCASE_TOOLS_CONFIGS = semu_cmp_list + [shadow_for_cmp]
