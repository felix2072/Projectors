import logging
import math
import os
import random

from enum import Enum
import bpy
from bpy import context, data, ops
from bpy.types import Operator

from .helper import (ADDON_ID, auto_offset,
                     get_projectors, get_projector, get_child_ID_by_name, get_child_ID_by_type, random_color)

logging.basicConfig(
    format='[ProjectorForks Addon]: %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(name=__file__)


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
    ('1000x2000', 'Landscape (1000x2000) 1:2', '', 14),
    # 2:1 aspect ratio
    ('2000x1000', 'Portrait (2000x1000) 2:1', '', 15)
]

PROJECTED_OUTPUTS = [(Textures.CHECKER.value, 'Checker', '', 1),
                     (Textures.COLOR_GRID.value, 'Color Grid', '', 2),
                     (Textures.CUSTOM_TEXTURE.value, 'Custom Texture', '', 3)]


class PROJECTOR_OT_change_color_randomly(Operator):
    """ Randomly change the color of the projected checker texture."""
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


def create_projector_textures():
    """ This function checks if the needed images exist and if not creates them. """
    name_template = '_proj.tex.{}'
    for res in RESOLUTIONS:
        img_name = name_template.format(res[0])
        w, h = res[0].split('x')
        if not bpy.data.images.get(img_name):
            log.debug(f'Create projection texture: {res}')
            bpy.ops.image.new(name=img_name,
                              width=int(w),
                              height=int(h),
                              color=(0.0, 0.0, 0.0, 1.0),
                              alpha=True,
                              generated_type='COLOR_GRID',
                              float=False)

        bpy.data.images[img_name].use_fake_user = True


