#!/bin/bash

cd application

mkdir packages

## user-profile-picture
mkdir "packages/$1"
cd "$1"
zip -r9 "../packages/$1.zip" .

cd ..

aws s3 cp "packages/$1.zip" "$2"

rm -rf packages
