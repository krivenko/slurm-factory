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
from __future__ import absolute_import, unicode_literals

import os
from subprocess import check_output
from warnings import warn

# Locate 'sbatch' binary
def locate_sbatch_path():
    for path in os.environ["PATH"].split(os.pathsep):
        p = os.path.join(path, "sbatch")
        if os.access(p, os.X_OK): default_sbatch_path = p

default_sbatch_path = locate_sbatch_path()
if not default_sbatch_path: warn("Could not locate 'sbatch' executable")

def slurm_version(sbatch_path = default_sbatch_path):
    output = check_output([sbatch_path, '--version'])
    return output.decode('utf-8').strip()

def slurm_version_info(sbatch_path = default_sbatch_path):
    sv = slurm_version(sbatch_path).replace('slurm', '').strip()
    def to_int_checked(x):
        try:
            return int(x)
        except ValueError:
            return x
    return tuple(map(to_int_checked, sv.split('.')))
