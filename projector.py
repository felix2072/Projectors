import bpy
from bpy.types import Operator

from .helper import get_projectors, random_color
from .projector_constants import PROJECTED_OUTPUTS, RESOLUTIONS, Textures
from .projector_factory import (
    add_projector_node_tree_to_spot,
    create_pixel_grid_node_group,
    create_projector,
    create_projector_textures,
    create_shape_from_verts,
    newMaterial,
    newShader,
)
from .projector_updates import (
    get_resolution,
    init_projector,
    update_checker_color,
    update_focus_distance,
    update_helper_lines_visibility,
    update_lens_shift,
    update_pixel_grid,
    update_power,
    update_projected_texture,
    update_projection_by_diagonal,
    update_projection_by_height,
    update_projection_by_width,
    update_projection_helper,
    update_projector_depth,
    update_projector_dimensions,
    update_projector_height,
    update_projector_visibility,
    update_projector_width,
    update_resolution,
    update_throw_ratio,
)

# Sichtbarkeit des Projector_Cube steuern
def update_projector_cube_visibility(proj_settings, context):
    """
    Zeigt oder versteckt den Projector_Cube je nach show_projector_cube Property.
    """
    from .helper import get_child_ID_by_name, get_projector
    projector = get_projector(context)
    if projector is None:
        return
    try:
        cube = projector.children[get_child_ID_by_name(projector.children, 'Cube')]
    except Exception:
        return
    visible = proj_settings.show_projector_cube
    cube.hide_viewport = not visible
    cube.hide_render = not visible
    update_projection_helper,
    update_projector_dimensions,
    update_projector_visibility,
    update_projector_width,
    update_projector_height,
    update_projector_depth,
    update_resolution,
    update_throw_ratio,


class PROJECTOR_OT_change_color_randomly(Operator):
    """Randomly change the color of the projected checker texture."""

    bl_idname = 'projector.change_color'
    bl_label = 'Change color of projection checker texture'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_projectors(context, only_selected=True)) == 1

    def execute(self, context):
        projectors = get_projectors(context, only_selected=True)
        new_color = random_color(alpha=True)
        for projector in projectors:
            projector.proj_settings['projected_color'] = new_color[:-1]
            update_checker_color(projector.proj_settings, context)
        return {'FINISHED'}


class PROJECTOR_OT_create_projector(Operator):
    """Create Projector"""

    bl_idname = 'projector.create'
    bl_label = 'Create a new Projector'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        projector = create_projector(context)
        init_projector(projector.proj_settings, context)
        update_projector_dimensions(projector.proj_settings, context)
        return {'FINISHED'}


class PROJECTOR_OT_delete_projector(Operator):
    """Delete Projector"""

    bl_idname = 'projector.delete'
    bl_label = 'Delete Projector'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(get_projectors(context, only_selected=True))

    def execute(self, context):
        selected_projectors = get_projectors(context, only_selected=True)
        for projector in selected_projectors:
            for child in projector.children:
                bpy.data.objects.remove(child, do_unlink=True)
            else:
                bpy.data.objects.remove(projector, do_unlink=True)
        return {'FINISHED'}


