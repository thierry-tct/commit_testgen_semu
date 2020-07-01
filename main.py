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
import glob

import muteria.common.fs as common_fs
from muteria.drivers import DriversUtils
from muteria.drivers.testgeneration.testcase_formats.ktest.utils import \
                                                    ConvertCollectKtestsSeeds
from muteria.drivers.testgeneration.testcase_formats.ktest.ktest import \
                                                                KTestTestFormat
#import muteria.controller.checkpoint_tasks as cp_tasks

import load

def error_exit(msg):
    print("Error: {}!".format(msg))
    exit(1)
#~ def error_exit()

def run_muteria_with_conf (conf_py):
    cmd = " ".join(['muteria', '--config', conf_py, '--lang c', 'run'])
    ret = os.system(cmd)
    return ret
#~ def run_muteria_with_conf ()

def run_cmtools_run_sh_with_conf(muteria_conf, muteria_output, res):
    script = '/home/cmtools/run.sh'
    # First patch script to remove yes (causes problem for some tests generation)
    os.system("sed -i'' 's/yes | //g' {}".format(script))
    cmd = " ".join([script, muteria_conf, muteria_output, res])
    ret = os.system(cmd)
    return ret
#~ def run_cmtools_run_sh_with_conf()

ORIGINAL_CONF_MODULE_KEY = "__ORIGINAL_CONF_MODULE__"
ORIGINAL_CONF_DIR_KEY = "__ORIGINAL_CONF_DIR__"
TG_CONF_MODULE_KEY = "__TG_CONF_MODULE__"
TG_CONF_DIR_KEY = "__TG_CONF_DIR__"
SEED_DIR_KEY = "__SEED_DIR__"
MUTERIA_OUTPUT_KEY = "__MUTERIA_OUTPUT__"
AVOID_META_TESTS_LIST_FILE_KEY = "__AVOID_META_TESTS_LIST_FILE__"
AVOID_META_MUTANTS_LIST_FILE_KEY = "__AVOID_META_MUTANTS_LIST_FILE__"
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
    parser.add_argument('--cleanstart', action="store_true", \
                                                help="delete out and restart")
    parser.add_argument('--only_gentests', action="store_true", \
                              help="only generate tests, no mutant execution")

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
    avoid_meta_mutants_list_file = os.path.join(outdir, mut_ex_prepa_data_dir, \
                                            "avoid_meta_mutants_list_file.txt")
    avoid_meta_tests_list_file = os.path.join(outdir, mut_ex_prepa_data_dir, \
                                            "avoid_meta_tests_list_file.txt")

    # check checkpoint and load if necessary
    cp_data = {
        SEED_COLLECTION: False,
        TEST_GENERATION: False,
        MUTANT_EXECUTION_PREPA: False,
        MUTANT_EXECUTION: False,
        DATA_SUMMARIZATION: False,
    }
    
    if args.only_gentests:
        cp_data[MUTANT_EXECUTION_PREPA] = true
        cp_data[MUTANT_EXECUTION] = true
        cp_data[DATA_SUMMARIZATION] = true

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
        prepare_mutant_execution(outdir, muteria_output, original_conf, \
                            mut_ex_prepa_data_dir, avoid_meta_tests_list_file,\
                                                avoid_meta_mutants_list_file)
        cp_data[MUTANT_EXECUTION_PREPA] = True
        common_fs.dumpJSON(cp_data, checkpoint_file, pretty=True)

    if not cp_data[MUTANT_EXECUTION]:
        print ("#(DBG): Executing {} ...".format(MUTANT_EXECUTION))
        mutant_execution(outdir, avoid_meta_tests_list_file, avoid_meta_mutants_list_file, \
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

def collect_seeds(outdir, seeds_out, muteria_output, original_conf, compress_dest=True):
    # set the temporary conf
    tmp_conf = os.path.join(outdir, '_seed_conf.py')
    tmp_conf_template = os.path.join(os.path.dirname(__file__), \
                                                        'get_seeds_conf.py')
    prev_sym_args_store_file = tmp_conf + ".symargs.json"
    with open(tmp_conf_template) as f:
        with open(tmp_conf, 'w') as g:
            o_c_dir = os.path.dirname(original_conf)
            o_c_module = os.path.splitext(os.path.basename(original_conf))[0]
            g.write(f.read().replace(ORIGINAL_CONF_DIR_KEY, o_c_dir)\
                                .replace(ORIGINAL_CONF_MODULE_KEY, o_c_module)\
                                .replace(MUTERIA_OUTPUT_KEY, muteria_output)\
                                .replace('__SYM_ARGS_STORE_FILE__', \
                                                    prev_sym_args_store_file))

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
                    'testscases_workdir', 'shadow_se', 'tests_files.tar.gz')
    if os.path.isfile(prev_sym_args_store_file):
        prev_sym_args = common_fs.loadJSON(prev_sym_args_store_file)
        os.remove(prev_sym_args_store_file)
        klee_tests_dir_or_sym_args = prev_sym_args
    else:
        klee_tests_dir_or_sym_args = None
    ccks = ConvertCollectKtestsSeeds(custom_binary_dir=None)
    ccks.generate_seeds_from_various_ktests(seeds_out, \
                                      zesti_tests_dir, \
                                      src_new_klee_ktest_dir_or_sym_args=\
                                               klee_tests_dir_or_sym_args, \
                                      klee_ktest_is_sym_args=True, \
                                      compress_dest=compress_dest)

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

    # prepare seeds
    tar_seeds_dir = seeds_dir + '.tar.gz'
    if not os.path.isdir(seeds_dir):
        if not os.path.isfile(tar_seeds_dir):
            error_exit("seed dir ({}) and tar seed dir ({}) are missing".format(\
                                                        seeds_dir, tar_seeds_dir))
        # decompress
        common_fs.TarGz.decompressDir(tar_seeds_dir)
        
    # run muteria
    if os.path.isdir(muteria_output):
        shutil.rmtree(muteria_output)
    retcode = run_muteria_with_conf(tg_conf)
    
    # revert seeds
    if os.path.isfile(tar_seeds_dir):
        shutil.rmtree(seeds_dir)
    
    if retcode != 0:
        error_exit("Muteria failed during test generation")        
