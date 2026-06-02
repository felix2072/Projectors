import json
import os

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
    
class PROJECTOR_OT_save_json(bpy.types.Operator):
    bl_idname = "projector.save_json"
    bl_label = "Save Projector as JSON"
    bl_description = "Speichert die aktuellen Projector-Werte als JSON in /json/"

    def execute(self, context):
        selected_projectors = get_projectors(context, only_selected=True)
        if not selected_projectors:
            self.report({'WARNING'}, "No projector selected.")
            return {'CANCELLED'}
        name = getattr(context.scene, 'projector_save_name', '').strip()
        if not name:
            self.report({'ERROR'}, "Bitte einen Namen für die JSON-Datei angeben.")
            return {'CANCELLED'}
        # Dateiname bereinigen
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(addon_dir, 'json', f"{safe_name}.json")
        for projector in selected_projectors:
            if not hasattr(projector, 'proj_settings'):
                continue
            proj_settings = projector.proj_settings
            data = {}
            for prop in proj_settings.bl_rna.properties:
                if prop.identifier == 'rna_type':
                    continue
                value = getattr(proj_settings, prop.identifier)
                try:
                    json.dumps(value)
                    data[prop.identifier] = value
                except Exception:
                    data[prop.identifier] = str(value)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        self.report({'INFO'}, f"Projector gespeichert als {os.path.basename(file_path)}.")
        return {'FINISHED'}

class ProjectorSettings(bpy.types.PropertyGroup):

    # Generic clamp helper for min/max/val triplets
    def clamp_property_with_min_max(self, context, prop_name, min_name, max_name):
        min_val = getattr(self, min_name)
        max_val = getattr(self, max_name)
        # Ensure min <= max
        if min_val > max_val:
            setattr(self, max_name, min_val)
            max_val = min_val
        elif max_val < min_val:
            setattr(self, min_name, max_val)
            min_val = max_val
        # Clamp value
        val = getattr(self, prop_name)
        if val < min_val:
            setattr(self, prop_name, min_val)
        elif val > max_val:
            setattr(self, prop_name, max_val)

    def update_throw_ratio_limits(self, context):
        self.clamp_property_with_min_max(context, 'throw_ratio', 'min_throw_ratio', 'max_throw_ratio')

    def update_v_shift_limits(self, context):
        self.clamp_property_with_min_max(context, 'v_shift', 'min_v_shift', 'max_v_shift')

    def update_h_shift_limits(self, context):
        self.clamp_property_with_min_max(context, 'h_shift', 'min_h_shift', 'max_h_shift')


    min_throw_ratio: bpy.props.FloatProperty(
        name='Min Throw Ratio',
        description='Minimaler Wert für Throw Ratio',
        default=0.1,
        min=0.01,
        max=7.0,
        update=update_throw_ratio_limits,
    )  # type: ignore
    max_throw_ratio: bpy.props.FloatProperty(
        name='Max Throw Ratio',
        description='Maximaler Wert für Throw Ratio',
        default=8.0,
        min=0.05,
        max=8.0,
        update=update_throw_ratio_limits,
    )  # type: ignore

    min_v_shift: bpy.props.FloatProperty(
        name='Min Vertical Shift',
        description='Minimaler Wert für Vertical Shift',
        default=-100.0,
        min=-1000.0,
        max=1000.0,
        update=update_v_shift_limits,
    )  # type: ignore
    max_v_shift: bpy.props.FloatProperty(
        name='Max Vertical Shift',
        description='Maximaler Wert für Vertical Shift',
        default=100.0,
        min=-1000.0,
        max=1000.0,
        update=update_v_shift_limits,
    )  # type: ignore

    min_h_shift: bpy.props.FloatProperty(
        name='Min Horizontal Shift',
        description='Minimaler Wert für Horizontal Shift',
        default=-100.0,
        min=-1000.0,
        max=1000.0,
        update=update_h_shift_limits,
    )  # type: ignore
    max_h_shift: bpy.props.FloatProperty(
        name='Max Horizontal Shift',
        description='Maximaler Wert für Horizontal Shift',
        default=100.0,
        min=-1000.0,
        max=1000.0,
        update=update_h_shift_limits,
    )  # type: ignore


    def clamp_throw_ratio(self, context):
        self.clamp_property_with_min_max(context, 'throw_ratio', 'min_throw_ratio', 'max_throw_ratio')
        update_throw_ratio(self, context)

    def clamp_v_shift(self, context):
        self.clamp_property_with_min_max(context, 'v_shift', 'min_v_shift', 'max_v_shift')
        update_lens_shift(self, context)

    def clamp_h_shift(self, context):
        self.clamp_property_with_min_max(context, 'h_shift', 'min_h_shift', 'max_h_shift')
        update_lens_shift(self, context)

    throw_ratio: bpy.props.FloatProperty(
        name='Throw Ratio',
        soft_min=0.1,  # Initialwert
        soft_max=8.0,  # Initialwert
        update=clamp_throw_ratio,
        subtype='FACTOR',
    )  # type: ignore

    focus_mode: bpy.props.EnumProperty(
        name="Focus Mode",
        description="Switch between Throw Ratio and Focus Distance",
        items=[
            ('THROW_RATIO', "Throw Ratio", ""),
            ('FOCUS_DISTANCE', "Focus Distance", "")
        ],
        default='THROW_RATIO'
    )  # type: ignore

    v_shift: bpy.props.FloatProperty(
        name='Vertical Shift',
        description='Vertical Lens Shift',
        soft_min=-100,
        soft_max=100,
        update=clamp_v_shift,
    )  # type: ignore

    h_shift: bpy.props.FloatProperty(
        name='Horizontal Shift',
        description='Horizontal Lens Shift',
        soft_min=-100,
        soft_max=100,
        update=clamp_h_shift,
    )  # type: ignore

    power: bpy.props.FloatProperty(
        name='Projector Power',
        soft_min=0.01,
        soft_max=5000,
        step=10,
        update=update_power,
        unit='POWER',
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
    bpy.utils.register_class(PROJECTOR_OT_save_json)
    bpy.types.Object.proj_settings = bpy.props.PointerProperty(type=ProjectorSettings)


def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_save_json)
    bpy.utils.unregister_class(PROJECTOR_OT_change_color_randomly)
    bpy.utils.unregister_class(PROJECTOR_OT_delete_projector)
    bpy.utils.unregister_class(PROJECTOR_OT_create_projector)
    bpy.utils.unregister_class(ProjectorSettings)
