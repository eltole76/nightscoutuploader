import os
import subprocess
import logging
from datetime import datetime
import argparse
from NightscoutUploader import NightscoutUploader  
from dotenv import load_dotenv

# Log file configuration
log_filename = 'mainprocess.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

def run_script(script, args):
    try:
        result = subprocess.run(['python', script] + args, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"Executed {script} successfully. Output: {result.stdout}")
        else:
            logging.error(f"Error executing {script}. Exit code: {result.returncode}. Error: {result.stderr}")
    except Exception as e:
        logging.error(f"Exception while executing {script}: {str(e)}")

def run_process_upload():
    uploader = NightscoutUploader(directory='.')
    uploader.process_and_upload_data()


def main():
    parser = argparse.ArgumentParser(description='Daily process to run scripts and log outputs.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show logs in the console')
    args = parser.parse_args()

    if args.verbose:
        # Logger configuration for the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(console_handler)

    logging.info("Start of daily process")
    
    load_dotenv()
    #print(os.getenv('NIGHTSCOUT_URL'))
    #print(os.getenv('API_SECRET'))
    
    # Run carelink_client2_cli.py with arguments -d -v
    run_script('..\carelink-python-client\carelink_client2_cli.py', ['-d', '-v'])
    
    # Run upload_to_nightscout.py
    run_process_upload()

    logging.info("End of daily process")

if __name__ == '__main__':
    main()