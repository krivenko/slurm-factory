#!/usr/bin/env python

# Scan a range of parameter 'x' submitting one job per value

# Import SLURMJob class and submit()
from slurm_factory.job import *

# NumPy
import numpy as np

# Values of 'x': 0, 0.1, 0.2, ..., 1.0
x_values = np.linspace(0, 1.0, 11)

# List of jobs to be submitted
jobs = []

# Create jobs
for x in x_values:
    job = SLURMJob(job_name = "run_x_%.1f" % x,        # Job name
                   nodes = 4,                          # Number of requested nodes
                   walltime = timedelta(minutes = 10)  # Wall time
                  )
    # I/O streams of the job
    job.job_streams(# File for standard output stream
                    output = "scan_x.out",
                    # File for standard error stream
                    error =  "scan_x.err",
                    # Open the files in the append mode
                    # to collect output from all jobs in one place
                    open_mode = 'a')
    # Add body to the script
    job.set_body("srun -n ${SLURM_NTASKS} ./scan_x %.1f" % x)

    # Append job to the list
    jobs.append(job)

# Submit jobs and collect their IDs
jobids = [submit(job) for job in jobs]

print("Job IDs:")
print(jobids)