def add_projector_node_tree_to_spot(spot):
    """
    This function turns a spot light into a projector.
    This is achieved through a texture on the spot light and some basic math.
    """

    spot.data.use_nodes = True
    root_tree = spot.data.node_tree
    root_tree.nodes.clear()

    node_group = bpy.data.node_groups.new('_Projector', 'ShaderNodeTree')

    # Create output sockets for the node group.
    if(bpy.app.version >= (4, 0)):
        node_group.interface.new_socket('texture vector',  in_out="OUTPUT", socket_type='NodeSocketVector')
        node_group.interface.new_socket('color', in_out="OUTPUT", socket_type='NodeSocketColor')
    else:
        output = node_group.outputs
        output.new('NodeSocketVector', 'texture vector')
        output.new('NodeSocketColor', 'color')

    # # Inside Group Node #
    # #####################

    # Hold important nodes inside a group node.
    group = spot.data.node_tree.nodes.new('ShaderNodeGroup')
    group.node_tree = node_group
    group.label = "!! Don't touch !!"

    nodes = group.node_tree.nodes
    tree = group.node_tree

    auto_pos = auto_offset()

    tex = nodes.new('ShaderNodeTexCoord')
    tex.location = auto_pos(200)

    geo = nodes.new('ShaderNodeNewGeometry')
    geo.location = auto_pos(0, -300)
    vec_transform = nodes.new('ShaderNodeVectorTransform')
    vec_transform.location = auto_pos(200)
    vec_transform.vector_type = 'NORMAL'

    map_1 = nodes.new('ShaderNodeMapping')
    map_1.vector_type = 'TEXTURE'
    # Flip the image horizontally and vertically to display it the intended way.
    if bpy.app.version < (2, 81):
        map_1.scale[0] = -1
        map_1.scale[1] = -1
    else:
        map_1.inputs[3].default_value[0] = -1
        map_1.inputs[3].default_value[1] = -1
    map_1.location = auto_pos(200)

    sep = nodes.new('ShaderNodeSeparateXYZ')
    sep.location = auto_pos(350)

    div_1 = nodes.new('ShaderNodeMath')
    div_1.operation = 'DIVIDE'
    div_1.name = ADDON_ID + 'div_01'
    div_1.location = auto_pos(200)

    div_2 = nodes.new('ShaderNodeMath')
    div_2.operation = 'DIVIDE'
    div_2.name = ADDON_ID + 'div_02'
    div_2.location = auto_pos(y=-200)

    com = nodes.new('ShaderNodeCombineXYZ')
    com.inputs['Z'].default_value = 1.0
    com.location = auto_pos(200)

    map_2 = nodes.new('ShaderNodeMapping')
    map_2.location = auto_pos(200)
    map_2.vector_type = 'TEXTURE'

    add = nodes.new('ShaderNodeMixRGB')
    add.blend_type = 'ADD'
    add.inputs[0].default_value = 1
    add.location = auto_pos(350)

    # Texture
    # a) Image
    img = nodes.new('ShaderNodeTexImage')
    img.extension = 'CLIP'
    img.location = auto_pos(200)

    # b) Generated checker texture.
    checker_tex = nodes.new('ShaderNodeTexChecker')
    # checker_tex.inputs['Color2'].default_value = random_color(alpha=True)
    checker_tex.inputs[3].default_value = 8
    checker_tex.inputs[1].default_value = (1, 1, 1, 1)
    checker_tex.location = auto_pos(y=-300)

    mix_rgb = nodes.new('ShaderNodeMixRGB')
    mix_rgb.name = 'Mix.001'
    mix_rgb.inputs[1].default_value = (0, 0, 0, 0)
    mix_rgb.location = auto_pos(200, y=-300)

    group_output_node = node_group.nodes.new('NodeGroupOutput')
    group_output_node.location = auto_pos(200)

    # # Root Nodes #
    # ##############
    auto_pos_root = auto_offset()
    # Image Texture
    user_texture = root_tree.nodes.new('ShaderNodeTexImage')
    user_texture.extension = 'CLIP'
    user_texture.label = 'Add your Image Texture or Movie here'
    user_texture.location = auto_pos_root(200, y=200)
    # Emission
    emission = root_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 1
    emission.location = auto_pos_root(300)
    # Material Output
    output = root_tree.nodes.new('ShaderNodeOutputLight')
    output.location = auto_pos_root(200)

    # # LINK NODES #
    # ##############

    # Link inside group node
    if(bpy.app.version >= (4, 0)):
        tree.links.new(geo.outputs['Incoming'], vec_transform.inputs['Vector'])
        tree.links.new(vec_transform.outputs['Vector'], map_1.inputs['Vector'])
    else:
        tree.links.new(tex.outputs['Normal'], map_1.inputs['Vector'])
    tree.links.new(map_1.outputs['Vector'], sep.inputs['Vector'])

    tree.links.new(sep.outputs[0], div_1.inputs[0])  # X -> value0
    tree.links.new(sep.outputs[2], div_1.inputs[1])  # Z -> value1
    tree.links.new(sep.outputs[1], div_2.inputs[0])  # Y -> value0
    tree.links.new(sep.outputs[2], div_2.inputs[1])  # Z -> value1

    tree.links.new(div_1.outputs[0], com.inputs[0])
    tree.links.new(div_2.outputs[0], com.inputs[1])

    tree.links.new(com.outputs['Vector'], map_2.inputs['Vector'])

    # Textures
    # a) generated texture
    tree.links.new(map_2.outputs['Vector'], add.inputs['Color1'])
    tree.links.new(add.outputs['Color'], img.inputs['Vector'])
    tree.links.new(add.outputs['Color'], group_output_node.inputs[0])
    # b) checker texture
    tree.links.new(add.outputs['Color'], checker_tex.inputs['Vector'])
    tree.links.new(img.outputs['Alpha'], mix_rgb.inputs[0])
    tree.links.new(checker_tex.outputs['Color'], mix_rgb.inputs[2])

    # Link in root
    root_tree.links.new(group.outputs['texture vector'], user_texture.inputs['Vector'])
    root_tree.links.new(group.outputs['color'], emission.inputs['Color'])
    root_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

    # Pixel Grid Setup
    pixel_grid_group = create_pixel_grid_node_group()
    pixel_grid_node = spot.data.node_tree.nodes.new('ShaderNodeGroup')
    pixel_grid_node.node_tree = pixel_grid_group
    pixel_grid_node.label = "Pixel Grid"
    pixel_grid_node.name = 'pixel_grid'
    loc = root_tree.nodes['Emission'].location
    pixel_grid_node.location = (loc[0], loc[1] - 150)

    root_tree.links.new(group.outputs[0], pixel_grid_node.inputs[1])
    root_tree.links.new(emission.outputs[0], pixel_grid_node.inputs[0])

