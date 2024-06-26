#!/bin/bash
source ~/.bashrc
cd /vagrant_data
echo "Starting Flask at $(date)" >> /vagrant_data/flask_log.txt
python3 /vagrant_data/app.py >> /vagrant_data/flask_log.txt 2>&1
