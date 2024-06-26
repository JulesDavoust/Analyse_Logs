from kafka import KafkaProducer
import json

# Configurer le producteur Kafka
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

logs = [
    {"timestamp": "2023-06-25T12:00:00", "log_level": "ERROR", "message": "Service started"},
    {"timestamp": "2023-06-25T12:01:00", "log_level": "WARNING", "message": "High memory usage detected"},
    {"timestamp": "2023-06-25T12:02:00", "log_level": "ERROR", "message": "Failed to connect to database"}
]

for log in logs:
    print(log)
    producer.send('logs', log)

producer.flush()


