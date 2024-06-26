# DevOps Labs and Project

## Requirments

Windows:

- Vagrant
- Virtualbox
- Kafka

## Setup

First of all run kafka on your computer then launch the vagrant VM :
```shell
vagrant up
vagrant ssh
```
### Filebeat and docker
Secondly, go in your filebeat file :
```bash
nano /etc/filebeat/filebeat.yml
```

Then past the following file :

```yml
filebeat.inputs:
- type: container
  enabled: true
  paths:
    - /var/lib/docker/containers/*/*.log
  processors:
    - add_docker_metadata: ~
    - decode_json_fields:
        fields: ["message"]
        target: ""
        overwrite_keys: true
  fields:
    log_topic: 'logs'
  fields_under_root: true

output.kafka:
  hosts: ["192.168.33.1:9092"] # Remplacez par l'adresse IP de votre hôte
  topic: '%{[log_topic]}'
  codec.json:
    pretty: false

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: false

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```
Then check if kafka is in the module list of filebeat :
```bash
sudo filebeat modules list
```

If there isn't, add it :
```bash
sudo filebeat modules enable kafka
```

Then, run a nginx image with docker :
```bash
docker run -d --name nginx-container nginx:latest -p 8080:80
```

Then restart filebeat :
```bash
sudo service filebeat restart
```

You can check if filebeat is working well with this command :
```bash
sudo tail -f /var/log/filebeat/filebeat
```

### Spark script
Finaly, execute the spark script :
```bash
screen -dmS spark /vagrant_data/script_spark.sh
```

And if you do :
```bash
curl localhost:5000/logs
```
You should be able to see the logs of your nginx container.

There are other routes like

localhost:5000/log-stats

or you can add parameters with logs :
```py
log_level = request.args.get('log_level', None)
container_name = request.args.get('container_name', None)
start_time = request.args.get('start_time', None)
end_time = request.args.get('end_time', None)
limit = int(request.args.get('limit', 100))
offset = int(request.args.get('offset', 0))
```

Moreover you can check the logs of the spark app if you do :
```bash
cat /vagrant_data/spark_log.txt
```
Or just open the file from your pc in the data folder