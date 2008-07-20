#!/usr/bin/env python

"""
lownote

Advanced note-taking program. Add notes and have them automatically link to
other notes containing key words. Signify a key word like so:
    This is a %keyword% in a sentence.

See all related notes for each note, create a link (without a keyword) to
any other note so that it will permanently become a related note, search
through all available notes, batch notes together into multiple topics
(i.e. a many-to-many relationship).

All keywords and topics are case-insensitive for context matching.

Add notes from the command line:
    lownote Write a kick-ass note-taking program in %%Python%%

Available options (these must precede the actual body of the note):
    -t [topic]  Specify the topic of the note (can be used multiple times).
    -i          Load in interactive mode (default if no options are given).

The interactive mode (i.e. the actual interface to your notes) uses ncurses.

The notes are stored in a SQLite database and SQLALchemy is used to interface
with it.
"""

from optparse import OptionParser
import curses
from lownote.noter import Noter
from lownote.rcfile import load_rc

def get_args():
    """Get the command line arguments and return them in the form:
    options, body
    Multiple topics can be specified with repeated use of the -t option
    so topics will be a list and the body will be the remaining arguments.

    The reason for passing "DEFAULT" instead of an actual default is so that
    when the rc file is loaded it know whether to override the default or not;
    I couldn't think of another way of doing this.
    """
    parser = OptionParser()
    parser.add_option("-t", "--topic", action="append", type="string",
                        help="Zero or more topics to describe this note.",
                        default=[], dest="topics")
    parser.add_option("-c", "--config", action="store", type="string",
                        help="Specify an alternate location for the rc file.",
                        default="DEFAULT", dest="rc_path")
    parser.add_option("-p", "--path", action="store", type="string",
                        help="Specify a path for the notes database.",
                        default="DEFAULT", dest="db_path")
    (options, args) = parser.parse_args()

    options = load_rc(options)
    return options, " ".join(args)


def main():
    options, body = get_args()
    notetaker = Noter(options.db_path)
    notetaker.add_note(body, topics=options.topics)

if __name__ == "__main__":
    main()
