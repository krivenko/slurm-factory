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
from subprocess import Popen, PIPE
from warnings import warn
from datetime import timedelta

# Locate default shell
shell_path = os.environ['SHELL']

# Locate 'sbatch' binary
default_sbatch_path = ""
for path in os.environ["PATH"].split(os.pathsep):
    p = os.path.join(path, "sbatch")
    if os.access(p, os.X_OK): default_sbatch_path = p
if not(default_sbatch_path): warn("Could not locate 'sbatch' executable")

# RegExp for job_id extraction
job_id_regexp = re.compile("^Submitted batch job ([0-9]+)$")

# Validate an e-mail address
def valid_email(email):
    from email.utils import parseaddr
    return '@' in parseaddr(email)[1]

# Add #SBATCH option line to 'text'
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

#Acceptable time formats include "minutes", "minutes:seconds", "hours:minutes:seconds", "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds"

class SLURMJob:
    """Description of a SLURM job"""

    def __init__(self, **kwargs):
        self.submitted = False
        self.hold = False

        # Job Name
        self.name = kwargs.pop('name','')
        # Wall time
        self.walltime = kwargs.pop('walltime',None)


        # List of jobs, this job depends on
#       self.dependencies = []

    #def add_dependency(job):
    #    """Add a new dependency"""
    #    self.dependencies.append(job)

#        # Submit in a held state
#        self.hold = False

    def set_walltime(self, *args, **kwargs):
        if len(args) > 0:
            assert len(args)==1 and len(kwargs)==0 and isinstance(args[0],timedelta)
            self.walltime = args[0]
        else:
            self.walltime = timedelta(**kwargs)

#    def hold(h = True):
#        """ """
#        self.hold = h

    def dump(self):
        t = "#!%s\n" % shell_path
        if self.name:     t += render_option("job-name", self.name)
        if self.walltime: t += render_option("time", format_timedelta(self.walltime))
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
            self.job_id = int(job_id_regexp.match(stdoutdata).group(1))
            return self.job_id

def chain_jobs():
    # TODO
    pass
