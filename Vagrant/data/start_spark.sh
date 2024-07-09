


#!/bin/bash
source ~/.bashrc
cd /vagrant_data
echo "Starting Spark at $(date)" >> /vagrant_data/spark_log.txt
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 /vagrant_data/spark_app2.py >> /vagrant_data/spark_log.txt 2>&1



