import functools
import logging
from typing import Callable, Optional, Tuple

import blinker

from user.models import User

log = logging.getLogger(__name__)
Transition = Tuple[str, str]


def connect(*signals, **kwargs):
    """
    Decorator to connect method to several signals.

    :param sender: If set will make decorated method to be called only when particular sender has
        called it. Defaults to ``ANY``

    :param weak: If true, the Signal will hold a weakref to *receiver*
        and automatically disconnect when *receiver* goes out of scope or
        is garbage collected.  Defaults to ``True``.

    """
    sender = kwargs.get('sender', blinker.ANY)
    weak = kwargs.get('weak', True)

    def decorator(func):

        for signal in signals:
            signal.connect(func, sender=sender, weak=weak)

        return func

    return decorator


def transition(state_before: Optional[str], state_now: str) -> Callable:
    def wrapper(func):
        def handler(user: User, transition: Transition, **kwargs):

            if state_before and transition != (state_before, state_now):
                return
            elif not state_before and transition[1] != state_now:
                return

            return func(user, transition=transition, **kwargs)

        User.on_transition.connect(handler, weak=False)

    return wrapper


def log_exception(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as ex:
            log.exception('Unhandled signal exception: %s', ex)

    return wrapper
