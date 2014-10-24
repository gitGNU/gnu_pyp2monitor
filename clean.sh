#!/bin/bash

echo "Removing src/*.pyc and doxygen documentation files"
rm -R src/*.pyc doc/  2>/dev/null
