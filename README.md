# deltaTG commit testing tool

deltaTG is a commit change testing tool that generates test inputs to test commit's changed code.
deltaTG makes use of differential symolic execution and implements a model that controls the propagation of the program state difference between the pre and post-commit version, in a way that balance the cost and effectiveness.

deltaTG is implemented based on [SEMu](https://github.com/thierry-tct/KLEE-SEMu) and [Muteria](https://github.com/muteria/muteria).

# USAGE

deltaTG runs into a Docker container where SEMu and Muteria are setup.

In order to generate test for a given program, the following procedure must be followed:

1. Create an execution configuration file, based on Muteria configuration format as described [here](https://github.com/muteria/example_c/blob/master/ctrl/conf_shadow_semu.py).

2. Put the configuration into the file `<path-to-workspace>/ctrl/conf.py`.

3. Execute deltaTG with the following command from this repository root:
``` bash
./deltaTG <path-to-workspace> 
```
The execution will create a compressed folder `<path-to-workspace>/DATA/muteria_output/latest/testscases_workdir/<semu-configuration-folder>/tests_files.tar.gz`. The generated tests are the `.ktest` file in there. 
`.ktest` test format is [KLEE](https://github.com/klee/klee) test format and can be executed using `klee-replay` tool from KLEE.

