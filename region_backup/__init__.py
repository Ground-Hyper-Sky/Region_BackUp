from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'restart_plugin',
    'version': '1.0.0',
    'name': 'Restart Plugin',
    'description': 'A simple plugin for restarting the server.',
    'author': 'mc_doge_'
}

class RestartPlugin:

    def __init__(self, server: PluginServerInterface, config: dict):
        self.server = server
        self.server.register_command(
            Literal('!!restart').runs(self.restart_server)
        )

    def on_load(self):
        self.server.logger.info('Restart Plugin loaded.')

    def on_unload(self):
        self.server.logger.info('Restart Plugin unloaded.')

    def restart_server(self, source: CommandSource):
        # 直接调用 MCDR 提供的 restart 方法进行服务器重启
        if not self.server.get_instance().restart():
            self.server.say('Failed to restart the server. The server may already be stopped.')
            return
            
        self.server.say('Server is restarting. Please reconnect later.')

def on_load(server: PluginServerInterface, old):
    return RestartPlugin(server, old)
