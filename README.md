# Mike's Boxes

Starter deploy instructions:

 - Run ./setup.sh dev
 - Install RabbitMQ, here's a simple (nonfunctional) example:
```
sudo apt -y install rabbitmq-server
sudo systemctl enable --now rabbitmq-server
sudo rabbitmqctl add_user myuser mypassword
sudo rabbitmqctl add_vhost myvhost
sudo rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
```
 - Copy systemd units to /etc/systemd/system - reload the daemon, enable and start these services
