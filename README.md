# Archicad Add-On CMake Tools

This repository contains the tools needed for Archicad Add-On compilation. The recommended way to use these tools is to add this code as a submodule to your own repository. See [archicad-addon-cmake](https://github.com/GRAPHISOFT/archicad-addon-cmake) for a usage example.

## APIDevKitLinks.json

There is a configuration file that consists of an object containing key-value pairs, in which the keys are Archicad version numbers, and their respective values are the direct download URLs to the public API Development Kit releases.

## Build script

The repo includes a BuildAddOn.py python script, that handles the building of the Add-Ons. This script takes up to 7 arguments:
- --init: re-generate IDE project
- --release: build addon with release mode
- -c, --configFile (mandatory): path to the JSON configuration file.
- -v, --acVersion (optional, but mandatory if --devKitPath is used): a list of Archicad version numbers, that the Add-On is built for. These versions must be present in the object keys of the APIDevKitLinks file. When not specified, the script takes all versions specified in the APIDevKitLinks file.
- -l, --allLocalizedVersions (optional): Toggles creating localized builds for all languages listed in the language object of the JSON configuration file. If not enabled, the configured defaultLanguage will be used.
- -d, --devKitPath (optional): path to a single local APIDevKit folder. When this argument is used, only one Archicad version should be provided in the --acVersion list.
- -b, --buildNum (optional, but mandatory if --devKitPath is used): Build number of the used local APIDevKit. Ex: -b 3001.
- -p, --package (optional): toggles creating zip archive with the built Add-On files.
- -a, --additionalCMakeParams (optional): a list of additional addon-specific CMake parameters as keys or key=value pairs. The build script will forward it to CMake. Ex: -a var1=value1 var2="value 2" var3.

## Library Part Conversion
1. Create an 'ACLib' folder in the 'R{Language}}'. (RINT, RJPN, etc)
2. Use the BuildAddOn.py script to build a project; this will automatically generate the 'aclibconfig.json' file.
3. Specify the path to your LP_XMLConverter in the JSON file.
4. Inside the ACLib folder, create a 'Src' subfolder and add all library part sources in HSF format to this folder.
5. Build your project (the MakeACLib.py script will execute, converting .hsf files to .gsm before running CompileResource.py).
6. RevertACLib.py reverts (convert gsm to hsf), if needed during your development.