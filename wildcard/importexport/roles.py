# for site-wide role assignments
# this handles groups and user assignments

# coding: utf-8
from Products.CMFPlone.utils import getToolByName
from Products.GenericSetup.utils import XMLAdapterBase
from zope.component import adapts
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.PlonePAS.interfaces.capabilities import IAssignRoleCapability


class RolesXMLAdapter(XMLAdapterBase):
    adapts(IAssignRoleCapability, ISetupEnviron)

    _LOGGER_ID = 'roleassignments.xml'

    name = 'roleassignments.xml'

    def roles(self):
        for id in self.context.listRoleIds():
            yield (id, self.context.listAssignedPrincipals(id))

    def _exportNode(self):
        """
        """
        pr = self.context
        root = self._getObjectNode('object')

        for role_id, principals in self.roles():
            info = pr.getRoleInfo(role_id)

            child = self._doc.createElement('role')
            child.setAttribute('id', role_id)
            child.setAttribute('title', info.pop('title', ''))
            child.setAttribute('description', info.pop('description', ''))

            for principal_id in principals:
                if type(principal_id) in (list, tuple, set):
                    principal_id = principal_id[0]
                assignment = self._doc.createElement('assignment')
                assignment.setAttribute('principal', principal_id)
                child.appendChild(assignment)
            root.appendChild(child)
        return root

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        for rolenode in node.getElementsByTagName('role'):
            id = rolenode.attributes['id'].value
            title = rolenode.attributes['title'].value
            description = rolenode.attributes['description'].value

            if id not in self.context.listRoleIds():
                self.context.addRole(id, title, description)

            currently_assigned = [a[0] for a in
                self.context.listAssignedPrincipals(id)]
            for assignmentnode in rolenode.getElementsByTagName('assignment'):
                principal = assignmentnode.attributes['principal'].value
                if principal not in currently_assigned:
                    self.context.assignRoleToPrincipal(id, principal)


def importRoleAssignments(context):
    site = context.getSite()
    acl = getToolByName(site, 'acl_users', None)
    pr = acl.portal_role_manager
    body = context.readDataFile('roleassignments.xml')
    if body:
        importer = RolesXMLAdapter(pr, context)
        importer.body = body


def exportRoleAssignments(context):
    site = context.getSite()
    acl = getToolByName(site, 'acl_users', None)
    pr = acl.portal_role_manager
    exporter = RolesXMLAdapter(pr, context)
    context.writeDataFile('roleassignments.xml', exporter.body,
        exporter.mime_type)
