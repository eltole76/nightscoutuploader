import os
import json
import pytz
import requests
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv

class NightscoutUploader:
    def __init__(self, directory='.'):
        # Load environment variables from the .env file
        load_dotenv()

        # Nightscout API configuration from environment variables
        self.NIGHTSCOUT_URL = os.getenv('NIGHTSCOUT_URL')
        self.API_SECRET = os.getenv('API_SECRET')
        self.directory = directory

        # Log file configuration with rotation
        log_filename = 'upload.log'
        log_handler = RotatingFileHandler(log_filename, maxBytes=2*1024*1024, backupCount=5)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

    def get_json_files(self):
        return [f for f in os.listdir(self.directory) if f.startswith('data-202') and f.endswith('.json')]

    def read_json_file(self, filepath):
        with open(filepath, 'r') as file:
            return json.load(file)

    def upload_to_nightscout(self, data, endpoint):
        headers = {
            'api-secret': self.API_SECRET,
            'Content-Type': 'application/json'
        }
        response = requests.post(self.NIGHTSCOUT_URL + endpoint, headers=headers, json=data)
        if response.status_code == 200:
            logging.info(f"Data {endpoint} uploaded successfully to {self.NIGHTSCOUT_URL}")
            return True
        else:
            logging.error(f"Error uploading data {endpoint} to {self.NIGHTSCOUT_URL}: {response.status_code} - {response.text}")
            return False

    def process_and_upload_data(self):
        json_files = self.get_json_files()
        if not json_files:
            logging.error("No JSON files found.")
            return

        # Get the most recent file
        latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(self.directory, f)))
        data = self.read_json_file(os.path.join(self.directory, latest_file))
        
        # Process and upload SG measurements
        sg_data = []
        for sg in data['patientData']['sgs']:
            sg_data.append({
                'date': int(datetime.strptime(sg['timestamp'], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000),
                'sgv': sg['sg'],
                'direction': 'None',
                'type': 'sgv'
            })
        sg_upload_success = self.upload_to_nightscout(sg_data, 'entries.json') if sg_data else True
        
        # Process and upload boluses
        bolus_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'INSULIN' and 'dataValues' in marker['data'] and 'deliveredFastAmount' in marker['data']['dataValues']:
                bolus_data.append({
                    'insulin': marker['data']['dataValues']['deliveredFastAmount'],
                    'created_at': datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').astimezone(tz=pytz.UTC).isoformat(),
                    'eventType': 'Bolus'
                })
        bolus_upload_success = self.upload_to_nightscout(bolus_data, 'treatments.json') if bolus_data else True

        # Process and upload carbohydrates
        carb_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'MEAL' and 'dataValues' in marker['data'] and 'amount' in marker['data']['dataValues']:
                carb_data.append({
                    'eventType': 'Meal Bolus',
                    'carbs': marker['data']['dataValues']['amount'],
                    'created_at': datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').astimezone(tz=pytz.UTC).isoformat(),
                    'enteredBy': 'carelink',
                    'notes': 'Meal'
                })
        carb_upload_success = self.upload_to_nightscout(carb_data, 'treatments.json') if carb_data else True

        # Process and upload calibrations
        calibration_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'CALIBRATION' and 'dataValues' in marker['data'] and marker['data']['dataValues'].get('calibrationSuccess') == True:
                calibration_data.append({
                    'eventType': 'Calibration',
                    'created_at': datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').astimezone(tz=pytz.UTC).isoformat(),
                    'enteredBy': 'carelink',
                    'notes': f"Calibration value: {marker['data']['dataValues']['unitValue']} {marker['data']['dataValues']['bgUnits']}"
                })
        calibration_upload_success = self.upload_to_nightscout(calibration_data, 'treatments.json') if calibration_data else True

        # Process and upload device information
        device_upload_success = True
        device_data = data.get('patientData')
        if device_data:
            # You can adapt this block according to the actual structure of your JSON
            devicestatus = [{
                "device": device_data.get("medicalDeviceInformation", {}).get("manufacturer", "Unknown"),
                "created_at": device_data.get("lastUpdate", datetime.now().isoformat()),
                "uploader": {
                    "battery": device_data.get("pumpBatteryLevelPercent", None),
                    "status": device_data.get("systemStatusMessage", None)
                },
                "pump": {
                    "reservoir": device_data.get("reservoirAmount", None),
                    "serialNumber": device_data.get("pumpSerialNumber", None)
                },
                "manufacturer": device_data.get("medicalDeviceInformation", {}).get("manufacturer", "Unknown"),
                  # You can adjust the fields according to what your Nightscout accepts
            }]
            device_upload_success = self.upload_to_nightscout(devicestatus, 'devicestatus.json')
            logging.info(f"device: {devicestatus}")
        # Example of processing exercise data
        exercise_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'EXERCISE' and 'dataValues' in marker['data']:
                exercise_data.append({
                    'eventType': 'Exercise',
                    'duration': marker['data']['dataValues'].get('duration', 0),  # minutes
                    'created_at': datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').astimezone(tz=pytz.UTC).isoformat(),
                    'enteredBy': 'carelink'
                })
        if exercise_data:
            self.upload_to_nightscout(exercise_data, 'treatments.json')

        # Process and upload blood glucose readings
        bg_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'BG_READING' and 'dataValues' in marker['data']:
                bg_data.append({
                    'date': int(datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000),
                    'mbg': marker['data']['dataValues']['bg'],
                    'type': 'mbg'
                })
        if bg_data:
            self.upload_to_nightscout(bg_data, 'entries.json')

        # Log the processed file
        logging.info(f"Processed file: {latest_file}")

        # Delete the file from disk after successful processing
        if sg_upload_success and bolus_upload_success and carb_upload_success and calibration_upload_success and device_upload_success:
            os.remove(os.path.join(self.directory, latest_file))
            logging.info(f"File deleted: {latest_file}")
        else:
            logging.error(f"Error uploading data. The file {latest_file} will not be deleted.")

if __name__ == '__main__':
    uploader = NightscoutUploader(directory='.')
    uploader.process_and_upload_data()