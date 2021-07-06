#!/usr/local/bin/python3

# next to lines are required for GUI file pickers
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path

# this is the brains of the operation
import Python_Resources.transform_vnp_xml_cmd as cmd_version

# for getting files form urls
import urllib.request
import ssl

# working with file paths
from os import path

# for geting the date
import datetime

# for making the prograpm pause
import time


class bcolors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# class for the GUI app
class EBApp:
    def __init__(self, master):

        # input file path
        self.working_folder = tk.StringVar()
        # input url path
        self.input_url     = tk.StringVar()

        # Date of VnP we want to produce
        self.sitting_date  = tk.StringVar()

        # add title to the window
        master.title("Get VnP XML")

        # create a counter to for the rows for the grid geometry
        rows = Counter()

        # make background frame
        self.frame_background = ttk.Frame(master)
        self.frame_background.pack(fill=tk.BOTH, expand=tk.TRUE)
        # add margin space
        self.inner_background = ttk.Frame(self.frame_background)
        self.inner_background.pack(fill=tk.BOTH, expand=tk.TRUE, padx=5, pady=20)

        # make frames for each step
        self.step_0 = ttk.LabelFrame(self.inner_background, text='Step 0')
        self.step_0.pack(padx=10, pady=5, fill=tk.BOTH, expand=tk.TRUE)
        self.step_1 = ttk.LabelFrame(self.inner_background, text='Step 1')
        self.step_1.pack(padx=10, pady=5, fill=tk.BOTH, expand=tk.TRUE)
        self.step_2 = ttk.LabelFrame(self.inner_background, text='Step 2')
        self.step_2.pack(padx=10, pady=5, fill=tk.BOTH, expand=tk.TRUE)
        self.step_3 = ttk.LabelFrame(self.inner_background, text='Step 3')
        self.step_3.pack(padx=10, pady=5, fill=tk.BOTH, expand=tk.TRUE)


        # url text entry lable
        self.url_box_lable = ttk.Label(self.step_0, text='You should not need to do anything here!\nIf you need to, You can change the base URL.\t[If you want to process a file replace the URL with the file path and delete the date from step 2]')
        self.url_box_lable.config(wraplength=350)
        self.url_box_lable.grid(row=rows.count(), column=0, stick='sw', padx=5, pady=3)
        # url text entry box
        self.url_box = ttk.Entry(self.step_0, textvariable=self.input_url, width=42)
        self.url_box.grid(row=rows.count(), column=0, stick='w', padx=5, pady=10)
        self.url_box.insert(0, 'http://services.vnp.parliament.uk/voteitems')

        # select folder lable
        self.select_folder_lable = ttk.Label(self.step_1, text='Select the folder that you would like the XML to be saved into. (VnP date folder).')
        self.select_folder_lable.config(wraplength=350)
        self.select_folder_lable.grid(row=rows.count(), column=0, stick='sw', padx=5, pady=3)
        # select folder button
        self.select_folder_button = ttk.Button(self.step_1, text="Select Folder", width=12, command=self.get_working_folder)
        self.select_folder_button.grid(row=rows.count(), column=0, stick='sw', padx=5, pady=10)

        # VnP date lable
        self.Creation_box_lable = ttk.Label(self.step_2, text='Check the VnP date is correct. This is the date of the VnP you are working on. The date must be in the form YYYY-MM-DD (e.g. 2016-09-11).')
        self.Creation_box_lable.config(wraplength=350)
        self.Creation_box_lable.grid(row=rows.count(), column=0, stick='sw', padx=5, pady=10)
        # VnP date box
        self.Creation_box = ttk.Entry(self.step_2, textvariable=self.sitting_date, width=10)
        self.Creation_box.grid(row=rows.count(), column=0, stick='w', padx=5, pady=3)
        self.Creation_box.insert(0, get_todays_date())

        # Run button lable
        self.run_lable = ttk.Label(self.step_3, text="Press Run and then look for the 'All Done' message in the console window.")
        self.run_lable.config(wraplength=350)
        self.run_lable.grid(row=rows.count(), column=0, stick='sw', padx=5, pady=10)
        # run button
        self.run_Transform_VnP_XML_button = ttk.Button(self.step_3, text="Run", width=20, command=self.run_Transform_VnP_XML)
        self.run_Transform_VnP_XML_button.grid(row=rows.count(), column=0, padx=10, pady=15)

    def run_Transform_VnP_XML(self):

        # validate
        if not self.validate():
            return

        # input file name
        infilename = self.input_url.get()
        sitting_date = self.sitting_date.get()
        working_folder = self.working_folder.get()

        if sitting_date != '':
            # only do this if there is a date entered. If not assume a filepath
            infilename += '/' + self.sitting_date.get() + '.xml'
            # create a filename for the XML as downloaded before transformation
            output_file_name = path.join(working_folder, 'as_downloaded_VnP_XML_' + sitting_date + '.xml')
            # get file from url
            print('\nThe URL we are trying is:\n{}'.format(infilename))
            infilename = get_file_from_url(infilename, output_file_name=output_file_name)
        else:
            sitting_date = get_todays_date()

        # run functions
        time.sleep(1)
        cmd_version.transform_xml(infilename, working_folder=working_folder, sitting_date=sitting_date)

        print('\nAll Done!')

    def get_working_folder(self):
        # where we expect we will want to save the vnp XML
        initialdir = Path.home() / 'UK Parliament' / 'PPU - Publications' / 'Votes_and_Proceedings'

        # make sure what we are expecting exsits
        if not initialdir.exists():
            initialdir = Path.home() / 'UK Parliament' / 'PPU - Publications'
        if not initialdir.exists():
            initialdir = Path.home() / 'UK Parliament'

        directory = filedialog.askdirectory(initialdir=initialdir)
        self.working_folder.set(directory)


    def validate(self):
        folder = self.working_folder.get()

        if not folder:
            show_error('Please select a folder in step 1.')
            return False

        if not os.access(folder, os.W_OK):
            show_error('{} is not a writabel folder. Please chose another folder.'.format(folder))
            return False

        try:
            datetime.datetime.strptime(self.sitting_date.get(), '%Y-%M-%d')
        except ValueError:
            show_error('Looks like you have not entered a valid date. Enter a date in the form YYYY-MM-DD')
            return False

        return True


