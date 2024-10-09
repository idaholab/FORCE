#!/bin/bash

# Set up the FORCE application bundle
# We'll set up the app so that some FORCE launcher script is the main executable, and the RAVEN,
# HERON, and TEAL executables are in the Resources directory.
# Build the initial app from the force_launcher.scpt AppleScript
osacompile -o FORCE.app force_launcher.scpt
# Now copy over the force_install directory contents to the application's Resources directory
cp -Rp force_install/* FORCE.app/Contents/Resources/
# Overwrite the app's icon with the FORCE icon
cp icons/FORCE.icns FORCE.app/Contents/Resources/applet.icns

# Create a new disk image
hdiutil create -size 5g -fs HFS+ -volname "FORCE" -o force_build.dmg

# Mount the new disk image
hdiutil attach force_build.dmg -mountpoint /Volumes/FORCE

# Mount the existing .dmg file file Workbench
hdiutil attach Workbench-5.4.1.dmg -mountpoint /Volumes/Workbench

# Add the workshop tests and data directories to FORCE so that Workbench's autocomplete works for workshop examples
mkdir FORCE.app/Contents/Resources/tests
mkdir FORCE.app/Contents/Resources/examples
cp -Rp examples/workshop FORCE.app/Contents/Resources/tests/
cp -Rp examples/data FORCE.app/Contents/Resources/examples/

# Move the FORCE app to the disk image
cp -Rp FORCE.app /Volumes/FORCE/
cp -Rp /Volumes/Workbench/Workbench-5.4.1.app /Volumes/FORCE/

# Move the "examples" and "docs" directories from the FORCE app bundle to the top level of the disk
# image to make them more accessible.
cp -Rp examples /Volumes/FORCE/
cp -Rp docs /Volumes/FORCE/

# Move the "examples" and "docs" directories from the FORCE app bundle to the top level of the disk
# image to make them more accessible.
if [ -d FORCE.app/Contents/Resources/examples ]; then
    mv /Volumes/FORCE/FORCE.app/Contents/Resources/examples /Volumes/FORCE/
else
    echo "WARNING: No examples directory found in FORCE.app bundle"
fi
if [ -d FORCE.app/Contents/Resources/docs ]; then
    mv FORCE.app/Contents/Resources/docs /Volumes/FORCE/
else
    echo "WARNING: No docs directory found in FORCE.app bundle"
fi

# Add .son file to Workbench app to provide a default HERON configuration
cp default.apps.son /Volumes/FORCE/Workbench-5.4.1.app/Contents/

# Create a symlink to the Applications directory in the app's build directory
ln -s /Applications /Volumes/FORCE/Applications

# Unmount all the disk images
hdiutil detach /Volumes/Workbench
hdiutil detach /Volumes/FORCE

# Convert to read-only compressed image
if [ -f FORCE.dmg ]; then
    rm FORCE.dmg
fi
hdiutil convert force_build.dmg -format UDZO -o FORCE.dmg

# Remove the temporary disk image
rm force_build.dmg
