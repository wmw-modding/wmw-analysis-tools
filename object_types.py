
import traceback
import logging
import os
import sys
import subprocess
import io
import platform
from datetime import datetime
import time

def createLogger(type = 'file', filename = 'logs/log.log'):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    format = '[%(levelname)s] %(message)s'
    datefmt = '%I:%M:%S %p'
    level = logging.DEBUG

    # filename = 'log.log'
    
    handlers = []

    if type == 'file':
        try:
            os.mkdir('logs')
        except:
            pass
        
        handlers.append(logging.FileHandler(filename))
        format = '[%(asctime)s] [%(levelname)s] %(message)s'

        # logging.basicConfig(filename=filename, filemode='w', format=format, datefmt=datefmt, level=level)
        # logger.info('logging file')
    
    handlers.append(logging.StreamHandler())
    logging.basicConfig(format=format, datefmt=datefmt, level=level, handlers=handlers)
    
    logger = logging.getLogger(__name__)
    logger.info(filename)


_log_filename = f'logs/{datetime.now().strftime("%m-%d-%y_%H-%M-%S")}.log'

createLogger('file', filename = _log_filename)

def log_exception():
    fileio = io.StringIO()
    traceback.print_exc(file = fileio)

    logging.error(fileio.getvalue())

import typing
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import copy

import wmwpy
import json

from json_utils import *
from settings import Settings

OBJECT_TYPES : dict[
    str, dict[
        str, dict[
            typing.Literal[
                'type',
                'values'
            ], typing.Literal['int', 'float', 'bool', 'bit', 'string'] | set[str]
        ]
    ]] = {}

class Object_Analysis():
    def __init__(
        self,
        gamepath : str = '',
        assets : str = '/assets',
        game : str = 'WMW',
        template : str = '',
        output : str = 'objects_output.json',
        load_callback : typing.Callable[[int, str, int], typing.Any] = None,
        analysis_callback : typing.Callable[[int, str, int], typing.Any] = None,
    ) -> None:
        if gamepath in ['', None]:
            raise TypeError('gamepath must be a path')
        
        self.load_callback = load_callback
        self.anaysis_callback = analysis_callback
        
        self.game : wmwpy.Game = wmwpy.load(
            gamepath = gamepath,
            assets = assets,
            game = game,
            hook = self.load_callback
        )
        
        self.template : dict[
            str, dict[
                str, dict[
                    typing.Literal[
                        'type',
                        'values'
                    ], typing.Literal['int', 'float', 'bool', 'bit', 'string'] | set[str]
                ]
            ]] = {}
        self.output_path = output
        
        if template not in ['', None]:
            if isinstance(template, str):
                with open(template, 'r') as file:
                    self.template = json.load(file)
            else:
                self.template = copy.deepcopy(template)
        self.template = list_to_set(self.template)
        
        self.object_types : dict[
            str, dict[
                str, dict[
                    typing.Literal[
                        'type',
                        'values'
                    ], typing.Literal['int', 'float', 'bool', 'bit', 'string'] | set[str]
                ]
            ]] = copy.deepcopy(self.template)
    
    def start(
        self,
        anaysis_callback : typing.Callable[[int, str, int], typing.Any] = None,
        load_callback : typing.Callable[[int, str, int], typing.Any] = None,
    ):
        if callable(anaysis_callback):
            self.anaysis_callback = anaysis_callback
        if callable(load_callback):
            self.load_callback = load_callback
        
        start_time = time.time()
        
        level_files = self.game.filesystem.listdir(
            recursive = True,
            search = '*/Levels/*.xml'
        )
        object_files = self.game.filesystem.listdir(
            recursive = True,
            search = '*.hs'
        )
        finished_objects = set()
        
        self.object_types = copy.deepcopy(self.template)
        
        progress = 0
        
        logging.debug(level_files)
        
        for path in level_files:
            if callable(self.anaysis_callback):
                self.anaysis_callback(progress, path, len(level_files))
            
            level = self.game.Level(
                path,
                load_callback = self.load_callback,
                ignore_errors = True,
            )
            
            self.analyze_level(level)
            level_objects = {obj.filename for obj in level.objects}
            finished_objects.union(level_objects)
            
            progress += 1
        
        if callable(self.anaysis_callback):
            self.anaysis_callback(progress, 'Levels finished', len(level_files))
        
        progress = 0
        
        object_files = [path for path in object_files if path not in finished_objects]
        
        for path in object_files:
            
            if callable(self.anaysis_callback):
                self.anaysis_callback(progress, path, len(level_files))
            
            try:
                obj = self.game.Object(
                    path,
                )
                
                self.analyze_object(obj)
            except:
                log_exception()
            
            progress += 1
        
        if callable(self.anaysis_callback):
            self.anaysis_callback(progress, 'Done!', len(object_files))
        
        self.export_objects()
        
        end_time = time.time()
        
        logging.info(f'Took: {start_time - end_time} seconds')
        
    def analyze_level(self, level : wmwpy.classes.Level):
        if not isinstance(level, wmwpy.classes.Level):
            raise TypeError('level must be Level object')
        
        for obj in level.objects:
            self.analyze_object(obj)
    
    def analyze_object(self, object : wmwpy.classes.Object):
        if not object.type in self.object_types:
            self.object_types[object.type] = {}
        
        for property in object.properties:
            if property == 'Type':
                continue
            
            if ('' in self.object_types) and (property in self.object_types['']):
                self.object_types[''][property]['values'].add(object.properties[property])
                continue
            
            if not property in self.object_types[object.type]:
                self.object_types[object.type][property] = {
                    'type' : 'any',
                    'values' : set()
                }
            
            self.object_types[object.type][property]['values'].add(str(object.properties[property]))
        
    def export_objects(self, output = None):
        if output not in ['', None] and isinstance(output, str):
            self.output_path = output
        
        object_types = make_json_friendly(self.object_types)
        
        with open(self.output_path, 'w') as file:
            json.dump(object_types, file, indent = 2)

