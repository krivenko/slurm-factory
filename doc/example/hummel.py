#!/usr/bin/env python
#
# Example script for Hummel, a HPC cluster at the University of Hamburg, Germany

# Import SLURMJob class and submit()
from slurm_factory.job import *

# 'timedelta' represents time durations
from datetime import timedelta

# Create a job description object
job = SLURMJob(job_name = "hummel_job",         # Job name
               nodes = 4,                       # Number of requested nodes
               walltime = timedelta(hours = 6), # Wall time
               partitions = "std"               # Alternatives: 'big', 'gpu', 'spc'
               )
# Cf. SLURMJob.job_name(), SLURMJob.nodes_allocation(minnodes = ...),
#     SLURMJob.walltime() and SLURMJob.partitions()

job.tasks_allocation(ntasks_per_node = 16, # Use 16 of MPI tasks per node
                     cpus_per_task =  1    # Number of of logical cores (CPUs) per MPI task
                     )

# Set working dir for the job
job.workdir("/work/xx0000/hummel_job/workdir")

# I/O streams of the job
job.job_streams(# File for standard output stream, hummel_job-<job id>-<rank>.out
                output = "hummel_job-%j-%t.out",
                # File for standard error stream, hummel_job-<job id>-<rank>.err
                error =  "hummel_job-%j-%t.err",
                # Send contents of 'input.txt' to the standard input of the job script
                input =  "input.txt",
                # Truncate output/error files, use 'a' to open in the append mode
                open_mode = 'w')

# Send e-mail when 80 percent of time limit has reached, and when job execution ends
job.email("maxmustermann@beispiel.de", ['TIME_LIMIT_80', 'END'])

# Propagate no environment variables, as recommended by Hummel's docs
job.export_env(export_vars = 'NONE')

# The job should never be requeued under any circumstances
job.requeue(False)

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
