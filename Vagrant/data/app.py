from flask import Flask, jsonify, Response
from pyspark.sql import SparkSession
import json

app = Flask(__name__)

# Créer une session Spark
spark = (SparkSession.builder
        .appName("FlaskAPI")
        .getOrCreate())

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        # Vérifier si la table existe
        tables = spark.catalog.listTables()
        if not any(table.name == 'logs_table' for table in tables):
            return jsonify({"error": "Table logs_table does not exist"}), 404
        
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