class ProjectorSettings(bpy.types.PropertyGroup):
    throw_ratio: bpy.props.FloatProperty(
        name='Throw Ratio',
        soft_min=0.1,
        soft_max=5,
        update=update_throw_ratio,
        subtype='FACTOR',
    )  # type: ignore

    power: bpy.props.FloatProperty(
        name='Projector Power',
        soft_min=0.01,
        soft_max=5000,
        step=10,
        update=update_power,
        unit='POWER',
    )  # type: ignore

    v_shift: bpy.props.FloatProperty(
        name='Vertical Shift',
        description='Vertical Lens Shift',
        soft_min=-100,
        soft_max=100,
        update=update_lens_shift,
    )  # type: ignore

    h_shift: bpy.props.FloatProperty(
        name='Horizontal Shift',
        description='Horizontal Lens Shift',
        soft_min=-100,
        soft_max=100,
        update=update_lens_shift,
    )  # type: ignore

    focus_distance: bpy.props.FloatProperty(
        name='Focus Distance',
        description='Set the focus distance in meter',
        soft_min=0.01,
        soft_max=30,
        update=update_focus_distance,
        subtype='DISTANCE',
    )  # type: ignore

    w_projection: bpy.props.FloatProperty(
        name='Projection Width',
        description='Get the projection width',
        soft_min=0,
        soft_max=10,
        update=update_projection_by_width,
        subtype='DISTANCE',
    )  # type: ignore

    h_projection: bpy.props.FloatProperty(
        name='Projection Height',
        description='Get the projection height',
        soft_min=0,
        soft_max=10,
        update=update_projection_by_height,
        subtype='DISTANCE',
    )  # type: ignore

    d_projection: bpy.props.FloatProperty(
        name='Projection Diagonal',
        description='Get the projection diagonal',
        soft_min=0,
        soft_max=10,
        update=update_projection_by_diagonal,
        subtype='DISTANCE',
    )  # type: ignore

    projector_w: bpy.props.FloatProperty(
        name='Projector Width',
        description='Set the width of the projector',
        soft_min=0.1,
        soft_max=1,
        update=update_projector_width,
        subtype='DISTANCE',
        unit='LENGTH',
    )  # type: ignore

    projector_h: bpy.props.FloatProperty(
        name='Projector Height',
        description='Set the height of the projector',
        soft_min=0.1,
        soft_max=1,
        update=update_projector_height,
        subtype='DISTANCE',
    )  # type: ignore

    projector_d: bpy.props.FloatProperty(
        name='Projector Depth',
        description='Set the depth of the projector',
        soft_min=0.1,
        soft_max=1,
        update=update_projector_depth,
        subtype='DISTANCE',
    )  # type: ignore

    resolution: bpy.props.EnumProperty(
        items=RESOLUTIONS,
        default='1920x1080',
        description='Select a Resolution for your Projector',
        update=update_resolution,
    )  # type: ignore

    use_custom_texture_res: bpy.props.BoolProperty(
        name='Let Image Define Projector Resolution',
        default=True,
        description='Use the resolution from the image as the projector resolution. Warning: After selecting a new image toggle this checkbox to update',
        update=update_throw_ratio,
    )  # type: ignore

    projected_color: bpy.props.FloatVectorProperty(
        subtype='COLOR',
        update=update_checker_color,
    )  # type: ignore

    projected_texture: bpy.props.EnumProperty(
        items=PROJECTED_OUTPUTS,
        default=Textures.CHECKER.value,
        description='What do you to project?',
        update=update_throw_ratio,
    )  # type: ignore

    show_pixel_grid: bpy.props.BoolProperty(
        name='Show Pixel Grid',
        description='When checked the image is divided into a pixel grid with the dimensions of the image resolution.',
        default=False,
        update=update_pixel_grid,
    )  # type: ignore

    show_helper_lines: bpy.props.BoolProperty(
        name='Lines',
        description='Helper lines visible in the viewport and render',
        default=True,
        update=update_helper_lines_visibility,
    )  # type: ignore

    show_projector_cube: bpy.props.BoolProperty(
        name='Cube',
        description='Projector Cube visible in the viewport and render',
        default=True,
        update=update_projector_cube_visibility,
    )  # type: ignore

    show_projector_spotlight: bpy.props.BoolProperty(
        name='Spotlight',
        description='Projector Light visible in the viewport and render',
        default=True,
        update=lambda self, context: update_projector_spotlight_visibility(self, context),
    )  # type: ignore
# Sichtbarkeit des Projector_Spotlight steuern
def update_projector_spotlight_visibility(proj_settings, context):
    """
    Zeigt oder versteckt den Projector_Spotlight je nach show_projector_spotlight Property.
    """
    from .helper import get_child_ID_by_name, get_projector
    projector = get_projector(context)
    if projector is None:
        return
    try:
        spot = projector.children[get_child_ID_by_name(projector.children, 'Projector_Spotlight')]
    except Exception:
        return
    visible = proj_settings.show_projector_spotlight
    spot.hide_viewport = not visible
    spot.hide_render = not visible


def register():
    bpy.utils.register_class(ProjectorSettings)
    bpy.utils.register_class(PROJECTOR_OT_create_projector)
    bpy.utils.register_class(PROJECTOR_OT_delete_projector)
    bpy.utils.register_class(PROJECTOR_OT_change_color_randomly)
    bpy.types.Object.proj_settings = bpy.props.PointerProperty(type=ProjectorSettings)


def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_change_color_randomly)
    bpy.utils.unregister_class(PROJECTOR_OT_delete_projector)
    bpy.utils.unregister_class(PROJECTOR_OT_create_projector)
    bpy.utils.unregister_class(ProjectorSettings)
