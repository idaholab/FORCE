#!/bin/bash
# Copies examples from the test directories of RAVEN and HERON to provide examples for users using
# the standalone install version of FORCE.

# Get the RAVEN and HERON locations as arguments "--raven-dir" and "--heron-dir"
# The destination directory is "examples" in the current directory but may be changed with the
# "--dest" argument.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
EXAMPLES_DIR="$SCRIPT_DIR/examples"

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --raven-dir)
        RAVEN_DIR="$2"
        shift
        shift
        ;;
        --heron-dir)
        HERON_DIR="$2"
        shift
        shift
        ;;
        --dest)
        EXAMPLES_DIR="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# The examples we want to copy are the RAVEN user_guide tests, the HERON workshop tests, and the
# HERON data directory which contains time series models for those workshop tests.
EXAMPLES=($RAVEN_DIR/tests/framework/user_guide $HERON_DIR/data $HERON_DIR/tests/workshop)
mkdir -p $EXAMPLES_DIR

for ex in ${EXAMPLES[@]}; do
    cp -R "$ex" "$EXAMPLES_DIR"
done

# Clean up the copied examples, removing files and directories created when running the tests.
DIRS_TO_REMOVE=("__pycache__" "gold" "*_o")
for dirname in ${DIRS_TO_REMOVE[@]}; do
    find $EXAMPLES_DIR -type d -name $dirname -exec rm -r {} \; 2>/dev/null
done
FILES_TO_REMOVE=("tests" "moped_input.xml" "outer.xml" "inner.xml" "cash.xml" "*.lib" "write_inner.py" "*.heron" "*.heron.xml")
for filename in ${FILES_TO_REMOVE[@]}; do
    find $EXAMPLES_DIR -name $filename -exec rm {} \; 2>/dev/null
done

# If building on Mac, replace the %HERON_DATA% magic string with a relative path to the data
# directory. This is a little hacky but the %HERON_DATA% magic string doesn't look everywhere for
# the data directory. This is only an issue for the Mac standalone install. HERON will find the
# data directory correctly on Windows.
# DATA_DIR=$EXAMPLES_DIR/data
# if [[ "$OSTYPE" == "darwin"* ]]; then
#     # Find all XML files recursively from the current directory
#     find $EXAMPLES_DIR/workshop -type f -name "*.xml" | while read -r file; do
#         # Check if the file contains the %HERON_DATA% magic string. If not, skip this file.
#         grep -q "%HERON_DATA%" "$file" || continue

#         # Get the directory of the current XML file
#         FILE_DIR=$(dirname "$file")

#         # Calculate the relative path from the XML file directory to the data directory
#         echo "FILE_DIR: $FILE_DIR   DATA_DIR: $DATA_DIR"
#         RELATIVE_PATH=$(python -c "import os.path; print(os.path.relpath('$DATA_DIR', '$FILE_DIR'))")
#         # RELATIVE_PATH=$(realpath -s --relative-to="$FILE_DIR" "$DATA_DIR")
#         echo $RELATIVE_PATH

#         # Use sed to replace %HERON_DATA% with the relative path to the data directory
#         sed -i '' "s|%HERON_DATA%|$RELATIVE_PATH|g" "$file"
#     done
# fi
