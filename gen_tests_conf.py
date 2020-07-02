import sys, os

sys.path.insert(0, "__ORIGINAL_CONF_DIR__")
from __ORIGINAL_CONF_MODULE__ import *
sys.path.pop(0)

# override
OUTPUT_ROOT_DIR="__MUTERIA_OUTPUT__"

# remove all criteria except code coverage
from muteria.drivers.criteria.tools_by_languages.c.gcov.\
                                        driver_config import DriverConfigGCov
gnucov = CriteriaToolsConfig(tooltype=CriteriaToolType.USE_ONLY_CODE, toolname='gcov', config_id=0, \
                                tool_user_custom=ToolUserCustom(
                                    DRIVER_CONFIG=DriverConfigGCov(allow_missing_coverage=True)
                                )
                            )
CRITERIA_TOOLS_CONFIGS_BY_CRITERIA[TestCriteria.STATEMENT_COVERAGE] = [gnucov]
CRITERIA_TOOLS_CONFIGS_BY_CRITERIA[TestCriteria.BRANCH_COVERAGE] = [gnucov]
CRITERIA_TOOLS_CONFIGS_BY_CRITERIA[TestCriteria.FUNCTION_COVERAGE] = [gnucov]

ENABLED_CRITERIA = [
        TestCriteria.STATEMENT_COVERAGE, 
        TestCriteria.BRANCH_COVERAGE,
        TestCriteria.FUNCTION_COVERAGE,
]

# remove all test tools and create a shadow tool to collect tests
from muteria.drivers.testgeneration.tools_by_languages.c.shadow_se.\
                                        driver_config import DriverConfigShadow
from muteria.drivers.testgeneration.tools_by_languages.c.semu.\
                                        driver_config import DriverConfigSemu

from muteria.drivers.testgeneration.tools_by_languages.c.semu.driver_config \
                                             import MetaMuSource, DriverConfigSemu

t_exec_timeout = 10

OLD = False  # change this to enable old

if OLD:
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
    common_pre_target_args = [
                                #('-semu-disable-statediff-in-testgen',),
                                #('-semu-continue-mindist-out-heuristic',),
                                #('-semu-use-basicblock-for-distance',),
                                ('-semu-forkprocessfor-segv-externalcalls',),
                                #('-semu-testsgen-only-for-critical-diffs',),
                                ('-semu-consider-outenv-for-diffs',),
                                ('-semu-disable-post-mutation-check',), # Suport for higher order mutants

                                ('-semu-checknum-before-testgen-for-discarded', '0'),
                                ('-semu-mutant-state-continue-proba', '0.0'),
                                ('-semu-precondition-length', '-2'), # start from top
                                #('-semu-max-total-tests-gen', '1000')
                                ('-semu-max-tests-gen-per-mutant', '2000'),
                                ('-solver-backend', 'z3'),
                                ('-max-memory', '150000'),

                                ('-seed-out-dir', "__SEED_DIR__"),
                            ]
    nsample = 5
    for only_branch, dist_start, dist_step in [(True, 0, 2), (False, 0, 20)]:
        for distance in range(dist_start, (nsample * dist_step) + dist_start, dist_step):
            custom_pta = [('-semu-mutant-max-fork', str(distance)),]
            omb = ''
            if only_branch:
                omb = '-omb'
                custom_pta.append(('-semu-use-only-multi-branching-for-depth',))
            semu_test_cmp = TestcaseToolsConfig(tooltype=TestToolType.USE_CODE_AND_TESTS, \
                                toolname='semu', \
                                config_id='cmp'+omb+str(distance), \
                                tool_user_custom=ToolUserCustom(
                                    PRE_TARGET_CMD_ORDERED_FLAGS_LIST=(common_pre_target_args+custom_pta),
                                    POST_TARGET_CMD_ORDERED_FLAGS_LIST=semu_sym_args,
                                    DRIVER_CONFIG = DriverConfigSemu(meta_mutant_source=MetaMuSource.ANNOTATION, verbose_generation=True),
                                )
                             )
            semu_test_cmp.set_one_test_execution_timeout(t_exec_timeout)
            semu_cmp_list.append(semu_test_cmp)
else:
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
    common_pre_target_args = [
                                #('-semu-disable-statediff-in-testgen',),
                                #('-semu-continue-mindist-out-heuristic',),
                                #('-semu-use-basicblock-for-distance',),
                                ('-semu-forkprocessfor-segv-externalcalls',),
                                #('-semu-testsgen-only-for-critical-diffs',),
                                ('-semu-consider-outenv-for-diffs',),
                                ('-semu-disable-post-mutation-check',), # Suport for higher order mutants

                                ('-semu-checknum-before-testgen-for-discarded', '0'),
                                ('-semu-mutant-state-continue-proba', '0.0'),
                                #('-semu-max-total-tests-gen', '1000')
                                ('-semu-max-tests-gen-per-mutant', '2000'),
                                ('-solver-backend', 'z3'),
                                ('-max-memory', '150000'),

                                ('-seed-out-dir', "__SEED_DIR__"),
                            ]
    nsample = 6
    dist_start = 0
    for PL, dist_step in [(-2, 4), (-1, 4)]:
        for distance in range(dist_start, (nsample * dist_step) + dist_start, dist_step):
            # common
            custom_pta = [('-semu-precondition-length', str(PL)),]
            custom_pta.append(('-semu-use-only-multi-branching-for-depth',))
            custom_pta.append(('-semu-mutant-max-fork', str(distance)))
            semu_test_cmp = TestcaseToolsConfig(tooltype=TestToolType.USE_CODE_AND_TESTS, \
                                toolname='semu', \
                                config_id='cmp'+'-PL'+str(PL)+'-CW'+str(distance), \
                                tool_user_custom=ToolUserCustom(
                                    PRE_TARGET_CMD_ORDERED_FLAGS_LIST=(common_pre_target_args+custom_pta),
                                    POST_TARGET_CMD_ORDERED_FLAGS_LIST=semu_sym_args,
                                    DRIVER_CONFIG = DriverConfigSemu(meta_mutant_source=MetaMuSource.ANNOTATION, verbose_generation=True),
                                )
                             )
            semu_test_cmp.set_one_test_execution_timeout(t_exec_timeout)
            semu_cmp_list.append(semu_test_cmp)
    
    
TESTCASE_TOOLS_CONFIGS = semu_cmp_list + [shadow_for_cmp] + [dev_test]

# Remove added corebench test
if len(__REMOVE_ADDED_DEVTESTS__) > 0:
    DEVELOPER_TESTS_LIST = [dt in DEVELOPER_TESTS_LIST if dt not in __REMOVE_ADDED_DEVTESTS__]
