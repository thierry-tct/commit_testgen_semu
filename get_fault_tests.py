import os
import shutil
import muteria.common.matrices as common_matrices
import muteria.common.fs as common_fs
from muteria.drivers import DriversUtils

from muteria.drivers.testgeneration.tools_by_languages.c.semu.semu import TestcasesToolSemu

def error_exit(err):
    print ("error: "+err)
    exit(1)
#~ def error_exit()
	
id_with_many_bugs = {
                        'cr-5': ['cr-5', 'cr-16'],
                        'cr-12': ['cr-12', 'cr-17'],
                    }
                    
def get_commit_fault_tests (cm_corebench_scripts_dir, c_id, conf_py, in_res_data_dir, out_top_dir):
    if c_id in id_with_many_bugs:
        for used_c_id in id_with_many_bugs[c_id]:
            outdir = os.path.join(out_top_dir, used_c_id)
            _get_fault_tests (cm_corebench_scripts_dir, used_c_id, conf_py, in_res_data_dir, outdir)
    else:
        outdir = os.path.join(out_top_dir, c_id)
        _get_fault_tests (cm_corebench_scripts_dir, c_id, conf_py, in_res_data_dir, outdir)
#~ def get_commit_fault_tests ()
	
def _get_fault_tests (cm_corebench_scripts_dir, c_id, conf_py, in_res_data_dir, outdir, get_difference=True):
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
	
    exe_dir=os.path.join(cm_corebench_scripts_dir, "bug_fixing_exes", c_id)
    exe_file=os.listdir(os.path.join(exe_dir, "old"))
    if len(exe_file) != 1:
        error_exit ("not one file for old")
    exe_file = exe_file[0]
	
    fail_test_execution=os.path.join(outdir, "fail_test_checking")
    if os.path.isdir(fail_test_execution):
        shutil.rmtree(fail_test_execution)
    if not os.path.isdir(fail_test_execution):
        os.makedirs(fail_test_execution)

    bug_finding_tests_list = os.path.join(fail_test_execution, "fault_reveling_tests.txt")

	# temporary
    test_list_file = os.path.join(fail_test_execution, "test_list.tmp")
	
    pass_fail_matrix = os.path.join(in_res_data_dir, "matrices", "PASSFAIL.csv")

    pf_mat = common_matrices.ExecutionMatrix(filename=pass_fail_matrix)
    with open(test_list_file, "w") as f:
        for test in pf_mat.get_nonkey_colname_list():
            f.write(test+"\n")
    
    nohash = ['--nohashoutlog']
    #nohash = []
    
    print("# info: running bug-fix old ...")
    version = "old"
    custom_exe = os.path.join(exe_dir, version, exe_file)
    stdin = "{}\n{}\n{}\n{}\n".format("tests", os.path.join(fail_test_execution, version),
                                      '{"src/'+exe_file+'": "'+custom_exe+'"}',
                                      test_list_file)
    if os.system(" ".join(["printf", "'"+stdin+"'", "|", "muteria", "--config", conf_py, "--lang", "c", "customexec"]+nohash)) != 0:
        assert False, "bug-fix old failed"
        
    print("# info: running bug-fix new ...")
    version = "new"
    custom_exe = os.path.join(exe_dir, version, exe_file)
    stdin = "{}\n{}\n{}\n{}\n".format("tests", os.path.join(fail_test_execution, version),
                                      '{"src/'+exe_file+'": "'+custom_exe+'"}',
                                        test_list_file)
    if os.system(" ".join(["printf", "'"+stdin+"'", "|", "muteria", "--config", conf_py, "--lang", "c", "customexec"]+nohash)) != 0:
        assert False, "bug-fix new failed"
	
    if get_difference:
        # get differences in bug introducing
        ## get diff exe file
        diff_exe_dir = os.path.join(os.path.dirname(in_res_data_dir), 'code_build_workdir')
        map_file_ = os.path.join(diff_exe_dir, 'files_map')
        map_ = common_fs.loadJSON(map_file_)
        diff_exe_file = None
        for f, dest in map_.items():
            if os.path.basename(f) == exe_file:
                assert diff_exe_file is None, "multiple exefile found in defference"
                diff_exe_file = os.path.join(diff_exe_dir, dest)
                assert os.path.isfile(diff_exe_file), "missing diff_exe_file: "+diff_exe_file
        assert diff_exe_file is not None, "diff exe file not found"
        ## Execution
        diff_test_execution=os.path.join(outdir, "diff_test_checking")
        diff_finding_tests_list = os.path.join(diff_test_execution, "diff_reveling_tests.txt")
        if os.path.isdir(diff_test_execution):
            shutil.rmtree(diff_test_execution)
        if not os.path.isdir(diff_test_execution):
            os.makedirs(diff_test_execution)

        print("# info: running bug-intro old ...")
        version = "old"
        stdin = "{}\n{}\n{}\n{}\n".format("tests", os.path.join(diff_test_execution, version),
                                          '{"src/'+exe_file+'": "'+diff_exe_file+'"}',
                                          test_list_file)
        if os.system(" ".join(["printf", "'"+stdin+"'", "|", "KLEE_CHANGE_RUNTIME_SET_OLD_VERSION=on", "muteria", "--config", conf_py, "--lang", "c", "customexec"]+nohash)) != 0:
            assert False, "bug-intro old failed"

        print("# info: running bug-intro new ...")
        version = "new"
        stdin = "{}\n{}\n{}\n{}\n".format("tests", os.path.join(diff_test_execution, version),
                                          '{"src/'+exe_file+'": "'+diff_exe_file+'"}',
                                            test_list_file)
        if os.system(" ".join(["printf", "'"+stdin+"'", "|", "muteria", "--config", conf_py, "--lang", "c", "customexec"]+nohash)) != 0:
            assert False, "bug-intro new failed"

    os.remove(test_list_file)
	 
    _, old_o = list(common_matrices.OutputLogData(os.path.join(fail_test_execution, 'old', 'program_output.json')).get_zip_objective_and_data())[0]
    _, new_o = list(common_matrices.OutputLogData(os.path.join(fail_test_execution, 'new', 'program_output.json')).get_zip_objective_and_data())[0]
    assert len(old_o) == len(new_o)
    diff_tests = []
    for tc in old_o:
        eq = common_matrices.OutputLogData.outlogdata_equiv(old_o[tc], new_o[tc])
        assert eq is not None, "PB"
        if not eq:
            diff_tests.append(tc)
    with open(bug_finding_tests_list, "w") as f:
	    for tc in diff_tests:
	        f.write(tc+"\n")
    print("# list printed")
