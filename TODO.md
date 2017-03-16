TODO list
=========

Tier 1 functionality
--------------------

* Resource allocation:
    - [DONE] `--partition=<partition_names>`
    - [DONE] `--time=<time>`
    - [DONE] `--time-min=<time>`
    - `--nodes=<minnodes[-maxnodes]>`
    - `--use-min-nodes`
    - `--ntasks=<number>`
    - `--cpus-per-task=<ncpus>`
    - `--ntasks-per-node=<ntasks>`
    - `--ntasks-per-socket=<ntasks>`
    - `--ntasks-per-core=<ntasks>`
    - `--mincpus=<n>`
    - `--overcommit`
    - `--switches=<count>[@<max-time>]`
    - `--core-spec=<num>`
    - `--thread-spec=<num>`
    - `--exclusive[=user|mcs]`
    - `--oversubscribe`
    - `--spread-job`
    - `--licenses=<license>`

* Node selection constraints:
    - `--extra-node-info=<sockets[:cores[:threads]]>`
    - `--sockets-per-node=<sockets>`
    - `--cores-per-socket=<cores>`
    - `--threads-per-core=<threads>`
    - `--mem=<size[units]>`
    - `--mem-per-cpu=<size[units]>`
    - `--tmp=<size[units]>`
    - [DONE] `--constraint=<list>`
    - `--gres=<list>`
    - `--gres-flags=enforce-binding`
    - `--contiguous`
    - `--nodelist=<node name list>`
    - `--nodefile=<node file>`
    - `--exclude=<node name list>`

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

* Signals
    - `--signal=[B:]<sig_num>[@<sig_time>]`

* Job dependencies:
    - `--dependency=<dependency_list>`
    - `--kill-on-invalid-dep=<yes|no>`

* Reservations:
    - `--reservation=<name>`

* Allocation time constraints:
    - `--begin=<time>`
    - `--deadline=<OPT>`
    - `--immediate`

* Quality of service
    - `--qos=<qos>`

* Cluster selection
    - `--clusters=<string>`

* **Unit tests**
* **Documentation**

Tier 2 functionality
--------------------

* Accounting:
    - `--account=<account>`
    - `--acctg-freq`
    - `--profile=<all|none|[energy[,|task[,|lustre[,|network]]]]>`

* Checkpointing:
    - `--checkpoint=<time>`
    - `--checkpoint-dir=<directory>`

* [DONE] SLURM version information:
    - [DONE] `--version`

* Scheduling priority
    - `--priority=<value>`
    - `--hold`

* Niceness settings
    - `--nice[=adjustment]`

* CPU frequency options for `srun`:
    - `--cpu-freq`

* Power management plugin options:
    - `--power=<flags>`

* Job requeuing:
    - `--requeue`
    - `--no-requeue`

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

* Environment variables propagation:
    - `--export=<environment variables | ALL | NONE>`
    - `--export-file=<filename | fd>`

* Test submission:
    - `--test-only`

* Workload Characterization Key:
    - `--wckey=<wckey>`

* Multi-Category Security:
    - `--mcs-label=<mcs>`

* Burst buffer specification (validate filename patterns):
    - `--bbf=<file_name>`

* Wait for job termination:
    - `--wait`

* Node failure treatment:
    - `--no-kill`

* Node reboot
    - `--delay-boot=<minutes>`
    - `--wait-all-nodes=<value>`

* Options specific to Cray systems:
    - `--network=<type>`

* Options specific to Blue Gene systems:
    - `--blrts-image=<path>`
    - `--cnload-image=<path>`
    - `--conn-type=<type>`
    - `--geometry=<XxYxZ> | <AxXxYxZ>`
    - `--ioload-image=<path>`
    - `--linux-image=<path>`
    - `--mloader-image=<path>`
    - `--no-rotate`
    - `--ramdisk-image=<path>`
