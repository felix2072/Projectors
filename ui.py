from .helper import get_projectors, get_child_ID_by_type, get_child_ID_by_name
from .projector import RESOLUTIONS, Textures

import bpy
from bpy.types import Panel, PropertyGroup, UIList, Operator



def get_json_files(self, context):
    import os
    json_dir = os.path.join(os.path.dirname(__file__), 'json')
    if os.path.exists(json_dir):
        files = [(f, os.path.splitext(f)[0], f) for f in os.listdir(json_dir) if f.endswith('.json')]
        if not files:
            files = [('','(keine Presets gefunden)','')]
        return files
    return [('','(keine Presets gefunden)','')]


def load_json_on_select(self, context):
    # Automatisches Laden des Presets beim Auswählen im Dropdown
    if self.projector_json_file:
        import os
        json_dir = os.path.join(os.path.dirname(__file__), 'json')
        filepath = os.path.join(json_dir, self.projector_json_file)
        bpy.ops.projector.load_json(filepath=filepath)


    def get_json_files(self, context):
        import os
        json_dir = os.path.join(os.path.dirname(__file__), 'json')
        if os.path.exists(json_dir):
            files = [(f, f, f) for f in os.listdir(json_dir) if f.endswith('.json')]
            if not files:
                files = [('','(keine Presets gefunden)','')]
            return files
        return [('','(keine Presets gefunden)','')]

class PROJECTOR_PT_projector_settings(Panel):
    bl_idname = 'OBJECT_PT_projector_n_panel'
    bl_label = 'Projector'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Projector"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row(align=True)
        row.operator('projector.create', icon='ADD', text="New")
        row.operator('projector.delete', text='Remove', icon='REMOVE')

        box = None
        if context.scene.render.engine == 'BLENDER_EEVEE':
            box = layout.box()
            box.label(text='Image Projection only works in Cycles.', icon='ERROR')
            box.operator('projector.switch_to_cycles')

        selected_projectors = get_projectors(context, only_selected=True)
        if len(selected_projectors) == 1:
            layout.label(text='Preset:')
            import os
            json_dir = os.path.join(os.path.dirname(__file__), 'json')
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')] if os.path.exists(json_dir) else []

            preset_box = layout.box()
            row_json = preset_box.row(align=True)

            row_json.prop(context.scene, "projector_json_file", text="")
            """ if context.scene.projector_json_file:
                op = row_json.operator('projector.load_json', text='Load Preset', icon='IMPORT')
                op.filepath = os.path.join(json_dir, context.scene.projector_json_file) """

            row_save = preset_box.row(align=True)
            # Platzhalter: gewählter Presetname in grau, falls Feld leer
            row_save.prop(context.scene, "projector_save_name", text="")
            row_save.operator('projector.save_json', text='Save Preset', icon='EXPORT')

            layout.label(text='Projector Settings:')
            # Eigene Box für Projector-Settings
            box = layout.box()
            res_row = box.row()
            projector = selected_projectors[0]
            proj_settings = projector.proj_settings
            res_row.prop(proj_settings, 'resolution',
                         text='Resolution', icon='MOD_LENGTH')
            if proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value and proj_settings.use_custom_texture_res:
                res_row.active = False
                res_row.enabled = False
            else:
                res_row.active = True
                res_row.enabled = True
            box.prop(proj_settings,
                        'projected_texture', text='Project')
            # Projecton Size

            box.prop(proj_settings, 'power', text='Power')

            # Focus Mode Switcher
            button_row = box.row(align=True)
            button_row.prop(proj_settings, 'focus_mode', text='Auto Adjust', expand=True)

            # Tabelle für Throw Ratio
            table = box.column(align=True)
            # Header-Grid direkt vor Wertezeile
            grid = table.grid_flow(columns=4, align=True)
            # Erste Spalte (Leer)
            row1 = grid.row()
            row1.alignment = 'CENTER'
            row1.label(text='')
            # Zweite Spalte
            row2 = grid.row()
            row2.alignment = 'CENTER'
            row2.label(text='value')
            # Dritte Spalte
            row3 = grid.row()
            row3.alignment = 'CENTER'
            row3.label(text='min')
            # Vierte Spalte
            row4 = grid.row()
            row4.alignment = 'CENTER'
            row4.label(text='max')
            # Wertezeile
            row = table.row(align=True)
            row.label(text='Throw Ratio')
            row.prop(proj_settings, 'throw_ratio', text='', slider=True)
            row.prop(proj_settings, 'min_throw_ratio', text='')
            row.prop(proj_settings, 'max_throw_ratio', text='')

            lense = box.column(align=True, heading='')
            # Lens Shift
            row = lense.row(align=True)
            row.label(text='Lens Shift V')
            row.prop(proj_settings, 'v_shift', text='', slider=True)
            row.prop(proj_settings, 'min_v_shift', text='')
            row.prop(proj_settings, 'max_v_shift', text='')

            row = lense.row(align=True)
            row.label(text='Lens Shift H')
            row.prop(proj_settings, 'h_shift', text='', slider=True)
            row.prop(proj_settings, 'min_h_shift', text='')
            row.prop(proj_settings, 'max_h_shift', text='')

            # Focus Distance (immer aktiv)
            box.prop(proj_settings, 'focus_distance', text='Focus Distance', slider=True)

            # Image Size (immer aktiv)
            img_size = box.column(align=True, heading='Image')
            img_size.prop(proj_settings, 'w_projection', text='Image Width', slider=True)
            img_size.prop(proj_settings, 'h_projection', text='Image Height', slider=True)
            img_size.prop(proj_settings, 'd_projection', text='Image Diagonal', slider=True)

            # Projector Size (immer aktiv)
            p_size = box.column(align=True, heading='Projector')
            p_size.prop(proj_settings, 'projector_w', text='Projector Width', slider=True)
            p_size.prop(proj_settings, 'projector_h', text='Projector Height', slider=True)
            p_size.prop(proj_settings, 'projector_d', text='Projector Depth', slider=True)

            row = box.column(align=True)            
            row.prop(proj_settings, 'show_helper_lines', text='Helper Lines', icon='LIGHT_SPOT')
            row.prop(proj_settings, 'show_projector_cube', text='Projector Cube', icon='MESH_CUBE')
            row.prop(proj_settings, 'show_projector_spotlight', text='Spotlight', icon='OUTLINER_OB_LIGHT')
            row.prop(proj_settings, 'show_pixel_grid', text='Pixel Grid', icon='TEXTURE_DATA')

            # Custom Texture
            if proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value:
                custom_box = layout.box()
                custom_box.prop(proj_settings, 'use_custom_texture_res')
                node = get_projectors(context, only_selected=True)[0].children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree.nodes['Image Texture']
                custom_box.template_image(node, 'image', node.image_user, compact=False)


