"""
Contains common CRUD+L abstract Resource classes,
for simple and fast use of ripozo.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo.resources.relationships.relationship import Relationship
from ripozo.resources.relationships.list_relationship import ListRelationship
from ripozo.decorators import apimethod, translate, classproperty
from ripozo.resources.resource_base import ResourceBase

import logging

_logger = logging.getLogger(__name__)


class Create(ResourceBase):
    """
    A base class to extend that allows for
    adding the create ability to your resource.
    """
    __abstract__ = True

    @apimethod(methods=['POST'], no_pks=True)
    @translate(manager_field_validators=True, validate=True)
    def create(cls, request):
        """
        Creates a new resource using the cls.manager.create
        method.  Returns the resource that was just created
        as an instance of the class that created it.

        :param RequestContainer request: The request in the standardized
            ripozo style.
        :return: An instance of the class
            that was called.
        :rtype: Update
        """
        _logger.debug('Creating a resource using manager %s', cls.manager)
        props = cls.manager.create(request.body_args)
        meta = dict(links=dict(created=props))
        return cls(properties=props, meta=meta, status_code=201)

    @classproperty
    def links(cls):
        """
        Appends the "created" link to the _links
        and returns the corresponding tuple.

        :return: The links defined on the class plus
            the "created" link that references the newly
            created link.
        :rtype: tuple
        """
        links = cls._links or tuple()
        return links + Create.get_base_links(cls)

    @staticmethod
    def get_base_links(actual_class):
        return (Relationship('created', relation=actual_class.__name__, embedded=True), )


class Retrieve(ResourceBase):
    """
    A base class to extend that allows for
    adding the retrieve ability to your resource.
    This is for a single resource retrieval
    """
    __abstract__ = True

    @apimethod(methods=['GET'])
    @translate(manager_field_validators=True)
    def retrieve(cls, request):
        """
        Retrieves an individual resource.

        :param RequestContainer request: The request in the standardized
            ripozo style.
        :return: An instance of the class
            that was called.
        :rtype: Retrieve
        :raises: NotFoundException
        """
        _logger.debug('Retrieving a resource using the manager %s', cls.manager)
        props = cls.manager.retrieve(request.url_params)
        return cls(properties=props, status_code=200)


class RetrieveList(ResourceBase):
    """
    Retrieving a list of resources with this
    class.  This class does not automatically assume
    that there is an individual retrieve function
    and therefor cannot link between the list
    and an individual resource.
    """
    __abstract__ = True

    @apimethod(methods=['GET'], no_pks=True)
    @translate(manager_field_validators=True, validate=False)
    def retrieve_list(cls, request):
        """
        A resource that contains the other resources as properties.

        :param RequestContainer request: The request in the standardized
            ripozo style.
        :return: An instance of the class
            that was called.
        :rtype: RetrieveList
        """
        _logger.debug('Retrieving list of resources using manager %s', cls.manager)
        props, meta = cls.manager.retrieve_list(request.query_args)
        return_props = {cls.resource_name: props}
        return_props.update(request.query_args)
        return cls(properties=return_props, meta=meta,
                   status_code=200, query_args=cls.manager.fields)

    @classproperty
    def links(cls):
        """
        Appends the "next" and "previous" links to the
        _links and returns the corresponding tuple.

        :return: The links defined on the class plus
            the "next" and "previous" link that references
            the newly created link.
        :rtype: tuple
        """
        links = cls._links or tuple()
        return links + cls.get_base_links(cls)

    @staticmethod
    def get_base_links(actual_class):
        """
        Gets the base links for this class.
        Necessary for properly inheriting links in
        descendant classes.
        """
        if actual_class.manager:
            fields = tuple(actual_class.manager.fields)
            fields += (actual_class.manager.pagination_pk_query_arg,
                       actual_class.manager.pagination_count_query_arg)
        else:
            fields = []
        return (Relationship('next', relation=actual_class.__name__,
                             query_args=fields, no_pks=True),
                Relationship('previous', relation=actual_class.__name__,
                             query_args=fields, no_pks=True),)


class RetrieveRetrieveList(RetrieveList, Retrieve):
    """
    Adds ability to link between the list resource
    and individual resources.  Allow both list
    retrieval and individual retrieval.
    """

    @classproperty
    def relationships(cls):
        """
        Appends the ListRelationship relationship that corresponds
        to the items returned.

        :return: The relationships on the class plus the
            cls.__name__
        :rtype: tuple
        """
        relationships = cls._relationships or tuple()
        return relationships + (ListRelationship(cls.resource_name, relation=cls.__name__),)


class Update(ResourceBase):
    """
    Adds the ability to do a partial
    update of your resource.
    """
    __abstract__ = True

    @apimethod(methods=['PATCH'])
    @translate(manager_field_validators=True, skip_required=True, validate=True)
    def update(cls, request):
        """
        Updates the resource using the manager
        and then returns the resource.

        :param RequestContainer request: The request in the standardized
            ripozo style.
        :return: An instance of the class
            that was called.
        :rtype: Create
        """
        _logger.debug('Updating a resource using the manager %s', cls.manager)
        props = cls.manager.update(request.url_params, request.body_args)
        return cls(properties=props, status_code=200)


class Delete(ResourceBase):
    """
    Adds the ability to delete your resource.
    """
    __abstract__ = True

    @apimethod(methods=['DELETE'])
    @translate(manager_field_validators=True)
    def delete(cls, request):
        """

        :param RequestContainer request: The request in the standardized
            ripozo style.
        :return: An instance of the class
            that was called.
        :rtype: Create
        """
        _logger.debug('Deleting the resource using manager %s ', cls.manager)
        props = cls.manager.delete(request.url_params)
        return cls(properties=props)


class RetrieveUpdate(Retrieve, Update):
    __abstract__ = True


class RetrieveUpdateDelete(Retrieve, Update, Delete):
    __abstract__ = True


class CreateRetrieve(Create, Retrieve):
    __abstract__ = True


class CreateRetrieveUpdate(Create, Retrieve, Update):
    __abstract__ = True


class CRUD(Create, Retrieve, Update, Delete):
    """
    Short cut for Create, Retrieve, Update, and Delete.
    In other words the single resource operations
    """
    __abstract__ = True


class CRUDL(Create, RetrieveRetrieveList, Update, Delete):
    """
    Short cut for inheriting from Create, RetrieveRetrieveList,
    Update, and Delete.  This is a full CRUD+L implementation.
    Requires that the manager is set on the class.
    """
    __abstract__ = True

    @classproperty
    def links(cls):
        links = cls._links or tuple()
        return links + Create.get_base_links(cls) + RetrieveRetrieveList.get_base_links(cls)
