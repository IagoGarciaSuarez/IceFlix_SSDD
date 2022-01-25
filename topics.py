#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

'''IceStorm tools'''

import IceStorm

DEFAULT_TOPICMANAGER_PROXY = 'IceStorm/TopicManager:tcp -p 10000'


def getTopicManager(broker, proxy=DEFAULT_TOPICMANAGER_PROXY): # pylint: disable=invalid-name
    '''Get TopicManager object'''
    proxy = broker.stringToProxy(proxy)
    topic_manager = IceStorm.TopicManagerPrx.checkedCast(proxy) # pylint: disable=no-member
    if not topic_manager:
        raise ValueError(f'Proxy {proxy} is not a valid TopicManager() proxy')
    return topic_manager


def getTopic(topic_manager, topic): # pylint: disable=invalid-name
    '''Get Topic proxy'''
    try:
        topic = topic_manager.retrieve(topic)
    except IceStorm.NoSuchTopic: # pylint: disable=no-member
        topic = topic_manager.create(topic)

    return topic
