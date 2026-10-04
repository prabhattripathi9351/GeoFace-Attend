#!/usr/bin/env bash
echo "=== CUSTOM BUILD SCRIPT RUNNING ==="
pip install "setuptools<81" wheel
pip install dlib-bin==20.0.1
pip install face_recognition_models==0.3.0
pip install --no-deps face_recognition==1.3.0
pip install -r requirements.txt