# nightscoutuploader

## Objective
The `nightscoutuploader` project is designed to integrate with [Nightscout](https://nightscout.github.io/), an open-source platform for visualizing and analyzing diabetes-related data. This tool processes JSON files containing health data (e.g., glucose levels, insulin doses) and uploads them to a Nightscout server for easy visualization and monitoring.

## Features
- Parses JSON files containing health data.
- Uploads the processed data to a Nightscout server.
- Enables real-time visualization and analysis of health metrics.

## Installation

To use this project, follow these steps:

1. **Clone the Repository**  
   Open your terminal and run:
   ```bash
   git clone https://github.com/eltole76/nightscoutuploader.git
   cd nightscoutuploader

2. **Install dependences**
    ```bash
    pip install -r requirements.txt
    ```

3. **this project use Carelink Python Client library**
    - [Carelink Python Client](https://github.com/ondrej1024/carelink-python-client)

4. **Run execution**
    First of all, you need to follow the next steps:
    
    ***Create the login data***

    The Carelink Client library needs the initial login data stored in the `logindata.json` file. This file is created by running the login script on a PC with a screen.

    The script opens a Firefox web browser with the Carelink login page. You have to provide your Carelink patients or follower credentials and solve the reCapcha. On successful completion of the login the data file will be created. 

    ```
    python ..\carelink-python-client\carelink_carepartner_api_login.py 
    ```
    The Carelink Client reads this file from the local folder and it will take care of refreshing automatically the login data when it expires. It should be able to do so within one week of the last refresh.

    ***Define environment variables***
    You need to define the NightScout API URL and access Token in your .env file.

    ***Run Main Process to upload***
    And the last step, you need to execute the mainprocess.py

    ```
    python .\mainprocess.py --verbose 
    ```
