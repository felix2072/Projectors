import bpy
from bpy.types import Operator


class PROJECTOR_OT_switch_to_cycles(Operator):
    """ Change the render engin to cycles. """
    bl_idname = 'projector.switch_to_cycles'
    bl_label = ' Change Render Engine to Cycles. '
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.render.engine = 'CYCLES'
        return {'FINISHED'}

class PROJECTOR_OT_toggle_spotlight(Operator):
    """Toggle Projector Spotlight on/off."""
    bl_idname = 'projector.toggle_spotlight'
    bl_label = 'Toggle Projector Spotlight'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .helper import get_projectors, get_child_ID_by_type
        projectors = get_projectors(context, only_selected=True)
        if not projectors:
            return {'CANCELLED'}
        projector = projectors[0]
        spot = None
        for child in projector.children:
            if child.type == 'LIGHT' and child.name == 'Projector_Spotlight':
                spot = child
                break
        if not spot:
            return {'CANCELLED'}
        spot.hide_viewport = not spot.hide_viewport
        spot.hide_render = spot.hide_viewport
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PROJECTOR_OT_switch_to_cycles)
    bpy.utils.register_class(PROJECTOR_OT_toggle_spotlight)


def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_toggle_spotlight)
    bpy.utils.unregister_class(PROJECTOR_OT_switch_to_cycles)
