import os, imp
from datetime import datetime

def parse_args():
    from argparse import ArgumentParser
    ap = ArgumentParser(prog='quick_update', description="Updates only open tasks")
    ap.add_argument(dest='settings_path', help='Settings Path')
    return ap.parse_args()

if __name__ == '__main__':   
    args = parse_args()
    settings_path = args.settings_path

    print('INFO:running quick update, Start Time:'+str(datetime.now()))

    # Load the settings file
    print('INFO:loading settings from:'+settings_path)
    settings = imp.load_source('settings', settings_path)

    # Run the quick update
    settings.myLauncher.update_open_tasks()

    print('INFO:finished quick update, End Time: '+str(datetime.now()))