def get_resolution(proj_settings, context):
    """ Find out what resolution is currently used and return it.
    Resolution from the dropdown or the resolution from the custom texture.
    """
    if proj_settings.use_custom_texture_res and proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value:
        projector = get_projector(context)
        root_tree = projector.children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree
        image = root_tree.nodes['Image Texture'].image
        if image:
            w = image.size[0]
            h = image.size[1]
        else:
            w, h = 300, 300
    else:
        w, h = proj_settings.resolution.split('x')

    return float(w), float(h)


def update_throw_ratio(proj_settings, context):
    """
    Adjust some settings on a camera to achieve a throw ratio
    """
    projector = get_projector(context)
    # Update properties of the camera.
    throw_ratio = proj_settings.throw_ratio
    focus_distance = proj_settings.focus_distance
    projector.data.lens = 10*throw_ratio
    #projector.data.display_size = 1.0/throw_ratio*focus_distance

    # Adjust Texture to fit new camera ###
    w, h = get_resolution(proj_settings, context)
    aspect_ratio = w/h
    inverted_aspect_ratio = 1/aspect_ratio

    # Projected Texture
    update_projected_texture(proj_settings, context)

    # Update spotlight properties.
    spot = projector.children[get_child_ID_by_type(projector.children,'LIGHT')]
    nodes = spot.data.node_tree.nodes['Group'].node_tree.nodes
    if bpy.app.version < (2, 81):
        nodes['Mapping'].scale[0] = 1 / throw_ratio
        nodes['Mapping'].scale[1] = 1 / throw_ratio * inverted_aspect_ratio
    else:
        nodes['Mapping'].inputs[3].default_value[0] = 1 / throw_ratio
        nodes['Mapping'].inputs[3].default_value[1] = 1 / \
            throw_ratio * inverted_aspect_ratio
        
    update_lens_shift(proj_settings,context)
    update_projection_helper(proj_settings, context)

def update_focus_distance(proj_settings, context):
    projector = get_projector(context)
    throw_ratio = proj_settings.throw_ratio
    focus_distance = proj_settings.focus_distance
    #projector.data.display_size = 1/throw_ratio*focus_distance
    update_projection_helper(proj_settings, context)

def update_lens_shift(proj_settings, context):
    """
    Apply the shift to the camera and texture.
    """
    projector = get_projector(context)
    h_shift = proj_settings.get('h_shift', 0.0) / 100
    v_shift = proj_settings.get('v_shift', 0.0) / 100
    throw_ratio = proj_settings.get('throw_ratio')

    w, h = get_resolution(proj_settings, context)
    v_shift_factor = h/w*v_shift

    # Update the properties of the camera.
    cam = projector
    cam.data.shift_x = h_shift
    cam.data.shift_y = v_shift_factor

    # Update spotlight node setup.
    spot = projector.children[get_child_ID_by_type(projector.children,'LIGHT')]
    nodes = spot.data.node_tree.nodes['Group'].node_tree.nodes
    if bpy.app.version < (2, 81):
        nodes['Mapping.001'].translation[0] = h_shift / throw_ratio
        nodes['Mapping.001'].translation[1] = v_shift_factor / throw_ratio
    else:
        nodes['Mapping.001'].inputs[1].default_value[0] = h_shift / throw_ratio
        nodes['Mapping.001'].inputs[1].default_value[1] = v_shift_factor / throw_ratio
    update_projection_helper(proj_settings, context)

def update_projection_by_width(proj_settings, context):
    w_projection = proj_settings.w_projection
    #proj_settings.throw_ratio = w_projection
    

def update_projection_by_height(proj_settings, context):
    h_projection = proj_settings.h_projection
    #proj_settings.throw_ratio = h_projection*0.1
    #update_throw_ratio(proj_settings, context)

def update_projection_by_diagonal(proj_settings, context):
    d_projection = proj_settings.d_projection
    #proj_settings.throw_ratio = d_projection*0.1
    #update_throw_ratio(proj_settings, context)

def update_projector_width(proj_settings, context):
    projector = get_projector(context)
    projector_cube = projector.children[get_child_ID_by_name(projector.children,'Cube')]
    projector_cube.dimensions[0] = proj_settings.projector_w*0.01

