import json

CONFIG_FILE = 'config.json'

# Load configuration
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {'movie_folders': [], 'genres': []}
