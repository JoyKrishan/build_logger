# Exercise Report: Downloading Build Logs from OpenDev Code Review

Build Logger to download all build log files from OpenDev code review record: https://review.opendev.org/c/openstack/watcher-tempest-plugin/+/954214. 

**all_logs.zip** - Contains all logs downloaded from the builds in the code review.

## Steps to Reproduce

1. **Clone the repository**
2. **Install dependencies**
    ```bash
    python3 -m venv .venv
    pip install -r requirements.txt
    pip install -e .
    ```
3. **Run the Script**
    ```bash
    build_logger -d 'path/to/download/directory'
    ```

How it looks when running:
![alt text](static_files/running_instance.png) 

## Logs Organization

Logs are saved in this folder structure:
```
<path>/<comment_id>/builds/<build_uuid>/
```

For example:
```
all_logs/2fec73a50ccb11733556f6d717ca16dbdba9e47b/builds/c83de12787bf4f91aa9829f5d5d30b4d/
```
This organization links each comment (comment_id) with its corresponding build logs. I could have organized by build outcome and job name, or created a CSV to track details, but preferred this simple structure to track the relationship between comment_id and the builds.


*Rationale on why all files under log tab are downloaded*: According to [Zuul documentation](https://zuul-ci.org/docs/zuul/latest/job-content.html#working-directory), the Zuul executor creates a directory containing all content related to a job. Therefore, downloading everything under the Log tab gives complete information about the build/test process and environment.

![alt text](static_files/zuul_ui.png)

*Disclosure of Help Taken*
- I utilized GitHub Copilot's autocomplete feature in Visual Studio Code while writing this script. 
- I did not use Copilot's chat interface or Copilot agent, so there are no chat logs.
- I have referred to public information on the internet to learn how to download logs from Zuul CI. To be specific, I used the following resource: [https://opendev.org/zuul/zuul-jobs/commit/ca2ee69e60accf0292b9e3fdb4605b51be646525]