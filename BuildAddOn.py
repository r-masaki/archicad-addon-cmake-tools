import argparse
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile


def ParseArguments ():
    parser = argparse.ArgumentParser ()
    parser.add_argument ('--init', required = False, action='store_true', help = 'Initialize project files')
    parser.add_argument ('--release', required = False, action='store_true', help = 'Build add-on with Release mode')
    parser.add_argument ('--notarize', required = False, action='store_true', help = 'Build add-on with Release mode and notarization for only macOSX')
    parser.add_argument ('-c', '--configFile', dest = 'configFile', required = True, help = 'JSON Configuration file')
    parser.add_argument ('-v', '--acVersion', dest = 'acVersion', nargs = '+', type = str, required = False, help = 'Archicad version number list. Ex: 26 27')
    parser.add_argument ('-l', '--allLocalizedVersions', dest = 'allLocalizedVersions', required = False, action='store_true', help = 'Create localized release builds for all configured languages.' )
    parser.add_argument ('-d', '--devKitPath', dest = 'devKitPath', type = str, required = False, help = 'Path to local APIDevKit')
    parser.add_argument ('-b', '--buildNum', dest = 'buildNum', type = str, required = False, help = 'Build number of local APIDevKit')
    parser.add_argument ('-p', '--package', dest = 'package', required = False, action='store_true', help = 'Create zip archive.')
    parser.add_argument ('-a', '--additionalCMakeParams', dest = 'additionalCMakeParams', nargs = '+', required = False, help = 'Add-On specific CMake parameter list of key=value pairs. Ex: var1=value1 var2="value 2"')
    args = parser.parse_args ()

    if args.devKitPath is not None:
        if args.acVersion is None or args.buildNum is None:
            raise Exception ('Must provide Archicad version and APIDevKit build number with local APIDevKit option!')
        if len (args.acVersion) != 1:
            raise Exception ('Only one Archicad version supported with local APIDevKit option!')
    
    return args


def PrepareParameters (args):

    genIDEFlag = args.init
    releaseFlag = args.release
    notarizeFlag = args.notarize
    
    # Check platform operating system
    platformName = None
    if platform.system () == 'Windows':
        platformName = 'WIN'
    elif platform.system () == 'Darwin':
        platformName = 'MAC'

    # Load DevKit download data
    devKitDataPath = pathlib.Path (__file__).absolute ().parent / 'APIDevKitLinks.json'
    with open (devKitDataPath, 'r') as devKitDataFile:
        devKitData = json.load (devKitDataFile)

    # Load config data
    configPath = pathlib.Path (args.configFile)
    if configPath.is_dir ():
        raise Exception (f'{configPath} is a directory!')
    with open (configPath, 'r') as configFile:
        configData = json.load (configFile)

    addOnName = configData['addOnName']
    acVersionList = None

    if args.acVersion:
        acVersionList = args.acVersion
    else:
        acVersionList = devKitData[platformName].keys ()

    # Get needed language codes
    languageList = [configData['defaultLanguage'].upper ()]
    if args.allLocalizedVersions:
        languageList = [lang.upper () for lang in configData['languages']]
                
    # Get additional CMake parameters
    additionalParams = None
    if 'additionalCMakeParams' in configData or args.additionalCMakeParams:
        additionalParams = {}

        if 'additionalCMakeParams' in configData:
            additionalParams = configData['additionalCMakeParams']

        if args.additionalCMakeParams:
            for param in args.additionalCMakeParams:
                if '=' not in param:
                    additionalParams[param] = "ON"
                else:
                    key, value = param.split ('=', 1)
                    if not value:
                        raise Exception (f'Value not provided for {key}!')
                    additionalParams[key] = value

    useBuiltinFlag = configData.get('useBuiltinLibrary', False)
                
    return [devKitData, platformName, addOnName, acVersionList, languageList, additionalParams, useBuiltinFlag, genIDEFlag, releaseFlag, notarizeFlag]