def update_projector_height(proj_settings, context):
    projector = get_projector(context)
    projector_cube = projector.children[get_child_ID_by_name(projector.children,'Cube')]
    projector_cube.dimensions[1] = proj_settings.projector_h*0.01

def update_projector_depth(proj_settings, context):
    projector = get_projector(context)
    projector_cube = projector.children[get_child_ID_by_name(projector.children,'Cube')]
    projector_cube.dimensions[2] = proj_settings.projector_d*0.01
    projector_cube.location[2] = projector_cube.dimensions[2]/2

def update_projector_dimensions(proj_settings, context):
    projector = get_projector(context)
    projector_cube = projector.children[get_child_ID_by_name(projector.children,'Cube')]
    projector_cube.scale = (proj_settings.projector_w*0.01,proj_settings.projector_h*0.01,proj_settings.projector_d*0.01)
    projector_cube.location[2] = projector_cube.dimensions[2]/2

def update_resolution(proj_settings, context):
    projector = get_projector(context)
    nodes = projector.children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree.nodes['Group'].node_tree.nodes
    # Change resolution image texture
    nodes['Image Texture'].image = bpy.data.images[f'_proj.tex.{proj_settings.resolution}']
    update_throw_ratio(proj_settings, context)
    update_pixel_grid(proj_settings, context)
    update_projection_helper(proj_settings, context)


def update_checker_color(proj_settings, context):
    # Update checker texture color
    projector = get_projector(context)
    nodes = get_projector(
        context).children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree.nodes['Group'].node_tree.nodes
    c = proj_settings.projected_color
    nodes['Checker Texture'].inputs['Color2'].default_value = [c.r, c.g, c.b, 1]


def update_power(proj_settings, context):
    # Update spotlight power
    projector = get_projector(context)
    spot = get_projector(context).children[get_child_ID_by_type(projector.children,'LIGHT')]
    spot.data.energy = proj_settings["power"]


def update_pixel_grid(proj_settings, context):
    """ Update the pixel grid. Meaning, make it visible by linking the right node and updating the resolution. """
    
    projector = get_projector(context)
    root_tree = get_projector(context).children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree
    nodes = root_tree.nodes
    pixel_grid_nodes = nodes['pixel_grid'].node_tree.nodes
    width, height = get_resolution(proj_settings, context)
    pixel_grid_nodes['_width'].outputs[0].default_value = width
    pixel_grid_nodes['_height'].outputs[0].default_value = height
    if proj_settings.show_pixel_grid:
        root_tree.links.new(nodes['pixel_grid'].outputs[0], nodes['Light Output'].inputs[0])
    else:
        root_tree.links.new(nodes['Emission'].outputs[0], nodes['Light Output'].inputs[0])