#~ def generate_tests()

def prepare_mutant_execution(outdir, muteria_output, original_conf, \
                                    prepare_data_dir, \
                    avoid_meta_tests_list_file, avoid_meta_mutants_list_file):
    if not os.path.isdir(prepare_data_dir):
        os.mkdir(prepare_data_dir)

    # Store the test list per technique
    test_list_file = os.path.join(muteria_output, 'latest', 'RESULTS_DATA', \
                                'other_copied_results', 'testcasesInfos.json')
    shutil.copy2(test_list_file, os.path.join(prepare_data_dir, \
                                'gentests_'+os.path.basename(test_list_file)))

    relevant_exec_outfolder = os.path.join(os.path.dirname(original_conf), \
                                                            'output', 'latest')

    # Do fdupes with relevant output tests of semu and shadow and store map
    r_shadow_tests_src = os.path.join(relevant_exec_outfolder, \
                            'testscases_workdir', 'shadow_se', 'tests_files')
    r_shadow_tests_src_tar = r_shadow_tests_src + '.tar.gz' 
    r_semu_tests_src = os.path.join(relevant_exec_outfolder, \
                                'testscases_workdir', 'semu', 'tests_files')
    r_semu_tests_src_tar = r_semu_tests_src + '.tar.gz'

    cur_exec_outfolder = os.path.join(muteria_output, 'latest')
    cur_exec_tg_folder = os.path.join(cur_exec_outfolder, 'testscases_workdir')
    
    cur_shadow_tests_src = None
    cur_semu_tests_srcs = []
    cur_semu_tests_src_tars = []
    for f in os.listdir(cur_exec_tg_folder):
        if f.startswith('semu'):
            cur_semu_tests_srcs.append(os.path.join(cur_exec_tg_folder, f, 'tests_files'))
            cur_semu_tests_src_tars.append(cur_semu_tests_srcs[-1] + '.tar.gz')
        elif f.startswith('shadow_se'):
            if cur_shadow_tests_src is not None:
                error_exit("Multiple shadow_se folders exist")
            cur_shadow_tests_src = os.path.join(cur_exec_tg_folder, f, 'tests_files')
            cur_shadow_tests_src_tar = cur_shadow_tests_src + '.tar.gz'
    # use folder fdupes from KtestFormat in muteria 
    ## decompress the folders
    common_fs.TarGz.decompressDir(r_shadow_tests_src_tar)
    common_fs.TarGz.decompressDir(r_semu_tests_src_tar)
    common_fs.TarGz.decompressDir(cur_shadow_tests_src_tar)
    for i in range (len(cur_semu_tests_src_tars)):
        common_fs.TarGz.decompressDir(cur_semu_tests_src_tars[i])

    ## apply fdupes
    def post_test_dup(stored_map, tests_to_avoid, origin, kepttest2duptest_map):
        for kept, duplist in kepttest2duptest_map.items():
            alias, _ = DriversUtils.reverse_meta_element(kept)
            if alias == origin:
                stored_map[kept] = []
                for dup in duplist:
                    dalias, dtest = DriversUtils.reverse_meta_element(dup)
                    if dalias == origin:
                        continue
                    stored_map[kept].append(dup)
                    tests_to_avoid.append(dup)
    #~ def post_test_dup()

    stored_map = {}
    stored_map_file = os.path.join(prepare_data_dir, 'stored_test_map.json')
    tests_to_avoid = []
    
    ### Shadow
    custom_bin = '/home/shadowvm/shadow/klee-change/Release+Asserts/bin/'
    folders = [r_shadow_tests_src, cur_shadow_tests_src]
    folder2alias = {d: os.path.basename(os.path.dirname(d)) for d in folders}
    origin = folder2alias[r_shadow_tests_src]
    kepttest2duptest_map, test2keptdup = KTestTestFormat.cross_folder_fdupes(\
                                            custom_bin, folders, folder2alias)
    post_test_dup(stored_map, tests_to_avoid, origin, kepttest2duptest_map)
    ## remove the untar dirs
    for d in folders:
        shutil.rmtree(d)

    ### Semu
    custom_bin = None
    folders = [r_semu_tests_src] + cur_semu_tests_srcs
    folder2alias = {d: os.path.basename(os.path.dirname(d)) for d in folders}
    origin = folder2alias[r_semu_tests_src]
    kepttest2duptest_map, test2keptdup = KTestTestFormat.cross_folder_fdupes(\
                                            custom_bin, folders, folder2alias)
    post_test_dup(stored_map, tests_to_avoid, origin, kepttest2duptest_map)
    for d in folders:
        shutil.rmtree(d)

    ## store dup map and tests to avoid
    common_fs.dumpJSON(stored_map, stored_map_file, pretty=True)
    common_fs.dumpJSON(tests_to_avoid, avoid_meta_tests_list_file, pretty=True)

    # XXX TODO: modify tg_conf to use tests to avoid

    # Get the criteria dir and add to the muteria out
    r_criteria_dir = os.path.join(relevant_exec_outfolder, 'criteria_workdir')
    dest_crit_work = os.path.join(muteria_output, 'latest', 'criteria_workdir')
    if os.path.isdir(os.path.join(dest_crit_work, 'mart_0')):
        shutil.rmtree(os.path.join(dest_crit_work, 'mart_0'))
    shutil.copytree(os.path.join(r_criteria_dir, 'mart_0'), os.path.join(dest_crit_work, 'mart_0'))

    # Get the selected mutants (mutants that are Not relevant w.r.t dev tests)
    r_res_top = os.path.dirname(os.path.dirname(original_conf))
    r_res = os.path.join(r_res_top, 'res')
    r_res_tar = glob.glob(r_res_top+'/*res.tar.gz')[0]
    
    ## untar res
    if os.system('cd {} && tar -xzf {} --exclude {} --exclude {} && test -d res'.format(\
                        r_res_top, os.path.basename(r_res_tar), \
                        'post/RESULTS_DATA/other_copied_results/Flakiness', \
                        'pre/RESULTS_DATA/other_copied_results/Flakiness')) != 0:
        error_exit("untar re failed")
    ## get relevant mutants to relevant tests
    all_tests, fail_tests, relevant_mutants_to_relevant_tests, \
                mutants_to_killingtests, tests_to_killed_mutants = load.load (r_res, fault_revealing=False)

    ## remove untar
    shutil.rmtree(r_res)
    ## filter mutants (remove those relevant w.r.t. dev tests)
    rel_to_reltests_file = os.path.join(prepare_data_dir, 'relevantmuts_to_relevanttests.json')
    mutants_to_avoid = []
    ### mutants relevant w.r.t. devtests added to avoid
    for mut, r_tests in relevant_mutants_to_relevant_tests.items():
        for rt in r_tests:
            alias, _ = DriversUtils.reverse_meta_element(rt)
            if alias.startswith("custom_devtests"):
                mutants_to_avoid.append(mut)
                break

    ## save filter mutants as to avoid
    common_fs.dumpJSON(relevant_mutants_to_relevant_tests, rel_to_reltests_file, pretty=True)
    common_fs.dumpJSON(mutants_to_avoid, avoid_meta_mutants_list_file, pretty=True)

