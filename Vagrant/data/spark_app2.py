from flask import Flask, jsonify, request, Response
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import from_json, col
from pyspark.sql.functions import to_timestamp
import threading
import json

app = Flask(__name__)

# Définir le schéma des messages JSON
schema = StructType([
    StructField("@timestamp", StringType(), True),
    StructField("log_level", StringType(), True),
    StructField("message", StringType(), True),
    StructField("container", StructType([
        StructField("name", StringType(), True),
        StructField("image", StructType([
            StructField("name", StringType(), True)
        ])),
        StructField("id", StringType(), True)
    ])),
    StructField("host", StructType([
        StructField("name", StringType(), True)
    ])),
    StructField("stream", StringType(), True)
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
        log_level = request.args.get('log_level', None)
        container_name = request.args.get('container_name', None)
        start_time = request.args.get('start_time', None)
        end_time = request.args.get('end_time', None)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        query = "SELECT * FROM logs_table"
        filters = []

        if log_level:
            filters.append(f"log_level = '{log_level}'")
        if container_name:
            filters.append(f"container.name = '{container_name}'")
        if start_time:
            filters.append(f"to_timestamp(`@timestamp`) >= to_timestamp('{start_time}')")
        if end_time:
            filters.append(f"to_timestamp(`@timestamp`) <= to_timestamp('{end_time}')")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += f" LIMIT {limit} OFFSET {offset}"

        logs_df = spark.sql(query)
        logs = logs_df.collect()
        
        logs_list = []
        for row in logs:
            logs_list.append({
                "timestamp": row["@timestamp"],
                "log_level": row.log_level,
                "message": row.message,
                "container": {
                    "name": row.container.name,
                    "id": row.container.id,
                    "image": row.container.image.name
                },
                "host": row.host.name,
                "stream": row.stream
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

@app.route('/log-stats', methods=['GET'])
def log_stats():
    try:
        stats_df = spark.sql("""
            SELECT 
                log_level, 
                COUNT(*) as count, 
                container.name as container_name 
            FROM logs_table 
            GROUP BY log_level, container.name
        """)
        stats = stats_df.collect()

        # Convertir les statistiques en JSON
        stats_list = []
        for row in stats:
            stats_list.append({
                "log_level": row.log_level,
                "count": row['count'],
                "container_name": row.container_name
            })

        return jsonify(stats_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
