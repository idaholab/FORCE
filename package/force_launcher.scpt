set options to {"HERON", "RAVEN", "TEAL", "Quit"}

set resourceName to "heron"
set filePathName to quoted form of POSIX path of (path to resource resourceName) as text

set selectedOption to choose from list options with title "FORCE Launcher" with prompt "Which FORCE application woudl you like to use?" default items {"HERON"}

if selectedOption is false then
    display dialog "No option selected. Exiting..." buttons {"OK"} default button "OK"
else
    set selectedOption to item 1 of selectedOption
    if selectedOption is "HERON" then
        set resourceName to "heron"
    else if selectedOption is "RAVEN" then
        set resourceName to "raven_framework"
    else if selectedOption is "TEAL" then
        set resourceName to "teal"
    else if selectedOption is "Quit" then
        display dialog "Exiting..." buttons {"OK"} default button "OK"
    end if
    set filePathName to quoted form of POSIX path of (path to resource resourceName) as text
    do shell script filePathName
end if
