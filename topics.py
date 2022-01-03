#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

'''IceStorm tools'''

import IceStorm


DEFAULT_TOPICMANAGER_PROXY = 'IceStorm/TopicManager:tcp -p 10000'


def getTopicManager(broker, proxy=DEFAULT_TOPICMANAGER_PROXY):
    '''Get TopicManager object'''
    proxy = broker.stringToProxy(proxy)
    tm = IceStorm.TopicManagerPrx.checkedCast(proxy)
    if not tm:
        raise ValueError(f'Proxy {proxy} is not a valid TopicManager() proxy')
    return tm


def getTopic(topicManager, topic):
    '''Get Topic proxy'''
    try:
        topic = topicManager.retrieve(topic)
    except IceStorm.NoSuchTopic:
        topic = topicManager.create(topic)
    finally:
        return topic
