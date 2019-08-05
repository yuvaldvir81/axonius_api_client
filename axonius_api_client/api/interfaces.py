# -*- coding: utf-8 -*-
"""Axonius API Client package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc

import six

from . import routers, utils
from .. import tools, constants, exceptions, models


@six.add_metaclass(abc.ABCMeta)
class UserDeviceModel(object):
    """Mixins for User & Device models."""

    @abc.abstractproperty
    def _default_fields(self):
        """Fields to set as default for methods with fields as kwargs.

        Returns:
            :obj:`dict`

        """
        raise NotImplementedError  # pragma: no cover

    def get_fields(self):
        """Get the fields.

        Notes:
            Will only return fields on Axonius v2.7 or greater. Caches result to self.

        Returns:
            :obj:`dict`

        """
        if not getattr(self, "_fields", None):
            self._fields = self._request(method="get", path=self._router.fields)
        return self._fields

    # FUTURE: needs tests
    def get_labels(self):
        """Get the labels.

        Returns:
            :obj:`list` of :obj:`str`

        """
        return self._request(method="get", path=self._router.labels)

    # FUTURE: needs tests
    def add_labels_by_rows(self, rows, labels):
        """Add labels to objects using rows returned from :meth:`get`.

        Args:
            rows (:obj:`list` of :obj:`dict`):
                Rows returned from :meth:`get`
            labels (:obj:`list` of `str`):
                Labels to add to rows.

        Returns:
            :obj:`int`: Number of objects that had labels added

        """
        ids = [row["internal_axon_id"] for row in rows]

        processed = 0

        # only do 100 labels at a time, more seems to break API
        for group in tools.grouper(ids, 100):
            group = [x for x in group if x is not None]
            response = self._add_labels(labels=labels, ids=group)
            processed += response

        return processed

    # FUTURE: needs tests
    def add_labels_by_query(self, query, labels):
        """Add labels to objects using a query to select objects.

        Args:
            query (:obj:`str`):
                Query built from Query Wizard in GUI to select objects to add labels to.
            labels (:obj:`list` of `str`):
                Labels to add to rows returned from query.

        Returns:
            :obj:`int`: Number of objects that had labels added

        """
        rows = list(self.get(query=query, default_fields=False))
        return self.add_labels_by_rows(rows=rows, labels=labels)

    # FUTURE: needs tests
    def delete_labels_by_rows(self, rows, labels):
        """Delete labels from objects using rows returned from :meth:`get`.

        Args:
            rows (:obj:`list` of :obj:`dict`):
                Rows returned from :meth:`get`
            labels (:obj:`list` of `str`):
                Labels to delete from rows.

        Returns:
            :obj:`int`: Number of objects that had labels deleted.

        """
        ids = [row["internal_axon_id"] for row in rows]

        processed = 0

        # only do 100 labels at a time, more seems to break API
        for group in tools.grouper(ids, 100):
            group = [x for x in group if x is not None]
            response = self._delete_labels(labels=labels, ids=group)
            processed += response

        return processed

    # FUTURE: needs tests
    def delete_labels_by_query(self, query, labels):
        """Delete labels from objects using a query to select objects.

        Args:
            query (:obj:`str`):
                Query built from Query Wizard in GUI to select objects to delete labels
                from.
            labels (:obj:`list` of `str`):
                Labels to delete from rows returned from query.

        Returns:
            :obj:`int`: Number of objects that had labels deleted

        """
        rows = list(self.get(query=query, default_fields=False))
        return self.delete_labels_by_rows(rows=rows, labels=labels)

    def create_saved_query(
        self,
        name,
        query,
        page_size=constants.GUI_PAGE_SIZES[0],
        sort_field="",
        sort_descending=True,
        sort_adapter="generic",
        **fields
    ):
        """Create a saved query.

        Args:
            name (:obj:`str`):
                Name of saved query to create.
            query (:obj:`str`):
                Query built from Query Wizard in GUI to use in saved query.
            page_size (:obj:`int`, optional):
                Number of rows to show in each page in GUI.

                Defaults to: first item in
                :data:`axonius_api_client.constants.GUI_PAGE_SIZES`.
            sort_field (:obj:`str`, optional):
                Name of field to sort results on.

                Defaults to: "".
            sort_descending (:obj:`bool`, optional):
                Sort sort_field descending.

                Defaults to: True.
            sort_adapter (:obj:`str`, optional):
                Name of adapter sort_field is from.

                Defaults to: "generic".

        Returns:
            :obj:`str`: The ID of the new saved query.

        """
        # FUTURE: needs tests
        if page_size not in constants.GUI_PAGE_SIZES:
            msg = "page_size {size} invalid, must be one of {sizes}"
            msg = msg.format(size=page_size, sizes=constants.GUI_PAGE_SIZES)
            raise exceptions.ApiError(msg)

        utils.check_max_page_size(page_size=page_size)
        for k, v in self._default_fields.items():
            fields.setdefault(k, v)

        known_fields = self.get_fields()
        validated_fields = utils.validate_fields(known_fields=known_fields, **fields)

        if sort_field:
            sort_field = utils.find_field(
                name=sort_field, fields=known_fields, adapter=sort_adapter
            )

        data = {}
        data["name"] = name
        data["query_type"] = "saved"
        data["view"] = {}
        data["view"]["fields"] = validated_fields

        # FUTURE: find out what this is
        data["view"]["historical"] = None

        # FUTURE: find out if this only impacts GUI
        data["view"]["columnSizes"] = []

        # FUTURE: find out if this only impacts GUI
        data["view"]["page"] = 0

        # FUTURE: find out if this only impacts GUI
        data["view"]["pageSize"] = page_size

        data["view"]["query"] = {}

        # FUTURE: validate 'expressions' is not needed
        # data["view"]["query"]["expressions"] = []

        data["view"]["query"]["filter"] = query
        data["view"]["sort"] = {}
        data["view"]["sort"]["desc"] = sort_descending
        data["view"]["sort"]["field"] = sort_field

        return self._request(method="post", path=self._router.views, json=data)

    def delete_saved_query_by_name(self, name, regex=False, only1=True):
        """Delete a saved query by name.

        Args:
            name (:obj:`str`):
                Name of saved query to delete.
            regex (:obj:`bool`, optional):
                Search for name using regex.

                Defaults to: False.
            only1 (:obj:`bool`, optional):
                Only allow one match to name.

                Defaults to: True.

        Returns:
            :obj:`str`: empty string

        """
        found = self.get_saved_query_by_name(name=name, regex=regex, only1=True)
        ids = [x["uuid"] for x in found] if isinstance(found, list) else [found["uuid"]]
        return self._delete_saved_query(ids=ids)

    def get_saved_query(
        self, query=None, page_size=constants.DEFAULT_PAGE_SIZE, max_rows=0
    ):
        """Get saved queries using paging.

        Args:
            query (:obj:`str`, optional):
                Query to filter rows to return. This is NOT a query built by
                the Query Wizard in the GUI. This is something else. See
                :meth:`get_saved_query_by_name` for an example query.

                Defaults to: None.
            page_size (:obj:`int`, optional):
                Get N rows per page.

                Defaults to: :data:`axonius_api_client.constants.DEFAULT_PAGE_SIZE`.
            max_rows (:obj:`int`, optional):
                If not 0, only return up to N rows.

                Defaults to: 0.

        Yields:
            :obj:`dict`: Each row found in 'assets' from return.

        """
        page = self._get_saved_query(query=query, page_size=page_size, row_start=0)

        for row in page["assets"]:
            yield row

        seen = len(page["assets"])

        while True:
            page = self._get_saved_query(
                query=query, page_size=page_size, row_start=seen
            )

            for row in page["assets"]:
                yield row

            if (max_rows and seen >= max_rows) or not page["assets"]:
                break

            seen += len(page["assets"])

    def get_saved_query_by_name(self, name, regex=True, only1=False):
        """Get saved queries by name using paging.

        Args:
            name (:obj:`str`):
                Name of saved query to get.
            regex (:obj:`bool`, optional):
                Search for name using regex.

                Defaults to: True.
            only1 (:obj:`bool`, optional):
                Only allow one match to name.

                Defaults to: True.

        Raises:
            :exc:`exceptions.ObjectNotFound`

        Returns:
            :obj:`list` of :obj:`dict`: Each row matching name or :obj:`dict` if only1.

        """
        if regex:
            query = 'name == regex("{name}", "i")'.format(name=name)
        else:
            query = 'name == "{name}"'.format(name=name)

        found = list(self.get_saved_query(query=query))

        if not found or (len(found) > 1 and only1):
            object_type = "Saved Query for {o}".format(o=self._router._object_type)
            raise exceptions.ObjectNotFound(
                value=query, value_type="query", object_type=object_type
            )

        return found[0] if only1 else found

    def get_count(self, query=None):
        """Get the number of matches for a given query.

        Args:
            query (:obj:`str`, optional):
                Query built from Query Wizard in GUI.

        Returns:
            :obj:`int`

        """
        params = {}
        if query:
            params["filter"] = query
        return self._request(method="get", path=self._router.count, params=params)

    def get_by_saved_query(self, name, page_size=constants.DEFAULT_PAGE_SIZE):
        """Pass.

        Future: Flush out.
        """
        sq = self.get_saved_query_by_name(name=name, regex=False, only1=True)
        return list(
            self.get(
                query=sq["view"]["query"]["filter"],
                page_size=page_size,
                manual_fields=sq["view"]["fields"],
            )
        )

    def get(
        self,
        query=None,
        page_size=constants.DEFAULT_PAGE_SIZE,
        page_count=None,
        row_count_min=None,
        row_count_max=None,
        default_fields=True,
        manual_fields=None,
        **fields
    ):
        """Get objects for a given query using paging.

        Args:
            query (:obj:`str`, optional):
                Query built from Query Wizard in GUI to select rows to return.

                Defaults to: None.
            page_size (:obj:`int`, optional):
                Get N rows per page.

                Defaults to: :data:`axonius_api_client.constants.DEFAULT_PAGE_SIZE`.
            default_fields (:obj:`bool`, optional):
                Update fields with :attr:`_default_fields` if no fields supplied.

                Defaults to: True.
            fields: Fields to include in result.

                >>> generic=['f1', 'f2'] # for generic fields.
                >>> adapter=['f1', 'f2'] # for adapter specific fields.

        Yields:
            :obj:`dict`: each row found in 'assets' from return.

        """
        row_count_total = self.get_count(query=query)

        if row_count_min == 1 and row_count_max == 1 and row_count_total != 1:
            raise exceptions.ObjectNotFound(
                value=query,
                value_type="query",
                object_type=self._router._object_type,
                exc=None,
            )

        if row_count_min is not None and row_count_total < row_count_min:
            raise exceptions.TooFewObjectsFound(
                value=query,
                value_type="query",
                object_type=self._router._object_type,
                row_count_total=row_count_total,
                row_count_min=row_count_min,
            )

        if row_count_max is not None and row_count_total > row_count_max:
            raise exceptions.TooManyObjectsFound(
                value=query,
                value_type="query",
                object_type=self._router._object_type,
                row_count_total=row_count_total,
                row_count_max=row_count_max,
            )

        if not fields and default_fields:
            for k, v in self._default_fields.items():
                fields.setdefault(k, v)

        if manual_fields:
            validated_fields = manual_fields
        else:
            known_fields = self.get_fields()
            validated_fields = utils.validate_fields(
                known_fields=known_fields, **fields
            )

        row_count_seen = 0
        page_count_seen = 0

        page = self._get(
            query=query,
            fields=validated_fields,
            row_start=0,
            page_size=row_count_max if row_count_max else page_size,
        )

        page_count_seen += 1

        for row in page["assets"]:
            row_count_seen += 1
            yield row

        while not row_count_seen >= row_count_total:
            if page_count is not None and page_count_seen >= page_count:
                return

            page = self._get(
                query=query,
                fields=validated_fields,
                row_start=row_count_seen,
                page_size=page_size,
            )

            page_count_seen += 1

            for row in page["assets"]:
                row_count_seen += 1
                yield row

    def get_by_id(self, id):
        """Get an object by internal_axon_id.

        Args:
           id (:obj:`str`):
               internal_axon_id of object to get.

        Raises:
           :exc:`exceptions.ObjectNotFound`:

        Returns:
           :obj:`dict`

        """
        path = self._router.by_id.format(id=id)
        try:
            data = self._request(method="get", path=path)
        except exceptions.ResponseError as exc:
            raise exceptions.ObjectNotFound(
                value=id,
                value_type="Axonius ID",
                object_type=self._router._object_type,
                exc=exc,
            )
        return data

    def get_by_field_value(self, value, field, field_adapter, regex=False, **kwargs):
        """Build query to perform equals or regex search.

        Args:
            value (:obj:`str`):
                Value to search for equals or regex query against field.
            field (:obj:`str`):
                Field to use when building equals or regex query.
            field_adapter (:obj:`str`):
                Adapter field is from.
            regex (:obj:`bool`, optional):
                Build a regex instead of equals query.
            kwargs:
                Passed through to :meth:`get`.

        Returns:
            :obj:`list` of :obj:`dict` or :obj:`dict`

        """
        if regex:
            query = '{field} == regex("{value}", "i")'
        else:
            query = '{field} == "{value}"'

        known_fields = self.get_fields()
        field = utils.find_field(name=field, fields=known_fields, adapter=field_adapter)

        kwargs.setdefault("row_count_min", 1)
        kwargs.setdefault("row_count_max", 1)
        kwargs.setdefault("query", query.format(field=field, value=value))

        found = list(self.get(**kwargs))

        only1 = kwargs["row_count_min"] == 1 and kwargs["row_count_max"] == 1

        return found[0] if only1 else found

    def _get(self, query=None, fields=None, row_start=0, page_size=0):
        """Get a page for a given query.

        Args:
            query (:obj:`str`, optional):
                Query built from Query Wizard in GUI to select rows to return.

                Defaults to: None.
            fields (:obj:`list` of :obj:`str` or :obj:`str`):
                List of fields to include in return.
                If str, CSV seperated list of fields.
                If list, strs of fields.

                Defaults to: None.
            row_start (:obj:`int`, optional):
                If not 0, skip N rows in the return.

                Defaults to: 0.
            page_size (:obj:`int`, optional):
                If not 0, include N rows in the return.

                Defaults to: 0.

        Returns:
            :obj:`dict`

        """
        utils.check_max_page_size(page_size=page_size)
        params = {}

        if row_start:
            params["skip"] = row_start

        if page_size:
            params["limit"] = page_size

        if query:
            params["filter"] = query

        if fields:
            if isinstance(fields, (list, tuple)):
                fields = ",".join(fields)
            params["fields"] = fields
        return self._request(method="get", path=self._router.root, params=params)

    def _get_saved_query(self, query=None, row_start=0, page_size=0):
        """Get device saved queries.

        Args:
            query (:obj:`str`, optional):
                Query to filter rows to return. This is NOT a query built by
                the Query Wizard in the GUI. This is something else. See
                :meth:`get_saved_query_by_name` for an example query. Empty
                query will return all rows.

                Defaults to: None.
            row_start (:obj:`int`, optional):
                If not 0, skip N rows in the return.

                Defaults to: 0.
            page_size (:obj:`int`, optional):
                If not 0, include N rows in the return.

                Defaults to: 0.

        Returns:
            :obj:`dict`

        """
        utils.check_max_page_size(page_size=page_size)
        params = {}

        if page_size:
            params["limit"] = page_size

        if row_start:
            params["skip"] = row_start

        if query:
            params["filter"] = query

        return self._request(method="get", path=self._router.views, params=params)

    def _delete_saved_query(self, ids):
        """Delete saved queries by ids.

        Args:
            ids (:obj:`list` of :obj:`str`):
                List of UUID's of saved queries to delete.

        Returns:
            :obj:`str`: empty string

        """
        data = {"ids": ids}
        return self._request(method="delete", path=self._router.views, json=data)

    # FUTURE: needs tests
    def _add_labels(self, labels, ids):
        """Add labels to object IDs.

        Args:
            labels (:obj:`list` of `str`):
                Labels to add to ids.
            ids (:obj:`list` of `str`):
                Axonius internal object IDs to add to labels.

        Returns:
            :obj:`int`: Number of objects that had labels added

        """
        data = {}
        data["entities"] = {}
        data["entities"]["ids"] = ids
        data["labels"] = labels
        return self._request(method="post", path=self._router.labels, json=data)

    # FUTURE: needs tests
    def _delete_labels(self, labels, ids):
        """Delete labels from object IDs.

        Args:
            labels (:obj:`list` of `str`):
                Labels to delete from ids.
            ids (:obj:`list` of `str`):
                Axonius internal object IDs to delete from labels.

        Returns:
            :obj:`int`: Number of objects that had labels deleted.

        """
        data = {}
        data["entities"] = {}
        data["entities"]["ids"] = ids
        data["labels"] = labels
        return self._request(method="delete", path=self._router.labels, json=data)


class Users(models.ApiModel, UserDeviceModel):
    """User related API methods."""

    @property
    def _router(self):
        """Router for this API client.

        Returns:
            :obj:`axonius_api_client.api.routers.Router`

        """
        return routers.ApiV1.users

    @property
    def _default_fields(self):
        """Fields to set as default for methods with fields as kwargs.

        Returns:
            :obj:`dict`

        """
        return {
            "generic": [
                "adapters",
                "labels",
                "specific_data.data.username",
                "specific_data.data.last_seen",
                "specific_data.data.mail",
            ]
        }

    def get_by_name(self, value, **kwargs):
        """Get objects by name using paging.

        Args:
            value (:obj:`int`):
                Value to find using field "specific_data.data.username".
            **kwargs: Passed thru to :meth:`UserDeviceModel.get_by_field_value`

        Returns:
            :obj:`list` of :obj:`dict`: Each row matching name or :obj:`dict` if only1.

        """
        kwargs.setdefault("field", "specific_data.data.username")
        kwargs.setdefault("field_adapter", "generic")
        kwargs["value"] = value
        return self.get_by_field_value(**kwargs)

    def get_by_email(self, value, **kwargs):
        """Get objects by email using paging.

        Args:
            value (:obj:`int`):
                Value to find using field "specific_data.data.mail".
            **kwargs: Passed thru to :meth:`UserDeviceModel.get_by_field_value`

        Returns:
            :obj:`list` of :obj:`dict`: Each row matching email or :obj:`dict` if only1.

        """
        kwargs.setdefault("field", "specific_data.data.mail")
        kwargs.setdefault("field_adapter", "generic")
        kwargs["value"] = value
        return self.get_by_field_value(**kwargs)


class Devices(models.ApiModel, UserDeviceModel):
    """Device related API methods."""

    @property
    def _router(self):
        """Router for this API client.

        Returns:
            :obj:`axonius_api_client.api.routers.Router`

        """
        return routers.ApiV1.devices

    @property
    def _default_fields(self):
        """Fields to set as default for methods with fields as kwargs.

        Returns:
            :obj:`dict`

        """
        return {
            "generic": [
                "adapters",
                "labels",
                "specific_data.data.hostname",
                "specific_data.data.network_interfaces.ips",
                "specific_data.data.last_seen",
            ]
        }

    def get_by_name(self, value, **kwargs):
        """Get objects by name using paging.

        Args:
            value (:obj:`int`):
                Value to find using field "specific_data.data.username".
            **kwargs: Passed thru to :meth:`UserDeviceModel.get_by_field_value`

        Returns:
            :obj:`list` of :obj:`dict`: Each row matching name or :obj:`dict` if only1.

        """
        kwargs.setdefault("field", "specific_data.data.hostname")
        kwargs.setdefault("field_adapter", "generic")
        kwargs["value"] = value
        return self.get_by_field_value(**kwargs)

    # TODO: get_by_ip
    # TODO: get_by_in_subnet
    # TODO: get_by_not_in_subnet
    def get_by_mac(self, value, **kwargs):
        """Get objects by MAC using paging.

        Args:
            value (:obj:`int`):
                Value to find using field "specific_data.data.network_interfaces.mac".
            **kwargs: Passed thru to :meth:`UserDeviceModel.get_by_field_value`

        Returns:
            :obj:`list` of :obj:`dict`: Each row matching email or :obj:`dict` if only1.

        """
        kwargs.setdefault("field", "specific_data.data.network_interfaces.mac")
        kwargs.setdefault("field_adapter", "generic")
        kwargs["value"] = value
        return self.get_by_field_value(**kwargs)


# FUTURE: needs tests
class Actions(models.ApiModel):
    """Action related API methods.

    Notes:
        The REST API will need to be updated to allow more power in this library.
        Until then, this class should be considered **BETA**.

    """

    @property
    def _router(self):
        """Router for this API client.

        Returns:
            :obj:`axonius_api_client.api.routers.Router`

        """
        return routers.ApiV1.actions

    def get(self):
        """Get all actions.

        Returns:
            :obj:`list` of :obj:`str`

        """
        return self._request(method="get", path=self._router.root)

    def run(self, name, ids, command):
        """Run an action.

        Args:
            name (:obj:`str`):
                Name of action to run.
            ids (:obj:`list` of :obj:`str`):
                Internal axonius IDs of device to run action against.
            command (:obj:`str`):
                Command to run.

        Returns:
            :obj:`object`

        """
        data = {}
        data["action_name"] = name
        data["internal_axon_ids"] = ids
        data["command"] = command
        return self._request(method="post", path=self._router.shell, json=data)

    # FUTURE: Figure out return.
    def deploy(self, name, ids, binary_uuid, binary_filename, params=None):
        """Deploy an action.

        Args:
            name (:obj:`str`):
                Name of action to deploy.
            ids (:obj:`list` of :obj:`str`):
                Internal axonius IDs of device to deploy action against.
            binary_uuid (:obj:`str`):
                UUID of binary to use in deployment.
            binary_filename (:obj:`str`):
                Filename of binary to use in deployment.
            params (:obj:`str`, optional):
                Defaults to: None.

        Returns:
            :obj:`object`

        """
        data = {}
        data["action_name"] = name
        data["internal_axon_ids"] = ids
        data["binary"] = {}
        data["binary"]["filename"] = binary_filename
        data["binary"]["uuid"] = binary_uuid
        if params:
            data["params"] = params
        return self._request(method="post", path=self._router.deploy, json=data)

    def upload_file(self, binary, filename):
        """Upload a file to the system for use in deployment.

        Args:
            binary (:obj:`io.BytesIO`):
                Binary bits of file to upload.
            filename (:obj:`str`):
                Name of file to upload.

        Returns:
            :obj:`str`: UUID of uploaded file.

        """
        data = {}
        data["field_name"] = "binary"
        files = {}
        files["userfile"] = (filename, binary)
        return self._request(
            method="post", path=self._router.upload_file, data=data, files=files
        )


# FUTURE: needs tests
class Adapters(models.ApiModel):
    """Adapter related API methods.

    Notes:
        The REST API will need to be updated to allow more power in this library.
        Until then, this class should be considered **BETA**.

    """

    @property
    def _router(self):
        """Router for this API client.

        Returns:
            :obj:`axonius_api_client.api.routers.Router`

        """
        return routers.ApiV1.adapters

    def get(self):
        """Get all adapters.

        Returns:
            :obj:`object`

        """
        return self._request(method="get", path=self._router.root)

    # FUTURE: public method
    def _check_client(self, name, config, node_id):
        """Check connectivity for a client of an adapter.

        Args:
            name (:obj:`str`):
                Name of adapter to check client connectivity of.
            config (:obj:`dict`):
                Client configuration.
            node_id (:obj:`str`):
                Node ID.

        Returns:
            :obj:`object`

        """
        data = {}
        data.update(config)
        data["instanceName"] = node_id
        data["oldInstanceName"] = node_id
        path = self._router.clients.format(adapter_name=name)
        return self._request(method="post", path=path, json=data)

    # FUTURE: public method
    def _add_client(self, name, config, node_id):
        """Add a client to an adapter.

        Args:
            name (:obj:`str`):
                Name of adapter to add client to.
            config (:obj:`dict`):
                Client configuration.
            node_id (:obj:`str`):
                Node ID.

        Returns:
            :obj:`object`

        """
        data = {}
        data.update(config)
        data["instanceName"] = node_id
        path = self._router.clients.format(adapter_name=name)
        return self._request(method="put", path=path, json=data)

    # FUTURE: public method
    def _delete_client(self, name, id, node_id):
        """Delete a client from an adapter.

        Args:
            name (:obj:`str`):
                Name of adapter to delete client from.
            id (:obj:`str`):
                ID of client to remove.
            node_id (:obj:`str`):
                Node ID.

        Returns:
            :obj:`object`

        """
        data = {}
        data["instanceName"] = node_id
        path = self._router.clients.format(adapter_name=name)
        path += "/{id}".format(id=id)
        return self._request(method="delete", path=path, json=data)


# FUTURE: needs tests
class Enforcements(models.ApiModel):
    """Enforcement related API methods.

    Notes:
        The REST API will need to be updated to allow more power in this library.
        Until then, this class should be considered **BETA**.

    """

    @property
    def _router(self):
        """Router for this API client.

        Returns:
            :obj:`axonius_api_client.api.routers.Router`

        """
        return routers.ApiV1.alerts

    def _delete(self, ids):
        """Delete objects by internal axonius IDs.

        Args:
            ids (:obj:`list` of :obj:`str`):
                List of internal axonius IDs of objects to delete.

        Returns:
            None

        """
        return self._request(method="delete", path=self._router.root, json=ids)

    # FUTURE: public method
    def _create(self, name, main, success=None, failure=None, post=None, triggers=None):
        """Create an enforcement.

        Args:
            name (:obj:`str`):
                Name of new enforcement to create.
            main (:obj:`dict`):
                Main action to run for this enforcement.
            success (:obj:`list` of :obj:`dict`, optional):
                Actions to run on success.

                Defaults to: None.
            failure (:obj:`list` of :obj:`dict`, optional):
                Actions to run on failure.

                Defaults to: None.
            post (:obj:`list` of :obj:`dict`, optional):
                Actions to run on post.

                Defaults to: None.
            triggers (:obj:`list` of :obj:`dict`, optional):
                Triggers for this enforcement.

                Defaults to: None.

        Notes:
            This will get a public create method once the REST API server has been
            updated to expose /enforcements/actions, /api/enforcements/actions/saved,
            and others.

        Returns:
            :obj:`str`: ID of newly created object.

        """
        data = {}
        data["name"] = name
        data["actions"] = {}
        data["actions"]["main"] = main
        data["actions"]["success"] = success or []
        data["actions"]["failure"] = success or []
        data["actions"]["post"] = success or []
        data["triggers"] = triggers or []
        return self._request(method="put", path=self._router.root, json=data)

    def get(self, query=None, row_start=0, page_size=0):
        """Get a page for a given query.

        Args:
            query (:obj:`str`, optional):
                Query to filter rows to return. This is NOT a query built by
                the Query Wizard in the GUI. This is something else. See
                :meth:`get_by_name` for an example query. Empty
                query will return all rows.

                Defaults to: None.
            row_start (:obj:`int`, optional):
                If not 0, skip N rows in the return.

                Defaults to: 0.
            page_size (:obj:`int`, optional):
                If not 0, include N rows in the return.

                Defaults to: 0.

        Returns:
            :obj:`dict`

        """
        params = {}

        if page_size:
            params["limit"] = page_size

        if row_start:
            params["skip"] = row_start

        if query:
            params["filter"] = query

        response = self._request(method="get", path=self._router.root, params=params)
        return response["assets"]

    def delete_by_name(self, name, regex=False, only1=True):
        """Delete an enforcement by name.

        Args:
            name (:obj:`str`):
                Name of object to delete.
            regex (:obj:`bool`, optional):
                Search for name using regex.

                Defaults to: False.
            only1 (:obj:`bool`, optional):
                Only allow one match to name.

                Defaults to: True.

        Returns:
            :obj:`str`: empty string

        """
        found = self.get_by_name(name=name, regex=regex, only1=True)
        ids = [x["uuid"] for x in found] if isinstance(found, list) else [found["uuid"]]
        return self._delete(ids=ids)

    def get_by_name(self, name, regex=True, only1=False):
        """Get enforcements by name.

        Args:
            name (:obj:`str`):
                Name of object to get.
            regex (:obj:`bool`, optional):
                Search for name using regex.

                Defaults to: True.
            only1 (:obj:`bool`, optional):
                Only allow one match to name.

                Defaults to: True.

        Raises:
            :exc:`exceptions.ObjectNotFound`

        Returns:
            :obj:`list` of :obj:`dict`: Each row matching name or :obj:`dict` if only1.

        """
        if regex:
            query = 'name == regex("{name}", "i")'.format(name=name)
        else:
            query = 'name == "{name}"'.format(name=name)

        found = self.get(query=query)

        if not found or (len(found) > 1 and only1):
            raise exceptions.ObjectNotFound(
                value=query, value_type="query", object_type="Alert", exc=None
            )

        return found[0] if only1 else found