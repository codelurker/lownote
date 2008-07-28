"""Routines for parsing and loading the rc file."""
import shlex
import os

def _makedir(path):
    """Take a path to a file and try to create the directory the file is in and
    deal with any issues that may come up along the way."""

    dir_path = os.path.dirname(path)
    if dir_path and os.path.exists(dir_path) and not os.path.isdir(dir_path):
        raise IOError("'%s' is not a directory." % (dir_path,))
    if dir_path and not os.path.isdir(dir_path):
        os.makedirs(dir_path)

def load_rc(options):
    """Load the rc file and grab the following:
        * The location of the database;

        (to be continued...)
        The object returned is an updated object of options with any options
        specified at the command line overriding the rc file options.
    """
    defaults = {
        "db_path": "~/.lownote/lownote.sqlite",
    }
    
    rc_default = False
    if options.rc_path == "DEFAULT":
        rc_default = True
        options.rc_path = "~/.lownote/lownoterc"

    options.rc_path = os.path.expanduser(options.rc_path)
    options.db_path = os.path.expanduser(options.db_path)

    _makedir(options.rc_path)

# Try to open the rc file, but remain silent if the rc file was the default, as
# this will just assume that the user wants to use the program defaults and not
# use a rc file.
    try:
        f = open(options.rc_path)
    except IOError, e:
        if not rc_default:
            print "Could not read rc file: %s" % (options.rc_path,)
            raise SystemExit
        return options

    config = parse_rc(f)
    f.close()

# This is a little bit tricky, but it just checks that the key it found in the
# config file is in the defaults (i.e. it is a valid option) and, if it is,
# check that the option wasn't specified at the command line, and if it wasn't,
# add the value to the options.
    for key in config:
        if key not in defaults:
            print "Invalid option: %s" % (key,)
            continue
        if getattr(options, key) == "DEFAULT":
            setattr(options, key, config[key])
    options.db_path = os.path.expanduser(options.db_path)
    _makedir(options.db_path)
    return options

def get_token(tokens):
    """Receive an iterator of the result of shlex.split and return a key/value
    pair for each setting. The caller should catch StopIteration. The values
    returned from the shlex parser's get_token method don't seem to strip
    quotes, but shlex.split does, which is why I've done it like this."""

    k = tokens.next()
    v = None

    bools = {
        'true': True,
        'yes': True,
        'on': True,
        'y': True,
        'Y': True,
        'false': False,
        'no': False,
        'off': False,
        'n': True,
        'N': True,
    }

    k = k.lower()

    if tokens.next() == '=':
        v = tokens.next() or None

    if v is not None:
        try:
            v = int(v)
        except ValueError:
            if v.lower() in bools:
                v = bools[v.lower()]

    return k, v

def parse_rc(f):
    """Simple parser using shlex to get the contents of the rc file token by
    token and then try to convert any numbers to ints, also check to see if
    they're booleans, otherwise leave them as strings and return a dict of
    options."""

    tokens = iter(shlex.split(f.read()))
    f.close()
    config = {}

    while True:
        try:
            k, v = get_token(tokens)
            config[k] = v
        except StopIteration:
            break
    return config

