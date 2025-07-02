import json
import os

from app import create_app


def load_config(path='config/config.json'):
    default = {
        'host': '127.0.0.1',
        'port': 5000,
        'nodes_db': 3,
        'API_TOKEN': 'your_api_token_here'
    }
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(default, f)
        return default
    with open(path) as f:
        try:
            return {**default, **json.load(f)}
        except Exception:
            return default


def main():
    config = load_config()
    app = create_app(config)
    app.run(host=config.get('host', '127.0.0.1'), port=config.get('port', 5000))


if __name__ == '__main__':
    main()