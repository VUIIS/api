import os, imp
from datetime import datetime

def parse_args():
    from argparse import ArgumentParser
    ap = ArgumentParser(prog='lastupdated_subj2sess', description="Sets last_updated field on sessions for subjects that are up-to-date")
    ap.add_argument(dest='settings_path', help='Settings Path')
    return ap.parse_args()

if __name__ == '__main__':   
    args = parse_args()
    settings_path = args.settings_path

    # Load the settings file
    print('INFO:loading settings from:'+settings_path)
    settings = imp.load_source('settings', settings_path)
    lockfile_prefix = os.path.splitext(os.path.basename(settings_path))[0]

    # Run the updates
    print('INFO:setting last_upated, Start Time:'+str(datetime.now()))
    settings.myLauncher.lastupdated_subj2sess()
    print('INFO:finished setting last_updated, End Time: '+str(datetime.now()))
