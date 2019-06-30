""" decorative helpers """
import logging

from functools import wraps

from campscrape.msgtype import MessageType
from campscrape.db import db


logger = logging.getLogger(__name__)


def check_cache(func):
    """ decorator for looking up and storing message content """
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            m, mtype = args
            if mtype == MessageType.error:
                # message error skip db
                return func(*args, **kwargs)
            else:
                content = "{0}:{1}:{2}:{3}".format(
                    m.get('num_avail'),
                    m.get('unit_type'),
                    m.get('campsite_name'),
                    m.get('date_avail')
                )
                already_seen_msg = db.get_set(bytes(content, 'utf8'))
                if already_seen_msg:
                    kwargs["msg_type"] = MessageType.cached
                    return func(args, kwargs)
                logger.info("Skipping alert on previously seen message: {}".format(content))
                return None
        except Exception as exc:
            logger.error("Error checking cache {}".format(exc))
    return inner
