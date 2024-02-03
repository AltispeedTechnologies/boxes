# Mike's Boxes

Starter deploy instructions:

```bash
# Migrate the database, run after every update
python3 manage.py migrate

# Import/update data, can be ran on an existing instance
# Be careful when modifying initial_data! Existing entries are clobbered over
python3 manage.py loaddata initial_data.json
```