class PROJECTOR_PT_projected_color(Panel):
    bl_label = "Projected Color"
    bl_parent_id = "OBJECT_PT_projector_n_panel"
    bl_option = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(self, context):
        """ Only show if projected texture is set to  'checker'."""
        projector = context.object
        return bool(get_projectors(context, only_selected=True)) and projector.proj_settings.projected_texture == Textures.CHECKER.value

    def draw(self, context):
        projector = context.object
        layout = self.layout
        layout.use_property_decorate = False
        col = layout.column()
        col.use_property_split = True
        col.prop(projector.proj_settings, 'projected_color', text='Color')
        col.operator('projector.change_color',
                     icon='MODIFIER_ON', text='Random Color')


def append_to_add_menu(self, context):
    self.layout.operator('projector.create',
                         text='Projector', icon='CAMERA_DATA')



def register():
    import bpy
    bpy.utils.register_class(PROJECTOR_PT_projector_settings)
    bpy.utils.register_class(PROJECTOR_PT_projected_color)
    # Register create  in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.append(append_to_add_menu)
    if not hasattr(bpy.types.Scene, 'projector_json_file'):
        bpy.types.Scene.projector_json_file = bpy.props.EnumProperty(
            name="Projector Preset",
            description="Wähle eine JSON Datei zum Laden",
            items=get_json_files,
            update=load_json_on_select
        )
    if not hasattr(bpy.types.Scene, 'projector_save_name'):
        bpy.types.Scene.projector_save_name = bpy.props.StringProperty(
            name="Name",
            description="Name für die gespeicherte JSON-Datei",
            default="Preset Name"
        )


def unregister():
    # Register create in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.remove(append_to_add_menu)
    bpy.utils.unregister_class(PROJECTOR_PT_projected_color)
    bpy.utils.unregister_class(PROJECTOR_PT_projector_settings)
    if hasattr(bpy.types.Scene, 'projector_json_file'):
        del bpy.types.Scene.projector_json_file
    if hasattr(bpy.types.Scene, 'projector_save_name'):
        del bpy.types.Scene.projector_save_name
