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

## Credits and License

Copyright 2024 Altispeed Technologies
Author: Simon Quigley <squigley@altispeed.com>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License in the LICENSE file for more details.
