from . import ui
from . import projector
from . import operators
from . import projector_load

bl_info = {
    "name": "Projector",
    "author": "Jonas Schell / Felix Worseck",
    "description": "Easy Projector creation and modification.",
    "blender": (2, 81, 0),
    "version": (2026, 5, 0),
    "location": "3D Viewport > Add > Light > ProjectorFork",
    "category": "Lighting",
    "wiki_url": "https://github.com/Ocupe/Projectors/wiki",
    "tracker_url": "https://github.com/Ocupe/Projectors/issues"
}


def register():
    projector.register()
    operators.register()
    ui.register()
    projector_load.register()


def unregister():
    ui.unregister()
    operators.unregister()
    projector.unregister()
    projector_load.unregister()
