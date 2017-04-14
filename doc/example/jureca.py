#!/usr/bin/env python
#
# Example script for JURECA (Juelich Research on Exascale Cluster Architectures)

# Import SLURMJob class and submit()
from slurm_factory.job import *

# 'timedelta' represents time durations
from datetime import timedelta

# Create a job description object
job = SLURMJob(job_name = "jureca_job",         # Job name
               nodes = 4,                       # Number of requested nodes
               walltime = timedelta(hours = 6)  # Wall time
               )
# Cf. SLURMJob.job_name(), SLURMJob.nodes_allocation(minnodes = ...),
#     SLURMJob.walltime() and SLURMJob.partitions()

# Standard partition for batch jobs
job.partitions(["batch"])

# Alternative partition/GRES specifications
# 256 GiB main memory:
job.constraints(gres = "mem256")
# 512 GiB main memory
job.partitions(["mem512"])
job.constraints(gres = "mem512")
# 2 GPUs per node
job.partitions(["gpus"])
job.constraints(gres = [("gpu",2)])
# 4 GPUs per node
job.partitions(["gpus"])
job.constraints(gres = [("gpu",4)])
# 1 TiB main memory
job.partitions(["mem1024"])
job.constraints(gres = "mem1024")
# 1 TiB main memory and 2 GPUs per node
job.partitions(["vis"])
job.constraints(gres = ["mem1024", ("gpu",2)])

# Use 48 of MPI tasks per node
job.tasks_allocation(ntasks_per_node = 48)

# Set working dir for the job
job.workdir("/homec/hhh00/hhh000/jureca_job/workdir")

# I/O streams of the job
job.job_streams(# File for standard output stream, jureca_job-<job id>-<rank>.out
                output = "jureca_job-%j-%t.out",
                # File for standard error stream, jureca_job-<job id>-<rank>.err
                error =  "jureca_job-%j-%t.err",
                # Send contents of 'input.txt' to the standard input of the job script
                input =  "input.txt",
                # Truncate output/error files, use 'a' to open in the append mode
                open_mode = 'w')

# Send e-mail when 80 percent of time limit has reached, and when job execution ends
job.email("maxmustermann@beispiel.de", ['TIME_LIMIT_80', 'END'])

job.export_env(# Export the current environment variables into the batch job environment
               export_vars = 'ALL',
               # In addition to that set OMP_NUM_THREADS variable to 1
               set_vars = {'OMP_NUM_THREADS' : 1})

# Submit job in the held state
job.hold(True)

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
