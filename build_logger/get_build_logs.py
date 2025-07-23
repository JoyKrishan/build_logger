import os
import gzip
import json
import argparse
import subprocess
import shutil
import urllib.request
from urllib.error import HTTPError

from tqdm import tqdm
import requests

REVIEW_URL = "https://review.opendev.org/c/openstack/watcher-tempest-plugin/+/954214"
ZUUL_API= "https://zuul.opendev.org/api/tenant/openstack"
OPENDEV_API = "https://review.opendev.org/changes"
SOFTWAREFACTORY_API = "https://softwarefactory-project.io/zuul/api/tenant/rdoproject.org"

def get_change_details():
    change_id = REVIEW_URL.split("/")[-1]
    opendev_api_url = f"{OPENDEV_API}/{change_id}/detail"
    response = requests.get(opendev_api_url, 
                            headers={"Accept": "application/json"})
    if response.status_code == 200:
        response_data = json.loads(response.text.replace(")]}'", "", 1))
    else:
        print(f"Failed to access API: {response.status_code} - {response.text}")
        return None
    
    return response_data

def extract_build_links(comments):
    build_links = []
    for comment in comments:
        comment_id = comment.get('id', '')
        comment_text = comment.get('message', '')
        author_username = comment.get('author', {}).get('username', '')
        author_name = comment.get('author', {}).get('name', '')

        if (author_username.lower() == 'zuul' and author_name.lower() == 'zuul') or (author_username.lower() == 'sf-project-io' and author_name.lower() == 'software factory ci'):
            lines = comment_text.split('\n')
            for line in lines:
                if line.startswith('- '): 
                    line = line.strip().split(' ')
                    if len(line) == 8 and line[2].startswith('https://zuul.opendev.org/t/openstack/build/') or line[2].startswith('https://softwarefactory-project.io/zuul/t/rdoproject.org/build/'):
                        build_links.append({
                            'ci': author_username.lower(),
                            'comment_id': comment_id,
                            'url': line[2],
                            'job_name': line[1],
                            'outcome': line[4],
                            'build_time': line[6] + ' ' + line[7],
                        })
        else:
            continue
    
    return build_links

def collect_all_log_files(uuid, ci):
    if ci == 'zuul':
        zuul_api_url = f"{ZUUL_API}/build/{uuid}"
    elif ci == 'sf-project-io':
        zuul_api_url = f"{SOFTWAREFACTORY_API}/build/{uuid}"
    else:
        print(f"Unknown CI system: {ci}")
        return 
    
    try:
        base_url = urllib.request.urlopen(zuul_api_url).read()
        base_json = json.loads(base_url)
        manifest_url = [x['url'] for x in base_json['artifacts'] if x.get('metadata', {}).get('type') == 'zuul_manifest'][0]
        manifest = urllib.request.urlopen(manifest_url)
        if manifest.info().get('Content-Encoding') == 'gzip':
            manifest_json = json.loads(gzip.decompress(manifest.read()))
        else:
            manifest_json = json.loads(manifest.read())
    except HTTPError as e:
        if e.code == 404:
            print("Could not find build UUID in Zuul API. This can happen with")
        else:
            print(e)
        return
        
    def collect_files(node, parent):
        files = []
        if node.get('mimetype') != 'application/directory':
            files.append(parent+node['name'].split(' ')[0])
            
        if node.get('children'):
            for child in node.get('children'):
                    files.extend(collect_files(child, parent + node['name'] + '/'))
        return files

    all_files = [base_json['log_url']]
    for i in manifest_json['tree']:
        all_files.extend(collect_files(i, ''))

    return all_files

def save_log_files(file_path, base_url, save_dir):
    xtra_args = ["--compressed"]
    if file_path.endswith('.xz'):
        xtra_args = []
    
    cmd = ['curl', '-s', '--globoff'] + xtra_args + ['--create-dirs', '-o', file_path, base_url + file_path]
    result = subprocess.run(cmd, cwd=save_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to download {base_url}/{file_path} skipping")
        print(f"Error: {result.stderr}")
        return
    
    if file_path.endswith('.gz'):
        file_result = subprocess.run(['file', file_path], cwd=save_dir, capture_output=True, text=True)
        file_type = file_result.stdout
        
        if 'ASCII text' in file_type or 'Unicode text' in file_type:
            new_name = file_path[:-3]  # Remove .gz extension
            os.rename(file_path, new_name)

def main():
    parser = argparse.ArgumentParser(description="Download build logs from review")
    parser.add_argument('-d', '--download_path', default='all_logs', help='Path to save downloaded logs')
    args = parser.parse_args()
    download_path = args.download_path
    
    change_details = get_change_details()
    if change_details:
        comments = change_details.get('messages', [])
        if comments:
            all_build_links = extract_build_links(comments)
            print(f"Found {len(all_build_links)} build links in this code review: {REVIEW_URL}")
            
            shutil.rmtree(download_path, ignore_errors=True) # remove previous logs
            for build_info in tqdm(all_build_links, desc="Processing builds", position=0, leave=True, colour='green'):
                comment_id = build_info['comment_id']
                uuid = build_info['url'].split('/')[-1]
                ci_username = build_info['ci']
                log_files = collect_all_log_files(uuid, ci_username)
                
                save_dir = os.path.join(download_path, comment_id, 'builds', uuid)
                os.makedirs(save_dir, exist_ok=True)
                
                base_log_url = log_files[0]
                for log_file in tqdm(log_files[1:], desc=f"Downloading logs for build:{uuid}", position=1, leave=False):
                    save_log_files(log_file, base_log_url, save_dir)  
            
            shutil.make_archive(f'{download_path.split("/")[-1]}', 'zip', download_path)
            print(f"All logs downloaded to {download_path}")
        else:
            print("No messages found in the review details.") 
    else:
        print("No change details found.")

if __name__ == "__main__":
    main()