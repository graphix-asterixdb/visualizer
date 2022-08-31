#!/bin/bash

PYTHON_EXECUTABLE_PATH="venv/bin/python3"
if test -f "$PYTHON_EXECUTABLE_PATH"; then
  $PYTHON_EXECUTABLE_PATH visualize.py "$@"
else
  echo "python3 executable not found: ${PYTHON_EXECUTABLE_PATH}, using system default: $(which python3)"
  python3 visualize.py "$@"
fi
