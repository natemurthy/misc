#!/bin/bash

VERSION="$(cut -d '"' -f2 < version.sbt)"
echo $VERSION
