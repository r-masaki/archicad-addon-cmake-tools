import argparse
import json
import pathlib
import plistlib


def ParseArguments ():
    parser = argparse.ArgumentParser (description = 'Generate .vscode/tasks.json and launch.json for building and debugging the add-on with Archicad.')
    parser.add_argument ('appPath', type = str, help = 'Path to the Archicad.app bundle (e.g. "/Applications/GRAPHISOFT/Archicad 29/Archicad 29.app")')
    parser.add_argument ('-b', '--buildConfig', dest = 'buildConfig', type = str, default = 'Debug', help = 'Build configuration to use (default: Debug)')
    return parser.parse_args ()


def GetArchicadExecutablePath (appPath):
    appPath = pathlib.Path (appPath)
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
                'command': 'python3',
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


def WriteLaunchJson (vscodeFolder, executablePath, taskLabel, launchName):
    launchJson = {
        'version': '0.2.0',
        'configurations': [
            {
                'name': launchName,
                'type': 'lldb',
                'request': 'launch',
                'program': str (executablePath),
                'args': [],
                'cwd': '${workspaceFolder}',
                'preLaunchTask': taskLabel
            }
        ]
    }

    with open (vscodeFolder / 'launch.json', 'w') as launchFile:
        json.dump (launchJson, launchFile, indent = 4, ensure_ascii = False)
        launchFile.write ('\n')


def main ():
    args = ParseArguments ()

    executablePath = GetArchicadExecutablePath (args.appPath)

    workspaceRoot = pathlib.Path (__file__).absolute ().parent.parent
    vscodeFolder = workspaceRoot / '.vscode'
    vscodeFolder.mkdir (parents = True, exist_ok = True)

    taskLabel = f'Build SiteManager Add-On ({args.buildConfig})'
    launchName = f'Debug {pathlib.Path (args.appPath).stem} (lldb)'

    WriteTasksJson (vscodeFolder, args.buildConfig, taskLabel)
    WriteLaunchJson (vscodeFolder, executablePath, taskLabel, launchName)

    print (f'Generated {vscodeFolder / "tasks.json"}')
    print (f'Generated {vscodeFolder / "launch.json"}')


if __name__ == '__main__':
    main ()
