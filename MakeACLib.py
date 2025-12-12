import subprocess
import os
import sys
import pathlib
import json
import argparse
import shutil


exclude_extensions = ['.tif', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

def run_application(converterPath, srcPath, destPath):

    try:
        result = subprocess.run([
            str(converterPath),
            "hsf2l",
            str(srcPath),
            str(destPath)
        ])

        if result.returncode == 0:
            print("MakeLib Succeeded")
            return True
        else:
            print(f"MakeLib Failed: converter returned non-zero exit status {result.returncode}")
            return False

    except Exception as e:
        print("MakeLib Failed:", e)
        return False



def copy_folder_contents(src_folder, dest_folder):
    for item in os.listdir(src_folder):
        src_item = os.path.join(src_folder, item)
        dest_item = os.path.join(dest_folder, item)

        if os.path.isdir(src_item):
            copy_folder_contents(src_item, dest_folder)
        else:
            file_extension = os.path.splitext(src_item)[1]
            if file_extension not in exclude_extensions:
                shutil.copy2(src_item, dest_item)

    # shutil.copytree(destPath, imagePath, dirs_exist_ok=True)

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
            converterPath = pathlib.Path (configData['LPXML_Converter_Path'])

            if sys.platform == "darwin" and converterPath.suffix == ".app":
                bin_path = converterPath / "Contents" / "MacOS" / converterPath.stem
                if bin_path.exists():
                    converterPath = bin_path
                else:
                    # 念のため MacOS フォルダ内の何か1つを候補にする
                    macos_dir = converterPath / "Contents" / "MacOS"
                    if macos_dir.exists():
                        candidates = list(macos_dir.glob("*"))
                        if len(candidates) == 1:
                            converterPath = candidates[0]
                        else:
                            print(f"Could not determine converter binary inside: {macos_dir}")
                            sys.exit(1)
                    else:
                        print(f"Invalid .app bundle, missing MacOS folder: {macos_dir}")
                        sys.exit(1)

            if not os.path.exists(converterPath):
                print("Not found LPXML_Converter. Please set proper path to LP_XMLConverter")
                sys.exit(1)
            
            src_folder_name = target_folder_path / 'Src'
            dest_folder_name = target_folder_path / 'Bin'
            srcPath = pathlib.Path (src_folder_name)
            destPath = pathlib.Path (dest_folder_name)

            ok = run_application(converterPath, srcPath, destPath)
            if not ok:
                sys.exit(1)

            # create Images folder if not exist
            images_dir = current_file_path / 'RFIX' / 'Images'
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            # copy files to Images folder
            imagePath = pathlib.Path(images_dir)
            copy_folder_contents(destPath, imagePath)

        except Exception as e:
            print (e)
            sys.exit (1)

    else:
        print ("Skip MakeLib: Not found ACLib folder")
        sys.exit()

if __name__ == "__main__":
    Main (sys.argv)
