"""Provide the models for the database to be used with SQLAlchemy."""
import datetime

class Note(object):
    def __init__(self, body):
        self.body = body
        self.date = datetime.datetime.now()

    def __repr__(self):
        return self.body[:30]

class Keyword(object):
    def __init__(self, keyword):
        self.keyword = keyword

    def __repr__(self):
        return self.keyword

class Topic(object):
    def __init__(self, topic):
        self.topic = topic

    def __repr__(self):
        return self.topic

