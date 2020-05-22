#! /usr/bin/env python

"""
Run this on projects where mutation was already ran for relevant mutation
All this is ran within the cm_tools docker
"""

import os
import sys
import argparse
import shutil
import json

import muteria.common.fs as common_fs
from muteria.drivers.testgeneration.testcase_formats.ktest.utils import \
                                                    ConvertCollectKtestsSeeds
import muteria.controller.checkpoint_tasks as cp_tasks

def error_exit(msg):
    print("Error: {}!".format(msg))
#~ def error_exit()

def run_muteria_with_conf (conf_py):
    cmd = " ".join(['muteria', '--config', conf_py, '--lang c', 'run'])
    ret = os.system(cmd)
    return ret
#~ def run_muteria_with_conf ()

def run_cmtools_run_sh_with_conf(muteria_conf, muteria_output, res):
    srcipt = '/home/cmtools/run.sh'
    cmd = " ".join([srcipt, muteria_conf, muteria_output, res])
    ret = os.system(cmd)
    return ret
#~ def run_cmtools_run_sh_with_conf()

ORIGINAL_CONF_MODULE_KEY = "__ORIGINAL_CONF_MODULE__"
ORIGINAL_CONF_DIR_KEY = "__ORIGINAL_CONF_DIR__"
TG_CONF_MODULE_KEY = "__TG_CONF_MODULE__"
TG_CONF_DIR_KEY = "__TG_CONF_DIR__"
SEED_DIR_KEY = "__SEED_DIR__"
MUTERIA_OUTPUT_KEY = "__MUTERIA_OUTPUT__"
META_MUTANTS_LIST_FILE_KEY = "__META_MUTANTS_LIST_FILE__"
FIRST_TIME_MUTANT_EXECUTION_KEY = '__FIRST_TIME_MUTANT_EXECUTION__'


SEED_COLLECTION='seed_collection'.upper()
TEST_GENERATION='test_generation'.upper()
MUTANT_EXECUTION_PREPA='mutant_execution_prepa'.upper()
MUTANT_EXECUTION='mutant_execution'.upper()
DATA_SUMMARIZATION='data_summarization'.upper()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outdir', help="outdir of the execution")
    parser.add_argument('original_conf', help="config of the project")
    parser.add_argument('--cleanstart', type=bool, action="store_true", \
                                                help="delete out and restart")

    args = parser.parse_args()
    outdir = os.path.abspath(args.outdir)
    original_conf = os.path.abspath(args.original_conf)
    if args.cleanstart:
        if os.path.isdir(outdir):
            shutil.rmtree(outdir)
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    seeds_dir = os.path.join(outdir, "ktests_seeds")
    checkpoint_file = os.path.join(outdir, 'checkpoint.json')

    tg_conf = os.path.join(outdir, "tg_conf.py")
    muteria_output = os.path.join(outdir, "muteria_output")
    mut_ex_prepa_data_dir = os.path.join(outdir, "mut_ex_prepa_data")
    summarized_data_dir = os.path.join(outdir, "summarized_data_dir")
    mutant_exec_res = os.path.join(outdir, "mutant_exec_res")
    meta_mutants_list_file = os.path.join(outdir, mut_ex_prepa_data_dir, \
                                                "meta_mutants_list_file.txt")

    # check checkpoint and load if necessary
    cp_data = {
        SEED_COLLECTION: False,
        TEST_GENERATION: False,
        MUTANT_EXECUTION_PREPA: False,
        MUTANT_EXECUTION: False,
        DATA_SUMMARIZATION: False,
    }

    if os.path.isfile (checkpoint_file):
        cp_data = common_fs.loadJSON(checkpoint_file)

    if not cp_data[SEED_COLLECTION]:
        print ("#(DBG): Executing {} ...".format(SEED_COLLECTION))
        collect_seeds (outdir, seeds_dir, muteria_output, original_conf)
        cp_data[SEED_COLLECTION] = True
        common_fs.dumpJSON(cp_data, checkpoint_file, pretty=True)

    if not cp_data[TEST_GENERATION]:
        print ("#(DBG): Executing {} ...".format(TEST_GENERATION))
        generate_tests (outdir, seeds_dir, muteria_output, original_conf, \
                                                                    tg_conf)
        cp_data[TEST_GENERATION] = True
        common_fs.dumpJSON(cp_data, checkpoint_file, pretty=True)

    if not cp_data[MUTANT_EXECUTION_PREPA]:
        print ("#(DBG): Executing {} ...".format(MUTANT_EXECUTION_PREPA))
        prepare_mutant_execution(outdir, muteria_output, \
                                mut_ex_prepa_data_dir, meta_mutants_list_file)
        cp_data[MUTANT_EXECUTION_PREPA] = True
        common_fs.dumpJSON(cp_data, checkpoint_file, pretty=True)

    if not cp_data[MUTANT_EXECUTION]:
        print ("#(DBG): Executing {} ...".format(MUTANT_EXECUTION))
        mutant_execution(outdir, meta_mutants_list_file, \
                                    muteria_output, tg_conf, mutant_exec_res)
        cp_data[MUTANT_EXECUTION] = True
        common_fs.dumpJSON(cp_data, checkpoint_file, pretty=True)

    if not cp_data[DATA_SUMMARIZATION]:
        print ("#(DBG): Executing {} ...".format(DATA_SUMMARIZATION))
        summarize_data(outdir, summarized_data_dir, mutant_exec_res, \
                                                        mut_ex_prepa_data_dir)
        cp_data[DATA_SUMMARIZATION] = True
        common_fs.dumpJSON(cp_data, checkpoint_file, pretty=True)

    print("\n# DONE!\n")
#~ def main()

