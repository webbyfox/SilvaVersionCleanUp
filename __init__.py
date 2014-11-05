# -*- coding: iso-8859-1 -*-
# Copyright (c) 2003-2007 ETH Zurich, IT services. Written by Benno Luthiger. All rights reserved.
# See also LICENSE.txt
# $Revision: 3663 $

from Products.SilvaVersionCleanUp import VersionCleanUp

def initialize(context):

    context.registerClass(
        VersionCleanUp.VersionCleanUp,
        constructors = (VersionCleanUp.manage_addVersionCleanUpForm,
                        VersionCleanUp.manage_addVersionCleanUp),
        icon = "www/version_cleanup.gif"
    )