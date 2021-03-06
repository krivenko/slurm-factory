#!/usr/bin/env python
#
# Example script for Edison, a Cray XC30 cluster at
# the National Energy Research Scientific Computing Center

# Import SLURMJob class and submit()
from slurm_factory.job import *

# 'timedelta' represents time durations
from datetime import timedelta

# Create a job description object
job = SLURMJob(job_name = "edison_job",         # Job name
               nodes = 4,                       # Number of requested nodes
               walltime = timedelta(hours = 6), # Wall time
               partitions = "regular"           # Use 'debug' for small, short test runs
               )
# Cf. SLURMJob.job_name(), SLURMJob.nodes_allocation(minnodes = ...),
#     SLURMJob.walltime() and SLURMJob.partitions()

job.tasks_allocation(ntasks_per_node = 24, # Use 32 of MPI tasks per node
                     cpus_per_task =  2    # Number of of logical cores (CPUs) per MPI task
                     )

# Set working dir for the job
job.workdir("/global/homes/j/johndoe/edison_job/workdir")

# File system licenses
job.licenses(['SCRATCH', 'project'])

# Charge this job to the NERSC repository 'repo'
job.account('repo')

# I/O streams of the job
job.job_streams(# File for standard output stream, edison_job-<job id>-<rank>.out
                output = "edison_job-%j-%t.out",
                # File for standard error stream, edison_job-<job id>-<rank>.err
                error =  "edison_job-%j-%t.err",
                # Send contents of 'input.txt' to the standard input of the job script
                input =  "input.txt",
                # Truncate output/error files, use 'a' to open in the append mode
                open_mode = 'w')

# Send e-mail when 80 percent of time limit has reached, and when job execution ends
job.email("johndoe@example.com", ['TIME_LIMIT_80', 'END'])

job.export_env(# Export the current environment variables into the batch job environment
               export_vars = 'ALL',
               # In addition to that set OMP_NUM_THREADS variable to 1
               set_vars = {'OMP_NUM_THREADS' : 1})

# Request premium Quality of Service
job.qos("premium")

# Core specialization: isolate 2 cores on each node to run OS tasks
job.specialized(cores = 2)

# Add body to the job script
job.set_body("""
echo "Working in $(pwd) on host $(hostname)"
echo "Local date/time is $(date)"

srun -n ${SLURM_NTASKS} ./my_prog
""")

# Print generated job file
print(job.dump())

# Submit job
jobid = submit(job)
print("Submitted Job ID: %i" % jobid)
