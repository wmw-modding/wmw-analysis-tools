import os
import typing
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

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

class Window(tk.Tk):
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
        
        self.progress_bars : dict[typing.Literal['full', 'loading'], dict[typing.Literal['progress', 'label', 'var'], ttk.Progressbar | ttk.Label | tk.StringVar]] = {
            'full' : {},
            'loading' : {},
        }
        
        def create_progress_bar(
            parent : tk.Widget = self,
            row : int = 0,
        ) -> dict[typing.Literal[
            'var',
            'progress',
            'label'
        ], tk.StringVar |
           ttk.Progressbar |
           ttk.Label]:
            
            var = tk.StringVar()
            
            progress = ttk.Progressbar(
                parent
            )
            progress.grid(row = row, column = 0, sticky = 'ew', padx = 4, pady = 2)
            
            label = ttk.Label(
                parent,
                textvariable = var,
            )
            label.grid(row = row, column = 1, sticky = 'ew', padx = 4, pady = 2)
            
            
            return {
                'var' : var,
                'label' : label,
                'progress' : progress,
            }
            
        self.progress_bars['full'] = create_progress_bar(
            self.progress_frame,
            row = 0,
        )
        self.progress_bars['loading'] = create_progress_bar(
            self.progress_frame,
            row = 1,
        )

    def start_analysis(self):
        pass
    
def main():
    app = Window()
    app.mainloop()

if __name__ == '__main__':
    main()
