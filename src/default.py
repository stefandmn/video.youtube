# -*- coding: utf-8 -*-

from modshell import ModuleRunner as module
from resources.lib import provider

# Instantiate and run YouTube provider
module.run(provider.Provider())
