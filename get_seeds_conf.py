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
        shadow_for_seeds,
]