def update_projection_helper(proj_settings, context):
    
    projector = get_projector(context)
    #curve = projector.children.name.startswith('Projector.Plane')
    curve = projector.children[get_child_ID_by_name(projector.children,'Plane')]

    # todo: set transformation back to zero
    """ curve.delta_location((0.0, 0.0, 0.0))
    curve.delta_rotation_euler((0.0, 0.0, 0.0), 'XYZ') """

    pn = curve.data.splines[0].points
    """ end_point_idx = (len(obj.data.splines[0].points) - 1)
    pn[end_point_idx].select = True """

    throw_ratio = proj_settings.throw_ratio
    focus_distance = proj_settings.focus_distance
    resolution = proj_settings.resolution
    cut = resolution.index('x')
    w = float(proj_settings.resolution[0:cut])
    h = float(proj_settings.resolution[cut+1:])
    factor = focus_distance*1/throw_ratio/2
    
    w, h = get_resolution(proj_settings, context)
    h_shift = proj_settings.get('h_shift', 0.0) / 100
    v_shift = proj_settings.get('v_shift', 0.0) / 100
    v_shift_factor = h/w*v_shift / throw_ratio

    pn[0].co.x = -factor+h_shift
    pn[0].co.y = h/w*factor+v_shift_factor
    pn[0].co.z = -focus_distance

    pn[1].co.x = factor+h_shift
    pn[1].co.y = h/w*factor+v_shift_factor
    pn[1].co.z = -focus_distance

    pn[2].co.x = factor+h_shift
    pn[2].co.y = -(h/w*factor)+v_shift_factor
    pn[2].co.z = -focus_distance

    pn[3].co.x = -factor+h_shift
    pn[3].co.y = -(h/w*factor)+v_shift_factor
    pn[3].co.z = -focus_distance

    pn[4].co.x = pn[0].co.x
    pn[4].co.y = pn[0].co.y
    pn[4].co.z = pn[0].co.z

    pn[5].co = ((0.0,0.0,0.0,0.0))
    pn[6].co = ((pn[1].co.x,pn[1].co.y,pn[1].co.z,0.0))
    pn[7].co = ((0.0,0.0,0.0,0.0))
    pn[8].co = ((pn[2].co.x,pn[2].co.y,pn[2].co.z,0.0))
    pn[9].co = ((0.0,0.0,0.0,0.0))
    pn[10].co = ((pn[3].co.x,pn[3].co.y,pn[3].co.z,0.0))
    pn[11].co = ((0.0,0.0,0.0,0.0))
    pn[12].co = ((0.0,0.0,0.0,0.0))
    pn[13].co = ((0.0,0.0,0.0,0.0))
    pn[14].co = ((0.0,0.0,0.0,0.0))
    pn[15].co = ((0.0,0.0,0.0,0.0))
    pn[16].co = ((0.0,0.0,0.0,0.0))
    

    proj_settings.w_projection = (pn[0].co - pn[1].co).length
    proj_settings.h_projection = (pn[1].co - pn[2].co).length
    proj_settings.d_projection = (pn[0].co - pn[2].co).length

def update_projector_visibility(context):
    projector = get_projector(context)
    projector.hide_viewport = False
    projector.hide_render = False

def create_pixel_grid_node_group():
    node_group = bpy.data.node_groups.new(
        '_Projectors-Addon_PixelGrid', 'ShaderNodeTree')

    # Create input/output sockets for the node group.
    if(bpy.app.version >= (4, 0)):
        node_group.interface.new_socket('Shader', socket_type='NodeSocketShader')
        node_group.interface.new_socket('Vector', socket_type='NodeSocketVector')

        node_group.interface.new_socket('Shader', in_out='OUTPUT', socket_type='NodeSocketShader')
    else:
        inputs = node_group.inputs
        inputs.new('NodeSocketShader', 'Shader')
        inputs.new('NodeSocketVector', 'Vector')

        outputs = node_group.outputs
        outputs.new('NodeSocketShader', 'Shader')

    nodes = node_group.nodes

    auto_pos = auto_offset()

    group_input = nodes.new('NodeGroupInput')
    group_input.location = auto_pos(200)

    sepXYZ = nodes.new('ShaderNodeSeparateXYZ')
    sepXYZ.location = auto_pos(200)

    in_width = nodes.new('ShaderNodeValue')
    in_width.name = '_width'
    in_width.label = 'Width'
    in_width.location = auto_pos(100)

    in_height = nodes.new('ShaderNodeValue')
    in_height.name = '_height'
    in_height.label = 'Height'
    in_height.location = auto_pos(y=-200)

    mul1 = nodes.new('ShaderNodeMath')
    mul1.operation = 'MULTIPLY'
    mul1.location = auto_pos(100)

    mul2 = nodes.new('ShaderNodeMath')
    mul2.operation = 'MULTIPLY'
    mul2.location = auto_pos(y=-200)

    mod1 = nodes.new('ShaderNodeMath')
    mod1.operation = 'MODULO'
    mod1.inputs[1].default_value = 1
    mod1.location = auto_pos(100)

    mod2 = nodes.new('ShaderNodeMath')
    mod2.operation = 'MODULO'
    mod2.inputs[1].default_value = 1
    mod2.location = auto_pos(y=-200)

    col_ramp1 = nodes.new('ShaderNodeValToRGB')
    col_ramp1.color_ramp.elements[1].position = 0.025
    col_ramp1.color_ramp.interpolation = 'CONSTANT'
    col_ramp1.location = auto_pos(100)

    col_ramp2 = nodes.new('ShaderNodeValToRGB')
    col_ramp2.color_ramp.elements[1].position = 0.025
    col_ramp2.color_ramp.interpolation = 'CONSTANT'
    col_ramp2.location = auto_pos(y=-200)

    mix_rgb = nodes.new('ShaderNodeMixRGB')
    mix_rgb.use_clamp = True
    mix_rgb.blend_type = 'MULTIPLY'
    mix_rgb.inputs[0].default_value = 1
    mix_rgb.location = auto_pos(200)
    
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = auto_pos(y=-200)

    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = auto_pos(100)

    group_output = nodes.new('NodeGroupOutput')
    group_output.location = auto_pos(100)
    
    # Link Nodes
    links = node_group.links

    links.new(group_input.outputs[0], mix_shader.inputs[2])
    links.new(group_input.outputs[1], sepXYZ.inputs[0])

    links.new(in_width.outputs[0], mul1.inputs[1])
    links.new(in_height.outputs[0], mul2.inputs[1])

    links.new(sepXYZ.outputs[0], mul1.inputs[0])
    links.new(sepXYZ.outputs[1], mul2.inputs[0])

    links.new(mul1.outputs[0], mod1.inputs[0])
    links.new(mul2.outputs[0], mod2.inputs[0])

    links.new(mod1.outputs[0], col_ramp1.inputs[0])
    links.new(mod2.outputs[0], col_ramp2.inputs[0])

    links.new(col_ramp1.outputs[0], mix_rgb.inputs[1])
    links.new(col_ramp2.outputs[0], mix_rgb.inputs[2])

    links.new(mix_rgb.outputs[0], mix_shader.inputs[0])
    links.new(transparent.outputs[0], mix_shader.inputs[1])

    links.new(mix_shader.outputs[0], group_output.inputs[0])

    return node_group
    

