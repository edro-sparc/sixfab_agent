import time
import logging
from pms_api import SixfabPMS
from pms_api.exceptions import CRCCheckFailed

def try_until_get(api, function):
    while True:
        try:
            resp = getattr(api, function)()
        except CRCCheckFailed:
            logging.error("\033[33m[{}] \033[0m crc check failed, reinitializing api".format(function))
            del api
            api = SixfabPMS()
        except TypeError:
            logging.error("\033[33m[{}] \033[0m TypeError raised, clearing pipe".format(function))
            api.clearPipe()
        except Exception as e:
            logging.error("\033[33m[{}] \033[0m unknown exception raised".format(function))
        else:
            logging.debug("\033[94m[{}] \033[0m done".format(function))
            return resp
            
        logging.error("[{}] trying again".format(function))
        time.sleep(0.5)


def try_until_done(api, function, *args, **kwargs):
    while True:
        try:
            resp = getattr(api, function)(*args, **kwargs)
        except CRCCheckFailed:
            logging.error("\033[33m[{}] \033[0m crc check failed, reinitializing api".format(function))
            del api
            api = SixfabPMS()
        except TypeError:
            logging.error("\033[33m[{}] \033[0m TypeError raised, clearing pipe".format(function))
            api.clearPipe()
        except Exception as e:
            logging.error("\033[33m[{}] \033[0m unknown exception raised".format(function))
        else:
            logging.debug("\033[94m[{}] \033[0m Function executed success".format(function))
            return resp


        logging.error("[{}] trying again".format(function))
        time.sleep(0.5)