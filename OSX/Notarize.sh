#! /bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path>"
    exit 1
fi

bundlePath=$1
bundleName=$(basename "$bundlePath")
directory=$(dirname "$bundlePath")

if [ ! -e "$bundlePath" ]; then
    echo "Error: Bundle Path '$bundlePath' does not exist."
    exit 1
fi

echo "Running script for Release configuration"
echo "Notarizing: ${bundlePath}"
echo "Compressing bundle…: ${bundlePath}"
/usr/bin/ditto -c -k --keepParent "$bundlePath" "${bundleName}.zip"

#notarize:
echo "Submitting compressed bundle for notarization…"
xcrun notarytool submit "${bundleName}.zip" --keychain-profile "GSJAddon" --wait

if [ $? -eq 0 ]; then
    echo "notarytool successfully submitted the file."

    # copy apx to project folder
    destination="${directory}/notarized"
    if [ -d "$destination" ]; then
        rm -r -f "$destination"
    fi

    mkdir -p "$destination"
    cp -r "$bundlePath" "$destination"

    open "$destination"

else
    echo "notarytool encountered an error."
fi

rm -r "${bundleName}.zip"

exit 0