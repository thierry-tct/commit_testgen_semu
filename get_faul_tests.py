import os
import muteria.common.matrices as common_matrices
from muteria.drivers import DriversUtils

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
		for used_c_id inid_with_many_bugs[c_id]:
			outdir = os.path.join(out_top_dir, used_c_id)
			_get_fault_tests (cm_corebench_scripts_dir, used_c_id, conf_py, in_res_data_dir, outdir)
	else:
		outdir = os.path.join(out_top_dir, c_id)
		_get_fault_tests (cm_corebench_scripts_dir, c_id, conf_py, in_res_data_dir, outdir)
#~ def get_commit_fault_tests ()
	
def _get_fault_tests (cm_corebench_scripts_dir, c_id, conf_py, in_res_data_dir, outdir):
	if not os.path.isdir(outdir):
		os.mkdir(outdir)
	
	exe_dir=os.path.join(cm_corebench_scripts_dir, "bug_fixing_exes", c_id)
	exe_file=os.listdir(os.path.join(exe_dir, "old"))
	if len(exe_file) != 1:
		error_exit ("not one file for old")
	exe_file = exe_file[0]
	
	fail_test_execution=os.path.join(outdir, "fail_test_checking")
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

	print("# info: running old ...")
	version = "old"
	custom_exe = os.path.join(exe_dir, version, exe_file)
	DriversUtils.execute_and_get_retcode_out_err("muteria", ["--config", conf_py, "--lang", "c", "customexec"], 
						     stdin="{}\n{}\n{}\n{}\n".format("tests", 
										   os.path.join(fail_test_execution, version),
										  '{"src/'+exe_file+'": "'+custom_exe+'"}',
										   test_list_file)
						     )
	print("# info: running new ...")
	version = "new"
	custom_exe = os.path.join(exe_dir, version, exe_file)
	DriversUtils.execute_and_get_retcode_out_err("muteria", ["--config", conf_py, "--lang", "c", "customexec"], 
						     stdin="{}\n{}\n{}\n{}\n".format("tests", 
										   os.path.join(fail_test_execution, version),
										  '{"src/'+exe_file+'": "'+custom_exe+'"}',
										   test_list_file)
						     )

	os.remove(test_list_file)
	 
	import muteria.common.matrices as common_matrices
	_, old_o = list(common_matrices.OutputLogData(os.path.join(fail_test_execution, 'old', 'program_output.json').get_zip_objective_and_data())[0]
	_, new_o = list(common_matrices.OutputLogData(os.path.join(fail_test_execution, 'new', 'program_output.json').get_zip_objective_and_data())[0]
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
