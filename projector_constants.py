from enum import Enum


class Textures(Enum):
    CHECKER = 'checker_texture'
    COLOR_GRID = 'color_grid_texture'
    CUSTOM_TEXTURE = 'custom_texture'


RESOLUTIONS = [
    # 16:10 aspect ratio
    ('1280x800', 'WXGA (1280x800) 16:10', '', 1),
    ('1440x900', 'WXGA+ (1440x900) 16:10', '', 2),
    ('1920x1200', 'WUXGA (1920x1200) 16:10', '', 3),
    # 16:9 aspect ratio
    ('1280x720', '720p (1280x720) 16:9', '', 4),
    ('1920x1080', '1080p (1920x1080) 16:9', '', 5),
    ('3840x2160', '4K Ultra HD (3840x2160) 16:9', '', 6),
    # 4:3 aspect ratio
    ('768x576', 'PAL-D (768x576) 4:3', '', 7),
    ('800x600', 'SVGA (800x600) 4:3', '', 8),
    ('1024x768', 'XGA (1024x768) 4:3', '', 9),
    ('1400x1050', 'SXGA+ (1400x1050) 4:3', '', 10),
    ('1600x1200', 'UXGA (1600x1200) 4:3', '', 11),
    # 17:9 aspect ratio
    ('4096x2160', 'Native 4K (4096x2160) 17:9', '', 12),
    # 1:1 aspect ratio
    ('1000x1000', 'Square (1000x1000) 1:1', '', 13),
    # 1:2 aspect ratio
    ('1000x2000', 'Portrait (1000x2000) 1:2', '', 14),
    # 2:1 aspect ratio
    ('2000x1000', 'Landscape (2000x1000) 2:1', '', 15),
]

PROJECTED_OUTPUTS = [
    (Textures.CHECKER.value, 'Checker', '', 1),
    (Textures.COLOR_GRID.value, 'Color Grid', '', 2),
    (Textures.CUSTOM_TEXTURE.value, 'Custom Texture', '', 3),
]
