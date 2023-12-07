from .helper import get_projectors, get_child_ID_by_type, get_child_ID_by_name
from .projector import RESOLUTIONS, Textures

import bpy
from bpy.types import Panel, PropertyGroup, UIList, Operator


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
        row.operator('projector.create',
                     icon='ADD', text="New")
        row.operator('projector.delete',
                     text='Remove', icon='REMOVE')

        if context.scene.render.engine == 'BLENDER_EEVEE':
            box = layout.box()
            box.label(text='Image Projection only works in Cycles.', icon='ERROR')
            box.operator('projector.switch_to_cycles')

        selected_projectors = get_projectors(context, only_selected=True)
        if len(selected_projectors) == 1:
            projector = selected_projectors[0]
            proj_settings = projector.proj_settings

            layout.separator()

            layout.label(text='Projector Settings:')
            box = layout.box()

            box.prop(proj_settings, 'throw_ratio')
            box.prop(proj_settings, 'power', text='Power')

            # Lens Shift
            col = box.column(align=True)
            col.prop(proj_settings, 'v_shift', text='Vertical Shift')
            col.prop(proj_settings, 'h_shift', text='Horizontal Shift')

            box.prop(data=proj_settings, property='focus_distance', text='Focus Distance',slider=True)

            #pro = col.split(factor=0.0, align=True)
            img_size = box.column(align=True, heading='Image')
            img_size.prop(proj_settings, 'w_projection', text='Image Width',slider=True)
            img_size.prop(proj_settings, 'h_projection', text='Image Height',slider=True)
            img_size.prop(proj_settings, 'd_projection', text='Image Diagonal',slider=True)
            
            p_size = box.column(align=True, heading='Projector')
            p_size.prop(proj_settings, 'projector_w', text='Projector Width',slider=True)
            p_size.prop(proj_settings, 'projector_h', text='Projector Height',slider=True)
            p_size.prop(proj_settings, 'projector_d', text='Projector Depth',slider=True)

            res_row = box.row()
            res_row.prop(proj_settings, 'resolution',
                         text='Resolution', icon='PRESET')
            if proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value and proj_settings.use_custom_texture_res:
                res_row.active = False
                res_row.enabled = False
            else:
                res_row.active = True
                res_row.enabled = True
            layout.prop(proj_settings,
                        'projected_texture', text='Project')
            # Projecton Size

            # Pixel Grid
            box.prop(proj_settings, 'show_pixel_grid')

            # Custom Texture
            if proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value:
                box = layout.box()
                box.prop(proj_settings, 'use_custom_texture_res')
                node = get_projectors(context, only_selected=True)[0].children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree.nodes['Image Texture']
                box.template_image(node, 'image', node.image_user, compact=False)


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
    bpy.utils.register_class(PROJECTOR_PT_projector_settings)
    bpy.utils.register_class(PROJECTOR_PT_projected_color)
    # Register create  in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.append(append_to_add_menu)


def unregister():
    # Register create in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.remove(append_to_add_menu)
    bpy.utils.unregister_class(PROJECTOR_PT_projected_color)
    bpy.utils.unregister_class(PROJECTOR_PT_projector_settings)
