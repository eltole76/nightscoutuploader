import os
import subprocess
import logging
from datetime import datetime
import argparse
from NightscoutUploader import NightscoutUploader  
from dotenv import load_dotenv

# Configuración del archivo de log
log_filename = 'mainprocess.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

def run_script(script, args):
    try:
        result = subprocess.run(['python', script] + args, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"Ejecutado {script} con éxito. Salida: {result.stdout}")
        else:
            logging.error(f"Error al ejecutar {script}. Código de salida: {result.returncode}. Error: {result.stderr}")
    except Exception as e:
        logging.error(f"Excepción al ejecutar {script}: {str(e)}")

def run_process_upload():
    uploader = NightscoutUploader(directory='.')
    uploader.process_and_upload_data()


def main():
    parser = argparse.ArgumentParser(description='Proceso diario para ejecutar scripts y registrar logs.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mostrar logs en la consola')
    args = parser.parse_args()

    if args.verbose:
        # Configuración del logger para la consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logging.getLogger().addHandler(console_handler)

    logging.info("Inicio del proceso diario")
    
    load_dotenv()
    #print(os.getenv('NIGHTSCOUT_URL'))
    #print(os.getenv('API_SECRET'))
    
    # Ejecutar carelink_client2_cli.py con los argumentos -d -v
    run_script('..\carelink-python-client\carelink_client2_cli.py', ['-d', '-v'])
    
    # Ejecutar upload_to_nightscout.py
    run_process_upload()

    logging.info("Fin del proceso diario")

if __name__ == '__main__':
    main()