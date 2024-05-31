"""
This file is for cloning the repository in Yeska's other machine
"""
import os
import json

with open('jsons/before_cvv_cves.json', 'r') as f:
    cve_data = json.load(f)
# Directory where repositories will be cloned
base_dir = '/home/deck/Documents/masterGT/MT_dataset_repos'

os.makedirs(base_dir, exist_ok=True)
app_counter = 0
for appname, data in cve_data.items():
    if appname:
        gh_link = data.get('gh_link')
        if gh_link:
            #print(gh_link, " ", appname)
            # Create directory for the app
            app_dir = os.path.join(base_dir, appname)
            os.makedirs(app_dir, exist_ok=True)

            # Clone repository
            os.system(f'git clone {gh_link}.git {app_dir}')
            print(f"Cloned {appname} repository to {app_dir}")
            app_counter += 1

print("total app is ", app_counter) #this is to check if the number of app is correct