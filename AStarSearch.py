# fix AI
# red trail
# scrolling boxes
#

import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, InstructionGroup
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics.instructions import Callback
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

from time import sleep
import operator
from random import shuffle

kivy.require('1.10.0')

# neighbor's relative coordinates
nrc = [(0,0), (0,1), (1,0), (1,1), (0,0), (0,-1), (-1,0), (-1,-1)]


class Block(Label):
    def __init__(self, **kwargs):
        super(Block, self).__init__(**kwargs)


class OpenLabel(Label):
    def __init__(self, **kwargs):
        super(OpenLabel, self).__init__(**kwargs)


class ClosedLabel(Label):
    def __init__(self, **kwargs):
        super(ClosedLabel, self).__init__(**kwargs)


def adjust_content(self, *args):
    Root.cb.ask_update()
    if Root.agent is not None and Root.board.current is not None:
        Root.agent.center = Root.board.current.center
    [adjust_label(l) for t in Root.board.children for l in t.children]


def adjust_input(self, *args):
    self.font_size = self.height * .65
    Root.board.size = Root.board_space.size
    Root.board.pos = Root.board_space.pos


def adjust_label(l, *args):
    parent = l.parent
    parent.remove_widget(l)
    parent.add_widget(l)
    l.size = l.text_size = l.parent.size
    l.pos = l.parent.pos


class Agent(Label):
    def __init__(self, **kwargs):
        super(Agent, self).__init__(**kwargs)


class FloatSection(FloatLayout):
    def __init__(self, **kwargs):
        super(FloatSection, self).__init__(**kwargs)


class Dimension(GridLayout):
    def __init__(self, **kwargs):
        super(Dimension, self).__init__(cols=3, rows=1, **kwargs)
        if self.id == 'x_dim':
            xl = self.xl = BlackScaleLabel(text='COLS')
            xti = self.xti = ScaleLabel(text='15')
            xti.bind(size=adjust_input)
            xb = self.xb = GridLayout(rows=1, cols=2)
            self.add_widget(xl)
            self.add_widget(xti)
            self.add_widget(xb)
            minus = self.minus = Button(text='-', background_color=(1, .8, .8, 1))
            minus.bind(on_press=self.dec_x)
            xb.add_widget(minus)
            plus = self.plus = Button(text='+', background_color=(.8, 1, .8, 1))
            xb.add_widget(plus)
            plus.bind(on_press=self.inc_x)
        else:
            yl = self.yl = BlackScaleLabel(text='ROWS')
            yti = self.yti = ScaleLabel(text='15')
            yti.bind(size=adjust_input)
            yb = self.yb = GridLayout(rows=1, cols=2)
            self.add_widget(yl)
            self.add_widget(yti)
            self.add_widget(yb)
            minus = self.minus = Button(text='-', background_color=(1, .8, .8, 1))
            minus.bind(on_press=self.dec_y)
            yb.add_widget(minus)
            plus = self.plus = Button(text='+', background_color=(.8, 1, .8, 1))
            yb.add_widget(plus)
            plus.bind(on_press=self.inc_y)

    def dec_x(self, *args):
        if int(self.xti.text) > 2:
            self.xti.text = str(int(self.xti.text) - 1)

    def inc_x(self, *args):
        if int(self.xti.text) < 25:
            self.xti.text = str(int(self.xti.text) + 1)

    def dec_y(self, *args):
        if int(self.yti.text) > 2:
            self.yti.text = str(int(self.yti.text) - 1)

    def inc_y(self, *args):
        if int(self.yti.text) < 25:
            self.yti.text = str(int(self.yti.text) + 1)


