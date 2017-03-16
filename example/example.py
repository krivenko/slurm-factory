import sys
sys.path = ['..'] + sys.path

from datetime import timedelta
from slurm_factory import *

job = SLURMJob(name = "hello_world")

job.set_partitions("debug")
job.set_time(timedelta(minutes = 19, seconds = 12), timedelta(minutes = 15))
job.set_workdir("./job_dir")
job.set_job_streams(r"slurm-%x-%8j.out", r"slurm-%x-%8j.err", "/dev/random", 'a')
job.set_email("slurm-user@example.com", 'END')
job.set_constraint("haswell23*4")
job.set_constraint("haswell23,con19x,xx89a")
job.set_constraint("haswell23*2|con19x|xx89a*7")
job.set_constraint("haswell23*4&con19x&xx89a*7")
job.set_constraint("[haswell23*7|con19x|xx89a*9]")
job.set_signal(sig_num='USR1', sig_time=600, shell_only=True)

job.set_body("""
srun -n ${SLURM_NTASKS} pwd
""")
print(job.dump())

#from slurm_factory.job import valid_filename_patterns
#print(valid_filename_patterns('\\%sdsd'))
#print(valid_filename_patterns(r'%0ksd'))
#print(valid_filename_patterns(r'%12kdsd'))
#print(valid_filename_patterns(r'%0usd%11urf'))
#print(valid_filename_patterns(r'%12usd%17urf'))

#print(slurm_version())
#print(slurm_version_info())