#~ def _get_fault_tests ()
			
def fault_analysis (cm_corebench_scripts_dir, c_id, conf_py, in_muteria_outdir, out_top_dir):
    if not os.path.isdir(out_top_dir):
        os.mkdir(out_top_dir)
		
    in_res_data_dir = os.path.join(in_muteria_outdir, 'latest', 'RESULTS_DATA')
    testtools_workdir = os.path.join(in_muteria_outdir, 'latest', 'testscases_workdir')
    pass_fail_matrix = os.path.join(in_res_data_dir, "matrices", "PASSFAIL.csv")

    pf_mat = common_matrices.ExecutionMatrix(filename=pass_fail_matrix)
    test_list = list(pf_mat.get_nonkey_colname_list())
    #semu_tool_dirs = [d for d in os.listdir(testtools_workdir) if d.startswith('semu_cmp-')]
    
    # get fault tests
    get_commit_fault_tests(cm_corebench_scripts_dir, c_id, conf_py, in_res_data_dir, out_top_dir)
    
    # get test to timestamp
    test_timestamp_file = os.path.join(out_top_dir, "test_to_timestamp.json")
    test2timestamp = {}
    ## get tests by tools
    tools2tests = {}
    for test in test_list:
        alias, _ = DriversUtils.reverse_meta_element(test)
        # XXX: only SEMU
        if not alias.startswith('semu_cmp-'):
            continue
        if alias not in tools2tests:
            tools2tests[alias] = set()
        tools2tests[alias].add(test)
    ## untar tests dir
    for alias, tests in tools2tests.items():
        d = os.path.join(testtools_workdir, alias)
        assert os.path.isdir(d), "test tool dir "+d+" missing for alias "+ alias
        test_tar = os.path.join(d, 'tests_files.tar.gz')
        es = common_fs.TarGz.decompressDir(test_tar)
        assert es is None, "decompress error: "+es
        tests_files = os.path.join(d, 'tests_files')
        assert os.path.isdir(tests_files), "dir missing after decompress"
        for test in tests:
            _, simple_test = DriversUtils.reverse_meta_element(test)
            gt = TestcasesToolSemu._get_generation_time_of_test(simple_test, tests_files)
            test2timestamp[test] = gt
        shutil.rmtree(tests_files)
    
    common_fs.dumpJSON(test2timestamp, test_timestamp_file, pretty=True)
#~ def fault_analysis ()
