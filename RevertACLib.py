import subprocess
import os
import sys
import pathlib
import json
import argparse


def run_application(converterPath, srcPath, destPath):

    try:
        subprocess.call([
            converterPath,
            "l2hsf",
            srcPath,
            destPath
        ])

        print("RevertLib Successed")

    except Exception as e:
        print("RevertLib Failed:", e)


def Main (argv):

    # check language code
    parser = argparse.ArgumentParser (description = 'Archicad Add-On Resource Compiler.')
    parser.add_argument ('languageCode', help = 'Language code of the Add-On.')

    args = parser.parse_args ()
    languageCode = args.languageCode

    current_file_path = pathlib.Path (__file__).parent.absolute ().parent.absolute()

    # check config file
    configPath = current_file_path / 'aclibconfig.json'
    if configPath.exists():
        with open (configPath, 'r') as configFile:
            configData = json.load (configFile)
    else:
        print("Skip MakeLib: aclibconfig.json not found at the specified path.")
        sys.exit()


    # check source folder
    resource_folder_name = "R" + languageCode
    aclib_folder_name = "ACLib"
    target_folder_path = current_file_path / resource_folder_name / aclib_folder_name

    if os.path.exists(target_folder_path):
        try:
            converterPath =  pathlib.Path (configData['LPXML_Converter_Path'])
            if not os.path.exists(converterPath):
                print("Not found converter. Please set proper path to LP_XMLConverter")
                sys.exit(1)
            
            src_folder_name = target_folder_path / 'Bin'
            dest_folder_name = target_folder_path /'Rev'

            srcPath = pathlib.Path (src_folder_name)
            destPath = pathlib.Path (dest_folder_name)

            run_application(converterPath, srcPath, destPath)

        except Exception as e:
                print (e)
                sys.exit (1)

    else:
        print ("Error RevertLib")
        sys.exit()

if __name__ == "__main__":
    Main (sys.argv)
