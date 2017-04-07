import sys
sys.path = ['..'] + sys.path

from datetime import timedelta, date, time, datetime
from slurm_factory import *

job = SLURMJob(name = "hello_world")

job.partitions("debug")
job.walltime(timedelta(minutes = 19, seconds = 12), timedelta(minutes = 15))
job.nodes_allocation(16, 32, use_min_nodes = True)
job.tasks_allocation(ntasks = 128,
                     cpus_per_task = 2,
                     ntasks_per_node = 4,
                     ntasks_per_socket = 2,
                     ntasks_per_core = 1,
                     overcommit = True,
                     oversubscribe = True,
                     exclusive = 'user',
                     spread_job = True)
job.specialized(threads = 4)
job.workdir("./job_dir")
job.job_streams(output = r"slurm-%x-%8j.out",
                error = r"slurm-%x-%8j.err",
                input = "/dev/random", open_mode = 'a')
job.email("slurm-user@example.com", 'END')
job.constraints(mincpus = 4,
                sockets_per_node = 2,
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
                exclude = ['node[17-19]', 'node20'],
                switches = (2,timedelta(hours = 2)))
job.signal(sig_num='USR1', sig_time=600, shell_only=True)
job.reservation("user_23")
job.qos("myqos")
job.account("myaccount")
job.licenses([('foo',4),'bar'])
job.deadline(datetime(2017, 8, 11, 10, 8))
job.defer_allocation(immediate = True, begin = timedelta(minutes = 15, days = 23))
job.clusters(['cluster1','cluster2'])

export_file = open('export.txt', 'w')
job.export_env(export_vars = ['SHELL', 'EDITOR'], set_vars = {'PATH' : '/opt/bin'},
               export_file = export_file.fileno())

job.set_body("""
srun -n ${SLURM_NTASKS} pwd
""")
print(job.dump())

#job.add_dependencies('afterok', [123456, 456789])
#job.add_dependencies('afterany', [785672])
#job.add_dependencies('expand', [777777])
#job.add_dependencies('singleton')
#job.dependencies_require_any(True)

jobs = [SLURMJob(name = "hello_world") for n in range(5)]
for j in jobs:
    j.constraints(constraints = 'haswell')
    j.set_body("""
hostname
""")

chain_jobs(jobs, 'afterok')

#for j in jobs: submit(j)

#print(slurm_version())
#print(slurm_version_info())

cjob = CrayJob(name = "cray_job", time = timedelta(hours = 1))
cjob.network('blade')

print(cjob.dump())
