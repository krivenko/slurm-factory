#!/usr/bin/env python
#
# Example script for Stampede, a Dell PowerEdge cluster at
# the Texas Advanced Computing Center

# Import SLURMJob class and submit()
from slurm_factory.job import *

# 'timedelta' represents time durations
from datetime import timedelta

# Create a job description object
job = SLURMJob(job_name = "stampede_job",       # Job name
               nodes = 4,                       # Number of requested nodes
               walltime = timedelta(hours = 6), # Wall time
               partitions = "normal"            # Other options are 'development', 'largemem', ...
               )
# Cf. SLURMJob.job_name(), SLURMJob.nodes_allocation(minnodes = ...),
#     SLURMJob.walltime() and SLURMJob.partitions()

job.tasks_allocation(ntasks_per_node = 16, # Use 16 of MPI tasks per node
                     cpus_per_task =  2    # Number of of logical cores (CPUs) per MPI task
                     )

# Set working dir for the job
job.workdir("/home1/12345/tg000000/stampede_job/workdir")

# Charge job to the specified project/allocation number
job.account('projectnumber')

# I/O streams of the job
job.job_streams(# File for standard output stream, stampede_job-<job id>-<rank>.out
                output = "stampede_job-%j-%t.out",
                # File for standard error stream, stampede_job-<job id>-<rank>.err
                error =  "stampede_job-%j-%t.err",
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
