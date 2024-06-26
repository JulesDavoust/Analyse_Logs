from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import from_json, col
from flask import Flask, jsonify, Response
import threading
import time
import json

app = Flask(__name__)

# Définir le schéma des messages JSON
schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("log_level", StringType(), True),
    StructField("message", StringType(), True)
])

# Créer une session Spark avec le package Kafka pour Spark 3.5.1 et Scala 2.12
spark = (SparkSession.builder
        .appName("KafkaConnectivityTest")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
        .getOrCreate())

# Lire les logs depuis Kafka
df = (spark
    .readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "192.168.33.1:9092")  # Remplacez par l'adresse IP de votre hôte
    .option("subscribe", "logs")
    .load())

# Convertir les messages JSON en colonnes
logs = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

# Enregistrer les logs dans une table temporaire
query_memory = (logs
        .writeStream
        .outputMode("append")
        .format("memory")
        .queryName("logs_table")
        .start())

# Afficher les logs dans la console (facultatif)
query_console = (logs
        .writeStream
        .outputMode("append")
        .format("console")
        .start())

def keep_spark_streaming():
    # Cette fonction permet de maintenir le stream Spark actif
    query_memory.awaitTermination()
    query_console.awaitTermination()

# Exécuter le streaming Spark dans un thread séparé pour ne pas bloquer Flask
thread = threading.Thread(target=keep_spark_streaming)
thread.daemon = True
thread.start()

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        # Lire les données de la table temporaire Spark
        logs_df = spark.sql("SELECT * FROM logs_table")
        logs = logs_df.collect()

        # Convertir les logs en JSON
        logs_list = []
        for row in logs:
            logs_list.append({
                "timestamp": row.timestamp,
                "log_level": row.log_level,
                "message": row.message
            })

        return jsonify(logs_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tables', methods=['GET'])
def list_tables():
    try:
        tables = spark.catalog.listTables()
        table_list = [table.name for table in tables]
        return Response(json.dumps(table_list), mimetype='application/json')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)