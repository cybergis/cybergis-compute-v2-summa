# SUMMA model support in CyberGIS-Compute V2

This repo implemented support for running ensemble SUMMA models on HPC resources via CyberGIS-Compute V2.

Model developers who may want to contribute other models to CyberGIS-Compute can use this repo as an example.

For end-users can refer to the exampe notebook here: Open demo notebook with CyberGIS-Jupyter for Water (CJW) <a href="http://go.illinois.edu/cybergis-jupyter-water/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fcybergis%2Fcybergis-compute-v2-summa&urlpath=tree%2Fcybergis-compute-v2-summa%2Fsumma3_ensemble_hpc_compute-v2.ipynb&branch=main" target="_blank">HERE</a>

## mainfest.json

Supported HPCs are listed by key "supported_hpc" and default HPC by key "default_hpc";

The key "slurm_input_rules" lists ranges and limits of different slurm flags will be shown to end-users with SDK GUI; For a full list of avaiable keys see https://github.com/cybergis/cybergis-compute-core/blob/v2/src/types.ts#L70

The key "pre_processing_stage", "execution_stage" and "post_processing_stage" specify the commands (and scripts) to run in preprocessing, model execution and postprocessing stages;

The key "container" lists the singularity container to use on HPC (placed on HPC already);

Other kyes for metadata: "name", "description", "estimated_runtime"

## preprocessing.py

This is file is not being used right now. Just keep it as a placeholder for later use

## main.py

This script is called inside the singularity container in a MPI environment for executing predefined ensemble SUMMA models. Since in SUMMA each member of the ensemble is independent, the script splits all the ensemble models evenly over all MPI ranks and they run in paralel.  Rank 0 first ceates a "workers" for each MPI rank, and then each rank copies model files into its rank-specific job folder, calls pysumma to configure the local models and runs them one bye one.

## postprocessing.py

This script is used only for reproducing the experiments done in SUMMA CAMELS paper. Not for general SUMMA ensemble modelling purpose.

## "images" folder

This folder contains the dockerfile that builds the summa environment image and a singlarity DEF script that importes the docker image and converts to singularity container.

