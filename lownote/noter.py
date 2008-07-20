"""The main legwork of the note-taking, this is where all the SQL stuff
goes."""
from sqlalchemy import (create_engine, Table, Column, Integer, String,
                        DateTime, MetaData, ForeignKey)
from sqlalchemy.orm import mapper, sessionmaker, relation, backref
from sqlalchemy.exceptions import InvalidRequestError
from lownote.model import Note, Keyword, Topic
import re

class Noter(object):
    """There needs to be an abstraction between the actual database and the
    concept of note-taking within the context of lownote, so this class
    provides that API such that this class will encapsulate all the SQL
    work and provide a completely abstracted interface for the rest of 
    the program to work with."""

    def __init__(self, db_path):
        """Initialise the database if it doesn't already exist; the notes
        table needs to have a many-to-many relationship with both the keywords
        and the topics tables."""

        self.db_path = db_path
        self.engine = create_engine('sqlite:///' + db_path, echo=False)

        self.metadata = MetaData()

        notes_table = Table('notes', self.metadata,
            Column('id', Integer, primary_key=True, index=True),
            Column('body', String(4000)),
            Column('date', DateTime()),
       )

        keywords_table = Table('keywords', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('keyword', String(50), nullable=False, index=True),
            Column('note', Integer, ForeignKey('notes.id')),
       )
            
        topics_table = Table('topics', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('topic', String(100), nullable=False, index=True),
            Column('note', Integer, ForeignKey('notes.id')),
       )

        mapper(Note, notes_table, properties={
            'topics': relation(Topic),
            'keywords': relation(Keyword),
            }
       )
        mapper(Keyword, keywords_table)
        mapper(Topic, topics_table)

        self.metadata.create_all(self.engine) 
        
        Session = sessionmaker(bind=self.engine, autoflush=True,
                                  transactional=True)

        self.session = Session()

    def get_keywords(self, body):
        """Parse the body of the note and yield keywords as they are found.
        Note that this method also needs to check if any keywords are found in
        the note that are not explicitly %%referenced%% by checking the
        keywords table and comparing each word in the body of the note to
        it."""

        keywords = set([])
        for keyword in re.finditer("%%(.+?)%%", body):
            keyword = keyword.group(1).lower()
            keywords.add(keyword)
            yield keyword.lower()
        
        db_keywords = set(x.keyword for x in self.session.query(Keyword))
        for word in re.split(r'\b(.+?)\b', body):
            if not word:
                continue
            word = word.lower()
            if word not in keywords and word in db_keywords:
                yield word


    def add_note(self, body, topics=[]):
        """The body of the note is always required, otherwise there's no note
        to add. "topics" and "keywords" are not required but they must always
        be a list, even if it contains one element (so as not to need any type
        checking). This method needs to process the note (i.e. parse for
        keywords) and add it to the database."""
        
        note = Note(body)
        self.session.save(note)

        for topic in topics:
            note.topics.append(Topic(topic))

        for keyword in self.get_keywords(body):
            note.keywords.append(Keyword(keyword))

        self.session.commit()

