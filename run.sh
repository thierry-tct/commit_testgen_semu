#! /bin/bash

# ./run.sh <id> <CPU count>

set -u

error_exit()
{
    echo "ERROR: $1"
    exit 1
}

# id
# cpu
# root
# expensive

only_gentests=""
if [ $# = 3 ]; then
    [ "$3" = "--only_gentests" ] || error_exit "3rd para must be --only_gentests"
    only_gentests="--only_gentests"
else
    [ $# = 2 ] || error_exit "expect 2 argument (id and number of cpu). passed $# agrs"
fi

mountfold=$(readlink -f $1)
id=$2
CPU=1

####

TOPDIR=$(dirname $(readlink -f $0))
workspace_dir=$(readlink -f $mountfold/executions/workspace/$id)
tmpcmd=in_docker_run.sh
in_docker_script=$workspace_dir/$tmpcmd

echo '
#! /bin/bash
set -u

ogt=''
if [ $# -eq 1 ]; then
    ogt=$1
    echo ">>>>> ogt is $ogt"
fi

# Temporary
curdir=`pwd`
cd /home/klee-semu/klee_build \
	&& sudo git clone https://github.com/thierry-tct/klee-semu /tmp/klee-semu \
	&& sudo cp /tmp/klee-semu/lib/Mutation/*.{cpp,h} ../klee_src/lib/Mutation \
	&& sudo rm -rf /tmp/klee-semu \
	&& sudo make -j2
[ $? -ne 0 ] && { echo "ERROR: Semu update failed!"; exit 1; }



cd $curdir

# Actual execution
pip install -U git+https://github.com/muteria/muteria
#export COREUTILS_TEST_EXPENSIVE=off
#export COREUTILS_TEST_ROOT=on
export COREUTILS_TEST_ROOT=1
TOPDIR=$(dirname $(readlink -f $0))
conf_py=$TOPDIR/ctrl/conf.py
runner=/work_scripts/main.py
outdir=/work_data/$(basename $TOPDIR)
python $runner $outdir $conf_py $ogt
exit $?
' > $in_docker_script

chmod +x $in_docker_script

# RUN DOCKER
cd $mountfold || error_exit "cd failed to mountfold"
# Check this for ptrace user uid problem: https://seravo.fi/2019/align-user-ids-inside-and-outside-docker-with-subuser-mapping
# Also: https://github.com/rocker-org/rocker/wiki/Sharing-files-with-host-machine
#sudo docker run -it --rm --cap-add=SYS_PTRACE --security-opt seccomp=unconfined -security-opt apparmor=unconfined --mount type=bind,src=$(pwd),dst=/work --user 1000:1000 --privileged \
sudo docker run -it --rm --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
                                        --mount type=bind,src=$(pwd),dst=/work \
                                        --mount type=bind,src=$TOPDIR,dst=/work_scripts \
					--mount type=bind,src=$(readlink -f $TOPDIR/../DATA),dst=/work_data \
                                        --user 1000:1000 --privileged \
									    --cpus=${CPU} maweimarvin/cm bash -c "cd /work/executions/workspace/$id && bash ./${tmpcmd} $only_gentests"

# Copy info about changed lines
#test -f $workspace_dir/res/klee_changed_src.summary \
#                    || cp $mountfold/shadow-test/coreutils/$id/klee_changed_src.summary $workspace_dir/res/klee_changed_src.summary \
#                    || error_exit "failed to copy change lines summary"

rm $in_docker_script || error_exit "failed to remove in_docker_script"

echo "ALL DONE!"