def create_projector(context):
    """
    Create a new projector composed out of a camera (parent obj) and a spotlight (child not intended for user interaction).
    The camera is the object intended for the user to manipulate and custom properties are stored there.
    The spotlight with a custom nodetree is responsible for actual projection of the texture.
    """
    create_projector_textures()
    log.debug('Creating projector.')

    # Create a camera and a spotlight
    # ### Spot Light ###
    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0))
    spot = context.object
    spot.name = 'Projector_Spotlight'
    spot.scale = (.01, .01, .01)
    spot.data.spot_size = math.pi - 0.001
    spot.data.spot_blend = 0
    spot.data.shadow_soft_size = 0.0
    spot.hide_select = True
    spot[ADDON_ID.format('spot')] = True
    spot.data.cycles.use_multiple_importance_sampling = False
    add_projector_node_tree_to_spot(spot)

    # ### Camera ###
    bpy.ops.object.camera_add(enter_editmode=False,
                              location=(0, 0, 0),
                              rotation=(0, 0, 0))
    cam = context.object
    cam.name = 'Projector_Camera.001'
    cam.data.lens_unit = 'MILLIMETERS'
    cam.data.sensor_width = 10
    cam.data.display_size = 0.01

    #cam.hide_render = False

    # Parent light to cam.
    spot.parent = cam

    # Move newly create projector (cam and spotlight) to 3D-Cursor position.
    cam.location = context.scene.cursor.location
    #cam.rotation_euler = context.scene.cursor.rotation_euler
    cam.rotation_euler = rotation=(math.pi*0.5, 0, 0)

    bpy.ops.curve.primitive_nurbs_path_add(radius=1, enter_editmode=True)
    obj = bpy.context.object

    obj.name = "Projector_Plane"

    # De-select all points
    for pn in obj.data.splines[0].points:
        pn.select = False

    # Select the last point
    pn = obj.data.splines[0].points
    """ end_point_idx = (len(obj.data.splines[0].points) - 1)
    pn[end_point_idx].select = True """

    pn[0].co.x = -1.0
    pn[0].co.y = 1.0
    pn[1].co.x = 1.0
    pn[1].co.y = 1.0
    pn[2].co.x = 1.0
    pn[2].co.y = -1.0
    pn[3].co.x = -1.0
    pn[3].co.y = -1.0
    pn[4].co.x = -1.0
    pn[4].co.y = 1.0

    obj = bpy.context.object

    # how to delete points
    """splines     = obj.data.splines
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.curve.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')

    line0       = splines[0]
    pt          = line0.points[4]
    pt.select   = True 
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.curve.delete(type='VERT')"""


    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.subdivide()
    bpy.ops.curve.subdivide()
    bpy.ops.curve.handle_type_set(type='VECTOR')
    bpy.ops.curve.spline_type_set(type='POLY')
    bpy.ops.object.mode_set(mode = 'OBJECT')



    """ bpy.ops.curve.extrude_move(CURVE_OT_extrude={"mode":'TRANSLATION'},
    TRANSFORM_OT_translate={"value":(0, 2, 0)}) """

    """ objects = bpy.data.objects
    basic_cube = objects['Cube']
    basic_cube.parent = cam """
    # Create a bezier circle and enter edit mode.
    """ ops.curve.primitive_bezier_circle_add(radius=1.0,
                                        location=(0.0, 0.0, 0.0),
                                        enter_editmode=True)
    
    
    #cut
    #ops.curve.subdivide(number_cuts=1)
    
    ops.transform.vertex_random(offset=1.0, uniform=0.1, normal=0.0, seed=0)

    # Scale the curve while in edit mode.
    ops.transform.resize(value=(2.0, 2.0, 3.0))

    # Return to object mode.
    ops.object.mode_set(mode='OBJECT')  """

    # Paren Curve to Cam
    curves = context.object
    curves.parent = cam

    bpy.ops.mesh.primitive_cube_add(enter_editmode=False,align='WORLD',location=(0,0,0),scale=(1,1,1))
    projector_cube = bpy.context.object
    projector_cube.name = 'Projector_Cube'
    projector_cube.dimensions = (1,1,1)
    projector_cube.visible_shadow = False
    projector_cube.parent = cam

    bpy.context.view_layer.objects.active = cam
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[cam.name].select_set(True)
    cam = context.object
    return cam


