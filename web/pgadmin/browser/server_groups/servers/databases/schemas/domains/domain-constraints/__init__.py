##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Implements the Domain Constraint Module."""

import json
from flask import render_template, make_response, request, jsonify
from flask.ext.babel import gettext
from pgadmin.utils.ajax import make_json_response, \
    make_response as ajax_response, internal_server_error
from pgadmin.browser.utils import PGChildNodeView
from pgadmin.browser.collection import CollectionNodeModule
import pgadmin.browser.server_groups.servers.databases.schemas.domains \
    as domains
from pgadmin.utils.ajax import precondition_required
from pgadmin.utils.driver import get_driver
from config import PG_DEFAULT_DRIVER
from functools import wraps


class DomainConstraintModule(CollectionNodeModule):
    """
    class DomainConstraintModule(CollectionNodeModule):

        This class represents The Domain Constraint Module.

    Methods:
    -------
    * __init__(*args, **kwargs)
      - Initialize the Domain Constraint Module.

    * get_nodes(gid, sid, did, scid)
      - Generate the Domain Constraint collection node.

    * node_inode(gid, sid, did, scid)
      - Returns Domain Constraint node as leaf node.

    * script_load()
      - Load the module script for the Domain Constraint, when any of the
        Domain node is initialized.
    """
    NODE_TYPE = 'domain-constraints'
    COLLECTION_LABEL = gettext("Domain Constraints")

    def __init__(self, *args, **kwargs):
        super(DomainConstraintModule, self).__init__(*args, **kwargs)
        self.min_ver = None
        self.max_ver = None

    def get_nodes(self, gid, sid, did, scid, doid):
        """
        Generate the Domain Constraint collection node.
        """
        yield self.generate_browser_collection_node(doid)

    @property
    def node_inode(self):
        """
        Returns Domain Constraint node as leaf node.
        """
        return False

    @property
    def script_load(self):
        """
        Load the module script for the Domain Constraint, when any of the
        Domain node is initialized.
        """
        return domains.DomainModule.NODE_TYPE

    @property
    def csssnippets(self):
        """
        Returns a snippet of css to include in the page
        """
        return [
                render_template(
                    "domain-constraints/css/domain-constraints.css",
                    node_type=self.node_type
                    )
                ]



blueprint = DomainConstraintModule(__name__)


