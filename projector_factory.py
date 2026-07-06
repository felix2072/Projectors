import logging
import math

import bmesh
import bpy

from .helper import ADDON_ID, auto_offset
from .resolution_presets import get_resolution_items

logging.basicConfig(
    format='[ProjectorForks Addon]: %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(name=__file__)


def ensure_projector_texture(resolution_id):
    """Create the generated texture for one 'WIDTHxHEIGHT' resolution id if it doesn't exist yet."""
    img_name = f'_proj.tex.{resolution_id}'
    if not bpy.data.images.get(img_name):
        w, h = resolution_id.split('x')
        log.debug(f'Create projection texture: {img_name}')
        bpy.ops.image.new(
            name=img_name,
            width=int(w),
            height=int(h),
            color=(0.0, 0.0, 0.0, 1.0),
            alpha=True,
            generated_type='COLOR_GRID',
            float=False,
        )
    bpy.data.images[img_name].use_fake_user = True


def create_projector_textures():
    """Ensure the generated textures for all currently known resolution presets exist."""
    for identifier, _label, _desc, _number in get_resolution_items(None, None):
        ensure_projector_texture(identifier)


def add_projector_node_tree_to_spot(spot):
    """Turn a spot light into a projector by assigning a node setup."""
    spot.data.use_nodes = True
    root_tree = spot.data.node_tree
    root_tree.nodes.clear()

    node_group = bpy.data.node_groups.new('_Projector', 'ShaderNodeTree')

    if bpy.app.version >= (4, 0):
        node_group.interface.new_socket('texture vector', in_out='OUTPUT', socket_type='NodeSocketVector')
        node_group.interface.new_socket('color', in_out='OUTPUT', socket_type='NodeSocketColor')
    else:
        output = node_group.outputs
        output.new('NodeSocketVector', 'texture vector')
        output.new('NodeSocketColor', 'color')

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

    img = nodes.new('ShaderNodeTexImage')
    img.extension = 'CLIP'
    img.location = auto_pos(200)

    checker_tex = nodes.new('ShaderNodeTexChecker')
    checker_tex.inputs[3].default_value = 8
    checker_tex.inputs[1].default_value = (1, 1, 1, 1)
    checker_tex.location = auto_pos(y=-300)

    mix_rgb = nodes.new('ShaderNodeMixRGB')
    mix_rgb.name = 'Mix.001'
    mix_rgb.inputs[1].default_value = (0, 0, 0, 0)
    mix_rgb.location = auto_pos(200, y=-300)

    group_output_node = node_group.nodes.new('NodeGroupOutput')
    group_output_node.location = auto_pos(200)

    auto_pos_root = auto_offset()
    user_texture = root_tree.nodes.new('ShaderNodeTexImage')
    user_texture.extension = 'CLIP'
    user_texture.label = 'Add your Image Texture or Movie here'
    user_texture.location = auto_pos_root(200, y=200)

    emission = root_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 1
    emission.location = auto_pos_root(300)

    output = root_tree.nodes.new('ShaderNodeOutputLight')
    output.location = auto_pos_root(200)

    if bpy.app.version >= (4, 0):
        tree.links.new(geo.outputs['Incoming'], vec_transform.inputs['Vector'])
        tree.links.new(vec_transform.outputs['Vector'], map_1.inputs['Vector'])
    else:
        tree.links.new(tex.outputs['Normal'], map_1.inputs['Vector'])
    tree.links.new(map_1.outputs['Vector'], sep.inputs['Vector'])

    tree.links.new(sep.outputs[0], div_1.inputs[0])
    tree.links.new(sep.outputs[2], div_1.inputs[1])
    tree.links.new(sep.outputs[1], div_2.inputs[0])
    tree.links.new(sep.outputs[2], div_2.inputs[1])

    tree.links.new(div_1.outputs[0], com.inputs[0])
    tree.links.new(div_2.outputs[0], com.inputs[1])
    tree.links.new(com.outputs['Vector'], map_2.inputs['Vector'])

    tree.links.new(map_2.outputs['Vector'], add.inputs['Color1'])
    tree.links.new(add.outputs['Color'], img.inputs['Vector'])
    tree.links.new(add.outputs['Color'], group_output_node.inputs[0])

    tree.links.new(add.outputs['Color'], checker_tex.inputs['Vector'])
    tree.links.new(img.outputs['Alpha'], mix_rgb.inputs[0])
    tree.links.new(checker_tex.outputs['Color'], mix_rgb.inputs[2])

    root_tree.links.new(group.outputs['texture vector'], user_texture.inputs['Vector'])
    root_tree.links.new(group.outputs['color'], emission.inputs['Color'])
    root_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

    pixel_grid_group = create_pixel_grid_node_group()
    pixel_grid_node = spot.data.node_tree.nodes.new('ShaderNodeGroup')
    pixel_grid_node.node_tree = pixel_grid_group
    pixel_grid_node.label = 'Pixel Grid'
    pixel_grid_node.name = 'pixel_grid'
    loc = root_tree.nodes['Emission'].location
    pixel_grid_node.location = (loc[0], loc[1] - 150)

    root_tree.links.new(group.outputs[0], pixel_grid_node.inputs[1])
    root_tree.links.new(emission.outputs[0], pixel_grid_node.inputs[0])


def create_pixel_grid_node_group():
    node_group = bpy.data.node_groups.new('_Projectors-Addon_PixelGrid', 'ShaderNodeTree')

    if bpy.app.version >= (4, 0):
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


def create_shape_from_verts(obj_name):
    mesh = bpy.data.meshes.new(f'{obj_name}_mesh')
    mesh_obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)

    bm = bmesh.new()

    vert_coords = [
        (1.0, 1.0, 0.0),
        (1.0, -1.0, 0.0),
        (-1.0, -1.0, 0.0),
        (-1.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ]

    for coord in vert_coords:
        bm.verts.new(coord)

    face_vert_indices = [
        (0, 1, 2, 3),
        (4, 1, 0),
        (4, 2, 1),
        (4, 3, 2),
        (4, 0, 3),
    ]

    bm.verts.ensure_lookup_table()

    for vert_indices in face_vert_indices:
        bm.faces.new([bm.verts[index] for index in vert_indices])

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()


def create_projector(context):
    """Create a camera + spotlight projector rig."""
    create_projector_textures()
    log.debug('Creating projector.')

    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0))
    spot = context.object
    spot.name = 'Projector_Spotlight'
    spot.scale = (0.01, 0.01, 0.01)
    spot.data.spot_size = math.pi - 0.001
    spot.data.spot_blend = 0
    spot.data.shadow_soft_size = 0.0
    spot.hide_select = True
    spot[ADDON_ID.format('spot')] = True
    spot.data.cycles.use_multiple_importance_sampling = False
    add_projector_node_tree_to_spot(spot)

    bpy.ops.object.camera_add(enter_editmode=False, location=(0, 0, 0), rotation=(0, 0, 0))
    cam = context.object
    cam.name = 'Projector_Camera.001'
    cam.data.lens_unit = 'MILLIMETERS'
    cam.data.sensor_width = 10
    cam.data.display_size = 0.01

    spot.parent = cam

    cam.location = context.scene.cursor.location
    cam.rotation_euler = (math.pi * 0.5, 0, 0)

    bpy.ops.curve.primitive_nurbs_path_add(radius=1, enter_editmode=True)
    obj = bpy.context.object
    obj.name = 'Projector_HelperLine'
    obj.location = (0, 0, 0)

    for pn in obj.data.splines[0].points:
        pn.select = False

    pn = obj.data.splines[0].points
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

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.subdivide()
    bpy.ops.curve.subdivide()
    bpy.ops.curve.handle_type_set(type='VECTOR')
    bpy.ops.curve.spline_type_set(type='POLY')
    bpy.ops.object.mode_set(mode='OBJECT')

    curves = context.object
    curves.parent = cam

    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    projector_cube = bpy.context.object
    projector_cube.name = 'Projector_Cube'
    projector_cube.dimensions = (1, 1, 1)
    projector_cube.visible_shadow = False
    projector_cube.parent = cam
    bpy.ops.object.material_slot_add()
    projector_cube.material_slots[0].link = 'OBJECT'
    projector_cube_mat = bpy.data.materials.new('Projector_Cube_Mat')
    projector_cube.material_slots[0].material = projector_cube_mat

    projector_helper_plane_mat = newShader(cam.name + '_HelperPlaneMat', 'principled', 1, 1, 1)
    for i in range(4):
        bpy.ops.mesh.primitive_plane_add()
        projector_helper_plane = bpy.context.object
        projector_helper_plane.name = 'Projector_HelperPlane_' + str(i) + '.001'
        projector_helper_plane.dimensions = (1, 1, 1)
        projector_helper_plane.visible_shadow = False
        projector_helper_plane.parent = cam
        projector_helper_plane.data.materials.append(projector_helper_plane_mat)

    bpy.context.view_layer.objects.active = cam

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[cam.name].select_set(True)
    cam = context.object
    return cam


