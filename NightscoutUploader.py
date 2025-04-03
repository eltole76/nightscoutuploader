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
        # Cargar variables de entorno desde el archivo .env
        load_dotenv()

        # Configuración de la API de Nightscout desde variables de entorno
        self.NIGHTSCOUT_URL = os.getenv('NIGHTSCOUT_URL')#, 'http://localhost/api/v1/')
        self.API_SECRET = os.getenv('API_SECRET')#, 'your-secret-key')
        self.directory = directory

        # Configuración del archivo de log con rotación
        log_filename = 'upload.log'
        log_handler = RotatingFileHandler(log_filename, maxBytes=2*1024*1024, backupCount=5)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

    def get_json_files(self):
        return [f for f in os.listdir(self.directory) if f.startswith('data-2025') and f.endswith('.json')]

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
            logging.info(f"Datos {endpoint} subidos correctamente a {self.NIGHTSCOUT_URL}")
            return True
        else:
            logging.error(f"Error al subir datos {endpoint} a {self.NIGHTSCOUT_URL}: {response.status_code} - {response.text}")
            return False

    def process_and_upload_data(self):
        json_files = self.get_json_files()
        if not json_files:
            logging.error("No se encontraron archivos JSON.")
            return

        # Obtener el archivo más reciente
        latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(self.directory, f)))
        data = self.read_json_file(os.path.join(self.directory, latest_file))
        
        # Procesar y subir mediciones SG
        sg_data = []
        for sg in data['patientData']['sgs']:
            sg_data.append({
                'date': int(datetime.strptime(sg['timestamp'], '%Y-%m-%dT%H:%M:%S').timestamp() * 1000),
                'sgv': sg['sg'],
                'direction': 'None',
                'type': 'sgv'
            })
        sg_upload_success = self.upload_to_nightscout(sg_data, 'entries.json') if sg_data else True
        
        # Procesar y subir bolos
        bolus_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'INSULIN' and 'dataValues' in marker['data'] and 'deliveredFastAmount' in marker['data']['dataValues']:
                bolus_data.append({
                    'insulin': marker['data']['dataValues']['deliveredFastAmount'],
                    'created_at': datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').astimezone(tz=pytz.UTC).isoformat(),
                    'eventType': 'Bolus'
                })
        bolus_upload_success = self.upload_to_nightscout(bolus_data, 'treatments.json') if bolus_data else True

        # Procesar y subir carbohidratos
        carb_data = []
        for marker in data['patientData']['markers']:
            if marker.get('type') == 'MEAL' and 'dataValues' in marker['data'] and 'amount' in marker['data']['dataValues']:
                carb_data.append({
                    'eventType': 'Meal Bolus',
                    'carbs': marker['data']['dataValues']['amount'],
                    'created_at': datetime.strptime(marker['timestamp'], '%Y-%m-%dT%H:%M:%S').astimezone(tz=pytz.UTC).isoformat(),
                    'enteredBy': 'carelink',
                    'notes': 'Comida'
                })
        carb_upload_success = self.upload_to_nightscout(carb_data, 'treatments.json') if carb_data else True

        # Procesar y subir calibraciones
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

        # Registrar el archivo procesado en el log
        logging.info(f"Archivo procesado: {latest_file}")

        # Eliminar el archivo del disco después de procesarlo correctamente
        if sg_upload_success and bolus_upload_success and carb_upload_success and calibration_upload_success:
            os.remove(os.path.join(self.directory, latest_file))
            logging.info(f"Archivo eliminado: {latest_file}")
        else:
            logging.error(f"Error en la subida de datos. El archivo {latest_file} no se eliminará.")

if __name__ == '__main__':
    uploader = NightscoutUploader(directory='.')
    uploader.process_and_upload_data()