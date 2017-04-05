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
from collections import Iterable, OrderedDict
from warnings import warn
from inspect import stack

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

# Format GRES string
def format_gres(g):
    if isinstance(g, str): return g
    s = str(g[0])
    if len(g) == 2:   s += ":%i" % g[1]
    elif len(g) == 3: s += ":%s:%i" % (g[2], g[1])
    return s

# Format license string
def format_license(license):
    return "%s:%s" % license if isinstance(license, tuple) else license

# A bit more advanced asserts
def assert_(cond, msg):
    assert cond, stack()[1][3] + ": " + msg

def assert_no_args_left(kwargs):
    assert_(not kwargs, "unexpected keyword arguments %s" % ','.join(kwargs.keys()))

class SLURMJob:
    """Description of a SLURM job"""

    def __init__(self, **kwargs):
        self.submitted = False

        # Dictionary of all options
        # Each option is either True or option's argument
        self.options = OrderedDict()

        # Job Name
        self.job_name(kwargs.pop('name', None))
        # Partitions
        self.partitions(kwargs.pop('partition', None))
        # Time & minimal time
        self.walltime(kwargs.pop('time', None), kwargs.pop('time_min', None))
        # Working dir
        self.workdir(kwargs.pop('workdir', None))
        # Job streams
        self.job_streams(output = kwargs.pop('output', None),
                         error = kwargs.pop('error', None),
                         input = kwargs.pop('input', None),
                         open_mode = kwargs.pop('open_mode', None))
        # E-mail notifications
        self.email(kwargs.pop('mail_user', None), kwargs.pop('mail_type', None))

        # Job script body
        self.set_body(kwargs.pop('body', ''))

        # List of jobs, this job depends on
        # TODO
        #self.dependencies = []

    # Some options need to be rendered in a special way
    renderers = {
        'partition' :       lambda arg: arg if isinstance(arg, str) else ','.join(map(str, arg)),
        'time' :            format_timedelta,
        'time-min' :        format_timedelta,
        'exclusive' :       lambda arg: None if arg is True else arg,
        'nodes' :           lambda arg: '-'.join(map(str, arg)),
        'gres' :            lambda arg: ','.join(map(format_gres, arg)),
        'gres-flags' :      lambda arg: "enforce-binding",
        'nodelist' :        lambda arg: ','.join(arg),
        'exclude' :         lambda arg: ','.join(arg),
        'switches' :        lambda arg: arg if isinstance(arg, str) else "%i@%s" % (arg[0], format_timedelta(arg[1])),
        'open-mode' :       lambda arg: {'w' : 'truncate', 'a' : 'append'}[arg],
        'signal' :          lambda arg: "%s%s%s" % ('B:' if arg[2] else '', arg[0], '' if arg[1] is None else '@' + str(arg[1])),
        'begin' :           lambda arg: { str :       lambda s: s,
                                          date :      lambda s: s.isoformat(),
                                          time :      lambda s: s.isoformat(),
                                          datetime :  lambda s: s.isoformat(),
                                          timedelta : lambda s: 'now+' + (str(s.days)+"days" if s.days > 0 else str(s.seconds))
                                        }[type(arg)](arg),
        'deadline' :        lambda arg: arg.isoformat(),
        'licenses' :        lambda arg: ','.join(map(format_license, arg)),
        'clusters' :        lambda arg: ','.join(map(str, arg)),
        'export' :          lambda arg: ','.join(map(lambda e: "%s=%s" % e if isinstance(e, tuple) else e, arg))
    }

    def _add_option(self, name, arg, checks = []):
        if arg is None or arg is False:
            self.options.pop(name, None)
            return False
        else:
            for check, msg in checks:
                assert check(arg), "%s: %s" % (stack()[1][3], msg)
            self.options[name] = arg
            return True

    def _add_option_from_dict(self, name, d, d_name, checks = []):
        if not d_name in d: return False
        r = self._add_option(name, d[d_name], checks)
        del d[d_name]
        return r

    def set_body(self, body):
        """
        TODO
        """
        self.body = body.replace('\r\n', '\n')

    def job_name(self, name):
        """
        TODO
        """
        self._add_option('job-name', name)

    def partitions(self, names = None):
        """
        TODO
        """
        self._add_option('partition', names)

    def walltime(self, time = None, time_min = None):
        """
        TODO
        """
        positive_td = lambda td: td >= timedelta(0)
        self._add_option('time', time, [(positive_td, "negative 'time' durations are not allowed")])
        self._add_option('time-min', time_min, [(positive_td, "negative 'time_min' durations are not allowed")])
        if 'time-min' in self.options:
            assert_('time' in self.options, "cannot set 'time_min' without setting 'time'")
            assert_(self.options['time'] >= self.options['time-min'], "'time_min' cannot exceed 'time'")

    def nodes_allocation(self, minnodes = None, maxnodes = None, use_min_nodes = None):
        """
        TODO
        """
        has_min = self._add_option('minnodes', minnodes, [(lambda n: n > 0, "'minnodes' must be positive")])
        has_max = self._add_option('maxnodes', maxnodes, [(lambda n: n > 0, "'maxnodes' must be positive")])

        if has_max:
            assert_(has_min, "cannot set 'maxnodes' without setting 'minnodes'")
            assert_(self.options['maxnodes'] >= self.options['minnodes'], "'minnodes' cannot exceed 'maxnodes'")
            self.options['nodes'] = (self.options.pop('minnodes'), self.options.pop('maxnodes'))
        elif has_min:
            self.options['nodes'] = (self.options.pop('minnodes'),)

        self._add_option('use-min-nodes', use_min_nodes)

    def tasks_allocation(self, **kwargs):
        """
        TODO
        """
        for p in ('ntasks','cpus_per_task','ntasks_per_node','ntasks_per_socket','ntasks_per_core'):
            self._add_option_from_dict(p.replace('_','-'), kwargs, p, [(lambda n: n > 0, "'%s' must be positive" % p)])

        self._add_option_from_dict('overcommit', kwargs, 'overcommit')

        self._add_option_from_dict('exclusive', kwargs, 'exclusive',
                                   [(lambda e: e is True or e in ('user','mcs'), "invalid 'exclusive' option")])

        self._add_option_from_dict('oversubscribe', kwargs, 'oversubscribe')
        assert_(not(self.options.get('exclusive', None) is True and 'oversubscribe' in self.options),
                "'exclusive' and 'oversubscribe' options are mutually exclusive")

        self._add_option_from_dict('spread-job', kwargs, 'spread_job')

        assert_no_args_left(kwargs)

    def specialized(self, **kwargs):
        """
        TODO
        """
        self._add_option_from_dict('core-spec', kwargs, 'cores', [(lambda n: n > 0, "'cores' must be positive")])
        self._add_option_from_dict('thread-spec', kwargs, 'threads', [(lambda n: n > 0, "'threads' must be positive")])
        assert_(not('core-spec' in self.options and 'thread-spec' in self.options),
                "'cores' and 'threads' options are mutually exclusive")

        assert_no_args_left(kwargs)

    def constraints(self, **kwargs):
        """
        TODO
        """
        self._add_option_from_dict('mincpus', kwargs, 'mincpus', [(lambda n: n > 0, "'mincpus' must be positive")])

        for p in ('sockets_per_node', 'cores_per_socket', 'threads_per_core'):
            self._add_option_from_dict(p.replace('_','-'), kwargs, p, [(lambda n: n > 0, "'%s' must be positive" % p)])

        for p in ('mem', 'mem_per_cpu', 'tmp'):
            self._add_option_from_dict(p.replace('_','-'), kwargs, p, [(valid_memory_size, "invalid size argument to '%s' option" % p)])
        assert_(not('mem' in self.options and 'mem-per-cpu' in self.options), "'mem' and 'mem_per_cpu' options are mutually exclusive")

        self._add_option_from_dict('constraint', kwargs, 'constraints',
                                   [(lambda c: any(not r.match(c) is None for r in constraints_regexps), "invalid constraints")])
        self._add_option_from_dict('gres', kwargs, 'gres',
                                   [(lambda gg: all(valid_gres(g) for g in gg), "invalid generic consumable resources")])
        self._add_option_from_dict('gres-flags', kwargs, 'gres_enforce_binding')

        self._add_option_from_dict('contiguous', kwargs, 'contiguous')

        self._add_option_from_dict('nodelist', kwargs, 'nodelist', [(lambda nl: isinstance(nl, Iterable), "'nodelist' must be iterable")])
        self._add_option_from_dict('exclude', kwargs, 'exclude', [(lambda ex: isinstance(ex, Iterable), "'exclude' must be iterable")])
        self._add_option_from_dict('nodefile', kwargs, 'nodefile')

        valid_switches = lambda sw: isinstance(sw, int) or (len(sw) == 2 and sw[0] > 0 and sw[1] >= timedelta(0))
        self._add_option_from_dict('switches', kwargs, 'switches', [(valid_switches, "invalid 'switches' specification")])

        assert_no_args_left(kwargs)

    def workdir(self, workdir = None):
        """
        TODO
        """
        self._add_option('workdir', workdir)

    def job_streams(self, **kwargs):
        """
        TODO
        """
        for s in ('output', 'error', 'input'):
            self._add_option_from_dict(s, kwargs, s,
                                       [(valid_filename_patterns, "invalid filename pattern in '%s' argument" % s)])
        self._add_option_from_dict('open-mode', kwargs, 'open_mode', [(lambda m: m in ('w','a'), "invalid open mode")])

        assert_no_args_left(kwargs)

    def email(self, mail_user = None, mail_type = None):
        """
        TODO
        """
        self._add_option('mail-user', mail_user)

        valid_types = ('BEGIN', 'END', 'FAIL', 'REQUEUE', 'ALL', 'STAGE_OUT',
                       'TIME_LIMIT', 'TIME_LIMIT_90', 'TIME_LIMIT_80', 'TIME_LIMIT_50')
        self._add_option('mail-type', mail_type, [(lambda t: t in valid_types, "invalid event type")])

        if 'mail-type' not in self.options or self.options['mail-type'] == 'NONE':
            self.options.pop('mail-user', None)

    def signal(self, sig_num = None, sig_time = None, shell_only = False):
        """
        TODO
        """
        if sig_num is None:
            self.options.pop('signal', None)
            return

        assert_(sig_num in all_signals.keys() or sig_num in all_signals.values(),
                "unknown signal number/name " + str(sig_num))

        if sig_time is None:
            self.signal = (sig_num, None, shell_only)
        elif not 0 <= sig_time <= 0xffff:
            raise AssertionError("signal: 'sig_time' must be an integer between 0 and 65535")
        else:
            self.options['signal'] = (sig_num, sig_time, shell_only)

    def reservation(self, reservation = None):
        """
        TODO
        """
        self._add_option('reservation', reservation, [(valid_reservation, "invalid reservation name")])

    def defer_allocation(self, begin = None, immediate = False):
        """
        TODO
        """
        self._add_option('immediate', immediate)

        time_txt = ('midnight', 'noon', 'fika', 'teatime', 'today', 'tomorrow')
        self._add_option('begin', begin,
            [(lambda b: any(isinstance(b, t) for t in (date, time, datetime, timedelta)) or (b in time_txt),
              "'begin' has a wrong type"),
             (lambda b: not (isinstance(b, timedelta) and begin.days < 0),
              "negative 'begin' durations are not allowed")])

    def deadline(self, deadline = None):
        """
        TODO
        """
        self._add_option('deadline', deadline,
                         [(lambda d: any(isinstance(d, t) for t in (date, time, datetime)),
                           "'deadline' has a wrong type")])

    def qos(self, qos = None):
        """
        TODO
        """
        self._add_option('qos', qos)

    def account(self, account = None):
        """
        TODO
        """
        self._add_option('account', account)

    def licenses(self, licenses = None):
        """
        TODO
        """
        self._add_option('licenses', licenses,
                         [(lambda ll: all(valid_license(l) for l in ll), "invalid licenses %s" % licenses)])

    def clusters(self, clusters = None):
        """
        TODO
        """
        self._add_option('clusters', clusters)

    def export_env(self, export_vars = None, set_vars = None, export_file = None):
        """
        TODO
        """
        export = []
        if not export_vars is None:
            if export_vars in ('ALL', 'NONE'):
                export = [export_vars]
            else:
                assert_(all(isinstance(v, str) for v in export_vars), "'export_vars' must contain strings")
                export += export_vars

        if not set_vars is None:
            assert_(all(isinstance(v, str) for v in set_vars.keys()), "keys of 'set_vars' must be strings")
            export += set_vars.items()

        if export:
            self.options['export'] = export
        else:
            del self.options['export']

        has_export_file = self._add_option('export-file', export_file,
                              [(lambda ef: isinstance(ef, str) or isinstance(ef, int), "invalid 'export_file' value")])
        if has_export_file and isinstance(self.options['export-file'], int):
            try:
                os.fstat(self.options['export-file'])
            except OSError:
                warn("export_env: invalid file descriptor in 'export_file'")

    # TODO
    #def add_dependency(job):
    #    """Add a new dependency"""
    #    self.dependencies.append(job)

    def dump(self):
        """
        TODO
        """
        # Add shebang
        t = "#!%s\n" % shell_path

        # Generate header
        for name in self.options:
            arg = self.options[name]
            if name in SLURMJob.renderers:
                t += render_option(name, SLURMJob.renderers[name](arg))
            elif arg is True:
                t += render_option(name)
            else:
                t += render_option(name, str(arg))

        t += render_option("parsable")
        t += render_option("quiet")
        # Add body
        t += self.body

        return t

def submit(self, sbatch_path = None):
    """
    TODO
    """
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

def chain_jobs(jobs):
    """
    TODO
    """
    pass
