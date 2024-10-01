from . import uiFork
from . import projectorfork
from . import operatorsFork

bl_info = {
    "name": "ProjectorFork",
    "author": "Jonas Schell",
    "description": "Easy Projector creation and modification.",
    "blender": (4, 2, 1),
    "version": (2024, 3, 0),
    "location": "3D Viewport > Add > Light > ProjectorFork",
    "category": "Lighting",
    "wiki_url": "https://github.com/Ocupe/Projectors/wiki",
    "tracker_url": "https://github.com/Ocupe/Projectors/issues"
}


def register():
    projectorfork.register()
    operatorsFork.register()
    uiFork.register()


def unregister():
    uiFork.unregister()
    operatorsFork.unregister()
    projectorfork.unregister()