class Objects_analysis_gui(tk.Tk):
    def __init__(self, master = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title('Find object properties')
        self.geometry('%dx%d' % (500 , 300) )
        
        self.settings = Settings(
            'config_object_properties.json',
            {
                'version' : 1,
                'gamepath' : '',
                'assets' : '/assets',
                'game' : 'WMW',
                'template' : 'object_type_lists/wmw-template.json',
                'output' : 'wmw_objects.json',
            }
        )
        
        self.game : wmwpy.Game = None

        self.create_window()

    def create_window(self):
        self.create_config()
        self.start_button = ttk.Button(
            text = 'Start',
            command = self.start_analysis,
        )
        self.start_button.pack()
        self.create_progress_bars()
    
    def create_config(self):
        self.config_frame = ttk.Frame()
        self.config_frame.pack(side = 'top', fill = 'both', )
        self.config_frame.columnconfigure(1, weight=1)
        
        self.config_widgets : dict[str, tk.Widget | dict[str, tk.Widget]] = {}
        
        def create_row(
            parent : tk.Widget = self,
            label_text : str = '',
            entry_type : typing.Literal['text', 'options'] = 'text',
            entry_callback : typing.Callable[[str], str] = None,
            default_value : str = '',
            use_button : bool = True,
            button_text : str = 'Browse',
            button_callback : typing.Callable[[str], typing.Any] = None,
            row = 0,
            options : list[str] = []
        ) -> dict[typing.Literal[
            'label',
            'var',
            'entry',
            'button',
        ]]:
            
            label = ttk.Label(
                parent,
                text = label_text,
            )
            label.grid(row = row, column = 0, sticky='ew', padx=4, pady=2)
            
            var = tk.StringVar(
                value = default_value,
            )
            var.trace(
                'w',
                lambda *args : entry_callback(var.get()),
            )
            
            def get_entry(
                type : typing.Literal['text', 'options'],
                var,
                options : list = [],
            ):
                if type == 'options':
                    return ttk.Combobox(
                        parent,
                        textvariable = var,
                        values = options,
                    )
                else:
                    return ttk.Entry(
                        parent,
                        textvariable = var,
                    )
            
            entry = get_entry(
                entry_type,
                var = var,
                options = options,
            )
            # entry.insert(0, var.get())
            entry.grid(row = row, column = 1, sticky = 'ew', padx=4, pady=2)
            
            button = None
            
            if use_button:
                button = ttk.Button(
                    parent,
                    text = button_text,
                    command = lambda *args : var.set(button_callback(var.get())),
                )
                button.grid(row = row, column = 2, sticky = 'ew', padx=4, pady=2)
            
            return {
                'label' : label,
                'var' : var,
                'entry' : entry,
                'button' : button,
            }
        
        def validate(
            default = '',
            result = None,
        ):
            
            if result in ['', None]:
                return default
            else:
                return result
        
        self.config_widgets['gamepath'] = create_row(
            self.config_frame,
            label_text = 'Game path',
            entry_type = 'text',
            entry_callback = lambda value : self.settings.set('gamepath', value),
            default_value = self.settings.get('gamepath'),
            button_callback = lambda path : validate(
                path,
                filedialog.askdirectory(
                    initialdir = os.path.dirname(path),
                    title = 'Game directory',
                )
            ),
            row = 0,
        )
        self.config_widgets['assets'] = create_row(
            self.config_frame,
            label_text = 'Assets path',
            entry_type = 'text',
            entry_callback = lambda value : self.settings.set('assets', value),
            default_value = self.settings.get('assets'),
            button_callback = lambda path : os.path.relpath(
                validate(
                    wmwpy.Utils.path.joinPath(self.settings.get('gamepath'), path),
                    filedialog.askdirectory(
                        initialdir = os.path.dirname(wmwpy.Utils.path.joinPath(self.settings.get('gamepath'), path)),
                        title = 'Assets directory',
                    )
                ),
                self.settings.get('gamepath')
            ),
            row = 1,
        )
        self.config_widgets['game'] = create_row(
            self.config_frame,
            label_text = 'Game',
            entry_type = 'options',
            options = list(wmwpy.GAMES.keys()),
            entry_callback = lambda value : self.settings.set('game', value),
            default_value = self.settings.get('game'),
            use_button = False,
            row = 2,
        )
        self.config_widgets['template'] = create_row(
            self.config_frame,
            label_text = 'Object Template',
            entry_type = 'text',
            entry_callback = lambda value : self.settings.set('template', value),
            default_value = self.settings.get('template'),
            button_callback = lambda path : validate(
                path,
                filedialog.askopenfilename(
                    title = 'Select objects template',
                    defaultextension = '.json',
                    filetypes = (('JSON file', '.json'),
                                 ('Any', '*.*')),
                    initialdir = os.path.dirname(path),
                )
            ),
            row = 3,
        )
        self.config_widgets['template'] = create_row(
            self.config_frame,
            label_text = 'Output',
            entry_type = 'text',
            entry_callback = lambda value : self.settings.set('output', value),
            default_value = self.settings.get('output'),
            button_callback = lambda path : validate(
                path,
                filedialog.asksaveasfilename(
                    title = 'Select output filename',
                    defaultextension = '.json',
                    filetypes = (('JSON file', '.json'),
                                 ('Any', '*.*')),
                    initialdir = os.path.dirname(path),
                )
            ),
            row = 4,
        )
        
        
        
    def create_progress_bars(self):
        
        self.progress_frame = ttk.Frame()
        self.progress_frame.columnconfigure(0, weight = 1, uniform = 'progress')
        self.progress_frame.columnconfigure(1, weight = 1, uniform = 'progress')
        self.progress_frame.pack(side = 'bottom', fill = 'both', )
        
        self.progress_bars : dict[typing.Literal['full', 'loading'], dict[typing.Literal['progress', 'label', 'var', 'callback'], ttk.Progressbar | ttk.Label | tk.StringVar]] = {
            'full' : {},
            'loading' : {},
        }
        
        def create_progress_bar(
            parent : tk.Widget = self,
            row : int = 0,
        ) -> dict[typing.Literal[
            'var',
            'progress',
            'label',
            'callback',
        ], tk.StringVar |
           ttk.Progressbar |
           ttk.Label]:
            
            var = tk.StringVar()
            
            progress : ttk.Progressbar = ttk.Progressbar(
                parent
            )
            progress.grid(row = row, column = 0, sticky = 'ew', padx = 4, pady = 2)
            
            label = ttk.Label(
                parent,
                textvariable = var,
            )
            label.grid(row = row, column = 1, sticky = 'ew', padx = 4, pady = 2)
            
            def callback(index, name, max):
                progress['max'] = max
                progress['value'] = index
                var.set(name)
                
                self.update()
            
            return {
                'var' : var,
                'label' : label,
                'progress' : progress,
                'callback' : callback,
            }
            
        self.progress_bars['full'] = create_progress_bar(
            self.progress_frame,
            row = 0,
        )
        self.progress_bars['loading'] = create_progress_bar(
            self.progress_frame,
            row = 1,
        )
        
    def set_state(
        self,
        state : typing.Literal['enabled', 'disabled'] = 'enabled',
        widget : tk.Widget = None,
    ):
        if widget == None:
            widget = self
        
        if len(widget.winfo_children()) < 1:
            return
        
        for child in widget.winfo_children():
            try:
                child.configure(state = state)
            except:
                pass
            # if isinstance(child, (tk.Frame, ttk.Frame)):
            #     self.set_state(
            #         state,
            #         child,
            #     )

    def start_analysis(self):
        self.set_state('disabled')
        self.set_state('disabled', self.config_frame)
        
        try:
            analysis = Object_Analysis(
                self.settings.get('gamepath'),
                self.settings.get('assets'),
                self.settings.get('game'),
                self.settings.get('template'),
                self.settings.get('output'),
                load_callback = self.progress_bars['loading']['callback'],
                analysis_callback = self.progress_bars['full']['callback'],
            )
        except:
            log_exception()
        
        try:
            analysis.start()
        except:
            log_exception()
        
        self.set_state('enabled')
        self.set_state('enabled', self.config_frame)
    
def main():
    app = Objects_analysis_gui()
    app.mainloop()

if __name__ == '__main__':
    main()