class DomainConstraintView(PGChildNodeView):
    """
    class DomainConstraintView(PGChildNodeView):

    This class inherits PGChildNodeView to get the different routes for
    the module.

    The class is responsible to Create, Read, Update and Delete operations for
    the Domain Constraint.

    Methods:
    -------

    * module_js():
      - Load JS file (domain-constraints.js) for this module.

    * check_precondition(f):
      - Works as a decorator.
      -  Checks database connection status.
      -  Attach connection object and template path.

    * list(gid, sid, did, scid, doid):
      - List the Domain Constraints.

    * nodes(gid, sid, did, scid):
      - Returns all the Domain Constraints to generate Nodes in the browser.

    * properties(gid, sid, did, scid, doid):
      - Returns the Domain Constraint properties.

    * create(gid, sid, did, scid):
      - Creates a new Domain Constraint object.

    * update(gid, sid, did, scid, doid):
      - Updates the Domain Constraint object.

    * delete(gid, sid, did, scid, doid):
      - Drops the Domain Constraint object.

    * sql(gid, sid, did, scid, doid=None):
      - Returns the SQL for the Domain Constraint object.

    * msql(gid, sid, did, scid, doid=None):
      - Returns the modified SQL.

    * get_sql(gid, sid, data, scid, doid=None):
      - Generates the SQL statements to create/update the Domain Constraint.
        object.

    * dependents(gid, sid, did, scid, doid, coid):
      - Returns the dependents for the Domain Constraint object.

    * dependencies(gid, sid, did, scid, doid, coid):
      - Returns the dependencies for the Domain Constraint object.
    """
    node_type = blueprint.node_type

    parent_ids = [
        {'type': 'int', 'id': 'gid'},
        {'type': 'int', 'id': 'sid'},
        {'type': 'int', 'id': 'did'},
        {'type': 'int', 'id': 'scid'},
        {'type': 'int', 'id': 'doid'}
    ]
    ids = [
        {'type': 'int', 'id': 'coid'}
    ]

    operations = dict({
        'obj': [
            {'get': 'properties', 'delete': 'delete', 'put': 'update'},
            {'get': 'list', 'post': 'create'}
        ],
        'delete': [{'delete': 'delete'}],
        'children': [{'get': 'children'}],
        'nodes': [{'get': 'node'}, {'get': 'nodes'}],
        'sql': [{'get': 'sql'}],
        'msql': [{'get': 'msql'}, {'get': 'msql'}],
        'stats': [{'get': 'statistics'}],
        'dependency': [{'get': 'dependencies'}],
        'dependent': [{'get': 'dependents'}],
        'module.js': [{}, {}, {'get': 'module_js'}]
    })

    def validate_request(f):
        """
        Works as a decorator.
        Validating request on the request of create, update and modified SQL.

        Required Args:
                    name: Name of the Domain Constraint
                    consrc: Check Constraint Definition

        Above both the arguments will not be validated in the update action.
        """

        @wraps(f)
        def wrap(self, **kwargs):

            data = {}
            if request.data:
                req = json.loads(request.data.decode())
            else:
                req = request.args or request.form

            if 'coid' not in kwargs:
                required_args = [
                    'name',
                    'consrc'
                ]

                for arg in required_args:
                    if arg not in req or req[arg] == '':
                        return make_json_response(
                            status=410,
                            success=0,
                            errormsg=gettext(
                                "Couldn't find the required parameter \
                                (%s)." % arg
                            )
                        )

            try:
                for key in req:
                    if key == 'convalidated':
                        data[key] = True if (req[key] == 'true' or req[key] is
                                             True) else False
                    else:
                        data[key] = req[key]

            except Exception as e:
                return internal_server_error(errormsg=str(e))

            self.request = data
            return f(self, **kwargs)

        return wrap

    def module_js(self):
        """
        Load JS file (domain-constraints.js) for this module.
        """
        return make_response(
            render_template(
                "domain-constraints/js/domain-constraints.js",
                _=gettext
            ),
            200, {'Content-Type': 'application/x-javascript'}
        )

    def check_precondition(f):
        """
        Works as a decorator.
        Checks database connection status.
        Attach connection object and template path.
        """
        @wraps(f)
        def wrap(*args, **kwargs):
            self = args[0]
            driver = get_driver(PG_DEFAULT_DRIVER)
            self.manager = driver.connection_manager(kwargs['sid'])
            self.conn = self.manager.connection(did=kwargs['did'])
            self.qtIdent = driver.qtIdent

            # If DB not connected then return error to browser
            if not self.conn.connected():
                return precondition_required(
                    gettext("Connection to the server has been lost!")
                )

            ver = self.manager.version

            # we will set template path for sql scripts
            if ver >= 90200:
                self.template_path = 'domain-constraints/sql/9.2_plus'
            elif ver >= 90100:
                self.template_path = 'domain-constraints/sql/9.1_plus'

            return f(*args, **kwargs)

        return wrap

    @check_precondition
    def list(self, gid, sid, did, scid, doid):
        """
        List the Domain Constraints.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
        """
        SQL = render_template("/".join([self.template_path,
                                        'properties.sql']),
                              doid=doid)
        status, res = self.conn.execute_dict(SQL)

        if not status:
            return internal_server_error(errormsg=res)
        return ajax_response(
            response=res['rows'],
            status=200
        )

    @check_precondition
    def nodes(self, gid, sid, did, scid, doid):
        """
        Returns all the Domain Constraints.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
        """
        res = []
        SQL = render_template("/".join([self.template_path,
                                        'properties.sql']),
                              doid=doid)
        status, rset = self.conn.execute_2darray(SQL)

        if not status:
            return internal_server_error(errormsg=rset)

        for row in rset['rows']:
            if 'convalidated' not in row:
                icon = 'icon-domain-constraints'
            elif row['convalidated']:
                icon = 'icon-domain-constraints'
            else:
                icon = 'icon-domain-constraints-bad'
            res.append(
                self.blueprint.generate_browser_node(
                    row['oid'],
                    doid,
                    row['name'],
                    icon=icon
                ))

        return make_json_response(
            data=res,
            status=200
        )

    @check_precondition
    def properties(self, gid, sid, did, scid, doid, coid):
        """
        Returns the Domain Constraints property.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """

        SQL = render_template("/".join([self.template_path,
                                        'properties.sql']),
                              doid=doid, coid=coid)
        status, res = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)

        data = res['rows'][0]
        return ajax_response(
            response=data,
            status=200
        )

    @check_precondition
    @validate_request
    def create(self, gid, sid, did, scid, doid):
        """
        Creates a new Domain Constraint object.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id

        Returns:
            Domain Constraint object in json format.
        """
        data = self.request
        try:
            status, SQL = self.get_sql(gid, sid, data, scid, doid)
            if not status:
                return internal_server_error(errormsg=SQL)

            status, res = self.conn.execute_scalar(SQL)

            if not status:
                return internal_server_error(errormsg=res)

            # Get the recently added constraints oid
            SQL = render_template("/".join([self.template_path,
                                            'get_oid.sql']),
                                  doid=doid, name=data['name'])
            status, coid = self.conn.execute_scalar(SQL)
            if not status:
                return internal_server_error(errormsg=coid)

            if 'convalidated' not in data:
                icon = 'icon-domain-constraints'
            elif 'convalidated' in data and data['convalidated']:
                icon = 'icon-domain-constraints'
            else:
                icon = 'icon-domain-constraints-bad'

            return jsonify(
                node=self.blueprint.generate_browser_node(
                    coid,
                    doid,
                    data['name'],
                    icon=icon
                )
            )
        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def delete(self, gid, sid, did, scid, doid, coid):
        """
        Drops the Domain Constraint object.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """
        try:
            SQL = render_template("/".join([self.template_path,
                                            'properties.sql']),
                                  doid=doid, coid=coid)
            status, res = self.conn.execute_dict(SQL)

            if not status:
                return internal_server_error(errormsg=res)

            data = res['rows'][0]

            SQL = render_template("/".join([self.template_path,
                                            'delete.sql']),
                                  data=data)
            status, res = self.conn.execute_scalar(SQL)
            if not status:
                return internal_server_error(errormsg=res)

            return make_json_response(
                success=1,
                info=gettext("Domain Constraint dropped"),
                data={
                    'id': doid,
                    'scid': scid,
                    'sid': sid,
                    'gid': gid,
                    'did': did
                }
            )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    @validate_request
    def update(self, gid, sid, did, scid, doid, coid):
        """
        Updates the Domain Constraint object.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """
        data = self.request
        status, SQL = self.get_sql(gid, sid, data, scid, doid, coid)

        try:
            if SQL and status:
                status, res = self.conn.execute_scalar(SQL)
                if not status:
                    return internal_server_error(errormsg=res)

                if 'convalidated' in data and data['convalidated']:
                    icon = 'icon-domain-constraints'
                elif 'convalidated' in data and not data['convalidated']:
                    icon = 'icon-domain-constraints-bad'
                else:
                    icon = ''

                return make_json_response(
                    success=1,
                    info="Domain Constraint updated",
                    data={
                        'id': coid,
                        'doid': doid,
                        'scid': scid,
                        'sid': sid,
                        'gid': gid,
                        'did': did,
                        'icon': icon
                    }
                )
            else:
                return make_json_response(
                    success=1,
                    info="Nothing to update",
                    data={
                        'id': coid,
                        'doid': doid,
                        'scid': scid,
                        'sid': sid,
                        'gid': gid,
                        'did': did
                    }
                )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    @check_precondition
    def sql(self, gid, sid, did, scid, doid, coid=None):
        """
        Returns the SQL for the Domain Constraint object.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """

        # Get Schema and Domain.
        domain, schema = self._get_domain(doid)

        SQL = render_template("/".join([self.template_path,
                                        'properties.sql']),
                              doid=doid, coid=coid)
        status, res = self.conn.execute_dict(SQL)
        if not status:
            return internal_server_error(errormsg=res)

        data = res['rows'][0]

        SQL = render_template("/".join([self.template_path,
                                        'create.sql']),
                              data=data, domain=domain, schema=schema)

        sql_header = """-- CHECK: {1}.{0}

-- ALTER DOMAIN {1} DROP CONSTRAINT {0};

""".format(data['name'], schema + '.' + domain)

        SQL = sql_header + SQL

        return ajax_response(response=SQL)

    @check_precondition
    @validate_request
    def msql(self, gid, sid, did, scid, doid, coid=None):
        """
        Returns the modified SQL.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id

        Returns:
            Domain Constraint object in json format.
        """
        data = self.request

        status, SQL = self.get_sql(gid, sid, data, scid, doid, coid)
        if status and SQL:
            return make_json_response(
                data=SQL,
                status=200
            )
        else:
            return SQL

    def get_sql(self, gid, sid, data, scid, doid, coid=None):
        """
        Generates the SQL statements to create/update the Domain Constraint.

         Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """
        try:
            if coid is not None:
                SQL = render_template("/".join([self.template_path,
                                                'properties.sql']),
                                      doid=doid, coid=coid)
                status, res = self.conn.execute_dict(SQL)

                if not status:
                    return False, internal_server_error(errormsg=res)

                old_data = res['rows'][0]

                SQL = render_template(
                    "/".join([self.template_path, 'update.sql']),
                    data=data, o_data=old_data, conn=self.conn
                    )
            else:
                domain, schema = self._get_domain(doid)

                SQL = render_template("/".join([self.template_path,
                                                'create.sql']),
                                      data=data, domain=domain, schema=schema)
            return True, SQL.strip('\n')
        except Exception as e:
            return False, internal_server_error(errormsg=str(e))

    def _get_domain(self, doid):
        """
        Returns Domain and Schema name.

        Args:
            doid: Domain Id

        """
        SQL = render_template("/".join([self.template_path,
                                        'get_domain.sql']),
                              doid=doid)
        status, res = self.conn.execute_2darray(SQL)

        if not status:
            return False, internal_server_error(errormsg=res)

        return res['rows'][0]

    @check_precondition
    def dependents(self, gid, sid, did, scid, doid, coid):
        """
        This function get the dependents and return ajax response
        for the Domain Constraint node.

        Args:
            gid:  Server Group Id
            sid:  Server Id
            did:  Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """
        dependents_result = self.get_dependents(self.conn, coid)
        return ajax_response(
                response=dependents_result,
                status=200
                )

    @check_precondition
    def dependencies(self, gid, sid, did, scid, doid, coid):
        """
        This function get the dependencies and return ajax response
        for the Domain Constraint node.

        Args:
            gid: Server Group Id
            sid: Server Id
            did: Database Id
            scid: Schema Id
            doid: Domain Id
            coid: Domain Constraint Id
        """
        dependencies_result = self.get_dependencies(self.conn, coid)
        return ajax_response(
                response=dependencies_result,
                status=200
                )

DomainConstraintView.register_node_view(blueprint)
