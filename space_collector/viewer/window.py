import logging
import random
from queue import Queue
from typing import NoReturn

import arcade

from space_collector.viewer.animation import set_date, date
from space_collector.viewer.constants import constants
from space_collector.viewer.player import Player
from space_collector.viewer.space_background import SpaceBackground
from space_collector.viewer.score import Score

input_queue: Queue = Queue()


class Window(arcade.Window):
    def __init__(self) -> None:
        super().__init__(
            constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, constants.SCREEN_TITLE
        )
        arcade.set_background_color(arcade.csscolor.BLACK)
        self.background = SpaceBackground()
        self.score = Score()
        self.players: list[Player] = [Player(team) for team in range(4)]

    def setup(self) -> None:
        pass
        self.background.setup()
        self.score.setup()
        for player in self.players:
            player.setup()

    def on_draw(self):
        if not input_queue.empty():
            data = input_queue.get()
            date_server = data["time"]
            duration = max(0, date_server - date())
            set_date(date_server)
            for player, player_data in zip(self.players, data["players"]):
                player.update(player_data, duration)
            self.score.update(data)

        self.clear()
        self.background.draw()
        for player in self.players:
            player.draw()
        self.score.draw()


def gui_thread() -> None:
    window = Window()
    try:
        window.setup()
        arcade.run()
    except Exception:  # noqa: PIE786
        logging.exception("uncaught exception")
