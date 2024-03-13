import subprocess
import os
import sys
import pathlib
import json

def run_application(converterPath, srcPath, destPath):

    try:
        subprocess.call([
            converterPath,
            "hsf2l",
            srcPath,
            destPath
        ])

        print("MakeLib Successed")

    except Exception as e:
        print("MakeLib Failed:", e)


def Main ():

    current_file_path = pathlib.Path (__file__).parent.absolute ().parent.absolute()
    aclib_folder_name = "ACLib"
    target_folder_path = current_file_path / aclib_folder_name

    if os.path.exists(target_folder_path):
        try:
            configFile = target_folder_path / 'aclibconfig.json'

            # Load config data
            configPath = pathlib.Path (configFile)
            if configPath.is_dir ():
                raise Exception (f'{configPath} is a directory!')
            with open (configPath, 'r') as configFile:
                configData = json.load (configFile)

            converterPath =  pathlib.Path (configData['LPXML_Converter_Path'])

            if not os.path.exists(converterPath):
                print("Not found converter. Please set proper path to LP_XMLConverter")
                sys.exit(1)
            
            src_folder_name = target_folder_path / 'Src'
            dest_folder_name = current_file_path / 'RFIX'/'Images'
            srcPath = pathlib.Path (src_folder_name)
            destPath = pathlib.Path (dest_folder_name)

            run_application(converterPath, srcPath, destPath)

        except Exception as e:
                print (e)
                sys.exit (1)

    else:
        print ("Skip MakeLib: Not found ACLib folder")
        sys.exit()

if __name__ == "__main__":
    Main ()
