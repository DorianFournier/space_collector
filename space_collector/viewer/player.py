import logging

import arcade
from space_collector.game.math import Vector

from space_collector.viewer.constants import TEAM_HUES
from space_collector.viewer.planet import Planet
from space_collector.viewer.spaceship import SpaceShip, Collector, Attacker, Explorator
from space_collector.viewer.utils import hue_changed_texture, map_coord_to_window_coord
from space_collector.game.player_orientations import player_orientations

type_name_to_class = {
    "collector": Collector,
    "attacker": Attacker,
    "explorer": Explorator,
}


class Player:
    def __init__(self, team: int) -> None:
        self.name = ""
        self.blocked = True
        self.orientation = "S"
        self.spaceships: list[SpaceShip] = []
        self.planets: dict[int, Planet] = {}
        self.team = team

    def setup(self) -> None:
        self.base_sprite = arcade.Sprite(
            texture=hue_changed_texture(
                "space_collector/viewer/images/station.png", TEAM_HUES[self.team]
            )
        )
        self.base_sprite.width = 200
        self.base_sprite.height = 200
        orientation = player_orientations[self.team]
        self.base_sprite.angle = orientation.angle - 90
        base_offset = orientation.matrix @ Vector([0, -2500])
        self.base_sprite.position = map_coord_to_window_coord(
            *(Vector(orientation.base_position) + base_offset)
        )

    def draw(self) -> None:
        self.base_sprite.draw()
        for planet in self.planets.values():
            planet.draw()
        if not self.blocked:
            for spaceship in self.spaceships:
                spaceship.draw()

    def update(self, server_data: dict, duration: float) -> None:
        # logging.info("update player for %f: %s", duration, str(server_data))
        self.name = server_data["name"]
        self.blocked = server_data["blocked"]

        if not self.spaceships:
            for spaceship_data in server_data["spaceships"]:
                class_ = type_name_to_class[spaceship_data["type"]]
                self.spaceships.append(
                    class_(
                        spaceship_data["x"],
                        spaceship_data["y"],
                        spaceship_data["angle"],
                        self.team,
                    )
                )
                self.spaceships[-1].setup()
        for index, spaceship_data in enumerate(server_data["spaceships"]):
            self.spaceships[index].update(spaceship_data, duration)

        if not self.planets:
            for planet_data in server_data["planets"]:
                planet = Planet(
                    planet_data["x"],
                    planet_data["y"],
                    planet_data["id"],
                    self.team,
                    self.spaceships,
                )
                self.planets[planet.id] = planet
                planet.setup()
        for planet_data in server_data["planets"]:
            self.planets[planet_data["id"]].update(planet_data, duration)
