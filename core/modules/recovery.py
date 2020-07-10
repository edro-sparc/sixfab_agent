import time
import logging
from pms_api import SixfabPMS
from pms_api.exceptions import CRCCheckFailed

logger = logging.getLogger("agent")

def try_until_get(api, function):
    try_count = 1
    while True:
        if try_count > 5:
            logger.error("[{}] tried for 3 times and couldn't get response".format(function))
            raise OverflowError("")

        try:
            resp = getattr(api, function)()
        except CRCCheckFailed:
            logger.error("[{}] crc check failed, reinitializing api".format(function))
            del api
            api = SixfabPMS()
        except TypeError:
            logger.error("[{}] TypeError raised, clearing pipe".format(function))
            api.clearPipe()
        except Exception as e:
            logger.error("[{}] unknown exception raised".format(function))
        else:
            return resp
        finally:
            try_count += 1
            
        logger.error("[{}] trying again".format(function))
        time.sleep(0.5)


def try_until_done(api, function, *args, **kwargs):
    try_count = 1

    while True:
        if try_count > 5:
            logger.error("[{}] tried for 3 times and couldn't get response".format(function))
            raise OverflowError("")
        
        try:
            resp = getattr(api, function)(*args, **kwargs)
        except CRCCheckFailed:
            logger.error("[{}] crc check failed, reinitializing api".format(function))
            del api
            api = SixfabPMS()
        except TypeError:
            logger.error("[{}] TypeError raised, clearing pipe".format(function))
            api.clearPipe()
        except Exception as e:
            logger.error("[{}] unknown exception raised".format(function))
        else:
            return resp
        finally:
            try_count += 1


        logger.error("[{}] trying again".format(function))
        time.sleep(0.5)