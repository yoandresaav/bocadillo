import inspect
from functools import wraps
from http import HTTPStatus
from typing import Callable, Union, List

from asgiref.sync import sync_to_async

from .constants import ALL_HTTP_METHODS
from .exceptions import HTTPError
from .request import Request
from .response import Response


class ClassBasedView:
    """Class-based view interface."""

    def get(self, request: Request, response: Response, **kwargs):
        raise NotImplementedError

    def post(self, request: Request, response: Response, **kwargs):
        raise NotImplementedError

    def put(self, request: Request, response: Response, **kwargs):
        raise NotImplementedError

    def patch(self, request: Request, response: Response, **kwargs):
        raise NotImplementedError

    def delete(self, request: Request, response: Response, **kwargs):
        raise NotImplementedError


# Types
CallableView = Callable[[Request, Response, dict], None]
View = Union[CallableView, ClassBasedView]


def create_callable_view(view: View, methods: List[str]):
    """Create callable view from function (sync/async) or class based view."""
    if inspect.iscoroutinefunction(view):
        return _from_async_function(view, methods)
    elif inspect.isfunction(view):
        return _from_sync_function(view, methods)
    else:
        return _from_class_instance(view)


def _from_async_function(view: Callable, methods: List[str]):
    @wraps(view)
    async def callable_view(req, res, **kwargs):
        if req.method not in methods:
            raise HTTPError(status=HTTPStatus.METHOD_NOT_ALLOWED)
        await view(req, res, **kwargs)

    return callable_view


def _from_sync_function(view: Callable, methods: List[str]):
    return _from_async_function(sync_to_async(view), methods)


def _from_class_instance(view: ClassBasedView):
    def _find_for_method(method: str):
        try:
            return getattr(view, 'handle')
        except AttributeError:
            return getattr(view, method.lower(), None)

    async def callable_view(req, res, **kwargs):
        view_ = _find_for_method(req.method)
        if view_ is None:
            raise HTTPError(status=HTTPStatus.METHOD_NOT_ALLOWED)
        if not inspect.iscoroutinefunction(view_):
            view_ = sync_to_async(view_)
        await view_(req, res, **kwargs)

    return callable_view


def get_view_name(view: View, base: ClassBasedView = None) -> str:
    def _get_name(obj):
        return getattr(obj, '__name__', obj.__class__.__name__)

    return '.'.join(_get_name(part) for part in (base, view) if part)


def get_declared_method_views(view: ClassBasedView):
    for method in ('handle', *map(str.lower, ALL_HTTP_METHODS)):
        if hasattr(view, method):
            yield method, getattr(view, method)