def newMaterial(identifier):
    mat = bpy.data.materials.get(identifier)

    if mat is None:
        mat = bpy.data.materials.new(name=identifier)

    mat.use_nodes = True

    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()

    return mat


def newShader(identifier, shader_type, r, g, b):
    mat = newMaterial(identifier)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')

    if shader_type == 'principled':
        shader = nodes.new(type='ShaderNodeBsdfPrincipled')
        nodes['Principled BSDF'].inputs[0].default_value = (r, g, b, 1)
        nodes['Principled BSDF'].inputs[4].default_value = 0.5
    elif shader_type == 'diffuse':
        shader = nodes.new(type='ShaderNodeBsdfDiffuse')
        nodes['Diffuse BSDF'].inputs[0].default_value = (r, g, b, 1)
    elif shader_type == 'emission':
        shader = nodes.new(type='ShaderNodeEmission')
        nodes['Emission'].inputs[0].default_value = (r, g, b, 1)
        nodes['Emission'].inputs[1].default_value = 1
    elif shader_type == 'glossy':
        shader = nodes.new(type='ShaderNodeBsdfGlossy')
        nodes['Glossy BSDF'].inputs[0].default_value = (r, g, b, 1)
        nodes['Glossy BSDF'].inputs[1].default_value = 0
    else:
        raise ValueError(f'Unsupported shader type: {shader_type}')

    links.new(shader.outputs[0], output.inputs[0])

    return mat


