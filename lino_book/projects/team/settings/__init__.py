# -*- coding: UTF-8 -*-
# Copyright 2014-2017 Luc Saffre
# License: BSD (see file COPYING for details)
"""

.. autosummary::
   :toctree:

   doctests
   demo
   www



"""

from lino_noi.lib.noi.settings import *


class Site(Site):
    
    def get_installed_apps(self):
        """Implements :meth:`lino.core.site.Site.get_installed_apps` for Lino
        Noi.

        """
        yield super(Site, self).get_installed_apps()
        yield 'lino.modlib.restful'
        yield 'lino_xl.lib.caldav'