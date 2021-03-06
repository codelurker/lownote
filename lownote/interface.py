"""
Provide the main curses interface work. The interface takes a Note object,
although this can be any object with the right attributes, so there's no
dependency on any databasing stuff; just an object with body, date, keywords,
topics attributes (this may not be an exhaustive list)>
"""

import curses
import re
import textwrap
from lownote.keys import keys 

class Window(object):
    """Base class to wrap curses window functionality, should be inherited to
    provide more specific functionality."""

    # blacK, Red, Green, Yellow, Blue, Magenta, Cyan, White, Default:
    colours = {
        "K": 0,
        "R": 1,
        "G": 2,
        "Y": 3,
        "B": 4,
        "M": 5,
        "C": 6,
        "W": 7,
        "D": 8,
    }

    def __init__(self, y, x, height, width):
        """Nothing crazy; just initialise the window and attach it to the
        instance."""

        self.window = curses.newwin(height, width, y, x)
        self.window.keypad(1)
        self.window.scrollok(True)
        self.scrolling = 0
        self.width = width
        self.height = height
        self.y = y
        self.x = x
        self.fg = "W"
        self.bg = None

    def update(self):
        self.window.refresh()

    def echo_colour(self, string, fg, bg, pad=False, center=False):
        if center:
            x = self.window.getyx()[1]
            string = string.center(self.width - x)

        if pad:
            x = self.window.getyx()[1]
            pad_len = self.width - x - len(string) 
            string += " " * pad_len

        if bg is None:
            attr = curses.color_pair(self.colours[fg] + 1)
        else:
            attr = curses.color_pair(
                (self.colours[bg] * 8) + self.colours[fg] + 1
                )
        self.fg = fg
        self.bg = bg
        self.window.addstr(string, attr)

    def echo(self, string, pad=False, center=False):
        if '\n' in string:
            for line in string.split('\n'):
                self.echo_line(line, pad, center)
                self.window.addstr('\n')
        else:
            self.echo_line(string, pad, center)

    def echo_line(self, string, pad, center):
# XXX: If there's no \x03 colour code in the string (e.g. with the kind of data
# returned by textwrap.wrap, assume the last colour used:
        if not string.startswith("\x03"):
            if self.bg is not None:
                colour = self.fg + self.bg
            else:
                colour = self.fg
            colour = "\x03%s\x03" % colour
            self.echo(colour + string)
            return

        # Grab "\x03XX\x03foobarbaz" strings - the lookahead assert is
        # necessary to make it match up to the next \x03 or $ without actually
        # grabbing it (which would skip the next match):
        for section in re.findall("\x03([a-zA-Z][a-zA-Z]?)\x03(.*?)(?=(?:\x03|$))",
                                        string):
            fg = section[0][0].upper()
            bg = None
            if len(section[0]) == 2:
                bg = section[0][1].upper()

            self.echo_colour(section[1], fg, bg, pad, center)

    def insert_line(self, string, x, pad=False, center=False):
        self.window.move(x - self.scrolling + 1, 0)
        self.window.move(1,0)
        self.window.insertln()
        self.window.move(x - self.scrolling + 1, 0)
        self.echo_line(string, pad, center)

    def clear_line(self, index):
# Increment index by 1 to ignore the "title" of the index window:
        index += 1
        self.window.move(index - self.scrolling, 0)
        self.window.clrtoeol()
        self.window.move(index - self.scrolling, 0)

    def clear(self):
        self.window.erase()

    def wrap(self, text):
        lines = textwrap.wrap(text, self.width)
        return "\n".join(lines)


class MainWindow(Window):
    def __init__(self, y, x, height, width):
        super(MainWindow, self).__init__(y, x+1, height, width)
        self.seperator = Window(y, x, height, 1)
        self.seperator.window.attrset(
            curses.color_pair(self.colours["B"] + 1)
            )
        self.seperator.window.vline(curses.ACS_VLINE, height)

    def hard_update(self):
        self.window.touchwin()
        self.seperator.window.touchwin()

    def update(self):
        super(MainWindow, self).update()
        self.seperator.update()

    def display_note(self, note, keywords):
        self.clear()
        self.echo("\x03Y\x03Note made on: \x03G\x03%s\n"
                % note.date.strftime("%c"))
        if note.topics:
            topics_string = ", ".join(x.topic for x in note.topics)
        else:
            topics_string = "\x03b\x03[None]"
        self.echo("\x03Y\x03Listed under topics: \x03G\x03%s\n"
                % (topics_string,))
        body = note.body
        for keyword in keywords:
            body = re.sub("(?i)(%s)" % (keyword,),
                '\x03R\x03\\1\x03B\x03', body)
        body = self.wrap(body)

        self.echo("\x03B\x03%s" % body)
        self.update()