def init_projector(proj_settings, context):
    # # Add custom properties to store projector settings on the camera obj.
    proj_settings.throw_ratio = 1.0
    proj_settings.power = 100.0
    proj_settings.v_shift = 0.0
    proj_settings.h_shift = 0.0
    proj_settings.focus_distance = 1.0
    proj_settings.projector_w = 52.0
    proj_settings.projector_h = 14.0
    proj_settings.projector_d = 48.0
    proj_settings.projected_texture = Textures.CHECKER.value
    proj_settings.projected_color = random_color()
    proj_settings.resolution = '1920x1080'
    proj_settings.use_custom_texture_res = True

    # Init Projector
    update_throw_ratio(proj_settings, context)
    update_projected_texture(proj_settings, context)
    update_resolution(proj_settings, context)
    update_checker_color(proj_settings, context)
    update_lens_shift(proj_settings, context)
    update_power(proj_settings, context)
    update_pixel_grid(proj_settings, context)
    update_projection_helper(proj_settings, context)
    update_projector_visibility(context)
    update_projector_dimensions(proj_settings, context)


class PROJECTOR_OT_create_projector(Operator):
    """ Create Projector """
    bl_idname = 'projector.create'
    bl_label = 'Create a new Projector'
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        projector = create_projector(context)
        init_projector(projector.proj_settings, context)
        return {'FINISHED'}


