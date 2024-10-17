#!/bin/bash

# This script builds and gathers documentation from the FORCE tools to be included together as
# documentation for FORCE.
# Command line arguments:
#  --raven-dir <path>: Path to the RAVEN repository. If no other paths are provided, the script will
#                      look for HERON and TEAL as RAVEN plugins.
#  --heron-dir <path>: (Optional) Path to the HERON repository.
#  --teal-dir <path>: (Optional) Path to the HERON repository.
#  --dest <path>: (Optional) Path to the directory where the documentation will be copied to. Default
#                 is to create a "docs" directory the directory this script is in.
#  --no-build: (Optional) Skip building the documentation and only gather the existing documentation
#              PDFs. Default is to rebuild the documentation.

# Parse command line arguments
NO_BUILD=0
while [[ $# -gt 0 ]]; do
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
  --teal-dir)
    TEAL_DIR="$2"
    shift
    shift
    ;;
  --no-build)
    NO_BUILD=1
    shift
    ;;
  --dest)
    DOC_DIR="$2"
    shift
    shift
    ;;
  *)
    echo "Unknown option: $1"
    exit 1
    ;;
  esac
done

# Check that the RAVEN directory is provided
if [ -z "$RAVEN_DIR" ]; then
  echo "ERROR: The RAVEN directory must be provided with --raven-dir."
  exit 1
fi

# If the HERON and TEAL directories are not provided, look for them as plugins.
if [ -z "$HERON_DIR" ]; then
  HERON_DIR="$RAVEN_DIR/plugins/HERON"
fi
if [ -z "$TEAL_DIR" ]; then
  TEAL_DIR="$RAVEN_DIR/plugins/TEAL"
fi

# Default destination directory is a "docs" directory in the directory this script is in.
if [ -z "$DOC_DIR" ]; then
  DOC_DIR="$SCRIPT_DIR/docs"
fi

# Create a directory to store the documentation. We'll do that in the directory this script is in.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DOC_DIR="$SCRIPT_DIR/docs"
echo "FORCE documentation directory: $DOC_DIR"
mkdir -p "$DOC_DIR"

# Build the documentation for the FORCE tools
for loc in RAVEN_DIR HERON_DIR TEAL_DIR; do
  pushd "${!loc}/doc" > /dev/null
  echo $(pwd)

  # If the build flag is set, build the documentation.
  if [ $NO_BUILD -eq 0 ]; then
  echo "Building documentation for $(basename ${!loc})"
  if [[ -f "Makefile" ]] && command -v "make" >/dev/null 2>&1; then
    make
  elif [[ -f "make_docs.bat" ]] && [[ $OSTYPE == "msys" ]]; then
    ./make_docs.bat
  elif [[ -f "make_docs.sh" ]]; then
    bash make_docs.sh
  else
    echo "ERROR: No Makefile or make_docs.sh script found in $(basename ${!loc}) doc directory."
    exit 1
  fi
  fi

  # The PDFs that are generated are located in either a "pdfs" or "pdf" directory
  if [ -d pdfs ]; then
  cp pdfs/*.pdf $DOC_DIR
  elif [ -d pdf ]; then
  cp pdf/*.pdf $DOC_DIR
  else
  echo "ERROR: No PDFs found in $(basename ${!loc}) doc directory."
    exit 1
  fi

  popd > /dev/null
done
