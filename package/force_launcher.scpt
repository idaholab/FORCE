set options to {"HERON", "RAVEN", "TEAL", "Quit"}

set selectedOption to choose from list options with title "FORCE Launcher" with prompt "Which FORCE application would you like to use?" default items {"HERON"}

if selectedOption is false then
    display dialog "No option selected. Exiting..." buttons {"OK"} default button "OK"
else
    set selectedOption to item 1 of selectedOption
    if selectedOption is "HERON" then
        set filePathName to quoted form of "/Applications/FORCE.app/Contents/Resources/heron"
    else if selectedOption is "RAVEN" then
        set filePathName to quoted form of "/Applications/FORCE.app/Contents/Resources/raven_framework"
    else if selectedOption is "TEAL" then
        set filePathName to quoted form of "/Applications/FORCE.app/Contents/Resources/teal"
    else if selectedOption is "Quit" then
        display dialog "Exiting..." buttons {"OK"} default button "OK"
        return
    end if
    -- do shell script filePathName
    try
        do shell script "test -e " & filePathName
        -- If the test passes, the file exists and we proceed with the script
        do shell script filePathName
    on error
        -- If the file doesn't exist, display an error message
        display dialog "The file at " & filePathName & " does not exist." buttons {"OK"} default button "OK"
    end try
end if