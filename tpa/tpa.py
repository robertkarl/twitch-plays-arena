import irc
import irc.client
import irc.connection
import irc.events
import configparser
import ssl


def notify_on_message(connection, event):
    print("message received. event: {}".format(event))


class TpaEventHandler:
    def __init__(self, reactor, server):
        # type: (irc.client.server) -> None
        self.server = server
        self.reactor = reactor
        self._has_requested_perms = False

    def on_welcome(self, connection, event):
        self.request_only_once()

    def on_cap(self, connection, event):
        self.server.join("#wyattdarbymtg")

    def request_only_once(self):
        if self._has_requested_perms:
            return
        else:
            print("requesting permissions")
            self.server.cap("LS")
            self.server.cap(
                "REQ", "twitch.tv/commands", "twitch.tv/tags", "twitch.tv/membership"
            )
            self.server.cap("END")
            self._has_requested_perms = True

    def on_userstate(self, connection, event):
        print(event)

    def on_clearchat(self, connection, event):
        print(event)

    def on_anyevent(self, connection, event):
        print(event)


def main(config):
    server_addr = config["server"]
    port = int(config["port"])
    creds = config["creds"]

    ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)

    client = irc.client.Reactor()
    for event_type in irc.events.numeric.values():

        def cb(connection, event):
            print(event)

        client.add_global_handler(event_type, cb)
    server = client.server()
    server.connect(
        server=server_addr,
        port=port,
        nickname="rskjr",
        password=creds,
        connect_factory=ssl_factory,
    )
    print(server.get_server_name())

    tpa_handler = TpaEventHandler(client, server)
    client.add_global_handler("welcome", tpa_handler.on_welcome)
    client.add_global_handler("join", tpa_handler.on_anyevent)
    client.add_global_handler("userstate", tpa_handler.on_userstate)
    client.add_global_handler("clearchat", tpa_handler.on_clearchat)
    client.add_global_handler("roomstate", tpa_handler.on_anyevent)
    client.add_global_handler("cap", tpa_handler.on_cap)
    for protocol_name in irc.events.protocol:
        client.add_global_handler(protocol_name, tpa_handler.on_anyevent)

    client.process_forever()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    config = configparser.ConfigParser()
    config.read("tpa.ini")

    main(config["main"])
