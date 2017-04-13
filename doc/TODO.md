TODO list
=========

Tier 1 functionality
--------------------

* [DONE] Resource allocation:
    - [DONE] `--partition=<partition_names>`
    - [DONE] `--time=<time>`
    - [DONE] `--time-min=<time>`
    - [DONE] `--nodes=<minnodes[-maxnodes]>`
    - [DONE] `--use-min-nodes`
    - [DONE] `--ntasks=<number>`
    - [DONE] `--cpus-per-task=<ncpus>`
    - [DONE] `--ntasks-per-node=<ntasks>`
    - [DONE] `--ntasks-per-socket=<ntasks>`
    - [DONE] `--ntasks-per-core=<ntasks>`
    - [DONE] `--overcommit`
    - [DONE] `--core-spec=<num>`
    - [DONE] `--thread-spec=<num>`
    - [DONE] `--exclusive[=user|mcs]`
    - [DONE] `--oversubscribe`
    - [DONE] `--spread-job`

* [DONE] Node selection constraints:
    - [DONE] `--extra-node-info=<sockets[:cores[:threads]]>`
    - [DONE] `--sockets-per-node=<sockets>`
    - [DONE] `--cores-per-socket=<cores>`
    - [DONE] `--threads-per-core=<threads>`
    - [DONE] `--mincpus=<n>`
    - [DONE] `--mem=<size[units]>`
    - [DONE] `--mem-per-cpu=<size[units]>`
    - [DONE] `--tmp=<size[units]>`
    - [DONE] `--switches=<count>[@<max-time>]`
    - [DONE] `--constraint=<list>`
    - [DONE] `--gres=<list>`
    - [DONE] `--gres-flags=enforce-binding`
    - [DONE] `--contiguous`
    - [DONE] `--nodelist=<node name list>`
    - [DONE] `--nodefile=<node file>`
    - [DONE] `--exclude=<node name list>`

* [DONE] Working directory:
    - [DONE] `--workdir=<directory>`

* [DONE] Input/output/error files (validate filename patterns):
    - [DONE] `--input=<filename pattern>`
    - [DONE] `--output=<filename pattern>`
    - [DONE] `--error=<filename pattern>`
    - [DONE] `--open-mode=append|truncate`

* [DONE] E-mail notifications (with basic e-mail validation):
    - [DONE] `--mail-type=<type>`
    - [DONE] `--mail-user=<user>`

* [DONE] Signals
    - [DONE] `--signal=[B:]<sig_num>[@<sig_time>]`

* [DONE] Job dependencies:
    - [DONE] `--dependency=<dependency_list>`
    - [DONE] `--kill-on-invalid-dep=<yes|no>`

* [DONE] Reservations:
    - [DONE] `--reservation=<name>`

* [DONE] Allocation time constraints:
    - [DONE] `--begin=<time>`
    - [DONE] `--deadline=<OPT>`
    - [DONE] `--immediate`

* [DONE] Quality of service
    - [DONE] `--qos=<qos>`

* [DONE] Accounting
    - [DONE] `--account=<account>`

* [DONE] Licenses
    - [DONE] `--licenses=<license>`

* [DONE] Cluster selection
    - [DONE] `--clusters=<string>`

* [DONE] Environment variables propagation:
    - [DONE] `--export=<environment variables | ALL | NONE>`
    - [DONE] `--export-file=<filename | fd>`

* **Unit tests**
* **Documentation**
* **Burst buffer directives**
* **Submit over SSH**
* **PBS job generation**


Tier 2 functionality
--------------------

* Checkpointing:
    - `--checkpoint=<time>`
    - `--checkpoint-dir=<directory>`

* Profiling:
    - `--acctg-freq`
    - `--profile=<all|none|[energy[,|task[,|lustre[,|network]]]]>`

* [DONE] SLURM version information:
    - [DONE] `--version`

* Scheduling priority
    - `--priority=<value>`
    - [DONE] `--hold`

* Niceness settings
    - `--nice[=adjustment]`

* CPU frequency options for `srun`:
    - `--cpu-freq`

* Power management plugin options:
    - `--power=<flags>`

* [DONE] Job requeuing:
    - [DONE] `--requeue`
    - [DONE] `--no-requeue`

* Distribution methods for remote processes:
    - `--distribution=arbitrary|<block|cyclic|plane=<options>[:block|cyclic|fcyclic]>`

* Resource limits propagation:
    - `--propagate[=rlimitfR]`

* Task binding:
    - `--mem_bind=[{quiet,verbose},]type`
    - `--hint=<type>`

* root-only options (check process UID):
    - `--jobid=<jobid>`
    - `--uid=<user>`
    - `--gid=<group>`
    - `--reboot`

* Test submission:
    - `--test-only`

* Workload Characterization Key:
    - `--wckey=<wckey>`

* Multi-Category Security:
    - `--mcs-label=<mcs>`

* [DONE] Burst buffer specification (validate filename patterns):
    - [DONE] `--bbf=<file_name>`

* Wait for job termination:
    - `--wait`

* Node failure treatment:
    - `--no-kill`

* Node reboot
    - `--delay-boot=<minutes>`
    - `--wait-all-nodes=<value>`

* [DONE] Options specific to Cray systems (derived class `SLURMCrayJob`):
    - [DONE] `--network=<type>`

* Options specific to Blue Gene systems (derived class `SLURMBlueGeneJob`):
    - `--blrts-image=<path>`
    - `--cnload-image=<path>`
    - `--conn-type=<type>`
    - `--geometry=<XxYxZ> | <AxXxYxZ>`
    - `--ioload-image=<path>`
    - `--linux-image=<path>`
    - `--mloader-image=<path>`
    - `--no-rotate`
    - `--ramdisk-image=<path>`