class IndexWindow(Window):
    def __init__(self, y, x, height, width):
        super(IndexWindow, self).__init__(y, x, height, width)
        self.notes = []
        self.last_selected = self.selected = -1
        self.echo_title()

    def echo_title(self):
        self.echo("\x03BR\x03Notes:", pad=True, center=True)
        
    def get_note_count(self):
        return len(self.notes)

    def repopulate(self):
        self.clear()
        self.echo_title()
        for note in self.notes:
            self.echo_note(note)
        # This marks the current selection as dirty, so the selection will be
        # redrawn, e.g. after deletion/insertion:
        self.last_selected = -1
        self.update()
        
    def append(self, note):
        self.notes.append(note)
        self.echo_note(note)
        self.update()

    def delete(self, x):
        if not self.notes:
            return
        if len(self.notes) < x:
            return
        del self.notes[x]
        if x <= len(self.notes):
            self.selected -= 1
        self.repopulate()

    def insert(self, note, x):
        self.notes.insert(x, note)
        self.repopulate()
        self.selected += 1

    def echo_note(self, note):
        self.echo('\x03G\x03' + note.body[:self.width], pad=True)

    def echo_selected(self, note):
        self.echo('\x03KG\x03' + note.body[:self.width], pad=True)

    def up(self):
        if not self.notes:
            return
        if self.selected == 0:
            return
        
        self.last_selected = self.selected
        self.selected -= 1
        self.update()

    def down(self):
        if not self.notes:
            return
        if len(self.notes) == self.selected + 1:
            return

        self.last_selected = self.selected
        self.selected += 1
        self.update()

    def select(self, index):
        if self.last_selected != -1:
            self.clear_line(self.last_selected)
            self.echo_note(self.notes[self.last_selected])
        self.clear_line(self.selected)
        self.echo_selected(self.notes[self.selected])

# XXX: Might seem a bit weird, but update() checks for the difference and
# redraws if last_selected and selected don't match:
        self.last_selected = self.selected

    def hard_update(self):
        self.window.touchwin()

    def update(self):
        if self.selected != self.last_selected:
            self.select(self.selected)
        super(IndexWindow, self).update()

class Interface(object):
    """Main interface class; provide methods for initialising the screen with
    the window setup (left column with list of notes/topics, larger right
    column with the note contents), adding text to the screen (though
    high-level so no real understanding of 'text' is really necessary in terms
    of drawing to the screen - just pass a string to the right method and let
    it handle it. Also handle screen resizing and keyboard input."""

    def make_colours(self):
        curses.start_color()
        curses.use_default_colors()
        for i in range(63):
            if i > 7: j = i / 8
            else: j = -1
            curses.init_pair(i+1, i % 8, j)

    def __init__(self, scr, callback=None, timeout=500):
        """Work out how big to draw the columns and initialise them as separate
        windows. The curses screen comes externally so the caller can deal with
        the curses wrapper in the main script. The callback specified is for
        any processing that needs to be done by the caller when the interface
        does something (i.e. when a user hits a key or the timeout is
        reached)."""

        self.make_colours()
        curses.curs_set(0)
        self.scr = scr
        height, width = self.scr.getmaxyx()
        
        self.callback = callback
        self.keywords = set()
        index_width = int(width * 0.25)
        main_width = width - index_width

        self.note_index = IndexWindow(0, 0, height, index_width)
        self.note_display = MainWindow(0, index_width, height, main_width)
        self.note_display.window.timeout(timeout)
        self.update()

        self.selected = self.note_index

        self.keys_dispatch = {
            keys['exit']: self.exit,
            keys['up']: self.up,
            keys['down']: self.down,
            keys['delete']: self.delete,
        }
        
    def add_keyword(self, keyword):
        self.keywords.add(keyword)

    def exit(self):
        raise SystemExit

    def up(self):
        if not self.note_index.notes:
            return
        self.note_index.up()
        self.note_display.display_note(
            self.note_index.notes[self.note_index.selected],
            self.keywords
            )

    def down(self):
        if not self.note_index.notes:
            return
        self.note_index.down()
        self.note_display.display_note(
            self.note_index.notes[self.note_index.selected],
            self.keywords
            )

    def delete(self):
        if self.callback is not None:
            self.callback(self,
                    delete=self.note_index.notes[self.note_index.selected])
        self.note_index.delete(self.note_index.selected)

    def insert_note(self, note, x=0):
        self.note_index.insert(note, x)

    def add_note(self, note):
        self.note_index.append(note)

    @property
    def index_count(self):
        return self.note_index.get_note_count()

    def update(self):
        for win in (self.note_index, self.note_display):
            win.update()
        curses.doupdate()

    def hard_update(self):
        for win in (self.note_index, self.note_display):
            win.hard_update()
        self.update()

    def get_key(self):
        try:
            key = self.note_display.window.getkey()
        except curses.error, e:
            self.hard_update()
            key = None
        return key

    def handle_events(self):
        while True:
            key = self.get_key()
            if key in self.keys_dispatch:
                self.keys_dispatch[key]()
            if self.callback is not None:
                self.callback(self)
