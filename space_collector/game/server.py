import argparse
import contextlib
import json
import logging
import sys
from time import sleep

from space_collector.game.game import Game
from space_collector.network.data_handler import NetworkError
from space_collector.network.server import ClientData, Server

MAX_NB_PLAYERS = 4
SERVER_CONNECTION_TIMEOUT = 1  # TODO remettre 5


class GameServer(Server):
    def __init__(self: "GameServer", host: str, port: int):
        super().__init__(host, port)
        self.game = Game()
        self._wait_connections()
        for player_name in {player.name for player in self.players}:
            self.game.add_player(player_name)

    @property
    def players(self):
        return [client for client in self.clients if not client.spectator]

    @property
    def spectators(self):
        return [client for client in self.clients if client.spectator]

    def remove_client(self: "GameServer", client: ClientData) -> None:
        self.clients.remove(client)
        if not client.spectator:
            for player in self.game.players:
                if player.name == client.name:
                    player.blocked = True

    def _wait_connections(self: "GameServer") -> None:
        while not self.players:
            print("Waiting for player clients")
            sleep(1)

        for second in range(1, SERVER_CONNECTION_TIMEOUT + 1):
            print(f"Waiting other players ({second}/{SERVER_CONNECTION_TIMEOUT})")
            if len(self.players) == MAX_NB_PLAYERS:
                break
            sleep(1)

        print("Players ready: START!!!")

    def read(self, client: ClientData) -> str:
        try:
            text = client.network.readline()
        except NetworkError:
            logging.exception("timeout")
            self.remove_client(client)
            return ""

        logging.debug(text)
        return text

    def write(self, client: ClientData, text: str) -> None:
        if not text.endswith("\n"):
            text += "\n"
        logging.debug("sending to %s", client.name)
        try:
            client.network.write(text)
        except NetworkError:
            logging.exception("Problem sending state to client")
            self.remove_client(client)

    def run(self: "GameServer") -> None:
        while True:
            for player in self.players:
                if player.network.input_empty():
                    continue
                command = self.read(player)
                self.write(player, self.game.manage_command(command))
            for spectator in self.spectators:
                self.write(spectator, json.dumps(self.game.state()))
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Game server.")
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        help="name of server on the network",
        default="localhost",
    )
    parser.add_argument(
        "-p", "--port", type=int, help="location where server listens", default=16210
    )
    parser.add_argument(
        "-f",
        "--fast",
        help="fast simulation",
        action="store_true",
    )

    args = parser.parse_args()

    if args.fast:
        logging.basicConfig(handlers=[logging.NullHandler()])
        with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
            GameServer(args.address, args.port, args.fast).run()
    else:
        logging.basicConfig(
            filename="server.log",
            encoding="utf-8",
            level=logging.INFO,
            format=(
                "%(asctime)s [%(levelname)-8s] %(filename)20s(%(lineno)3s):"
                "%(funcName)-20s :: %(message)s"
            ),
            datefmt="%m/%d/%Y %H:%M:%S",
        )
        logging.info("Launching server")
        GameServer(args.address, args.port).run()
