#!/bin/bash

#SBATCH --job-name=trajectory-taubench  
#SBATCH -N 1            # number of nodes
#SBATCH -c 32           # number of cores 
#SBATCH -t 0-4:00:00   # time in d-hh:mm:ss
#SBATCH -p htc       # QOS
#SBATCH -q public       # QOS
#SBATCH --gpus=a30:1
#SBATCH --mem=64G
#SBATCH --mail-type=ALL # Send an e-mail when a job starts, stops, or fails
#SBATCH --export=NONE   # Purge the job-submitting shell environment
#SBATCH --account=grp_cbaral

source activate taubench

cd /home/rksing18/applied/tau-bench
bash sol_run.sh