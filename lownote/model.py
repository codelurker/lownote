"""Provide the models for the database to be used with SQLAlchemy."""
import datetime

class Note(object):
    def __init__(self, body, due_date):
        self.body = body
        self.date = datetime.datetime.now()
        if due_date is not None:
            if len(due_date) == 8:
                format = "%Y%m%d"
            elif len(due_date) == 6:
                format = "%y%m%d"
            else:
                raise ValueError("Format must be YYYYMMDD or YYMMDD.")
            self.due_date = datetime.datetime.strptime(due_date, format)
        else:
            self.due_date = None

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