def PrepareDirectories (args, devKitData, platformName, addOnName, acVersionList):
    # Create directory for Build and Package
    workspaceRootFolder = pathlib.Path (__file__).parent.absolute ().parent.absolute ()
    buildFolder = workspaceRootFolder / 'Build'
    packageRootFolder = buildFolder / 'Package' / addOnName
    devKitFolderList = {}

    if not buildFolder.exists ():
        buildFolder.mkdir (parents=True)

    if args.package:
        if (packageRootFolder).exists ():
            shutil.rmtree (packageRootFolder)

    # Set APIDevKit directory if local is used, else create new directories
    if args.devKitPath is not None:
        devKitPath = pathlib.Path (args.devKitPath)
        if not devKitPath.is_dir ():
            raise Exception (f'{devKitPath} is not a directory!')
        devKitFolderList[acVersionList[0]] = devKitPath
    else:
        print (f'{devKitPath} should be set!')
        sys.exit(1)

        # For every ACVersion
        # Check if APIDevKitLink is provided
        # Create directory for APIDevKit
        # Download APIDevKit
        # for version in acVersionList:
        #     if version in devKitData[platformName]:

        #         devKitFolder = buildFolder / 'DevKit' / f'APIDevKit-{version}'
        #         if not devKitFolder.exists ():
        #             devKitFolder.mkdir (parents=True)

        #         devKitFolderList[version] = devKitFolder
        #         DownloadAndUnzip (devKitData[platformName][version], devKitFolder)

        #     else:
        #         raise Exception ('APIDevKit download link not provided!')
            
    return [workspaceRootFolder, buildFolder, packageRootFolder, devKitFolderList]


def DownloadAndUnzip (url, dest):
    fileName = url.split ('/')[-1]
    filePath = pathlib.Path (dest, fileName)
    if filePath.exists ():
        return

    print (f'Downloading {fileName}')
    urllib.request.urlretrieve (url, filePath)

    print (f'Unzipping {fileName}')
    if platform.system () == 'Windows':
        with zipfile.ZipFile (filePath, 'r') as zip:
            zip.extractall (dest)
    elif platform.system () == 'Darwin':
        subprocess.call ([
            'unzip', '-qq', filePath,
            '-d', dest
        ])


def GetInstalledVisualStudioGenerator ():
    vsWherePath = pathlib.Path (os.environ["ProgramFiles(x86)"]) / 'Microsoft Visual Studio' / 'Installer' / 'vswhere.exe'
    if not vsWherePath.exists ():
        raise Exception ('Microsoft Visual Studio Installer not found!')
    vsWhereOutputStr = subprocess.check_output ([vsWherePath, '-sort', '-format', 'json', '-utf8'])
    vsWhereOutput = json.loads (vsWhereOutputStr)
    if len (vsWhereOutput) == 0:
        raise Exception ('No installed Visual Studio detected!')
    vsVersion = vsWhereOutput[0]['installationVersion'].split ('.')[0]
    if vsVersion == '17':
        return 'Visual Studio 17 2022'
    elif vsVersion == '16':
        return 'Visual Studio 16 2019'
    else:
        raise Exception ('Installed Visual Studio version not supported!')
    

def GetToolset (version):
    if version < 25:
        return 'v141'
    if version < 29:
        return 'v142'
    return 'v143'

