import sys
sys.path = ['..'] + sys.path

from datetime import timedelta
from slurm_factory import *

job = SLURMJob(name = "hello_world")
job.set_walltime(seconds = 45)
print(job.dump())
job.set_walltime(minutes = 35, seconds = 12)
print(job.dump())
job.set_walltime(hours = 7, minutes = 12, seconds = 55)
print(job.dump())
job.set_walltime(days = 4, hours = 7, minutes = 12, seconds = 55)
print(job.dump())

job.set_body("""
srun -n ${SLURM_NTASKS} /usr/bin/ls
""")
print(job.dump())
