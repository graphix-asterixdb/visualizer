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
