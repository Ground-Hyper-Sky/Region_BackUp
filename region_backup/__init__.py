PLUGIN_METADATA = {
    'id': 'hello_world',
    'version': '1.0.0',
    'name': 'My Hello World Plugin'
}


def on_load(server, old):
    server.logger.info('Hello world!')