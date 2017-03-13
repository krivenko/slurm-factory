import sys
sys.path = ['..'] + sys.path

from slurm_factory import *

job = SLURMJob(name = "hello_world")
print(job.dump())
