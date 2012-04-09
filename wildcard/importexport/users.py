from Products.GenericSetup.interfaces import IBody
from zope.interface import implements
# coding: utf-8
from Products.CMFPlone.utils import getToolByName
from Products.GenericSetup.utils import XMLAdapterBase
from zope.component import adapts
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.PlonePAS.interfaces.plugins import IUserManagement
from DateTime import DateTime


def getPropMap(md):
    prop_map = {}
    for prop in md._propertyMap():
        prop_map[prop['id']] = prop
    return prop_map


class UsersXMLAdapter(XMLAdapterBase):
    adapts(IUserManagement, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = 'users'

    name = 'users'

    def users(self):
        mt = getToolByName(self.context, 'portal_membership')
        users = []
        for id in mt.listMemberIds():
            member = mt.getMemberById(id)
            data = {
                'id': id,
                'login': self.context._userid_to_login[id],
                'password': self.context._user_passwords[id],
                'groups': member.getGroups()
            }
            data.update(mt.getMemberInfo(id))
            users.append(data)
        return users

    def _exportNode(self):
        """
        Export users:
            - member data
            - groups
        """
        memberdata = getToolByName(self.context, 'portal_memberdata')
        root = self._getObjectNode('object')

        for user in self.users():
            child = self._doc.createElement('user')
            child.setAttribute('id', user.pop('id'))
            child.setAttribute('login', user.pop('login'))
            child.setAttribute('password', user.pop('password'))

            prop_map = getPropMap(memberdata)
            memberdatanode = self._doc.createElement('memberdata')
            groups = user.pop('groups')
            for key, value in user.items():
                if key not in prop_map:
                    continue
                prop = prop_map[key]
                propele = self._doc.createElement('property')
                propele.setAttribute('name', key)
                if prop['type'] == 'string':
                    propele.setAttribute('value', value)
                elif prop['type'] == 'boolean':
                    propele.setAttribute('value', str(value))
                elif prop['type'] == 'date':
                    propele.setAttribute('value', value.ISO())
                elif prop['type'] == 'float':
                    propele.setAttribute('value', str(value))
                elif prop['type'] == 'text':
                    propele.appendChild(self._doc.createTextNode(value))
                memberdatanode.appendChild(propele)
            child.appendChild(memberdatanode)
            groupsnode = self._doc.createElement('groups')
            for group in groups:
                if group == 'AuthenticatedUsers':
                    continue
                groupnode = self._doc.createElement('group')
                groupnode.setAttribute('id', group)
                groupsnode.appendChild(groupnode)
            child.appendChild(groupsnode)
            root.appendChild(child)
        return root

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        memberdata = getToolByName(self.context, 'portal_memberdata')
        pm = getToolByName(self.context, 'portal_membership')
        acl = getToolByName(self.context, 'acl_users')
        portal_groups = getToolByName(self.context, 'portal_groups')
        prop_map = getPropMap(memberdata)
        for usernode in node.getElementsByTagName('user'):
            userid = usernode.attributes['id'].value
            login = usernode.attributes['login'].value
            passwd = usernode.attributes['password'].value
            props = {}

            properties = usernode.getElementsByTagName('memberdata')[0]
            for propnode in properties.getElementsByTagName('property'):
                name = propnode.attributes['name'].value
                prop = prop_map[name]
                if prop['type'] == 'string':
                    value = propnode.attributes['value'].value
                elif prop['type'] == 'boolean':
                    value = propnode.attributes['value'].value
                    if value.lower() == 'true':
                        value = True
                    else:
                        value = False
                elif prop['type'] == 'date':
                    value = DateTime(propnode.attributes['value'].value)
                elif prop['type'] == 'float':
                    value = float(propnode.attributes['value'].value)
                elif prop['type'] == 'text':
                    if len(propnode.childNodes) == 0:
                        value = ''
                    else:
                        value = propnode.toxml()
            member = pm.getMemberById(userid)
            if member is None:
                acl._doAddUser(userid, passwd, (), None)
                member = pm.getMemberById(userid)
            member.setMemberProperties(props)

            self.context.updateUser(userid, login)
            self.context._user_passwords[userid] = passwd

            groupsnode = usernode.getElementsByTagName('groups')[0]
            existing_groups = portal_groups.getGroupsByUserId(userid)
            for groupnode in groupsnode.getElementsByTagName('group'):
                groupid = groupnode.attributes['id'].value
                if groupid not in existing_groups:
                    portal_groups.addPrincipalToGroup(userid, groupid)


def importUsers(context):
    site = context.getSite()
    acl = getToolByName(site, 'acl_users', None)
    users = acl.source_users
    body = context.readDataFile('users.xml')
    if body:
        importer = UsersXMLAdapter(users, context)
        importer.body = body


def exportUsers(context):
    site = context.getSite()
    acl = getToolByName(site, 'acl_users', None)
    users = acl.source_users
    exporter = UsersXMLAdapter(users, context)
    context.writeDataFile('users.xml', exporter.body, exporter.mime_type)
