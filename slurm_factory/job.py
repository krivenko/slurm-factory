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

class SLURMJob:
    """Description of a SLURM job"""

    def __init__(self, **kwargs):
        self.submitted = False
        self.hold = False

        # Job Name
        self.name = kwargs.pop('name','')

        # List of jobs, this job depends on
#       self.dependencies = []

    #def add_dependency(job):
    #    """Add a new dependency"""
    #    self.dependencies.append(job)

#        # Submit in a held state
#        self.hold = False

#    def hold(h = True):
#        """ """
#        self.hold = h

    def dump(self):
        text = "#!%s\n" % shell_path
        if self.name: text += "#SBATCH --job-name=%s\n" % self.name
        return text

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
