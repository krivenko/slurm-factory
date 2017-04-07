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

from .job import SLURMJob

class CrayJob(SLURMJob):
    """
    TODO
    """

    def __init__(self, **kwargs):
        """
        TODO
        """
        SLURMJob.__init__(self, **kwargs)

    def network(self, type = None):
        """
        TODO
        """
        self._add_option('network', type, [(lambda t: t in ('system','blade'),
                                            "network type must be either 'system' or 'blade'")])

    def dump(self):
        """
        TODO
        """
        if 'network' in self.options:
            self.options['exclusive'] = True

        return SLURMJob.dump(self)
