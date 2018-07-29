from typing import Any, Awaitable, Callable, Dict, List

from . import sansio


AsyncCallback = Callable[..., Awaitable[None]]


class Router:
    """
    An object to route a :class:`gidgetlab.sansio.Event` instance to
    appropriate registered asynchronous callbacks.

    The initializer for this class takes an arbitrary number of other
    routers to help build a single router from sub-routers. Typically
    this is used when each semantic set of features has a router and
    are then used to construct a server-wide router.

    Each callback registered with this class is expected to be
    :term:`awaitable` and to accept at least a single
    :class:`~gidgetlab.sansio.Event` instance:

    .. code-block:: python

        async def callback(event, *args, **kwargs):
            ...
    """

    def __init__(self, *other_routers: "Router") -> None:
        """Instantiate a new router (possibly from other routers)."""
        self._shallow_routes: Dict[str, List[AsyncCallback]] = {}
        # event type -> data key -> data value -> callbacks
        self._deep_routes: Dict[str, Dict[str, Dict[Any, List[AsyncCallback]]]] = {}
        for other_router in other_routers:
            for event_type, callbacks in other_router._shallow_routes.items():
                for callback in callbacks:
                    self.add(callback, event_type)
            for event_type, object_attributes in other_router._deep_routes.items():
                for data_key, data_specifics in object_attributes.items():
                    for data_value, callbacks in data_specifics.items():
                        detail = {data_key: data_value}
                        for callback in callbacks:
                            self.add(callback, event_type, **detail)

    def add(
        self, func: AsyncCallback, event_type: str, **object_attribute: Any
    ) -> None:
        """Add an asynchronous callback for an event.

        The *event_type* argument corresponds to the
        :attr:`gidgetlab.sansio.Event.event` attribute of the event
        that the callback is interested in. The arbitrary keyword
        arguments is used as a key/value pair to compare against what
        is provided in :attr:`gidgetlab.sansio.Event.object_attributes`.
        Only 0 or 1 keyword-only arguments may be provided, otherwise
        :exc:`TypeError` is raised.

        For example, to register a callback for any opened issues,
        you would call:

        .. code-block:: python

            async def callback(event):
                ...

            router.add(callback, "Issue Hook", action="open")
        """
        if len(object_attribute) > 1:
            raise TypeError(
                "dispatching based on object attributes is only "
                "supported up to one level deep; "
                f"{len(object_attribute)} levels specified"
            )
        elif not object_attribute:
            callbacks = self._shallow_routes.setdefault(event_type, [])
            callbacks.append(func)
        else:
            data_key, data_value = object_attribute.popitem()
            object_attributes = self._deep_routes.setdefault(event_type, {})
            specific_detail = object_attributes.setdefault(data_key, {})
            callbacks = specific_detail.setdefault(data_value, [])
            callbacks.append(func)

    def register(
        self, event_type: str, **object_attribute: Any
    ) -> Callable[[AsyncCallback], AsyncCallback]:
        """A decorator that calls :meth:`add` on the decorated function.

        .. code-block:: python

            router = gidgetlab.routing.Router()

            @router.register("Issue Hook", action="open")
            async def callback(event):
                ...
        """

        def decorator(func: AsyncCallback) -> AsyncCallback:
            self.add(func, event_type, **object_attribute)
            return func

        return decorator

    async def dispatch(self, event: sansio.Event, *args: Any, **kwargs: Any) -> None:
        """Call the appropriate asynchronous callbacks for the *event*.
        The provided event and any other arguments will be passed
        down to the callback unmodified.
        """

        found_callbacks = []
        try:
            found_callbacks.extend(self._shallow_routes[event.event])
        except KeyError:
            pass
        try:
            details = self._deep_routes[event.event]
        except KeyError:
            pass
        else:
            for data_key, data_values in details.items():
                if data_key in event.object_attributes:
                    event_value = event.object_attributes[data_key]
                    if event_value in data_values:
                        found_callbacks.extend(data_values[event_value])
        for callback in found_callbacks:
            await callback(event, *args, **kwargs)
