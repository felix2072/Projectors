import bpy
from bpy.types import Operator


class PROJECTORFORK_OT_switch_to_cycles_fork(Operator):
    """ Change the render engin to cycles. """
    bl_idname = 'projectorfork.switch_to_cycles'
    bl_label = ' Change Render Engine to Cycles. '
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.render.engine = 'CYCLES'
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PROJECTORFORK_OT_switch_to_cycles_fork)


def unregister():
    bpy.utils.unregister_class(PROJECTORFORK_OT_switch_to_cycles_fork)
