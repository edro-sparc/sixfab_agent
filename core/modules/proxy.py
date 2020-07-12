import time
import logging
import requests

logger = logging.getLogger("agent")

DISTRIBUTION_SERVICE = "http://localhost:6060"

def get_metric_by_sensor(sensor, metric, default=None):
    try:
        return requests.get("{}/metrics/{}/{}".format(DISTRIBUTION_SERVICE, sensor, metric)).json()["value"]
    except:
        return default

def get_metric(metric, default=None):
    try:
        return requests.get("{}/metrics/{}".format(DISTRIBUTION_SERVICE, metric)).json()["value"]
    except:
        return default

def run_signal(signal, default=None):
    try:
        return requests.get("{}/signals/{}".format(DISTRIBUTION_SERVICE, signal)).json()["value"]
    except:
        return default

def update_configurations(body: dict, default=None):
    try:   
        return requests.post("{}/configurations".format(DISTRIBUTION_SERVICE), json=body).status_code
    except:
        return default

def get_scheduled_event_ids(default=None):
    try:
        return requests.get("{}/events".format(DISTRIBUTION_SERVICE)).json()["ids"]
    except:
        return default

def delete_scheduled_events(ids: list, default=None):
    try:
        return requests.delete("{}/events".format(DISTRIBUTION_SERVICE), json={"ids": [id for id in ids]}).json()["ids"]
    except:
        return default

def create_scheduled_event(events: list):
    try:
        return requests.post("{}/events".format(DISTRIBUTION_SERVICE), json={"events": events}).status_code
    except:
        pass


def lock_distribution_service():
    try:
        return requests.get("{}/locker/lock".format(DISTRIBUTION_SERVICE)).status_code
    except:
        pass

def release_distribution_service():
    try:
        return requests.get("{}/locker/release".format(DISTRIBUTION_SERVICE)).status_code
    except:
        pass