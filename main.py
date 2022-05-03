import os
SLURM_JOB_ID = os.environ.get("SLURM_JOB_ID", "")
prinrt("SLURM_JOB_ID: {}".format(SLURM_JOB_ID))


# load libs
import json
import os
from pathlib import Path
import traceback
import numpy as np
from mpi4py import MPI
import subprocess
import pysumma as ps
# init mpi env
comm = MPI.COMM_WORLD
# rank (0-based index for each mpi process)
rank = comm.Get_rank()
# size of mpi cluster
size = comm.Get_size()
hostname = MPI.Get_processor_name()
print("{}/{}: {}".format(rank, size, hostname))

# path to "executable" folder inside container
job_folder_path = os.environ["executable_folder"]
instance = "summa"
# path to "data" folder inside container
instance_path = os.environ["data_folder"]

# rank 0 to create a "workers" folder in the "executable" folder
workers_folder_name = "workers"
workers_folder_path = os.path.join(job_folder_path, workers_folder_name)
if rank == 0:
   os.system("mkdir -p {}".format(workers_folder_path))
comm.Barrier()
# each rank to create a <instance>_<X> in "workers" folder and copy model files
new_instance_path = os.path.join(workers_folder_path, instance + "_{}".format(rank))
os.system("cp -rf {} {}".format(instance_path, new_instance_path))
# each rank to call installTest_local.sh to localize SUMMA model
# make sure installTest_local.sh has the right permission to run
subprocess.run(
    ["chmod", "+x", "./installTestCases_local.sh"], cwd=new_instance_path,
)
subprocess.run(
    ["./installTestCases_local.sh"], cwd=new_instance_path,
)
# chech if "summa_options.json" exists (contains parameters for ensemble runs)
json_path = os.path.join(new_instance_path, "summa_options.json")
ensemble_flag = True
if not os.path.isfile(json_path):
    ensemble_flag = False
# replace path place holders (<PWD>, <BASEDIR>, BASEDIR) in "summa_options.json" with real values inside container
try:
    with Path(json_path) as f:
        f.write_text(f.read_text().replace('<PWD>', new_instance_path)
        .replace('PWD', new_instance_path)
        .replace('<BASEDIR>', new_instance_path)
        .replace('BASEDIR', new_instance_path))
    with open(json_path) as f:
        options_dict = json.load(f)
except Exception as ex:
    print("{}/{}: Error in parsing summa_options.js: {}".format(rank, size, ex))
    options_dict = {}
 
# group config_pairs
options_list = [(k,v) for k,v in options_dict.items()]
options_list.sort()
groups = np.array_split(options_list, size)
# assign to process by rank
config_pair_list = groups[rank].tolist()
print("{}/{}: {}".format(rank, size, str(config_pair_list)))
# if not a ensemble run, assign a fake config_pair to rank 0
if rank == 0 and (not ensemble_flag):
    config_pair_list = [("_single_run", {})]
# file manager path
file_manager = os.path.join(new_instance_path, "settings/file_manager.txt")
print("API submitted file_manager {}".format(file_manager))
executable = "/usr/bin/summa.exe"
#if len(config_pair_list) == 0:
#    config_pair_list = [("_test", {})]

# each rank to process the ensemble run assigned
for config_pair in config_pair_list:
    try:
        name = config_pair[0]
        config = config_pair[1]
        print(name)
        print(config)
        if "file_manager" in config:
            file_manager = config["file_manager"]
            print("Get file_manager form summa_options.json {}".format(file_manager))
        
        # init with file_manager
        ss = ps.Simulation(executable, file_manager)
        print("Init with file_manager: {}".format(file_manager))
        # apply config
        ss.apply_config(config)
        # change output folder
        ss.manager["outputPath"].value = ss.manager["outputPath"].value.replace(new_instance_path, os.environ["result_folder"])
        os.system("mkdir -p {}".format(ss.manager["outputPath"].value))
        # write configs in mem to disk
        ss.manager.write()
        # run model
        ss.run('local', run_suffix=name)
        # print debug info
        #print(ss.stdout) 
        
    except Exception as ex:
        print("Error in ({}/{}) {}: {}".format(rank, size, name, str(config)))
        print(ex)
        print(traceback.format_exc())
comm.Barrier()
print("Done in {}/{} ".format(rank, size))

