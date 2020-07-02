import os
id_with_many_bugs = {
                        'cr-5': ['cr-5', 'cr-16'],
                        'cr-12': ['cr-12', 'cr-17'],
                    }
                    
def get_fault_tests (cm_corebench_scripts_dir, c_id, conf_py, outdir):
	if not os.path.isdir(outdir):
		os.mkdir(outdir)
	
	####
	p_id=$(basename $TOPDIR)
	exe_dir=/work/executions/cm_corebench_scripts/bug_fixing_exes/$p_id
	exe_file=$(ls $exe_dir/old)

	fail_test_execution=$collect/fail_test_checking
	test -d $fail_test_execution || mkdir $fail_test_execution

	bug_finding_tests_list=$fail_test_execution/fault_reveling_tests.txt

	# temporary
	test_list_file=$TOPDIR/test_list.tmp

	cat $pass_fail_matrix | head -n1 | tr " " "\n" | sed 1d > $test_list_file || error_exit "failed to get testlist"

	custom_exe=$exe_dir/old/$exe_file
	echo "tests
	$fail_test_execution/old
	{\"src/$(basename $custom_exe)\": \"$custom_exe\"}
	$test_list_file" | muteria --config $conf_py --lang c customexec || error_exit "run failed"

	custom_exe=$exe_dir/new/$exe_file
	echo "tests
	$fail_test_execution/new
	{\"src/$(basename $custom_exe)\": \"$custom_exe\"}
	$test_list_file" | muteria --config $conf_py --lang c customexec || error_exit "run failed"

	rm -f $test_list_file
	 
	echo "import muteria.common.matrices as common_matrices" > $test_list_file
	echo "_, old_o = list(common_matrices.OutputLogData(\"$fail_test_execution/old/program_output.json\").get_zip_objective_and_data())[0]" >> $test_list_file
	echo "_, new_o = list(common_matrices.OutputLogData(\"$fail_test_execution/new/program_output.json\").get_zip_objective_and_data())[0]" >> $test_list_file
	echo "assert len(old_o) == len(new_o)" >> $test_list_file
	echo "diff_tests = []" >> $test_list_file
	echo "for tc in old_o:" >> $test_list_file
	echo "    eq = common_matrices.OutputLogData.outlogdata_equiv(old_o[tc], new_o[tc])" >> $test_list_file
	echo "    assert eq is not None, \"PB\"" >> $test_list_file
	echo "    if not eq:" >> $test_list_file
	echo "        diff_tests.append(tc)" >> $test_list_file
	echo "with open(\"$bug_finding_tests_list\", \"w\") as f:" >> $test_list_file
	echo "    for tc in diff_tests:" >> $test_list_file
	echo "        f.write(tc+\"\n\")" >> $test_list_file
	echo "print(\"# list printed\")" >> $test_list_file

	python $test_list_file || error_exit "python failed"

	rm -f $test_list_file
#~ def get_fault_tests ()
