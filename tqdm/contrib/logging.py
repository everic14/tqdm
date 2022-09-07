"""
Helper functionality for interoperability with stdlib `logging`.
"""
# pylint: disable=super-with-arguments
from __future__ import absolute_import

import logging
import sys
from contextlib import contextmanager

try:
    from typing import Iterator, List, Optional, Type  # pylint: disable=unused-import
except ImportError:
    pass

from ..std import tqdm as std_tqdm

LOGGER = logging.getLogger(__name__)


class _TqdmLoggingHandler(logging.StreamHandler):
    def __init__(
        self,
        tqdm_class=std_tqdm  # type: Type[std_tqdm]
    ):
        super(_TqdmLoggingHandler, self).__init__()
        self.tqdm_class = tqdm_class

    def emit(self, record):
        try:
            msg = self.format(record)
            self.tqdm_class.write(msg, file=self.stream)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # noqa pylint: disable=bare-except
            self.handleError(record)


def _is_console_logging_handler(handler):
    return (isinstance(handler, logging.StreamHandler)
            and handler.stream in {sys.stdout, sys.stderr})


def _get_first_found_console_logging_handler(handlers):
    for handler in handlers:
        if _is_console_logging_handler(handler):
            return handler
    return None


@contextmanager
def logging_redirect_tqdm(
    loggers=None,  # type: Optional[List[logging.Logger]]
    tqdm_class=std_tqdm  # type: Type[std_tqdm]
):
    # type: (...) -> Iterator[None]
    """
    Context manager redirecting console logging to `tqdm.write()`, leaving
    other logging handlers (e.g. log files) unaffected.

    Parameters
    ----------
    loggers  : list, optional
      Which handlers to redirect (default: [logging.root]).
    tqdm_class  : optional

    Example
    -------
    ```python
    import logging
    from tqdm import trange
    from tqdm.contrib.logging import logging_redirect_tqdm

    LOG = logging.getLogger(__name__)

    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO)
        with logging_redirect_tqdm():
            for i in trange(9):
                if i == 4:
                    LOG.info("console logging redirected to `tqdm.write()`")
        # logging restored
    ```
    """
    if loggers is None:
        loggers = [logging.root]
    original_handlers_list = [logger.handlers for logger in loggers]
    try:
        for logger in loggers:
            tqdm_handler = _TqdmLoggingHandler(tqdm_class)
            orig_handler = _get_first_found_console_logging_handler(logger.handlers)
            if orig_handler is not None:
                tqdm_handler.setFormatter(orig_handler.formatter)
                tqdm_handler.stream = orig_handler.stream
            logger.handlers = [
                handler for handler in logger.handlers
                if not _is_console_logging_handler(handler)] + [tqdm_handler]
        yield
    finally:
        for logger, original_handlers in zip(loggers, original_handlers_list):
            logger.handlers = original_handlers


@contextmanager
def tqdm_logging_redirect(
    *args,
    # loggers=None,  # type: Optional[List[logging.Logger]]
    # tqdm=None,  # type: Optional[Type[tqdm.tqdm]]
    **kwargs
):
    # type: (...) -> Iterator[None]
    """
    Convenience shortcut for:
    ```python
    with tqdm_class(*args, **tqdm_kwargs) as pbar:
        with logging_redirect_tqdm(loggers=loggers, tqdm_class=tqdm_class):
            yield pbar
    ```

    Parameters
    ----------
    tqdm_class  : optional, (default: tqdm.std.tqdm).
    loggers  : optional, list.
    **tqdm_kwargs  : passed to `tqdm_class`.
    """
    tqdm_kwargs = kwargs.copy()
    loggers = tqdm_kwargs.pop('loggers', None)
    tqdm_class = tqdm_kwargs.pop('tqdm_class', std_tqdm)
    with tqdm_class(*args, **tqdm_kwargs) as pbar:
        with logging_redirect_tqdm(loggers=loggers, tqdm_class=tqdm_class):
            yield pbar


class logging_tqdm(std_tqdm):  # pylint: disable=invalid-name
    """
    A version of tqdm that outputs the progress bar
    to Python logging instead of the console.
    The progress will be logged with the info level.

    Parameters
    ----------
    logger   : logging.Logger, optional
      Which logger to output to (default: logger.getLogger('tqdm.contrib.logging')).

    All other parameters are passed on to regular tqdm,
    with the following changed default:

    mininterval: 1
    bar_format: '{desc}{percentage:3.0f}%{r_bar}'
    desc: 'progress: '


    Example
    -------
    ```python
    import logging
    from time import sleep
    from tqdm.contrib.logging import logging_tqdm

    LOG = logging.getLogger(__name__)

    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO)
        for _ in logging_tqdm(range(10), mininterval=1, logger=LOG):
            sleep(0.3)  # assume processing one item takes less than mininterval
    ```
    """
    def __init__(
            self,
            *args,
            # logger=None,  # type: logging.Logger
            # mininterval=1,  # type: float
            # bar_format='{desc}{percentage:3.0f}%{r_bar}',  # type: str
            # desc='progress: ',  # type: str
            **kwargs):
        if len(args) >= 2:
            # Note: Due to Python 2 compatibility, we can't declare additional
            #   keyword arguments in the signature.
            #   As a result, we could get (due to the defaults below):
            #     TypeError: __init__() got multiple values for argument 'desc'
            #   This will raise a more descriptive error message.
            #   Calling dummy init to avoid attribute errors when __del__ is called
            super(logging_tqdm, self).__init__([], disable=True)
            raise ValueError('only iterable may be used as a positional argument')
        tqdm_kwargs = kwargs.copy()
        self._logger = tqdm_kwargs.pop('logger', None)
        tqdm_kwargs.setdefault('mininterval', 1)
        tqdm_kwargs.setdefault('bar_format', '{desc}{percentage:3.0f}%{r_bar}')
        tqdm_kwargs.setdefault('desc', 'progress: ')
        self._last_log_n = -1
        super(logging_tqdm, self).__init__(*args, **tqdm_kwargs)

    def _get_logger(self):
        if self._logger is not None:
            return self._logger
        return LOGGER

    def display(self, msg=None, pos=None):
        if not self.n:
            # skip progress bar before having processed anything
            LOGGER.debug('ignoring message before any progress: %r', self.n)
            return
        if self.n == self._last_log_n:
            # avoid logging for the same progress multiple times
            LOGGER.debug('ignoring log message with same n: %r', self.n)
            return
        self._last_log_n = self.n
        if msg is None:
            msg = self.__str__()
        if not msg:
            LOGGER.debug('ignoring empty message: %r', msg)
            return
        self._get_logger().info('%s', msg)
