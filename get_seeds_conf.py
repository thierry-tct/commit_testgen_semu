import sys, os

sys.path.insert(0, "__ORIGINAL_CONF_DIR__")
from __ORIGINAL_CONF_MODULE__ import *
sys.path.pop(0)

# override
OUTPUT_ROOT_DIR="__MUTERIA_OUTPUT__"

# remove all criteria to generate seeds from all tests
# Keep only coverage to generate only seeds of tests that 
# cover the change
ENABLED_CRITERIA = [
        TestCriteria.STATEMENT_COVERAGE, 
        TestCriteria.BRANCH_COVERAGE,
        TestCriteria.FUNCTION_COVERAGE,
]

# remove all test tools and create a shadow tool to collect tests
from muteria.drivers.testgeneration.tools_by_languages.c.shadow_se.\
                                        driver_config import DriverConfigShadow
shadow_for_seeds = TestcaseToolsConfig(tooltype=TestToolType.USE_CODE_AND_TESTS, toolname='shadow_se', \
                        tool_user_custom=ToolUserCustom(\
                            PATH_TO_TOOL_BINARY_DIR='/home/shadowvm/shadow/klee-change/Release+Asserts/bin/',
                            DRIVER_CONFIG=DriverConfigShadow(keep_first_test=True),
                            PRE_TARGET_CMD_ORDERED_FLAGS_LIST=[
                                ('-shadow-replay-standalone',),
                                ('-only-output-states-covering-new',),
                                ('-dont-simplify',),

                                ('--search', 'bfs'),
                            ]
                        ))
                        
TESTCASE_TOOLS_CONFIGS = [
        dev_test,
        shadow_for_seeds,
]

old_build_func = CODE_BUILDER_FUNCTION
def override_build(repo_root_dir, exe_rel_paths, compiler, flags_list, clean,\
                                                                reconfigure):
    # Make sure that shadow don't generate tests, but just replay
    # Remove the klee changes
    if flags_list is None:
        flags_list = [ "-DRESOLVE_KLEE_CHANGE=11" ]
    else:	
        flags_list.append("-DRESOLVE_KLEE_CHANGE=11")
    return old_build_func(repo_root_dir, exe_rel_paths, compiler, flags_list, clean,\
                                                                reconfigure)
  
CODE_BUILDER_FUNCTION=override_build

# Hook to get sym args
try:
    semu_sym_args
    with open("__SYM_ARGS_STORE_FILE__", 'w') as f:
        json.dump(semu_sym_args, f)
except NameError:
    pass

# Remove added corebench test
if len(__REMOVE_ADDED_DEVTESTS__) > 0:
    DEVELOPER_TESTS_LIST = [dt for dt in DEVELOPER_TESTS_LIST if dt not in __REMOVE_ADDED_DEVTESTS__]