def get_todays_date():
    tomorrow = datetime.date.today()
    return tomorrow.strftime('%Y-%m-%d')


def show_error(error_text):
    error_text = 'ERROR: ' + error_text
    # if os.name == 'posix':
    print(bcolors.FAIL + error_text + bcolors.ENDC)
    # else: print(error_text)
    messagebox.showerror("Error", error_text)


# counter
class Counter:
    def __init__(self):
        self.number = 0

    def increment(self):
        self.number += 1

    def count(self):
        self.increment()
        return self.number


def get_file_from_url(url, output_file_name='output.xml'):
    try:
        # ignore the ssl certificate
        context = ssl._create_unverified_context()
        response = urllib.request.urlopen(url, context=context)
    except:
        print('\nERROR:\tCan\'t get the XML from:\n{}\nCheck the url is right.'.format(url))
        return -1
    data = response.read()      # a `bytes` object
    # text = data.decode('utf-8')  # a `str`; this step can't be used if data is binary
    output_file = open(output_file_name, 'wb')
    output_file.write(data)
    output_file_path = path.abspath(output_file.name)
    output_file.close()
    print('\nDownloaded XML is at:\n{}'.format(output_file_path))
    return output_file_path


def main():

    # try and fix blury text on windows
    if os.name == "nt":
        from ctypes import windll
        try:
            windll.shcore.SetProcessDpiAwareness(1)
            kernel32 = windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass  # don't do anything

    run_Transform_VnP_XMLapp = tk.Tk()
    EBApp(run_Transform_VnP_XMLapp)
    run_Transform_VnP_XMLapp.mainloop()


if __name__ == "__main__": main()
