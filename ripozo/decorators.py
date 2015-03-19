from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import wraps

import logging
import six


class _apiclassmethod(object):
    if six.PY2:
        _name = six.binary_type('_apiclassmethod')
    else:
        _name = '_apiclassmethod'

    def __init__(self, f):
        self.f = f
        self.rest_route = True
        self.routes = getattr(f, 'routes', [])

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)

        method = self.f
        @wraps(method)
        def newfunc(*args):
            if not isinstance(args[0], type):
                return method(klass, *args)
            return method(*args)
        newfunc.__rest_route__ = True
        newfunc.routes = getattr(self.f, 'routes', [])
        return newfunc

    @property
    def __name__(self):
        return self._name

    @__name__.setter
    def __name__(self, value):
        self._name = value



class apimethod(object):
    """
    Decorator for declaring routes on a ripozo resource
    """
    def __init__(self, route='', endpoint=None, **options):
        """
        Hold on to the arguments for the decorator to append to the class map
        """
        logger = logging.getLogger(__name__)
        logger.info('Initializing apimethod route: {0} with options {1}'.format(route, options))
        self.route = route
        self.options = options
        self.endpoint = endpoint

    def __call__(self, f):
        """
        The actual decorator that will be called and returns the method
        that is a ripozo route.

        :param classmethod f:
        :return: The wrapped classmethod that is an action
            that can be performed on the resource.  For example,
            any sort of CRUD action.
        :rtype: classmethod
        """
        @wraps(f)
        def wrapped(cls, request, *args, **kwargs):
            for proc in cls.preprocessors:
                # TODO update docs for preprocessors and post processors
                proc(cls, f.__name__, request, *args, **kwargs)
            resource = f(cls, request, *args, **kwargs)
            for proc in cls.postprocessors:
                proc(cls, f.__name__, request, resource, *args, **kwargs)
            return resource

        wrapped.__rest_route__ = True
        wrapped.routes = getattr(f, 'routes', [])

        wrapped.routes.append((self.route, self.endpoint, self.options))
        return _apiclassmethod(wrapped)


class validate(object):
    """
    Decorator for validating the inputs to an apimethod
    and describing what is allowed for that apimethod to
    an adapter if necessary.
    """

    def __init__(self, fields=None, manager_field_validators=False, skip_required=False):
        """
        Initializes the decorator with the necessary fields.
        the fields should be instances of FieldBase and should
        give descriptions of the parameter and how to input them
        (i.e. query or body parameter)

        :param list fields: A list of FieldBase instances (or subclasses
            of FieldBase).
        """
        # TODO test and update docs for manager_field_validators
        self.fields = fields or []
        self.manager_field_validators = manager_field_validators
        self.skip_required = skip_required

    def __call__(self, f):
        """
        Wraps the function with translation and validation.
        This allows the inputs to be cast and validated as necessary.
        Additionally, it provides the adapter with information about
        what is necessary to successfully make a request to the wrapped
        apimethod.

        :param method f:
        :return: The wrapped function
        :rtype: function
        """
        @wraps(f)
        def action(cls, request, *args, **kwargs):
            # TODO This is so terrible.  I really need to fix this.
            if self.manager_field_validators:
                self.fields = self.original_fields + cls.manager.field_validators
                request.validate(action.original_fields + cls.manager.field_validators, skip_required=self.skip_required)
            else:
                request.validate(action.original_fields, skip_required=self.skip_required)
            return f(cls, request,  *args, **kwargs)

        action.fields = self.fields
        self.original_fields = self.fields
        action.original_fields = self.original_fields
        action.__manager_field_validators__ = self.manager_field_validators
        return action


class translate(object):
    """
    A decorator designed to be used in
    conjunction with an apimethod decorated
    method (though this is not necessary).  It
    calls request.translate before running the function.
    """
    def __init__(self, fields=None, manager_field_validators=False):
        """
        Just sets the fields parameter
        :param list fields: A list of BaseField (and its subclasses)
            instances
        """
        # TODO test and update docs for manager_field_validators
        self.fields = fields or []
        self.manager_field_validators = manager_field_validators

    def __call__(self, f):
        """
        The actual decorator portion

        :param types.MethodType f: The method to be decorated
        :return: The wrapped function
        :rtype: type.MethodType
        """
        @wraps(f)
        def action(cls, request, *args, **kwargs):
            if self.manager_field_validators:
                request.translate(action.original_fields + cls.manager.field_validators)
            else:
                request.translate(action.original_fields)
            return f(cls, request, *args, **kwargs)

        action.fields = self.fields
        action.original_fields = self.fields
        action.__manager_field_validators__ = self.manager_field_validators
        return action
