import irc
import irc.client
import irc.connection
import irc.events
import configparser
import ssl

def notify_on_join(connection, event):
    print('joined. event: {}'.format(event))

class TpaEventHandler:
    def __init__(self, client):
        self.client = client
    def do_init_commands(self, connection, event):
        self.client.join('#jeffhoogland')



def main(config):
    server_addr = config['server']
    port = int(config['port'])
    creds = config['creds']

    ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)

    client = irc.client.Reactor()
    for event_type in irc.events.numeric.values():
        def cb(connection, event):
            print(event)
        client.add_global_handler(event_type, cb)
    server = client.server()
    server.connect(server=server_addr, port=port,
                   nickname='rskjr', password=creds, connect_factory=ssl_factory)
    print(server.get_server_name())
    client.add_global_handler('JOIN', notify_on_join)
    tpa_handler = TpaEventHandler(client)
    client.add_global_handler('endofmotd', tpa_handler.do_init_commands)
    client.process_forever()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('tpa.ini')

    main(config['main'])
