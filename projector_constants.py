from enum import Enum

from .resolution_presets import get_resolution_items


class Textures(Enum):
    CHECKER = 'checker_texture'
    COLOR_GRID = 'color_grid_texture'
    CUSTOM_TEXTURE = 'custom_texture'


# Resolutions are stored as JSON presets (name, x, y) in resolutions/ and loaded from there.
RESOLUTIONS = get_resolution_items(None, None)

PROJECTED_OUTPUTS = [
    (Textures.CHECKER.value, 'Checker', '', 1),
    (Textures.COLOR_GRID.value, 'Color Grid', '', 2),
    (Textures.CUSTOM_TEXTURE.value, 'Custom Texture', '', 3),
]