def GetProjectGenerationParams (workspaceRootFolder, buildPath, addOnName, platformName, devKitFolder, version, languageCode, additionalParams):
    # Add params to configure cmake
    projGenParams = [
        'cmake',
        '-B', str (buildPath)
    ]

    if platformName == 'WIN':
        vsGenerator = GetInstalledVisualStudioGenerator ()
        projGenParams.append (f'-G {vsGenerator}')
        toolset = GetToolset (int (version))
        projGenParams.append (f'-T {toolset}')
    elif platformName == 'MAC':
        projGenParams.extend (['-G', 'Xcode'])

    projGenParams.append (f'-DAC_VERSION={version}')
    projGenParams.append (f'-DAC_ADDON_NAME={addOnName}')
    projGenParams.append (f'-DAC_API_DEVKIT_DIR={str (devKitFolder / "Support")}')
    projGenParams.append (f'-DAC_ADDON_LANGUAGE={languageCode}')

    if additionalParams and 'ADDITIONAL_INCLUDE_DIRS' in additionalParams and additionalParams['ADDITIONAL_INCLUDE_DIRS']:
        additionalIncludeDirList = [str(pathlib.Path(dir)) for dir in additionalParams['ADDITIONAL_INCLUDE_DIRS']]
        cmakeIncludeDirList = " ".join(additionalIncludeDirList);
        print ({cmakeIncludeDirList})
        projGenParams.append(f'-DADDITIONAL_INCLUDE_DIRS={cmakeIncludeDirList}')
    else:
        projGenParams.append(f'-DADDITIONAL_INCLUDE_DIRS=""')

    # if additionalParams is not None:
    #     for key in additionalParams:
    #         projGenParams.append (f'-D{key}={additionalParams[key]}')

    projGenParams.append (str (workspaceRootFolder))

    return projGenParams


def RunShellScript(script_path, bundle_path):
    try:
        # スクリプトと引数を結合して実行するコマンドを作成
        cmd = [script_path, bundle_path]
        
        # シェルスクリプトを実行
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_path}: {e}")
        sys.exit(1)


def BuildAddOn (addOnName, platformName, additionalParams, workspaceRootFolder, buildFolder, devKitFolder, version, configuration, languageCode, genIDEFlag, releaseFlag, notarizeFlag):
    buildPath = buildFolder / addOnName / version / languageCode

    # Add params to configure cmake
    if genIDEFlag:
        projGenParams = GetProjectGenerationParams (workspaceRootFolder, buildPath, addOnName, platformName, devKitFolder, version, languageCode, additionalParams)
        projGenResult = subprocess.call (projGenParams)
        if projGenResult != 0:
            raise Exception ('Failed to generate project!')

    # Add params to build AddOn
    if releaseFlag:
        if not os.path.exists(buildPath):
            raise Exception ('Failed: Project file does not exit!')

        # Clear build folder before building (Xcode: clean)
        if buildPath.exists():
            # For Xcode, use 'xcodebuild clean' to clear the build folder
            if platformName == 'MAC':
                xcodeproj_path = buildPath / f"{addOnName}.xcodeproj"
                if xcodeproj_path.exists():
                    subprocess.run([
                    'xcodebuild',
                    '-project', str(xcodeproj_path),
                    '-configuration', configuration,
                    'clean'
                    ], check=True)
                    
        buildParams = [
            'cmake',
            '--build', str (buildPath),
            '--config', configuration,
            '--clean-first'
        ]
        
        buildResult = subprocess.call (buildParams)
        if buildResult != 0:
            raise Exception ('Failed to build project!')

        # Open build folder
        if platformName == 'WIN':
            bundlePath = buildPath / configuration
            subprocess.run(['explorer', bundlePath])

        if notarizeFlag and platformName == 'MAC':
            # run notarize script
            print('start notarization')
            shPath = pathlib.Path (__file__).parent.absolute () / 'OSX' / 'Notarize.sh'
            extension = 'bundle'
            bundleFile = addOnName + "." + extension
            bundlePath = buildPath / configuration / bundleFile
            RunShellScript(shPath, bundlePath)