def collect_seeds(outdir, seeds_out, muteria_output, original_conf):
    # set the temporary conf
    tmp_conf = os.path.join(outdir, '.seed_conf.py')
    tmp_conf_template = os.path.join(os.path.dirname(__file__), \
                                                        'get_seeds_conf.py')
    with open(tmp_conf_template) as f:
        with open(tmp_conf, 'w') as g:
            o_c_dir = os.path.dirname(original_conf)
            o_c_module = os.path.splitext(os.path.basename(original_conf))[0]
            g.write(f.read().replace(ORIGINAL_CONF_DIR_KEY, o_c_dir)\
                                .replace(ORIGINAL_CONF_MODULE_KEY, o_c_module)\
                                .replace(MUTERIA_OUTPUT_KEY, muteria_output))

    # run muteria
    if os.path.isdir(muteria_output):
        shutil.rmtree(muteria_output)
    if run_muteria_with_conf(tmp_conf) != 0:
        error_exit("Muteria failed during seed collection")

    # collect the seeds using muteria ktest ...
    print("# Generating seeds after muteria...")
    if os.path.isdir(seeds_out):
        shutil.rmtree(seeds_out)
    zesti_tests_dir = os.path.join(muteria_output, 'latest', \
                    'testscases_workdir', 'shadow_se:0', 'tests_files.tar.gz')
    klee_tests_dir = None # TODO: get the relevant mutant semu gene test that is closer to a dev test
    ccks = ConvertCollectKtestsSeeds(custom_binary_dir=None)
    ccks.generate_seeds_from_various_ktests(seeds_out, \
                                            zesti_tests_dir, klee_tests_dir)

    # delete muteria output
    os.remove(tmp_conf)
    shutil.rmtree(muteria_output)
#~ def collect_seeds()

def generate_tests(outdir, seeds_dir, muteria_output, original_conf, tg_conf):
    # set the temporary conf
    tmp_conf_template = os.path.join(os.path.dirname(__file__), \
                                                        'gen_tests_conf.py')
    with open(tmp_conf_template) as f:
        with open(tg_conf, 'w') as g:
            o_c_dir = os.path.dirname(original_conf)
            o_c_module = os.path.splitext(os.path.basename(original_conf))[0]
            g.write(f.read().replace(ORIGINAL_CONF_DIR_KEY, o_c_dir)\
                                .replace(ORIGINAL_CONF_MODULE_KEY, o_c_module)\
                                .replace(MUTERIA_OUTPUT_KEY, muteria_output)\
                                            .replace(SEED_DIR_KEY, seeds_dir))

    # run muteria
    if os.path.isdir(muteria_output):
        shutil.rmtree(muteria_output)
    if run_muteria_with_conf(tg_conf) != 0:
        error_exit("Muteria failed during test generation")
#~ def generate_tests()

def prepare_mutant_execution(outdir, muteria_output, prepare_data_dir, \
                                                    meta_mutants_list_file):
    if not os.path.isdir(prepare_data_dir):
        os.mkdir(prepare_data_dir)

    # Store the test list per technique
    test_list_file = os.path.join(muteria_output, 'latest', 'RESULTS_DATA', \
                                'other_copied_results', 'testcasesInfos.json')
    shutil.copy2(test_list_file, os.path.join(prepare_data_dir, \
                                'gentests_'+os.path.basename(test_list_file)))

    # TODO

    # Do fdupes with relevant output tests of semu and shadow and store map

    # remove redundant tests

    # Get the criteria dir and add to the muteria out

    # Get the selected mutants (mutants that are Not relevant w.r.t dev tests)

    pass
#~ def prepare_mutant_execution()

def mutant_execution(outdir, meta_mutants_list_file, \
                                                muteria_output, tg_conf, res):
    # set the temporary conf
    tmp_conf = os.path.join(outdir, '.mut_exec_conf.py')
    tmp_conf_template = os.path.join(os.path.dirname(__file__), \
                                                        'gen_tests_conf.py')

    first_time = False
    cp_muteria = cp_tasks.TstOrderingDependency(common_fs.loadJSON(\
                                os.path.join(muteria_output, 'latest', '_controller_dat', 'checkpoint_states', 'execution_state')))
    has_sm_matrix = os.path.isfile(os.path.join(muteria_output, 'latest', 'RESULTS_DATA', 'matrices', 'STRONG_MUTATION.csv'))
    if cp_muteria.task_is_complete(cp_tasks.Tasks.FINISHED) and not has_sm_matrix:
        first_time = True

    with open(tmp_conf_template) as f:
        with open(tmp_conf, 'w') as g:
            tg_c_dir = os.path.dirname(tg_conf)
            tg_c_module = os.path.splitext(os.path.basename(tg_conf))[0]
            g.write(f.read().replace(TG_CONF_DIR_KEY, tg_c_dir)\
                                    .replace(TG_CONF_MODULE_KEY, tg_c_module)\
                                .replace(MUTERIA_OUTPUT_KEY, muteria_output)\
                        .replace(FIRST_TIME_MUTANT_EXECUTION_KEY, first_time)\
                .replace(META_MUTANTS_LIST_FILE_KEY, meta_mutants_list_file))

    # Run relevant mutant computation
    # Everything starting from test execution after all test generations (see cmtools/run.sh) TODO: implement it in mut_exe_conf
    if run_cmtools_run_sh_with_conf(tmp_conf, muteria_output, res) != 0:
        error_exit("cmtools/run.sh failed during mutant execution")

    # delete tmp conf
    os.remove(tmp_conf)
#~ def mutant_execution()

def summarize_data(outdir, summarized_data_dir, mutant_exec_res, \
                                                        mut_ex_prepa_data_dir):
    error_exit("To be implemented!")
#~ def summarize_data()

if __name__ == "__main__":
    main()