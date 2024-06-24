# Freeze the FORCE app using cx_Freeze. We require a suitable python environment to be active.
# set -e
# python setup.py install_exe --install-dir force_install

# Set up the FORCE application bundle
# We'll set up the app so that some FORCE launcher script is the main executable, and the RAVEN,
# HERON, and TEAL executables are in the Resources directory.
# Build the initial app from the force_launcher.scpt AppleScript
osacompile -o FORCE.app force_launcher.scpt
# Now copy over the force_install directory contents to the application's Resources directory
cp -R force_install/* FORCE.app/Contents/Resources/
# Overwrite the app's icon with the FORCE icon
cp FORCE.icns FORCE.app/Contents/Resources/applet.icns

# Create a new disk image
hdiutil create -size 3g -fs HFS+ -volname "FORCE" -o force_build.dmg

# Mount the new disk image
hdiutil attach force_build.dmg -mountpoint /Volumes/FORCE

# Mount the existing .dmg file file Workbench
# hdiutil attach Workbench-5.4.1.dmg -mountpoint /Volumes/Workbench

# Move the FORCE app to the disk image
cp -R FORCE.app /Volumes/FORCE/
# cp -R /Volumes/Workbench/* /Volumes/FORCE/

# Unmount all the disk images
# hdiutil detach /Volumes/Workbench
hdiutil detach /Volumes/FORCE

# Convert to read-only compressed image
hdiutil convert force_build.dmg -format UDZO -o FORCE.dmg

# Remove the temporary disk image
rm force_build.dmg
