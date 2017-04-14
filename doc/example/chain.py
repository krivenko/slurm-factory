#!/usr/bin/env python
#
# Example script showing how to use dependencies and job chains

# We want to submit 8 jobs with the following dependency graph:
#
#           preprocessing
#           /           \
#        job_a1         job_b1
#           |            |
#        job_a2         job_b2
#           |            |
#        job_a3         job_b3
#           \            /
#           postprocessing
#
# 'preprocessing' will start first. As soon as it is successfully completed
# two job chains will start: 'job_a1' -> 'job_a2' -> 'job_a3' and
# 'job_b1' -> 'job_b2' -> 'job_b3'.
# Within one chain, every next job starts when the previous one is completed.
# 'postprocessing' depends on both 'job_a3' and 'job_b3'.

# Import SLURMJob class, chain_jobs() and submit()
from slurm_factory.job import *

# 'timedelta' represents time durations
from datetime import timedelta

# This job will pre-process data
preprocessing = SLURMJob(job_name = "preprocessing",        # Job name
                         nodes = 1,                         # Number of requested nodes
                         walltime = timedelta(minutes = 20) # Wall time
                        )

# Jobs of chain A
jobs_a = [SLURMJob(job_name = "job_a" + str(n),
                   nodes = 8,
                   walltime = timedelta(hours = 6)
                   ) for n in (1,2,3)]

# Jobs of chain B
jobs_b = [SLURMJob(job_name = "job_b" + str(n),
                   nodes = 8,
                   walltime = timedelta(hours = 6)
                   ) for n in (1,2,3)]

# Form chains (set dependencies between jobs)
chain_jobs(jobs_a, 'afterok')
chain_jobs(jobs_b, 'afterok')

# This job will post-process computation results
postprocessing = SLURMJob(job_name = "postprocessing",       # Job name
                          nodes = 1,                         # Number of requested nodes
                          walltime = timedelta(minutes = 30) # Wall time
                         )

# 'job_a1' and 'job_b1' must depend on 'preprocessing'
jobs_a[0].add_dependencies('afterok', [preprocessing])
jobs_b[0].add_dependencies('afterok', [preprocessing])

# 'postprocessing' depends on 'job_a3' and 'job_b3'
postprocessing.add_dependencies('afterok', [jobs_a[2], jobs_b[2]])

# Uncomment to make 'postprocessing' start when AT LEAST ONE of
# 'job_a3' and 'job_b3' is successfully completed.
## postprocessing.dependencies_require_any(True)

# Submit everything
for job in [preprocessing] + jobs_a + jobs_b + [postprocessing]:
    submit(job)