#~ def prepare_mutant_execution()

def mutant_execution(outdir, avoid_meta_tests_list_file, avoid_meta_mutants_list_file, \
                                                muteria_output, tg_conf, res):
    # set the temporary conf
    tmp_conf = os.path.join(outdir, '_mut_exec_conf.py')
    tmp_conf_template = os.path.join(os.path.dirname(__file__), \
                                                        'mut_exe_conf.py')

    first_time = False
    cp_muteria = common_fs.loadJSON(os.path.join(muteria_output, 'latest', '_controller_dat', 'checkpoint_states', 'execution_state'))
    has_sm_matrix = os.path.isfile(os.path.join(muteria_output, 'latest', 'RESULTS_DATA', 'matrices', 'STRONG_MUTATION.csv'))
    if type(cp_muteria) == dict and cp_muteria["CHECKPOINT_DATA"] == "CHECK_POINTED_TASK_COMPLETED" and not has_sm_matrix:
        first_time = True

    with open(tmp_conf_template) as f:
        with open(tmp_conf, 'w') as g:
            tg_c_dir = os.path.dirname(tg_conf)
            tg_c_module = os.path.splitext(os.path.basename(tg_conf))[0]
            g.write(f.read().replace(TG_CONF_DIR_KEY, tg_c_dir)\
                                    .replace(TG_CONF_MODULE_KEY, tg_c_module)\
                                .replace(MUTERIA_OUTPUT_KEY, muteria_output)\
                        .replace(FIRST_TIME_MUTANT_EXECUTION_KEY, str(first_time))\
                .replace(AVOID_META_TESTS_LIST_FILE_KEY, avoid_meta_tests_list_file)\
                .replace(AVOID_META_MUTANTS_LIST_FILE_KEY, avoid_meta_mutants_list_file))

    # Run relevant mutant computation
    # Everything starting from test execution after all test generations (see cmtools/run.sh) TODO: implement it in mut_exe_conf
    if run_cmtools_run_sh_with_conf(tmp_conf, muteria_output, res) != 0:
        error_exit("cmtools/run.sh failed during mutant execution")

    # delete tmp conf
    os.remove(tmp_conf)
