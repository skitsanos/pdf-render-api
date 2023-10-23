import logging
import os
import socket

import yaml
from flask import Flask, g, render_template
from waitress import serve

app = Flask(__name__)


def load_routes(app, path):
    for root, dirs, files in os.walk(path):
        app.logger.info(root)
        for found_dir in dirs:
            route_path = os.path.relpath(os.path.join(root, found_dir), path)
            module_path = os.path.relpath(os.path.join(root, found_dir), path)

            # Check if dir starts with $
            if found_dir.startswith("$"):
                # Replace $ with < and > to make a path parameter
                route_path = os.path.relpath(os.path.join(root, f"<{found_dir.replace('$', '')}>"), path)

            methods = []
            for method in ("get", "post", "put", "delete", "options", "head", "patch"):
                if os.path.exists(os.path.join(root, found_dir, f"{method}.py")):
                    methods.append(method.upper())
                    module_name = f"routes.{module_path.replace(os.sep, '.')}.{method}"

                    app.logger.info(f'Route: {method.upper()} /{route_path} ({module_name})')

                    module = __import__(module_name, fromlist=["*"])
                    app.add_url_rule(f"/{route_path}",
                                     view_func=module.handler,
                                     endpoint=module_name,
                                     methods=[method.upper()]
                                     )
                    break


@app.before_request
def before_request():
    #
    # The request handler requires to have access to the app context
    #
    g.app = app


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # Disable Azure logging
    # logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)

    hostname = socket.gethostname()
    logging.basicConfig(
        level=logging.INFO,  # Set the desired logging level
        format=f'%(asctime)s [%(levelname)s] {hostname} %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    app.logger.info('Checking config...')
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            app.config.update(config)

    app.logger.info(f'Loading routes ({os.getcwd()}/routes)...')
    load_routes(app, "routes")
    app.logger.info('Routes loaded.')

    # Specify the host and port
    host = os.getenv('BIND') or '0.0.0.0'
    port = int(os.getenv('PORT') or '5000')

    # Start the Waitress server
    serve(app, host=host, port=port)