def update_projected_texture(proj_settings, context):
    """ Update the projected output source. """
    projector = get_projectors(context, only_selected=True)[0]
    root_tree = projector.children[get_child_ID_by_type(projector.children,'LIGHT')].data.node_tree
    group_tree = root_tree.nodes['Group'].node_tree
    group_output_node = group_tree.nodes['Group Output']
    group_node = root_tree.nodes['Group']
    emission_node = root_tree.nodes['Emission']

    # Switch between the three possible cases by relinking some nodes.
    case = proj_settings.projected_texture
    if case == Textures.CHECKER.value:
        mix_node = group_tree.nodes['Mix.001']
        group_tree.links.new(
            mix_node.outputs['Color'], group_output_node.inputs[1])
        root_tree.links.new(group_node.outputs[1], emission_node.inputs[0])
    elif case == Textures.COLOR_GRID.value:
        img_node = group_tree.nodes['Image Texture']
        group_tree.links.new(img_node.outputs[0], group_output_node.inputs[1])
        root_tree.links.new(group_node.outputs[1], emission_node.inputs[0])
    elif case == Textures.CUSTOM_TEXTURE.value:
        custom_tex_node = root_tree.nodes['Image Texture']
        root_tree.links.new(
            custom_tex_node.outputs[0], emission_node.inputs[0])


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
        name="Throw Ratio",
        soft_min=0.1, soft_max=5,
        update=update_throw_ratio,
        subtype='FACTOR') # type: ignore

    power: bpy.props.FloatProperty(
        name="Projector Power",
        soft_min=0.01, soft_max=30,
        update=update_power,
        unit='POWER') # type: ignore

    v_shift: bpy.props.FloatProperty(
        name="Vertical Shift",
        description="Vertical Lens Shift",
        soft_min=-100, soft_max=100,
        update=update_lens_shift,
        subtype='PERCENTAGE') # type: ignore

    h_shift: bpy.props.FloatProperty(
        name="Horizontal Shift",
        description="Horizontal Lens Shift",
        soft_min=-100, soft_max=100,
        update=update_lens_shift,
        subtype='PERCENTAGE') # type: ignore

    focus_distance: bpy.props.FloatProperty(
        name="Focus Distance",
        description="Set the focus distance in meter",
        soft_min=0.01, soft_max=30,
        update=update_focus_distance,
        subtype='DISTANCE') # type: ignore

    w_projection: bpy.props.FloatProperty(
        name="Projection Width",
        description="Get the projection width",
        soft_min=0, soft_max=10,
        update=update_projection_by_width,
        subtype='DISTANCE') # type: ignore

    h_projection: bpy.props.FloatProperty(
        name="Projection Height",
        description="Get the projection height",
        soft_min=0, soft_max=10,
        update=update_projection_by_height,
        subtype='DISTANCE') # type: ignore

    d_projection: bpy.props.FloatProperty(
        name="Projection Diagonal",
        description="Get the projection diagonal",
        soft_min=0, soft_max=10,
        update=update_projection_by_diagonal,
        subtype='DISTANCE') # type: ignore
    
    projector_w: bpy.props.FloatProperty(
        name="Projector Width",
        description="Set the width of the projector",
        soft_min=0, soft_max=100,
        update=update_projector_width) # type: ignore

    projector_h: bpy.props.FloatProperty(
        name="Projector Height",
        description="Set the height of the projector",
        soft_min=0, soft_max=50,
        update=update_projector_height,
        subtype='DISTANCE') # type: ignore
    
    projector_d: bpy.props.FloatProperty(
        name="Projector Depth",
        description="Set the depth of the projector",
        soft_min=0, soft_max=100,
        update=update_projector_depth,
        subtype='DISTANCE') # type: ignore
    
    resolution: bpy.props.EnumProperty(
        items=RESOLUTIONS,
        default='1920x1080',
        description="Select a Resolution for your Projector",
        update=update_resolution) # type: ignore

    use_custom_texture_res: bpy.props.BoolProperty(
        name="Let Image Define Projector Resolution",
        default=True,
        description="Use the resolution from the image as the projector resolution. Warning: After selecting a new image toggle this checkbox to update",
        update=update_throw_ratio) # type: ignore

    projected_color: bpy.props.FloatVectorProperty(
        subtype='COLOR',
        update=update_checker_color) # type: ignore

    projected_texture: bpy.props.EnumProperty(
        items=PROJECTED_OUTPUTS,
        default=Textures.CHECKER.value,
        description="What do you to project?",
        update=update_throw_ratio) # type: ignore

    show_pixel_grid: bpy.props.BoolProperty(
        name="Show Pixel Grid",
        description="When checked the image is divided into a pixel grid with the dimensions of the image resolution.",
        default=False,
        update=update_pixel_grid) # type: ignore


def register():
    bpy.utils.register_class(ProjectorSettings)
    bpy.utils.register_class(PROJECTOR_OT_create_projector)
    bpy.utils.register_class(PROJECTOR_OT_delete_projector)
    bpy.utils.register_class(PROJECTOR_OT_change_color_randomly)
    bpy.types.Object.proj_settings = bpy.props.PointerProperty(
        type=ProjectorSettings)


def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_change_color_randomly)
    bpy.utils.unregister_class(PROJECTOR_OT_delete_projector)
    bpy.utils.unregister_class(PROJECTOR_OT_create_projector)
    bpy.utils.unregister_class(ProjectorSettings)
