#!/usr/bin/env python
###################################################################################
#
# slurm_factory
#
# Copyright (C) 2017 by I. Krivenko
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

# Python 2/3 compatibility
from __future__ import absolute_import, print_function, unicode_literals
__metaclass__ = type

import os
import re
from subprocess import Popen, PIPE
from datetime import datetime, date, time, timedelta
from collections import Iterable
from warnings import warn

from .version import locate_sbatch_executable

# Locate default shell
shell_path = os.environ['SHELL']

# Names of all UNIX signals supported on this platform
import signal
all_signals = {k[3:] : v for k, v in sorted(signal.__dict__.items())
               if k.startswith('SIG') and not k.startswith('SIG_')}
del signal

# RegExp for job_id extraction
parse_job_id_regexp = re.compile(r"^(\d+)$")
# RegExp for filename pattern validation
filename_pattern_regexp = re.compile(r"%\d*[%AaJjNnstux]")
# RegExp list for constraints validation
constraints_regexps = (r"^\w+(\*\d)*(,\w+(\*\d)*)*$",      # List
                       r"^\w+(\*\d)*(\|\w+(\*\d)*)*$",     # OR
                       r"^\w+(\*\d)*(&\w+(\*\d)*)*$",      # AND
                       r"^\[\w+(\*\d)*(\|\w+(\*\d)*)*\]$") # Matching OR
constraints_regexps = tuple(re.compile(r) for r in constraints_regexps)
# RegExp for memory size expressions
memory_size_regexp = re.compile(r"^[0-9]+[KMGT]$")
# RegExp for reservation names
reservation_regexp = re.compile(r"^[_\-a-z0-9]*$")

# Validate filename pattern
def valid_filename_patterns(filename):
    if r'\\' in filename: return True
    return ('%' not in re.sub(filename_pattern_regexp,'', filename))

# Validate memory size int/string
def valid_memory_size(size):
    return (isinstance(size, int) and size > 0) or \
           (isinstance(size, str) and not memory_size_regexp.match(size) is None)

# Validate reservation name
def valid_reservation(reservation):
    return (not reservation_regexp.match(reservation) is None)

# Validate generic consumable resources
def valid_gres(gres):
    if isinstance(gres, str): return True
    if len(gres) > 3: return False
    return all(isinstance(f, t) for f, t in zip(gres, (str, int, str)))

# Validate license
def valid_license(license):
    if isinstance(license, str): return True
    if len(license) > 2: return False
    return isinstance(license[0], str) and isinstance(license[1], int)

# Add #SBATCH option line
def render_option(name, value = None):
    if value:
        return "#SBATCH --%s=%s\n" % (name, value)
    else:
        return "#SBATCH --%s\n" % name

# Print a timedelta object in SLURM format
def format_timedelta(td):
    if td.total_seconds() < 3600:
        return "%02i:%02i" % (td.seconds/60, td.seconds%60)
    else:
        hours = td.seconds / 3600
        seconds = td.seconds % 3600
        if td.days == 0:
            return "%02i:%02i:%02i" % (hours, seconds/60, seconds%60)
        else:
            return "%i-%02i:%02i:%02i" % (td.days, hours, seconds/60, seconds%60)

class SLURMJob:
    """Description of a SLURM job"""

    def __init__(self, **kwargs):
        self.submitted = False

        # Job Name
        self.name = kwargs.pop('name', '')
        # Partitions
        self.set_partitions(kwargs.pop('partition', None))
        # Time & minimal time
        self.set_time(kwargs.pop('time', None), kwargs.pop('time_min', None))
        # Number of nodes
        self.set_nnodes()
        # Specialized cores/threads
        self.set_specialized()
        # Node selection
        self.set_constraints()
        # Working dir
        self.set_workdir(kwargs.pop('workdir', None))
        # Job streams
        self.set_job_streams(kwargs.pop('output', None),
                             kwargs.pop('error', None),
                             kwargs.pop('input', None),
                             kwargs.pop('open_mode', None))
        # E-mail notifications
        self.set_email(kwargs.pop('mail_user', None), kwargs.pop('mail_type', None))
        # Signal
        self.signal = None
        # Reservation
        self.set_reservation()
        # Defer allocation
        self.defer_allocation()
        # Deadline
        self.set_deadline()
        # QoS
        self.set_qos()
        # Account
        self.set_account()
        # Licenses
        self.set_licenses()
        # Clusters
        self.set_clusters()
        # Export environment variables
        self.set_export_env()

        # Job script body
        self.set_body(kwargs.pop('body', ''))

        # List of jobs, this job depends on
