# coding: utf-8
from Products.CMFPlone.utils import getToolByName
from Products.GenericSetup.utils import XMLAdapterBase
from zope.component import adapts
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.PlonePAS.interfaces.group import IGroupManagement
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects


def _v(v):
    if _v is None:
        return ''
    return v


class GroupsXMLAdapter(XMLAdapterBase):
    adapts(IGroupManagement, ISetupEnviron)

    _LOGGER_ID = 'groups'

    name = 'groups'

    def groups(self):
        groups = []
        for id in self.context.getGroupIds():
            groups.append(self.context.getGroupInfo(id))
        return groups

    def _exportNode(self):
        """
        Export groups
        """
        root = self._getObjectNode('object')

        for group in self.groups():
            child = self._doc.createElement('group')
            child.setAttribute('id', _v(group['id']))
            child.setAttribute('title', _v(group['title']))
            child.setAttribute('description', _v(group['description']))
            root.appendChild(child)
        return root

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        groups = getToolByName(self.context, 'portal_groups')
        for groupnode in node.getElementsByTagName('group'):
            id = groupnode.attributes['id'].value
            title = groupnode.attributes['title'].value
            desc = groupnode.attributes['description'].value
            group = groups.getGroupById(id)
            if not group:
                groups.addGroup(id, (), (), title=title, description=desc)
            else:
                groups.editGroup(id, roles=None, groups=None,
                                     title=title, description=desc)


def importGroups(context):
    """Import actions tool.
    """
    site = context.getSite()
    acl = getToolByName(site, 'acl_users', None)
    groups = acl.source_groups
    importObjects(groups, '', context)


def exportGroups(context):
    """Export actions tool.
    """
    site = context.getSite()
    acl = getToolByName(site, 'acl_users', None)
    groups = acl.source_groups
    exportObjects(groups, '', context)