#~ def mutant_execution()

def summarize_data(outdir, summarized_data_dir, mutant_exec_res, \
                                                        mut_ex_prepa_data_dir):
    other_rel_to_reltests_file = os.path.join(mut_ex_prepa_data_dir, 'relevantmuts_to_relevanttests.json')
    other_rel_to_reltests = common_fs.loadJSON(other_rel_to_reltests_file)
    stored_map_file = os.path.join(mut_ex_prepa_data_dir, 'stored_test_map.json')
    stored_map = common_fs.loadJSON(stored_map_file)
    
    def get_too2relmuts(relmuts_to_reltests, toollist=None):
        res = {tool: set() for tool in toollist} if toollist is not None else {}
        for relmut, t_list in relmuts_to_reltests.items():
            for meta_t in t_list:
                toolalias, test = DriversUtils.reverse_meta_element(meta_t)
                if toollist is None:
                    if toolalias not in res:
                        res[toolalias] = set()
                else:
                    assert toolalias in toollist, "PB: toolalias ({}) not in toollist ({})".format(toolalias, toollist)
                res[toolalias].add(relmut)
        for toolalias in res:
            res[toolalias] = list(res[toolalias])
        return res
    #~ def get_too2relmuts()
    
    other_tool_to_relmuts = get_too2relmuts(other_rel_to_reltests)
    
    all_tests, fail_tests, relevant_mutants_to_relevant_tests, \
                mutants_to_killingtests, tests_to_killed_mutants = load.load (mutant_exec_res, fault_revealing=False)
    if not os.path.isdir(summarized_data_dir):
        os.mkdir(summarized_data_dir)
    
    cmp_result_file = os.path.join(summarized_data_dir, "compare_results.json")
    initial_relmuts_file = os.path.join(summarized_data_dir, "initial_relevant.json")
    rMS_file = os.path.join(summarized_data_dir, "rMS.json")
    
    # get relevant muts by tools
    # get tool list
    tinf = common_fs.loadJSON(os.path.join(mutant_exec_res, "post/RESULTS_DATA/other_copied_results/testcasesInfos.json"))
    tool2relmuts = get_too2relmuts(relevant_mutants_to_relevant_tests, toollist=list(set(tinf["CUSTOM"]) - {"custom_devtests"}))
    
    # update with stored map
    for relmut, t_list in other_rel_to_reltests.items():
        for other_meta_t in t_list:
            if other_meta_t in stored_map:
                for meta_t in stored_map[other_meta_t]:
                    toolalias, test = DriversUtils.reverse_meta_element(meta_t)
                    assert toolalias in tool2relmuts, "PB2: "
                    tool2relmuts[toolalias].append(relmut)
    for toolalias in tool2relmuts:
        tool2relmuts[toolalias] = list(set(tool2relmuts[toolalias]))    
    
    common_fs.dumpJSON(tool2relmuts, cmp_result_file, pretty=True)
    common_fs.dumpJSON(other_tool_to_relmuts, initial_relmuts_file, pretty=True)
    
    # Compute and print the relevant mutation score per tool
    all_rel_muts = set()
    devtest_rel = set()
    for talias, rellist in tool2relmuts.items():
        all_rel_muts |= set(rellist)
    for talias, rellist in other_tool_to_relmuts.items():
        all_rel_muts |= set(rellist)
        if talias.startswith("custom_devtests"):
            devtest_rel |= set(rellist)
            
    rMS = {"ALL-GENONLY": {}, "ALL-ALL": {}, "ADDITIONAL": {}}
    for talias, rellist in tool2relmuts.items():
        rMS["ALL-ALL"][talias] = len(set(rellist) | devtest_rel) * 100.0 / len(all_rel_muts)
        rMS["ALL-GENONLY"][talias] = len(rellist) * 100.0 / len(all_rel_muts)
        rMS["ADDITIONAL"][talias] = len(set(rellist) - devtest_rel) * 100.0 / len(all_rel_muts - devtest_rel)
    common_fs.dumpJSON(rMS, rMS_file, pretty=True)
#~ def summarize_data()

if __name__ == "__main__":
    main()