class Board(GridLayout):
    def __init__(self, **kwargs):
        super(Board, self).__init__(cols=int(Root.x_dim.xti.text), rows=int(Root.y_dim.yti.text, **kwargs))
        self.start = None
        self.goal = None
        self.current = None
        self.h = None
        self.open = []
        self.closed = []
        self.path = []
        self.done = False
        self.o = 0

    def load(self, *args):
        self.start = None
        self.goal = None
        self.current = None
        self.h = None
        self.open = []
        self.closed = []
        self.path = []
        self.done = False
        if Root.agent is not None:
            Root.board_space.remove_widget(Root.agent)
        self.pos = Root.board_space.pos
        self.size = Root.board_space.size
        if self.children is not None:
            self.clear_widgets()
        self.cols = int(Root.x_dim.xti.text)
        self.rows = int(Root.y_dim.yti.text)
        print(Root.x_dim.xti.text, Root.y_dim.yti.text)
        self.n = self.rows * self.cols

        l = [x for x in range(1, self.n + 1)]
        shuffle(l)
        self.blocks = l[:len(l) // 10 + (0 if len(l) % 10 == 0 else 1)]
        [l.remove(x) for x in self.blocks]
        self.tilenums = l

        Clock.schedule_interval(self.add_tile, 0.00001)
        self.i = 0

    def add_tile(self, *args):
        tile = Tile(text=str(self.i + 1), on_press=self.set_goal)
        tile.block = False
        if int(tile.text) in self.blocks:
            tile = Block()
            tile.block = True
        tile.loc = (self.i % self.cols + 1, self.cols - self.i // self.cols)
        print(tile.loc)
        tile.f = None
        tile.g = None
        tile.p = None
        tile.visit = False
        tile.open = False
        tile.closed = False
        self.add_widget(tile)
        self.i += 1
        if self.i >= self.n:
            Clock.unschedule(self.add_tile)

    def set_goal(self, tile, *args):
        if self.done is True:
            self.current = None
            self.h = None
            self.open = []
            self.closed = []
            self.path = []
            if Root.agent is not None:
                Root.board_space.remove_widget(Root.agent)
            Root.open_box.clear_widgets()
            Root.closed_box.clear_widgets()
        if len(self.children) == self.cols * self.rows or self.done is True:
            if self.done is True:
                self.goal.background_color = (1, 1, 1, 1)
                self.start.background_color = (1, 1, 1, 1)
                self.goal = None
                self.start = None
                self.done = False
            if self.start is not None and self.goal is None and self.start != tile:
                self.goal = tile
                with self.goal.canvas.before:
                    self.goal.background_color = (.5, 1, .5, 1)
            elif self.start is None:
                self.start = tile
                tile.g = 0
                tile.p = None
                with self.start.canvas.before:
                    self.start.background_color = (.5, .5, 1, 1)
            if self.start is not None and self.goal is not None and self.h is not True:
                self.h = True
                [self.assign_heuristic(t) for t in self.children if t.block is False]
                agent = Root.agent = Agent()
                agent.center = self.start.center
                Root.board_space.add_widget(agent)
                self.add_open(self.start)
                self.current = self.start
                Clock.schedule_interval(self.turn, 1 / Root.slider.value)


    def assign_heuristic(self, tile, *args):
        tile.clear_widgets()
        tile.closed = tile.open = False
        v = abs(self.goal.loc[1] - tile.loc[1])
        h = abs(self.goal.loc[0] - tile.loc[0])
        tile.h = v + h
        tile.g = None
        h = Label(text=str(tile.h), size=tile.size, pos=tile.pos, halign='right', valign='bottom')
        h.text_size = h.size
        tile.add_widget(h)
        print(tile.h)

    def turn(self, *args):
        Clock.schedule_once(self.pop_open, .5 / Root.slider.value)
        if self.current is self.goal and self.current is not None:
            self.done = True
            self.gen_path(self.goal)
        else:
            self.neighbors = [tile for tile in self.children
                              if tile.block is False  # tile is traversable
                              # and (abs(int(tile.text) - int(self.current.text)) / self.cols == 1
                              #      or abs(int(tile.text) - int(self.current.text)) == 1)  # tile is above or below current
                              and (tile.loc[0] - self.current.loc[0], tile.loc[1] - self.current.loc[1]) in nrc
                              and abs(self.current.loc[0] - tile.loc[0]) < 14
                              and abs(self.current.loc[1] - tile.loc[1]) < 14
                              and tile.closed is False]
            [self.value_tile(tile) for tile in self.neighbors]
            [self.add_open(tile) for tile in self.neighbors if tile.open is False]
            self.add_closed(self.current)

    def pop_open(self, *args):
        self.o += 1
        tiles = [t[0] for t in self.open]
        min_f = min(tiles, key=operator.attrgetter('f')).f
        min_h = min([t.h for t in tiles])
        self.min = [t for t in tiles if t.f == min_f and t.h == min_h]
        print(min_f, min_h)
        if len(self.min) == 0:
            self.min = min([t for t in tiles if t.f == min_f], key=operator.attrgetter('h'))
        else:
            self.min = self.min[-1]
        print(min_f, min_h)
        self.open.remove((self.min, self.min.f))
        self.current = self.min
        Root.open_box.remove_widget(self.current.ol)
        if len(self.open) == 0 and self.o > 1:
            self.done = True
            Clock.unschedule(self.turn)
            self.np = np = GridLayout(cols=1, rows=2)
            np.header = GridLayout(cols=2, rows=1, size_hint_y=.1)
            np.title = ScaleLabel(text='No Path Found')
            np.exit = Button(text='Exit', size_hint_x=.1, on_press=self.np_exit)
            np.add_widget(np.header)
            np.header.add_widget(np.title)
            np.header.add_widget(np.exit)
            self.np.pos = Root.board.pos
            Root.board_space.add_widget(np)

    def np_exit(self, *args):
        Root.board_space.remove_widget(self.np)
        Root.remove_widget(Root.agent)

    def gen_path(self, tile, *args):
        self.path.append(int(tile.text))
        if tile.p is not None:
            self.gen_path(tile.p)
        else:
            self.end()

    def end(self, *args):

        # mark path with red overlay
        # get rid of old start/goal
        Clock.unschedule(self.turn)
        self.p = p = GridLayout(cols=1, rows=2)
        p.header = GridLayout(cols=2, rows=1, size_hint_y=.1)
        p.title = ScaleLabel(text='Shortest Path')
        p.exit = Button(text='Exit', size_hint_x=.1, on_press=self.p_exit)
        s = ''
        i = 1
        for x in reversed(self.path[1:len(self.path)]):
            s += (str(x) + ('->' if i % 5 != 0 else '->\n'))
            i += 1
        s += str(self.path[-1])
        s = s[:-4]

        # adjusting font size won't work, change body to scroller of labels
        p.body = BlackScaleLabel(text=s)
        p.add_widget(p.header)
        p.add_widget(p.body)
        p.header.add_widget(p.title)
        p.header.add_widget(p.exit)
        self.p.pos = Root.board.pos
        Root.board_space.add_widget(p)

    def p_exit(self, *args):
        Root.board_space.remove_widget(self.p)

    def value_tile(self, tile, *args):
        if tile.g is None or tile.g > self.current.g + 1:
            tile.g = self.current.g + 1
            tile.p = self.current
        if tile.f is None:
            tile.f = tile.g + tile.h

    def add_open(self, tile, *args):
        tile.open = True
        if tile.g is None:
            tile.g = 0
        tile.f = tile.g + tile.h
        g_label = Label(text=str(tile.g), size=tile.size, pos=tile.pos, halign='right', valign='top')
        g_label.text_size = g_label.size
        tile.add_widget(g_label)
        f_label = Label(text=str(tile.f), size=tile.size, pos=tile.pos, halign='center', valign='center')
        f_label.text_size = f_label.size
        tile.add_widget(f_label)
        self.open.append((tile, tile.f))
        tile.ol = OpenLabel(text=tile.text)
        Root.open_box.add_widget(tile.ol)

    def add_closed(self, tile, *args):
        if tile.closed is False:
            tile.closed = True
            self.closed.append(tile)
            tile.cl = ClosedLabel(text=tile.text)
            Root.closed_box.add_widget(tile.cl)

    def move_agent(self, *args):
        pass


class MainWindow(GridLayout):
    def __init__(self, **kwargs):

        # Layer 1
        super(MainWindow, self).__init__(cols=2, rows=1, padding=10, spacing=10, **kwargs)
        global Root
        Root = self
        Root.agent = None
        with Root.canvas:
            Root.cb = Callback(adjust_content)

        # Layer 2
        left_side = self.left_side = Section(cols=1, rows=2, size_hint_x=.8, spacing=5)
        right_side = self.right_side = Section(cols=1, rows=4, size_hint_x=.2, spacing=10)
        self.add_widget(left_side)
        self.add_widget(right_side)

        # Layer 3
         # Left
        board_space = self.board_space = FloatSection(size_hint_y=.95)
        option_bar = self.option_bar = Section(cols=6, rows=1, size_hint_y=.05, padding=0)
        left_side.add_widget(board_space)
        left_side.add_widget(option_bar)

         # Right
        open_label = self.open_label = ScaleLabel(text='OPEN', size_hint_y=.15)
        open_box = self.open_box = StackLayout(size_hint=(1, 1))
        open_box.spacing = (open_box.width * .05, open_box.height * .05)
        right_side.add_widget(open_label)
        right_side.add_widget(open_box)

        closed_label = self.closed_label = ScaleLabel(text="CLOSED", size_hint_y=.15)
        closed_box = self.closed_box = StackLayout()
        right_side.add_widget(closed_label)
        right_side.add_widget(closed_box)

        # Layer 4
         # Left
          # option_bar contents
        x_dim = self.x_dim = Dimension(id='x_dim')
        y_dim = self.y_dim = Dimension(id='y_dim')
        option_bar.add_widget(x_dim)
        option_bar.add_widget(y_dim)

        s_label = self.s_label = BlackScaleLabel(text='SPEED', size_hint_x=.33)
        s_value = self.s_value = ScaleLabel(text='1.00', size_hint_x=.33)
        slider = self.slider = Slider(min=0.0001, max=8, value=1)
        slider.bind(value=self.set_speed)
        option_bar.add_widget(s_label)
        option_bar.add_widget(s_value)
        option_bar.add_widget(slider)

        btn = self.btn = Button(text='START / RESTART', font_size=self.height * .14)
        btn.bind(size=self.btn_text)
        board = self.board = Board()
        board_space.add_widget(board)
        btn.bind(on_press=board.load)
        option_bar.add_widget(btn)


    def btn_text(self, *args):
        self.btn.font_size = self.btn.height * .5

    def set_speed(self, *args):
        self.s_value.text = '{:.2f}'.format(self.slider.value)
        if len(Root.board.children) > 0:
            Clock.unschedule(Root.board.turn)
            Clock.schedule_interval(Root.board.turn, 1 / self.slider.value)


class ScaleInput(TextInput):
    def __init__(self, cols=15, rows=15, **kwargs):
        super(ScaleInput, self).__init__(**kwargs)


class Tile(Button):
    def __init__(self, **kwargs):
        super(Tile, self).__init__(**kwargs)


class BlackScaleLabel(Label):
    pass


class ScaleLabel(Label):
    def __init__(self, **kwargs):
        super(ScaleLabel, self).__init__(**kwargs)


class ListGrid(GridLayout):
    def __init__(self, **kwargs):
        super(ListGrid, self).__init__(**kwargs)


class Subsection(GridLayout):
    def __init__(self, **kwargs):
        super(Subsection, self).__init__(**kwargs)


class Section(GridLayout):
    def __init__(self, **kwargs):
        super(Section, self).__init__(**kwargs)


class AStarSearchApp(App):
    light = ObjectProperty(Image(source='Light Gray.png', anim_delay=.1))
    darkest = ObjectProperty(Image(source='Darkest Gray.png', anim_delay=.1))
    dark = ObjectProperty(Image(source='Dark Gray.png', anim_delay=.1))
    black = ObjectProperty(Image(source='Black.png', anim_delay=.1))
    agent = ObjectProperty(Image(source='Agent.png', anim_delay=.1))
    open = ObjectProperty(Image(source='Open.png', anim_delay=.1))
    closed = ObjectProperty(Image(source='Closed.png', anim_delay=.1))
    def build(self):
        return MainWindow()

if __name__ == '__main__':
    AStarSearchApp().run()
