# SUMMA model support in CyberGIS-Compute V2

This repo implemented support for running ensemble SUMMA models on HPC resources via CyberGIS-Compute V2.

## mainfest.json

Supported HPCs are listed by key "supported_hpc" and default HPC by key "default_hpc";

The key "slurm_input_rules" lists ranges and limits of different slurm flags will be shown to end-users with SDK GUI; For a full list of avaiable keys see https://github.com/cybergis/cybergis-compute-core/blob/v2/src/types.ts#L70

The key "pre_processing_stage", "execution_stage" and "post_processing_stage" specify the commands (and scripts) to run in preprocessing, model execution and postprocessing stages;

The key "container" lists the singularity container to use on HPC (placed on HPC already);

Other kyes for metadata: "name", "description", "estimated_runtime"



Open demo notebook with CyberGIS-Jupyter for Water (CJW) <a href="http://go.illinois.edu/cybergis-jupyter-water/hub/user-redirect/git-pull?repo=https%3A%2F%2Fgithub.com%2Fcybergis%2Fcybergis-compute-v2-summa&urlpath=tree%2Fcybergis-compute-v2-summa%2Fsumma3_ensemble_hpc_compute-v2.ipynb&branch=main" target="_blank">HERE</a>