#       self.dependencies = []

    #def add_dependency(job):
    #    """Add a new dependency"""
    #    self.dependencies.append(job)

    def __check_and_store(self, var_name, var_value, checks, apply_before_store = lambda x: x):
        if var_value is None:
            setattr(self, var_name, None)
            return
        for check, msg in checks:
            if not check(var_value):
                import inspect
                raise RuntimeError("%s: %s" % (inspect.stack()[1][3], msg))
        setattr(self, var_name, apply_before_store(var_value))

    def set_body(self, body):
        self.body = body.replace('\r\n', '\n')

    def set_partitions(self, partition_names):
        self.partitions = [partition_names] if isinstance(partition_names, str) else partition_names

    def set_time(self, time, time_min = None):
        self.__check_and_store('time', time,
            [(lambda t: t >= timedelta(0), "negative 'time' durations are not allowed")])
        self.__check_and_store('time_min', time_min,
            [(lambda t: t >= timedelta(0),     "negative 'time_min' durations are not allowed"),
             (lambda t: not self.time is None, "cannot set 'time_min' without setting 'time'"),
             (lambda t: self.time >= t,        "'time_min' cannot exceed 'time'")])

    def set_nnodes(self, minnodes = None, maxnodes = None, use_min_nodes = False):
        self.__check_and_store('minnodes', minnodes, [(lambda n: n > 0, "'minnodes' must be positive")])
        self.__check_and_store('maxnodes', maxnodes,
            [(lambda n: not self.minnodes is None, "cannot set 'maxnodes' without setting 'minnodes'"),
             (lambda n: n > 0,                     "'maxnodes' must be positive"),
             (lambda n: n >= self.minnodes,        "'minnodes' cannot exceed 'maxnodes'")])
        self.use_min_nodes = use_min_nodes

    def set_specialized(self, cores = None, threads = None):
        self.__check_and_store('core_spec', cores, [(lambda n: n > 0, "'cores' must be positive")])
        self.__check_and_store('thread_spec', threads, [(lambda n: n > 0, "'threads' must be positive")])

        if (not self.core_spec is None) and (not self.thread_spec is None):
            raise RuntimeError("set_specialized: 'cores' and 'threads' options are mutually exclusive")

    def set_constraints(self, mincpus = None,
                        sockets_per_node = None, cores_per_socket = None, threads_per_core = None,
                        mem = None, mem_per_cpu = None, tmp = None, constraints = None,
                        gres = None, gres_enforce_binding = False, contiguous = False,
                        nodelist = None, nodefile = None, exclude = None, switches = None):
        self.__check_and_store('mincpus', mincpus, [(lambda n: n > 0, "'mincpus' must be positive")])

        for p in ('sockets_per_node', 'cores_per_socket', 'threads_per_core'):
            self.__check_and_store(p, vars()[p], [(lambda n: n > 0, "'%s' must be positive" % p)])
        for p in ('mem', 'mem_per_cpu', 'tmp'):
            self.__check_and_store(p, vars()[p], [(valid_memory_size, "invalid size argument to '%s' option" % p)])

        if (not self.mem is None) and (not self.mem_per_cpu is None):
            raise RuntimeError("set_constraints: 'mem' and 'mem_per_cpu' options are mutually exclusive")

        self.__check_and_store('constraints', constraints,
            [(lambda c: any(not r.match(c) is None for r in constraints_regexps), "invalid constraints %s" % constraints)])
        self.__check_and_store('gres', gres,
            [(lambda gg: all(valid_gres(g) for g in gg), "invalid generic consumable resources %s" % gres)],
            lambda gg: map(lambda g: (g,) if isinstance(g, str) else g, gg))
        self.gres_enforce_binding = gres_enforce_binding

        self.contiguous = contiguous

        self.__check_and_store('nodelist', nodelist, [(lambda nl: isinstance(nl, Iterable), "'nodelist' must be iterable")])
        self.__check_and_store('exclude', exclude,   [(lambda ex: isinstance(ex, Iterable), "'exclude' must be iterable")])
        self.nodefile = nodefile

        valid_switches = lambda sw: isinstance(sw, int) or (len(sw) == 2 and sw[0] > 0 and sw[1] >= timedelta(0))
        self.__check_and_store('switches', switches, [(valid_switches, "'switches' invalid 'switches' specification")],
                               lambda sw: (sw,) if isinstance(sw, int) else sw)

    def set_workdir(self, workdir):
        self.workdir = workdir

    def set_job_streams(self, output, error = None, input = None, mode = 'w'):
        for s in ('output', 'error', 'input'):
            self.__check_and_store(s, vars()[s],
                [(valid_filename_patterns, "invalid filename pattern in '%s' argument" % s)])

        valid_modes = {'w' : 'truncate', 'a' : 'append'}
        self.__check_and_store('open_mode', mode,
            [(lambda m: m in valid_modes, "invalid open mode %s" % mode)], lambda m: valid_modes[m])

    def set_email(self, mail_user, mail_type):
        valid_types = ('BEGIN', 'END', 'FAIL', 'REQUEUE', 'ALL', 'STAGE_OUT',
                       'TIME_LIMIT', 'TIME_LIMIT_90', 'TIME_LIMIT_80', 'TIME_LIMIT_50')
        if mail_type is None or mail_type == 'NONE':
            self.mail_user = None
            self.mail_type = None
        elif mail_type not in valid_types:
            raise RuntimeError("set_email: invalid event type %s" % mail_type)
        else:
            self.mail_type = mail_type
            self.mail_user = mail_user

    def set_signal(self, sig_num, sig_time = None, shell_only = False):
        if not sig_num in all_signals.keys() and not sig_num in all_signals.values():
            raise RuntimeError("set_signal: unknown signal number/name " + str(sig_num))

        if sig_time is None:
            self.signal = (sig_num, None, shell_only)
        elif not 0 <= sig_time <= 0xffff:
            raise RuntimeError("set_signal: 'sig_time' must be an integer between 0 and 65535")
        else:
            self.signal = (sig_num, sig_time, shell_only)

    def set_reservation(self, reservation = None):
        self.__check_and_store('reservation', reservation, [(valid_reservation, "invalid reservation name")])

    def defer_allocation(self, begin = None, immediate = False):
        self.immediate = immediate

        self.__check_and_store('begin', begin,
            [(lambda b: any(isinstance(b, t) for t in (date, time, datetime, timedelta)) or \
                        (b in ('midnight', 'noon', 'fika', 'teatime', 'today', 'tomorrow')),
              "'begin' has a wrong type"),
             (lambda b: not (isinstance(b, timedelta) and begin.days < 0),
              "negative 'begin' durations are not allowed")])

    def set_deadline(self, deadline = None):
        self.__check_and_store('deadline', deadline,
            [(lambda d: any(isinstance(d, t) for t in (date, time, datetime)), "'deadline' has a wrong type")])

    def set_qos(self, qos = None):
        self.qos = qos

    def set_account(self, account = None):
        self.account = account

    def set_licenses(self, licenses = None):
        self.__check_and_store('licenses', licenses,
            [(lambda ll: all(valid_license(l) for l in ll), "invalid licenses %s" % licenses)],
            lambda ll: map(lambda l: (l,) if isinstance(l, str) else l, ll))

    def set_clusters(self, clusters = None):
        if clusters is None: self.clusters = None
        self.clusters = [clusters] if isinstance(clusters, str) else clusters

    def set_export_env(self, export_vars = None, set_vars = None, export_file = None):
        self.__check_and_store('export_vars', export_vars,
            [(lambda ev: all(isinstance(v, str) for v in ev) or (ev in ('ALL', 'NONE')),
             "'export_vars' must contain strings")])
        self.__check_and_store('set_vars', set_vars,
            [(lambda sv: all(isinstance(v, str) for v in sv.keys()), "keys of 'set_vars' must be strings")])
        self.__check_and_store('export_file', export_file,
            [(lambda ef: isinstance(ef, str) or isinstance(ef, int), "invalid 'export_file' value")])
        if isinstance(self.export_file, int):
            try:
                 os.fstat(self.export_file)
            except OSError:
                warn("set_export_env: invalid file descriptor in 'export_file'")

    def dump(self):
        # Add shebang
        t = "#!%s\n" % shell_path
        # Generate header
        if self.name:           t += render_option("job-name", self.name)
        if self.partitions:     t += render_option("partition", ','.join(map(str, self.partitions)))
        if self.time:           t += render_option("time", format_timedelta(self.time))
        if self.time_min:       t += render_option("time-min", format_timedelta(self.time_min))
        if self.minnodes:       t += render_option("nodes", str(self.minnodes) + ("-%d" % self.maxnodes
                                                                                  if self.maxnodes else ''))
        if self.use_min_nodes:  t += render_option("use-min-nodes")
        if self.core_spec:      t += render_option("core-spec",   str(self.core_spec))
        if self.thread_spec:    t += render_option("thread-spec", str(self.thread_spec))
        if self.mincpus:        t += render_option("mincpus", str(self.mincpus))
        extra_node_info = (self.sockets_per_node, self.cores_per_socket, self.threads_per_core)
        if any(s is None for s in extra_node_info):
            if self.sockets_per_node:   t += render_option("sockets-per-node", str(self.sockets_per_node))
            if self.cores_per_socket:   t += render_option("cores-per-socket", str(self.cores_per_socket))
            if self.threads_per_core:   t += render_option("threads-per-core", str(self.threads_per_core))
        else:
            t += render_option("extra-node-info", ':'.join(map(str, extra_node_info)))
        if self.mem:            t += render_option("mem", str(self.mem))
        if self.mem_per_cpu:    t += render_option("mem_per_cpu", str(self.mem_per_cpu))
        if self.tmp:            t += render_option("tmp", str(self.tmp))
        if self.constraints:    t += render_option("constraint", str(self.constraints))
        if self.gres:
            def render_gres(g):
                s = str(g[0])
                if len(g) == 2:   s += ":%i" % g[1]
                elif len(g) == 3: s += ":%s:%i" % (g[2], g[1])
                return s
            t += render_option("gres", ','.join(map(render_gres, self.gres)))
        if self.gres_enforce_binding: t += render_option("gres-flags", "enforce-binding")
        if self.contiguous:     t += render_option("contiguous")
        if self.nodelist:       t += render_option("nodelist", ','.join(self.nodelist))
        if self.nodefile:       t += render_option("nodefile", str(self.nodefile))
        if self.exclude:        t += render_option("exclude", ','.join(self.exclude))
        if self.switches:       t += render_option("switches", str(self.switches[0])
                                                               if len(self.switches) == 1 else
                                                               "%i@%s" % (self.switches[0],
                                                                          format_timedelta(self.switches[1])) )
        if self.workdir:        t += render_option("workdir", str(self.workdir))
        if self.output:         t += render_option("output", str(self.output))
        if self.error:          t += render_option("error", str(self.error))
        if self.input:          t += render_option("input", str(self.input))
        if self.open_mode:      t += render_option("open-mode", self.open_mode)
        if self.mail_type:
            t += render_option("mail-type", self.mail_type)
            t += render_option("mail-user", str(self.mail_user))
        if self.signal:
            t += render_option("signal", "%s%s%s" % ('B:' if self.signal[2] else '',
                                                     self.signal[0],
                                                     '' if self.signal[1] is None else '@' + str(self.signal[1])))
        if self.reservation:    t += render_option("reservation", str(self.reservation))
        if self.begin:          t += render_option("begin", {
                                                    str :       lambda s: s,
                                                    date :      lambda s: s.isoformat(),
                                                    time :      lambda s: s.isoformat(),
                                                    datetime :  lambda s: s.isoformat(),
                                                    timedelta : lambda s: 'now+' + (str(s.days)+"days" \
                                                                if s.days > 0 else str(s.seconds))
                                                   }[type(self.begin)](self.begin))
        if self.immediate:      t += render_option("immediate")
        if self.deadline:       t += render_option("deadline", self.deadline.isoformat())
        if self.qos:            t += render_option("qos", str(self.qos))
        if self.account:        t += render_option("account", str(self.account))
        if self.licenses:
            render_license = lambda l: str(l[0]) if len(l) == 1 else "%s:%i" % (l[0], l[1])
            t += render_option("licenses", ','.join(map(render_license, self.licenses)))
        if self.clusters:       t += render_option("clusters", ','.join(map(str, self.clusters)))
        if self.export_vars or self.set_vars:
            if self.export_vars in ('ALL', 'NONE'):
                t += render_option("export", self.export_vars)
            else:
                export = []
                if self.export_vars: export += self.export_vars
                if self.set_vars:    export += ["%s=%s" % (k, v) for k, v in self.set_vars.items()]
                t += render_option("export", ','.join(export))
        if self.export_file:    t += render_option("export-file", str(self.export_file))

        t += render_option("parsable")
        t += render_option("quiet")
        # Add body
        t += self.body

        return t

def submit(self, sbatch_path = None):
    if sbatch_path is None:
        sbatch_path = locate_sbatch_executable()

    p = Popen(sbatch_path, stdout = PIPE, stdin = PIPE, stderr = PIPE)
    stdoutdata, stderrdata = p.communicate(self.dump().encode('utf-8'))
    if p.returncode:
        error_msg = "%s failed to submit job '%s' with the following error message:\n%s" \
                    % (sbatch_path, self.name, stderrdata.decode('utf-8'))
        raise RuntimeError(error_msg)
    else:
        self.submitted = True
        self.job_id = int(parse_job_id_regexp.match(stdoutdata.decode('utf-8')).group(1))
        return self.job_id

def chain_jobs():
    # TODO
    pass
