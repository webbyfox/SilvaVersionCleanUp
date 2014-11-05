# -*- coding: iso-8859-1 -*-
# Copyright (c) 2003-2007 ETH Zurich, IT services. Written by Benno Luthiger. All rights reserved.
# See also LICENSE.txt
# $Revision: 3663 $

import os
from datetime import datetime, timedelta

# Zope
from AccessControl import ClassSecurityInfo, Permissions
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from zope.interface import implements
from DateTime import DateTime

#Formulator
from Products.Formulator.Form import ZMIForm
from Products.Formulator.XMLToForm import XMLToForm

#Silva
from Products.Silva.mangle import Id
from Products.Silva.adapters.version_management import getVersionManagementAdapter
from Products.Silva.helpers import add_and_edit

DOCUMENTS = ['Silva Document', 'IMAP Calendar List', 'Silva Personal Information', 'Silva VVZ Page']
CONTAINERS = ['Silva Folder','Silva Publication']

defaultMaxAge = 300

class ObjecScanner:
    '''
    Scans the ZODB for the objects defined in DOCUMENTS.
    '''

    def __init__(self):
        self._feedback = {'folders':0, 'documents':0}

    def start_scan(self, this_container, depth):
        self._feedback = {'folders':0, 'documents':0}
        self._scan_objects_in(this_container, depth)

    def _scan_objects_in(self, this_container, depth):
        self._scan_docs(this_container)
        if depth:
            for folder in this_container.objectValues(CONTAINERS):
                self._scan_objects_in(folder, depth-1)

    def _scan_docs(self, this_container):
        '''
        @param this_container: the actual container
        '''
        self._feedback['folders'] = self._feedback['folders'] + 1
        for model in this_container.objectValues(DOCUMENTS):
            self._feedback['documents'] = self._feedback['documents'] + 1
            self.process_doc(model)

    def process_doc(self, model):
        '''
        Subclasses must implement this method.
        @param model: the actual Silva document
        '''
        pass

class VersionCleanUp(SimpleItem, ObjecScanner):
    __doc__ = '''
    Helper module to clean up stale versions in Silva documents.
    '''

    meta_type = 'Silva Version CleanUp'
    security = ClassSecurityInfo()

    security.declareProtected(Permissions.view_management_screens, 'manage_objectEdit')
    manage_objectEdit = PageTemplateFile(
        'www/VersionCleanUpEdit', globals(),  __name__='VersionCleanUpEdit')

    security.declareProtected(Permissions.view_management_screens, 'manage_workspace')
    manage_workspace = manage_objectEdit

    def __init__(self, id, max_age, number_to_keep, pub_path):
        SimpleItem.inheritedAttribute('__init__')(self, id, '[VersionCleanUp Helper object]')
        self.id = id
        self._description = self.__doc__
        self._max_age = self._number_to_keep = self._removed = 0
        self._pub_path = pub_path
        self.set_max_age(max_age)
        self.set_number_to_keep(number_to_keep)
        self.set_pub_path(pub_path)

    security.declareProtected(Permissions.view_management_screens, 'manage_editVersionCleanUp')
    def manage_editVersionCleanUp(self, REQUEST=None):
        '''
        Stores the changed values.
        @param REQUEST:
        '''
        self.set_max_age(REQUEST.get("max_age"))
        self.set_number_to_keep(REQUEST.get("number_to_keep"))
        self.set_pub_path(REQUEST.get("pub_path"))
        return self.manage_workspace(manage_tabs_message='Saved changed values.')

    security.declareProtected(Permissions.view_management_screens, 'get_title')
    def get_title(self):
        """Fix title for this object."""
        return "VersionCleanUp Helper object"

    security.declareProtected(Permissions.view_management_screens, 'max_age')
    def max_age(self):
        return self._max_age

    security.declareProtected(Permissions.view_management_screens, 'set_max_age')
    def set_max_age(self, max_age):
        try:
            self._max_age = int(max_age)
        except:
            self._max_age = defaultMaxAge

    security.declareProtected(Permissions.view_management_screens, 'number_to_keep')
    def number_to_keep(self):
        return self._number_to_keep

    security.declareProtected(Permissions.view_management_screens, 'set_number_to_keep')
    def set_number_to_keep(self, number_to_keep):
        try:
            self._number_to_keep = int(number_to_keep)
        except:
            self._number_to_keep = None


    security.declareProtected(Permissions.view_management_screens, 'pub_path')
    def pub_path(self):
        return self._pub_path


    security.declareProtected(Permissions.view_management_screens, 'set_pub_path')
    def set_pub_path(self, pub_path):
        try:
            self._pub_path = str(pub_path)
        except:
            self._pub_path = None

    def startCleanUp(self):
        '''
        Starts the clean up of old versions of Silva documents.
        '''
        self._removed = 0

        path = self.restrictedTraverse(self._pub_path)

        if not path:
            path = self.aq_parent

        self.start_scan(path, -1)
        msg = "Scanned %i documents in %i folders. %i versions removed" %(self._feedback.get("documents"),
                                                                          self._feedback.get("folders"),
                                                                          self._removed)
        return self.manage_workspace(manage_tabs_message=msg)

    def process_doc(self, model):
        '''
        @param model:
        '''
        self._deleteOldVersionsByAge(model, self._max_age, self._number_to_keep)

    def _deleteOldVersionsByAge(self, model, max_age, number_to_keep=None):
        """Delete old versions.

        Deletes all version older than max_age (in days),
        but keep at least number_to_keep versions (if provided).

        @param model: the Silva document to process
        @param max_age: days, versions older than the max_age are scheduled for deletion
        @param number_to_keep: (if provided) number of versions to keep despite of old age
        """
        adapter = getVersionManagementAdapter(model)

        version_ids = self._getOldVersionIds(adapter)
        if number_to_keep is not None:
            if len(version_ids) < number_to_keep:
                return
            version_ids = version_ids[:-number_to_keep]

        then = datetime.now() - timedelta(days=max_age)
        oldest_time = DateTime(then.isoformat())

        index = None
        for id in version_ids:
            if adapter.getVersionModificationTime(id) >= oldest_time:
                break
            index = version_ids.index(id)

        delete_ids = []
        if index is not None:
            delete_ids = version_ids[:index]
        self._removed += len(delete_ids)
        model.manage_delObjects(delete_ids)

    def _getOldVersionIds(self, model):
        unapproved = model.getUnapprovedVersion()
        approved = model.getApprovedVersion()
        public = model.getPublishedVersion()
        version_ids = model.getVersionIds()
        if unapproved is not None and unapproved.id in version_ids:
            version_ids.remove(unapproved.id)
        if approved is not None and unapproved.id in version_ids:
            version_ids.remove(approved.id)
        if public is not None and public.id in version_ids:
            version_ids.remove(public.id)
        return version_ids

InitializeClass(VersionCleanUp)

manage_addVersionCleanUpForm = PageTemplateFile("www/VersionCleanUpAdd", globals(),
                                            __name__='manage_addVersionCleanUpForm')

def manage_addVersionCleanUp(self, id, max_age, number_to_keep=None, pub_path=None, REQUEST=None):
    """Add a VersionCleanUp object."""
    if not Id(self, id).isValid():
        return
    object = VersionCleanUp(id, max_age, number_to_keep, pub_path)
    self._setObject(id, object)
    add_and_edit(self, id, REQUEST, 'manage_workspace')
    return ''