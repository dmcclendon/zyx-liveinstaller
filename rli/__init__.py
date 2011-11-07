#############################################################################
#############################################################################
##
## rli: Support for installing a running LiveOS onto system storage volume(s)
##      (rebootlessly)
##
##  Copyright 2009, Douglas McClendon <dmc AT viros DOT org>
##
#############################################################################
#############################################################################


#############################################################################
#############################################################################
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#############################################################################
#############################################################################

from rli.installer import *

"""A class for rebootlessly installing a running LiveOS.

The following main installer class is exported:
  - ZyXLiveInstaller - installs running LiveOS to one or more storage volumes

Also exported is:
  - ZyXLiveInstallerError - all exceptions thrown are of this type

"""

__all__ = (
    'ZyXLiveInstallerError',
    'ZyXLiveInstaller',
)    
