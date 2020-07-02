#! /usr/bin/python

from __future__ import print_function

import os, sys
import json

def error_exit(err):
    print ("Error: "+err)
    exit (1)

def main():
    if len(sys.argv) != 2:
        error_exit("invalid number of args")
    repo = os.path.abspath(sys.argv[1])
    if not os.path.isdir(repo):
        error_exit("repo not existing")
    topdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    dest_file = os.path.join(topdir, "added_tests_map.json")
    tmp_file = os.path.join(topdir, ".tmp_file")

    for td in ['tests', 'tests.bak']:
        if not os.path.isdir(os.path.join(repo, td)):
            error_exit(td+" is not existing in repo")

    if os.system("cd {} && while read in; do nin=$(echo $in | sed 's|[0-9]\+_||g'); t_bak=$(echo $nin | sed 's|^tests/|tests.bak/|g'); test -f $t_bak || echo $in; done < tests/splittests_all.txt > {}".format(repo, tmp_file)) != 0:
        error_exit("get failed")

    p_id = os.path.basename(repo)

    obj = {}
    if os.path.isfile(dest_file):
        with open(dest_file) as f:
            obj = json.load(f)

    with open(tmp_file) as f:
        obj[p_id] = []
        for line in f:
            obj[p_id].append(line.strip())

    os.remove(tmp_file)

    with open(dest_file, 'w') as f:
        json.dump(obj, f, indent=2, sort_keys=True)

    print("# Done {}".format(p_id))

if __name__ == "__main__":
    main()


