# Mike's Boxes

- [Initial Setup](#initial-setup)
- [Update Setup](#update-setup)
- [Development Setup](#development-setup)

## Initial Setup

1. Install and Setup your Database. Sqlite and Postgres have both been tested.  For production instances, Postgres should be used.

2. Clone Repository
```bash
git clone git@gitlab.com:altispeed/internal/dev/mikes-boxes.git
```

3. Navigate into the cloned repository
```bash
cd mikes-boxes
```

4. Create environmental file
```bash
cp .env.dist .env
```

5. Install Python requirements
```bash
sudo apt update
sudo apt install python3-pip

python3 -m pip install -r requirements.txt
```

6. Migrate the database, run after every update and each time you set it up
```bash
ENV_PATH=.env python3 manage.py migrate
```

7. Import/update data for initial the setup, can be ran on an existing instance.  Be careful when modifying initial_data! Existing entries are clobbered over
```bash
ENV_PATH=.env python3 manage.py loaddata initial_data.json
```

8. Collect Static Files
```bash
ENV_PATH=.env python3 manage.py collectstatic
```

## Update Setup

1. Migrate the database, run after every update and each time you set it up
```bash
ENV_PATH=.env python3 manage.py migrate
```

2. Collect Static Files
```bash
ENV_PATH=.env python3 manage.py collectstatic
```

## Development Setup

1. Install and Setup your Database. Sqlite and Postgres have both been tested.  For production instances, Postgres should be used.

2. Install Python requirements
```bash
python3 -m pip install -r requirements.txt
```

3. Migrate the database, run after every update and each time you set it up
```bash
ENV_PATH=.env python3 manage.py migrate
```

4. Import/update data for initial the setup, can be ran on an existing instance.  Be careful when modifying initial_data! Existing entries are clobbered over
```bash
ENV_PATH=.env python3 manage.py loaddata initial_data.json
```

5. For Developement, you can load example data by running this command.
```bash
ENV_PATH=.env python3 manage.py loaddata package_seed_data.json
```

6. Collect Static Files
```bash
ENV_PATH=.env python3 manage.py collectstatic
```
