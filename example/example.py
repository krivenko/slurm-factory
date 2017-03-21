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
job.select_nodes(sockets_per_node = 2,
                 cores_per_socket = 16,
                 threads_per_core = 2,
                 mem = 16,
                 tmp = "32G",
                 constraints = "[haswell23*7|con19x|xx89a*9]")
job.set_qos("qos")
job.set_signal(sig_num='USR1', sig_time=600, shell_only=True)
job.set_clusters(['cluster1','cluster2'])
job.set_qos("qos")

job.set_body("""
srun -n ${SLURM_NTASKS} pwd
""")
print(job.dump())

#print(slurm_version())
#print(slurm_version_info())