def BuildAddOns (args, addOnName, platformName, languageList, additionalParams, workspaceRootFolder, buildFolder, devKitFolderList, genIDEFlag, releaseFlag, notarizeFlag):
    # At this point, devKitFolderList dictionary has all provided ACVersions as keys
    # For every ACVersion
    # If release, build Add-On for all languages with RelWithDebInfo configuration
    # Else build Add-On with Debug and RelWithDebInfo configurations, without language specified   
    # In each case, if package creation is enabled, copy the .apx/.bundle files to the Package directory
    try:
        for version in devKitFolderList:
            devKitFolder = devKitFolderList[version]

            for languageCode in languageList:                  
                BuildAddOn (addOnName, platformName, additionalParams, workspaceRootFolder, buildFolder, devKitFolder, version, 'Release', languageCode, genIDEFlag, releaseFlag, notarizeFlag)
                # BuildAddOn (addOnName, platformName, additionalParams, workspaceRootFolder, buildFolder, devKitFolder, version, 'RelWithDebInfo', languageCode)
                # if args.package is False:
                #     BuildAddOn (addOnName, platformName, additionalParams, workspaceRootFolder, buildFolder, devKitFolder, version, 'Debug', languageCode)


    except Exception as e:
        raise e


def Check7ZInstallation ():
    try:
        subprocess.call ('7z', stdout=subprocess.DEVNULL)
    except:
        raise Exception ('7Zip not installed!')


def CopyResultToPackage (packageRootFolder, buildFolder, version, addOnName, platformName, configuration, languageCode):
    packageFolder = packageRootFolder / version / languageCode
    sourceFolder = buildFolder / addOnName / version / languageCode / configuration

    if not packageFolder.exists ():
        packageFolder.mkdir (parents=True)

    if platformName == 'WIN':
        shutil.copy (
            sourceFolder / f'{addOnName}.apx',
            packageFolder / f'{addOnName}.apx',
        )
        shutil.copy (
            sourceFolder / f'{addOnName}.pdb',
            packageFolder / f'{addOnName}.pdb',
        )

    elif platformName == 'MAC':
        subprocess.call ([
            'cp', '-R',
            sourceFolder / f'{addOnName}.bundle',
            packageFolder / f'{addOnName}.bundle'
        ])


def GetDevKitVersion (args, devKitData, version, platformName):
    if args.devKitPath:
        buildNum = f'{version}.{args.buildNum}'
    else:
        url = devKitData[platformName][version]
        buildNum = url.split ('/')[-2]
    
    return buildNum


# Zip packages
def PackageAddOns (args, devKitData, addOnName, platformName, acVersionList, languageList, buildFolder, packageRootFolder):
    Check7ZInstallation ()

    for version in acVersionList:
        for languageCode in languageList:
            CopyResultToPackage (packageRootFolder, buildFolder, version, addOnName, platformName, 'RelWithDebInfo', languageCode)
    
            versionAndBuildNum = GetDevKitVersion (args, devKitData, version, platformName)
            subprocess.call ([
                '7z', 'a',
                str (packageRootFolder.parent / version / f'{addOnName}-{versionAndBuildNum}_{platformName}_{languageCode}.zip'),
                str (packageRootFolder / version / languageCode / '*')
            ])


def Main ():
    try:
        args = ParseArguments ()

        [devKitData, platformName, addOnName, acVersionList, languageList, additionalParams, useBuiltinFlag, genIDEFlag, releaseFlag, notarizeFlag] = PrepareParameters (args)

        [workspaceRootFolder, buildFolder, packageRootFolder, devKitFolderList] = PrepareDirectories (args, devKitData, platformName, addOnName, acVersionList)

        os.chdir (workspaceRootFolder)
        
        BuildAddOns (args, addOnName, platformName, languageList, additionalParams, workspaceRootFolder, buildFolder, devKitFolderList, genIDEFlag, releaseFlag, notarizeFlag)

        # Add empty config file
        if genIDEFlag and useBuiltinFlag:
            libConfig = {
                "LPXML_Converter_Path": ""
            }

            filePath = workspaceRootFolder / 'aclibconfig.json'
            with open(filePath, "w") as f:
                json.dump(libConfig, f, indent=4)

        if args.package:
            PackageAddOns (args, devKitData, addOnName, platformName, acVersionList, languageList, buildFolder, packageRootFolder)

        print ('Build succeeded!')
        sys.exit (0)
    
    except Exception as e:
        print (e)
        sys.exit (1)

if __name__ == "__main__":
    Main ()
