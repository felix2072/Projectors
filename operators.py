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


def _get_selected_projector_image_node(context):
    from .helper import get_projectors, get_child_ID_by_type

    projectors = get_projectors(context, only_selected=True)
    if not projectors:
        return None

    projector = projectors[0]
    try:
        light_id = get_child_ID_by_type(projector.children, 'LIGHT')
        light = projector.children[light_id]
        return light.data.node_tree.nodes.get('Image Texture')
    except Exception:
        return None


class PROJECTOR_OT_flip_texture_horizontal(Operator):
    """Flip custom texture horizontally."""

    bl_idname = 'projector.flip_texture_horizontal'
    bl_label = 'Flip Texture Horizontal'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        from .helper import get_projectors
        return bool(get_projectors(context, only_selected=True))

    def execute(self, context):
        node = _get_selected_projector_image_node(context)
        if node is None:
            self.report({'WARNING'}, 'Image Texture node not found.')
            return {'CANCELLED'}

        node.texture_mapping.scale[0] *= -1.0
        node.texture_mapping.translation[0] = 1.0 - node.texture_mapping.translation[0]
        return {'FINISHED'}


class PROJECTOR_OT_flip_texture_vertical(Operator):
    """Flip custom texture vertically."""

    bl_idname = 'projector.flip_texture_vertical'
    bl_label = 'Flip Texture Vertical'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        from .helper import get_projectors
        return bool(get_projectors(context, only_selected=True))

    def execute(self, context):
        node = _get_selected_projector_image_node(context)
        if node is None:
            self.report({'WARNING'}, 'Image Texture node not found.')
            return {'CANCELLED'}

        node.texture_mapping.scale[1] *= -1.0
        node.texture_mapping.translation[1] = 1.0 - node.texture_mapping.translation[1]
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PROJECTOR_OT_switch_to_cycles)
    bpy.utils.register_class(PROJECTOR_OT_toggle_spotlight)
    bpy.utils.register_class(PROJECTOR_OT_flip_texture_horizontal)
    bpy.utils.register_class(PROJECTOR_OT_flip_texture_vertical)


def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_flip_texture_vertical)
    bpy.utils.unregister_class(PROJECTOR_OT_flip_texture_horizontal)
    bpy.utils.unregister_class(PROJECTOR_OT_toggle_spotlight)
    bpy.utils.unregister_class(PROJECTOR_OT_switch_to_cycles)
