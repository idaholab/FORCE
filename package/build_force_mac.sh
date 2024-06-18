# Create a new disk image
hdiutil create -size 3g -fs HFS+ -volname "FORCE" -o force_build.dmg

# Mount the new disk image
hdiutil attach force_build.dmg -mountpoint /Volumes/FORCE

# Mount the existing .dmg files
hdiutil attach Workbench-5.4.1.dmg -mountpoint /Volumes/Workbench

# Copy the contents of the force_install directory and the Workbench .dmg file to the new disk image.
mkdir -p FORCE.app/Contents/MacOS
mkdir -p FORCE.app/Contents/Resources
# TODO: move icons to Resources?
cp -R force_install/* FORCE.app/Contents/MacOS/
cp -R force_install/* /Volumes/FORCE/
cp -R /Volumes/Workbench/* /Volumes/FORCE/

# Create the info.plist file with app metadata
# TODO: Which app do we point to?
cat <<EOF > FORCE.app/Contents/Info.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>FORCE</string>
    <key>CFBundleDisplayName</key>
    <string>FORCE</string>
    <key>CFBundleIdentifier</key>
    <string></string>
    <key>CFBundleVersion</key>
    <string>0.1</string>
    <key>CFBundleExecutable</key>
    <string>my_script.sh</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

# Unmount all the disk images
hdiutil detach /Volumes/Workbench
hdiutil detach /Volumes/FORCE

# Convert to read-only compressed image
hdiutil convert force_build.dmg -format UDZO -o FORCE.dmg

# Remove the temporary disk image
rm force_build.dmg
