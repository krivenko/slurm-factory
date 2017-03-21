#!/usr/bin/env python
###################################################################################
#
# slurm-factory
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
from subprocess import Popen, check_output, PIPE
from warnings import warn
from datetime import timedelta

# Locate default shell
shell_path = os.environ['SHELL']

# Locate 'sbatch' binary
default_sbatch_path = ""
for path in os.environ["PATH"].split(os.pathsep):
    p = os.path.join(path, "sbatch")
    if os.access(p, os.X_OK): default_sbatch_path = p
if not default_sbatch_path: warn("Could not locate 'sbatch' executable")

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

# Validate filename pattern
def valid_filename_patterns(filename):
    if r'\\' in filename: return True
    return ('%' not in re.sub(filename_pattern_regexp,'', filename))

# Validate memory size int/string
def valid_memory_size(size):
    return (isinstance(size, int) and size > 0) or \
           (isinstance(size, str) and not memory_size_regexp.match(size) is None)

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
        # Node selection
        self.select_nodes()
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
        #QoS
        self.qos = None
        # Clusters
        self.clusters = None

        # Job script body
        self.set_body(kwargs.pop('body', ''))

        # List of jobs, this job depends on
#       self.dependencies = []

    #def add_dependency(job):
    #    """Add a new dependency"""
    #    self.dependencies.append(job)

    def set_body(self, body):
        self.body = body.replace('\r\n', '\n')

    def set_partitions(self, partition_names):
        self.partitions = [partition_names] if isinstance(partition_names, str) else partition_names

    def set_time(self, time, time_min = None):
        if time is None: self.time = None
        elif time < timedelta(0):
            raise RuntimeError("set_time: negative 'time' durations are not allowed")
        else: self.time = time

        if time_min is None: self.time_min = None
        elif time_min < timedelta(0):
            raise RuntimeError("set_time: negative 'time-min' durations are not allowed")
        elif self.time is None:
            raise RuntimeError("set_time: cannot set 'time-min' without setting 'time'")
        else:
            self.time_min = time_min
            if self.time < self.time_min:
                raise RuntimeError("set_time: 'time-min' cannot exceed 'time'")

    def select_nodes(self, sockets_per_node = None, cores_per_socket = None, threads_per_core = None,
                     mem = None, mem_per_cpu = None, tmp = None, constraints = None):

        if sockets_per_node is None: self.sockets_per_node = None
        elif sockets_per_node <= 0:
            raise RuntimeError("select_nodes: sockets_per_node must be positive")
        else:
            self.sockets_per_node = sockets_per_node

        if cores_per_socket is None: self.cores_per_socket = None
        elif cores_per_socket <= 0:
            raise RuntimeError("select_nodes: cores_per_socket must be positive")
        else:
            self.cores_per_socket = cores_per_socket

        if threads_per_core is None: self.threads_per_core = None
        elif threads_per_core <= 0:
            raise RuntimeError("select_nodes: threads_per_core must be positive")
        else:
            self.threads_per_core = threads_per_core

        if mem is None: self.mem = None
        elif not valid_memory_size(mem):
            raise RuntimeError("select_nodes: invalid size argument to mem option")
        else:
            self.mem = mem

        if mem_per_cpu is None: self.mem_per_cpu = None
        elif not valid_memory_size(mem_per_cpu):
            raise RuntimeError("select_nodes: invalid size argument to mem_per_cpu option")
        else:
            self.mem_per_cpu = mem_per_cpu

        if (not self.mem is None) and (not self.mem_per_cpu is None):
            raise RuntimeError("select_nodes: mem and mem_per_cpu options are mutually exclusive")

        if tmp is None: self.tmp = None
        elif not valid_memory_size(tmp):
            raise RuntimeError("select_nodes: invalid size argument to tmp option")
        else:
            self.tmp = tmp

        if constraints is None: self.constraints = None
        elif all(r.match(constraints) is None for r in constraints_regexps):
            raise RuntimeError("select_nodes: invalid constraints %s" % constraints)
        else:
            self.constraints = constraints

    def set_workdir(self, workdir):
        self.workdir = workdir

    def set_job_streams(self, output, error = None, input = None, mode = 'w'):
        if output is None: self.output = None
        elif not valid_filename_patterns(output):
            raise RuntimeError("set_job_streams: invalid filename pattern in 'output' argument")
        else:
            self.output = output

        if error is None: self.error = None
        elif not valid_filename_patterns(error):
            raise RuntimeError("set_job_streams: invalid filename pattern in 'error' argument")
        else:
            self.error = error

        if input is None: self.input = None
        elif not valid_filename_patterns(input):
            raise RuntimeError("set_job_streams: invalid filename pattern in 'input' argument")
        else:
            self.input = input

        valid_modes = {'w' : 'truncate', 'a' : 'append'}
        if mode is None: self.open_mode = None
        elif mode not in valid_modes:
            raise RuntimeError("set_job_streams: invalid open mode %s" % mode)
        else:
            self.open_mode = valid_modes[mode]

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
            raise RuntimeError("set_signal: sig_time must be an integer between 0 and 65535")
        else:
            self.signal = (sig_num, sig_time, shell_only)

    def set_qos(self, qos):
        self.qos = qos

    def set_clusters(self, clusters):
        self.clusters = [clusters] if isinstance(clusters, str) else clusters

    def dump(self):
        # Add shebang
        t = "#!%s\n" % shell_path
        # Generate header
        if self.name:           t += render_option("job-name", self.name)
        if self.partitions:     t += render_option("partition", ','.join(map(str, self.partitions)))
        if self.time:           t += render_option("time", format_timedelta(self.time))
        if self.time_min:       t += render_option("time-min", format_timedelta(self.time_min))
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
        if self.qos:            t += render_option("qos", str(self.qos))
        if self.clusters:       t += render_option("clusters", ','.join(map(str, self.clusters)))

        t += render_option("parsable")
        t += render_option("quiet")
        # Add body
        t += self.body

        return t

    def submit(self, sbatch_path = default_sbatch_path):
        p = Popen(sbatch_path, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdoutdata, stderrdata = p.communicate(self.dump().encode('utf-8'))
        if p.returncode:
            error_msg = "%s failed to submit job '%s' with the following error message:\n%s" \
                        % (sbatch_path, self.name, stderrdata.decode('utf-8'))
            raise RuntimeError(error_msg)
        else:
            self.submitted = True
            self.job_id = int(parse_job_id_regexp.match(stdoutdata.decode('utf-8')).group(1))
            return self.job_id

def slurm_version(sbatch_path = default_sbatch_path):
    output = check_output([sbatch_path, '--version'])
    return output.decode('utf-8').strip()

def slurm_version_info(sbatch_path = default_sbatch_path):
    sv = slurm_version(sbatch_path).replace('slurm','').strip()
    def to_int_checked(x):
        try:
            return int(x)
        except ValueError:
            return x
    return tuple(map(to_int_checked, sv.split('.')))

def chain_jobs():
    # TODO
    pass
