import sys
sys.path = ['..'] + sys.path

from datetime import timedelta, date, time, datetime
from slurm_factory import *

job = SLURMJob(name = "hello_world")

job.set_partitions("debug")
job.set_time(timedelta(minutes = 19, seconds = 12), timedelta(minutes = 15))
job.set_nnodes(16, 32, use_min_nodes = True)
job.set_specialized(threads = 4)
job.set_workdir("./job_dir")
job.set_job_streams(r"slurm-%x-%8j.out", r"slurm-%x-%8j.err", "/dev/random", 'a')
job.set_email("slurm-user@example.com", 'END')
job.select_nodes(sockets_per_node = 2,
                 cores_per_socket = 16,
                 threads_per_core = 2,
                 mem = 16,
                 tmp = "32G",
                 constraints = "[haswell23*7|con19x|xx89a*9]",
                 gres = ['gpu', ('mic', 1), ('gpu', 2, 'kepler')],
                 gres_enforce_binding = True,
                 contiguous = True,
                 nodelist = ['node7', 'node[11-15]'],
                 nodefile = "nodes.txt",
                 exclude = ['node[17-19]', 'node20'])
job.set_signal(sig_num='USR1', sig_time=600, shell_only=True)
job.set_reservation("user_23")
job.set_qos("qos")
job.set_account("myaccount")
job.set_licenses([('foo',4),'bar'])
job.set_deadline(datetime(2017, 8, 11, 10, 8))
job.defer_allocation(immediate = True, begin = timedelta(minutes = 15, days = 23))
job.set_clusters(['cluster1','cluster2'])

job.set_body("""
srun -n ${SLURM_NTASKS} pwd
""")
print(job.dump())

print(slurm_version())
print(slurm_version_info())
