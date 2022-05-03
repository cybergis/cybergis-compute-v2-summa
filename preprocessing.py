import os
SLURM_JOB_ID = os.environ.get("SLURM_JOB_ID", "")
print("SLURM_JOB_ID: {}".format(SLURM_JOB_ID))

# single process for preprocessing
# current implementation of summa in cybergis-compute does not need preprocessing
# keep as a placeholder for later use

print("preprocessing")
