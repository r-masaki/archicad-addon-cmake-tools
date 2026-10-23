import argparse
import json
import pathlib
import platform
import plistlib
import xml.etree.ElementTree as ET


def ParseArguments ():
    parser = argparse.ArgumentParser (description = 'Generate .vscode/tasks.json and launch.json for building and debugging the add-on with Archicad.')
    parser.add_argument ('appPath', type = str, help = 'Path to the Archicad.app bundle on macOS or Archicad.exe on Windows')
    parser.add_argument ('-b', '--buildConfig', dest = 'buildConfig', type = str, default = 'Debug', help = 'Build configuration to use (default: Debug)')
    parser.add_argument ('-v', '--visualizers', '--lldbVisualizersPath', dest = 'visualizersPath', type = str, help = 'Path to LLDB_Visualizers.py on macOS or a directory of .natvis files on Windows')
    return parser.parse_args ()


def GetArchicadExecutablePath (appPath):
    appPath = pathlib.Path (appPath)

    if appPath.suffix.lower () == '.exe':
        if not appPath.is_file ():
            raise Exception (f'Archicad executable not found at {appPath}')
        return appPath

    if appPath.suffix != '.app':
        raise Exception (f'{appPath} is not an .app bundle!')

    infoPlistPath = appPath / 'Contents' / 'Info.plist'
    if not infoPlistPath.exists ():
        raise Exception (f'Info.plist not found at {infoPlistPath}')

    with open (infoPlistPath, 'rb') as infoPlistFile:
        infoPlist = plistlib.load (infoPlistFile)

    executableName = infoPlist.get ('CFBundleExecutable')
    if not executableName:
        raise Exception (f'CFBundleExecutable not found in {infoPlistPath}')

    executablePath = appPath / 'Contents' / 'MacOS' / executableName
    if not executablePath.exists ():
        raise Exception (f'Archicad executable not found at {executablePath}')

    return executablePath


def WriteTasksJson (vscodeFolder, buildConfig, taskLabel):
    tasksJson = {
        'version': '2.0.0',
        'tasks': [
            {
                'label': taskLabel,
                'type': 'shell',
                'command': 'python' if platform.system () == 'Windows' else 'python3',
                'args': ['Tools/BuildAddOn.py', '-c', 'config.json', '-d', '../../', '-b', buildConfig],
                'options': {'cwd': '${workspaceFolder}'},
                'group': {'kind': 'build', 'isDefault': True},
                'problemMatcher': []
            }
        ]
    }

    with open (vscodeFolder / 'tasks.json', 'w') as tasksFile:
        json.dump (tasksJson, tasksFile, indent = 4, ensure_ascii = False)
        tasksFile.write ('\n')


def CombineNatvisFiles (visualizersDirectory, outputFile):
    visualizersDirectory = pathlib.Path (visualizersDirectory)
    if not visualizersDirectory.is_dir ():
        raise Exception (f'Natvis directory not found at {visualizersDirectory}')

    natvisFiles = sorted (visualizersDirectory.rglob ('*.natvis'))
    if not natvisFiles:
        raise Exception (f'No .natvis files found in {visualizersDirectory}')

    combinedRoot = None
    for natvisFile in natvisFiles:
        root = ET.parse (natvisFile).getroot ()
        if root.tag.split ('}')[-1] != 'AutoVisualizer':
            raise Exception (f'{natvisFile} does not have an AutoVisualizer root element')

        if combinedRoot is None:
            combinedRoot = ET.Element (root.tag, root.attrib)
        elif root.tag != combinedRoot.tag:
            raise Exception (f'{natvisFile} uses a different AutoVisualizer XML namespace')

        combinedRoot.extend (root)

    outputFile.parent.mkdir (parents = True, exist_ok = True)
    ET.ElementTree (combinedRoot).write (outputFile, encoding = 'utf-8', xml_declaration = True)
    return outputFile


def WriteLaunchJson (vscodeFolder, executablePath, taskLabel, launchName, debuggerType, workingDirectory, visualizersPath = None):
    launchJson = {
        'version': '0.2.0',
        'configurations': [
            {
                'name': launchName,
                'type': debuggerType,
                'request': 'launch',
                'program': str (executablePath),
                'args': [],
                'cwd': str (workingDirectory),
                'preLaunchTask': taskLabel
            }
        ]
    }

    if visualizersPath and debuggerType == 'lldb':
        launchJson['configurations'][0]['initCommands'] = [
            f'command script import "{pathlib.Path (visualizersPath)}"'
        ]
    elif visualizersPath and debuggerType == 'cppvsdbg':
        natvisFile = CombineNatvisFiles (visualizersPath, vscodeFolder / 'combined.natvis')
        launchJson['configurations'][0]['visualizerFile'] = str (natvisFile)
        launchJson['configurations'][0]['showDisplayString'] = True

    with open (vscodeFolder / 'launch.json', 'w') as launchFile:
        json.dump (launchJson, launchFile, indent = 4, ensure_ascii = False)
        launchFile.write ('\n')


def main ():
    args = ParseArguments ()

    executablePath = GetArchicadExecutablePath (args.appPath)

    workspaceRoot = pathlib.Path (__file__).absolute ().parent.parent
    with open (workspaceRoot / 'config.json', 'r') as configFile:
        config = json.load (configFile)

    vscodeFolder = workspaceRoot / '.vscode'
    vscodeFolder.mkdir (parents = True, exist_ok = True)

    taskLabel = f'Build {config["addOnName"]} Add-On ({args.buildConfig})'
    isWindowsExecutable = executablePath.suffix.lower () == '.exe'
    debuggerType = 'cppvsdbg' if isWindowsExecutable else 'lldb'
    launchName = f'Debug {pathlib.Path (args.appPath).stem} ({debuggerType})'
    workingDirectory = executablePath.parent if isWindowsExecutable else '${workspaceFolder}'

    WriteTasksJson (vscodeFolder, args.buildConfig, taskLabel)
    WriteLaunchJson (vscodeFolder, executablePath, taskLabel, launchName, debuggerType, workingDirectory, args.visualizersPath)

    print (f'Generated {vscodeFolder / "tasks.json"}')
    print (f'Generated {vscodeFolder / "launch.json"}')


if __name__ == '__main__':
    main ()
