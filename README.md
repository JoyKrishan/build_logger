# Exercise: Downloading Build Logs from OpenDev Code Review

Build Logger to download all build log files from OpenDev code review record: https://review.opendev.org/c/openstack/watcher-tempest-plugin/+/954214. 

**all_logs.zip** contains all the logs from the builds in the code review.

## Steps to Reproduce

1. **Clone the repository**
2. **Install dependencies**
    ```bash
    python3 -m venv venv
    source venv/bin/activate     
    pip install -r requirements.txt
    pip install -e .
    ```
3. **Download logs**
    ```bash
    build_logger -d 'path/to/download/directory'
    ```

## Directory Structure 

Logs are saved in the following format:
```
<path_to_download_directory>/<comment_id>/builds/<zuul_build_uuid>/
```
This is done to track logs by the comment ID of the code review and the unique build UUID.

For example, if your download directory is `all_logs`, logs will be stored in:
```
all_logs/<comment_id>/builds/<zuul_build_uuid>/
```