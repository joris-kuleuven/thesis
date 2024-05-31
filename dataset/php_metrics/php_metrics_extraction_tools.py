import os
import subprocess
import xml.etree.ElementTree as ET
import shutil
import json

def prepare_files(appname, commit_sha, on_deck=False):
    if on_deck:
        base_path = '/home/deck/Documents/masterGT/MT_dataset_repos'
    else:
        base_path = 'C:\\MT_dataset_repos'
    repo_path = os.path.join(base_path, appname)
    temp_dir = os.path.join(repo_path, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Get the path of modified files
    command = ["git", "diff", "--name-only", f"{commit_sha}^", commit_sha]
    process = subprocess.Popen(command, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()

    if process.returncode == 0:
        modified_files = output.splitlines()
        print("There are ", len(modified_files), " modified files")
    else:
        raise Exception(error)

    # Revert modified files to the state of the commit and copy them to temporary directory
    php_file_counter = 0
    for file_path in modified_files:
        # Revert the files
        if file_path.endswith(".php"):
            php_file_counter += 1
            command = ["git", "checkout", commit_sha, "--", file_path]
            process = subprocess.Popen(command, cwd=repo_path)
            process.wait() #Wait until it's finished

            # Copy the reverted file to the temporary directory
            src = os.path.join(repo_path, file_path)
            dst = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
    return php_file_counter

def run_pdepend(app_temp_dir, on_deck=False):
    if on_deck:
        base_path = '/home/deck/Documents/masterGT/MT_dataset_repos'
    else:
        base_path = 'C:\\MT_dataset_repos'
    
    pdepend_path = os.path.join(base_path, "pdepend.phar")    
    command = ['php', pdepend_path, '--summary-xml=sum.xml', app_temp_dir]
    process = subprocess.Popen(command, cwd=base_path)
    process.wait()  # Wait until it's finished

    print("PDEPEND completed successfully.")

def process_class(class_elem):
    name = class_elem.get('name')
    loc = int(class_elem.get('loc'))
    ncloc = int(class_elem.get('ncloc'))
    dit = int(class_elem.get('dit'))
    nocc = int(class_elem.get('nocc'))
    cbo = int(class_elem.get('cbo'))
    wmc = int(class_elem.get('wmc'))
    
    methods = class_elem.findall('method')
    if methods:
        ccn_sum = 0
        hv_sum = 0
        for method in methods:
            ccn_sum += int(method.get('ccn'))
            hv_sum += float(method.get('hv'))
        average_ccn = ccn_sum / len(methods)
        average_hv = hv_sum / len(methods)
    else:
        average_ccn = 0
        average_hv = 0

    class_data = {
        'name': name,
        'loc': loc,
        'ncloc': ncloc,
        'dit': dit,
        'nocc': nocc,
        'cbo': cbo,
        'wmc': wmc,
        'average_ccn': average_ccn,
        'average_hv': average_hv
    }
    return class_data

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    commits_metrics = {
        'loc': 0,
        'ncloc': 0,
        'dit': 0,
        'nocc': 0,
        'cbo': 0,
        'wmc': 0,
        'total_classes': 0,
        'total_methods': 0,
        'total_ccn': 0,
        'total_hv': 0
    }

    for package in root.findall('package'):
        for class_elem in package.findall('class'):
            class_data = process_class(class_elem)
            
            # Accumulate metrics
            commits_metrics['loc'] += class_data['loc']
            commits_metrics['ncloc'] += class_data['ncloc']
            commits_metrics['dit'] += class_data['dit']
            commits_metrics['nocc'] += class_data['nocc']
            commits_metrics['cbo'] += class_data['cbo']
            commits_metrics['wmc'] += class_data['wmc']
            commits_metrics['total_classes'] += 1
            commits_metrics['total_ccn'] += class_data['average_ccn']
            commits_metrics['total_hv'] += class_data['average_hv']

    if commits_metrics['total_classes'] > 0:
        commits_metrics['average_loc'] = commits_metrics['loc'] / commits_metrics['total_classes']
        commits_metrics['average_ncloc'] = commits_metrics['ncloc'] / commits_metrics['total_classes']
        commits_metrics['average_dit'] = commits_metrics['dit'] / commits_metrics['total_classes']
        commits_metrics['average_nocc'] = commits_metrics['nocc'] / commits_metrics['total_classes']
        commits_metrics['average_cbo'] = commits_metrics['cbo'] / commits_metrics['total_classes']
        commits_metrics['average_wmc'] = commits_metrics['wmc'] / commits_metrics['total_classes']
        commits_metrics['average_ccn'] = commits_metrics['total_ccn'] / commits_metrics['total_classes']
        commits_metrics['average_hv'] = commits_metrics['total_hv'] / commits_metrics['total_classes']
    else:
        commits_metrics['average_loc'] = -1
        commits_metrics['average_ncloc'] = -1
        commits_metrics['average_dit'] = -1
        commits_metrics['average_nocc'] = -1
        commits_metrics['average_cbo'] = -1
        commits_metrics['average_wmc'] = -1
        commits_metrics['average_ccn'] = -1
        commits_metrics['average_hv'] = -1
    return commits_metrics

def clear_temp_files(appname, on_deck=False):
    # Define the path to the temporary directory
    if on_deck:
        base_path = '/home/deck/Documents/masterGT/MT_dataset_repos'
    else:
        base_path = 'C:\\MT_dataset_repos'
    temp_dir = os.path.join(base_path, appname, "temp")
    sum_dir = os.path.join(base_path, "sum.xml")

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print("Temporary files cleared for", appname)
    else:
        print("Temporary directory does not exist for", appname)
    
    if os.path.exists(sum_dir):
        os.remove(sum_dir)
        print("Temporary sum.xml cleared for", appname)
    else:
        print("Temporary sum.xml does not exist for", appname)

def parse_xml_one_package(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    class_data = []
    package = root.findall('package')[1]

    for class_elem in package.findall('class'):
        class_data.append(process_class(class_elem))

    for item in class_data:
        print(item)

def dict_to_json_file(input_dict, file_path):
    try:
        with open(file_path, 'w') as json_file:
            json.dump(input_dict, json_file, indent=4)
        print(f"JSON data saved to '{file_path}' successfully.")
    except Exception as e:
        print(f"Error: {e}")

def clear_all_temp_files():
    with open("/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/phpAppsWithGithubLinks.json", 'r') as file:
        php_ghlink = json.load(file)
    
    for entry in php_ghlink:
        clear_temp_files(entry["appname"], on_deck=True)

