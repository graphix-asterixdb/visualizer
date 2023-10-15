# Graphix Visualizer
A web-based query interface for Graphix.

## Getting Started

1. Ensure that Python 3.11 is installed on your client machine and that Graphix is installed (and launched) on your server machine. 
2. Install the requirements.txt file for your Python environment. 
    To create a virtual environment with all the necessary requirements, run the commands below.
    ```bash
    cd visualizer

    # Create an environment inside the visualizer/venv folder.
    python3 -m venv venv
    
    # Activate this environment.
    source venv/bin/activate
    
    # Install the requirements.
    python3 -m pip install -r requirements.txt
    ```
3. You should now be able to spinup the app locally! Execute the command below and navigate to http://127.0.0.1:8050 to view the query interface in the browser.
    ```bash
    python3 app.py
    ```
   
## Troubleshooting

1. Issuing the `python3 app.py` command on macOS raises an error containing `...in progress in another thread when fork() was called...`.
    This error might be caused by added security to restrict multithreading (see [here](https://stackoverflow.com/a/52230415)).
    Executing the command below should hopefully allow the visualizer to run.
    ```bash
    OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES python3 app.py
    ```

Running into another problem not listed in this doc?
File an issue on Github [here](https://github.com/graphix-asterixdb/visualizer/issues/new)!
