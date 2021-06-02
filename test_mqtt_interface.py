import os
import time
import traceback
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox as mb
from tkinter import *
from mqtt_interface import *
import threading

base_path = os.path.dirname(os.path.realpath(__file__))

DISPLAY_WIDTH  = 400
DISPLAY_HEIGHT = 400

BACKGROUND_COLOR = 'white'

class GCS():

    def __init__(self):
        
        self.root = tk.Tk()
        self.root.configure(bg=BACKGROUND_COLOR)
        self.root.resizable(False, False)
        self.root.title('NPNT Client')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        left = (self.root.winfo_screenwidth() - DISPLAY_WIDTH) / 2
        top = (self.root.winfo_screenheight() - DISPLAY_HEIGHT) / 2
        self.root.geometry('%dx%d+%d+%d' % (DISPLAY_WIDTH, DISPLAY_HEIGHT, left, top))
        self.root.after(100, self.update_interface)

        self.frame = tk.Frame(self.root)
        self.frame.pack()
        self.PA_filename = None
        self.PA_status = tk.Label(self.frame,text='')
        self.PA_status.pack()

        # the interface runs in a separate thread so we don't have to worry about updating it ourselves.
        self.mqtt_interface = mqtt_interface()
        # buttons that will call functions that call interface functions.
        self.PA_SEND_BUTTON = self._add_button(label='PA_SEND', parent=self.frame,
                                               callback = self.PA_func, disabled=True)
        self.GET_LOG_BUTTON = self._add_button(label='GET_LOG', parent=self.frame,
                                               callback=self.LOG_func, disabled = True)
        self.GET_APM_LOG_BUTTON = self._add_button(label='GET_APM_LOG',parent=self.frame,
                                                   callback=self.APM_LOG_func, disabled = True)
        self.GET_UIN_BUTTON = self._add_button(label = 'GET_DRONE_UIN', parent=self.frame,
                                               callback=self.UIN_func, disabled = True)
        
        self.FILE_SELECT_BUTTON = self._add_button(label='SELECT_PA_FILE', parent=self.frame,
                                                   callback = self.FILE_SELECT, disabled=False)
        self.filename = None
        self.filesize = None

    def _add_button(self, label, parent, callback, disabled=True):
        button = tk.Button(parent, text=label, command=callback)
        button.pack(side=tk.LEFT)
        button.config(state = 'disabled' if disabled else 'normal')
        return button

    def on_closing(self):
        ## you can add other stuff that you want to do before closing
        self.mqtt_interface.on_closing()

    def FILE_SELECT(self):
        self.PA_filename = filedialog.askopenfilename(initialdir = base_path,title = "Select file",filetypes = (("xml files","*.xml"),("all files","*.*")))

    def PA_func(self):
        if(self.PA_filename != None):
            self.mqtt_interface.PA_filename = self.PA_filename  # this could have been done in the file-select function
            self.mqtt_interface.PA_SEND()
        else:
            print("no PA file selected")

    def LOG_func(self):
        self.mqtt_interface.LOG_REQUEST()

    def APM_LOG_func(self):
        self.mqtt_interface.APM_LOG_REQUEST()

    def UIN_func(self):
        self.mqtt_interface.UIN_GET()

    def update_interface(self):
        if(self.mqtt_interface.new_error):
            self.mqtt_interface.new_error = False
            mb.showerror(self.mqtt_interface.error)
        elif(self.mqtt_interface.new_info):
            self.mqtt_interface.new_info = False
            mb.showinfo(self.mqtt_interface.info)

        if(self.mqtt_interface.RFM_connected == True):
            print("RFM connected")
            self.GET_LOG_BUTTON["state"] = "normal"
            self.GET_APM_LOG_BUTTON["state"] = "normal"
            self.GET_UIN_BUTTON["state"] = "normal"
            if(self.PA_filename != None):
                self.PA_SEND_BUTTON["state"] = "normal"

        self.root.after(100, self.update_interface)

gcs = GCS()
gcs.root.mainloop()


