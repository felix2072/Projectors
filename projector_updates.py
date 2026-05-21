_projection_update_in_progress = False
import bpy

from .helper import (
    get_child_ID_by_name,
    get_child_ID_by_type,
    get_projector,
    get_projectors,
    random_color,
)
from .projector_constants import Textures


def _get_projector_from_settings(proj_settings, context):
    """Prefer the property owner object over selection-dependent lookup."""
    owner = getattr(proj_settings, 'id_data', None)
    if owner is not None and getattr(owner, 'type', None) == 'CAMERA':
        return owner
    return get_projector(context)


def get_resolution(proj_settings, context):
    """Return active resolution either from preset or custom texture."""
    if proj_settings.use_custom_texture_res and proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value:
        projector = get_projector(context)
        root_tree = projector.children[get_child_ID_by_type(projector.children, 'LIGHT')].data.node_tree
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
    projector = get_projector(context)
    throw_ratio = proj_settings.throw_ratio

    projector.data.lens = 10 * throw_ratio

    w, h = get_resolution(proj_settings, context)
    aspect_ratio = w / h
    inverted_aspect_ratio = 1 / aspect_ratio

    update_projected_texture(proj_settings, context)

    spot = projector.children[get_child_ID_by_type(projector.children, 'LIGHT')]
    nodes = spot.data.node_tree.nodes['Group'].node_tree.nodes
    if bpy.app.version < (2, 81):
        nodes['Mapping'].scale[0] = 1 / throw_ratio
        nodes['Mapping'].scale[1] = 1 / throw_ratio * inverted_aspect_ratio
    else:
        nodes['Mapping'].inputs[3].default_value[0] = 1 / throw_ratio
        nodes['Mapping'].inputs[3].default_value[1] = 1 / throw_ratio * inverted_aspect_ratio

    update_lens_shift(proj_settings, context)
    update_projection_helper(proj_settings, context)


def update_focus_distance(proj_settings, context):
    update_projection_helper(proj_settings, context)


def update_lens_shift(proj_settings, context):
    projector = get_projector(context)
    h_shift = proj_settings.get('h_shift', 0.0) / 100
    v_shift = proj_settings.get('v_shift', 0.0) / 100

    h_shift_factor = h_shift * -1
    v_shift_factor = v_shift * -1

    res_w, res_h = get_resolution(proj_settings, context)
    projector.data.shift_x = -h_shift_factor
    projector.data.shift_y = -v_shift_factor*(res_h/res_w)

    spot = projector.children[get_child_ID_by_type(projector.children, 'LIGHT')]
    nodes = spot.data.node_tree.nodes['Group'].node_tree.nodes
    if bpy.app.version < (2, 81):
        nodes['Mapping.001'].translation[0] = h_shift_factor
        nodes['Mapping.001'].translation[1] = v_shift_factor
    else:
        nodes['Mapping.001'].inputs[1].default_value[0] = h_shift_factor
        nodes['Mapping.001'].inputs[1].default_value[1] = v_shift_factor
    update_projection_helper(proj_settings, context)



def update_projection_by_dimension(proj_settings, context, changed):
    """
    Allgemeine Update-Funktion für Projektionseigenschaften.
    changed: 'width', 'height' oder 'diagonal'
    """
    global _projection_update_in_progress
    if _projection_update_in_progress:
        return
    _projection_update_in_progress = True

    res_w, res_h = get_resolution(proj_settings, context)
    # Standardwerte falls Division durch 0
    aspect_w_h = res_w / res_h if res_h != 0 else 1.0
    aspect_h_w = res_h / res_w if res_w != 0 else 1.0

    if changed == 'width':
        w = proj_settings.w_projection
        h = w * aspect_h_w
        d = (w ** 2 + h ** 2) ** 0.5
        proj_settings['h_projection'] = h
        proj_settings['d_projection'] = d
    elif changed == 'height':
        h = proj_settings.h_projection
        w = h * aspect_w_h
        d = (w ** 2 + h ** 2) ** 0.5
        proj_settings['w_projection'] = w
        proj_settings['d_projection'] = d
    elif changed == 'diagonal':
        d = proj_settings.d_projection
        # Berechne w und h so, dass sie das Seitenverhältnis und die Diagonale erfüllen
        h = d / ((aspect_w_h ** 2 + 1) ** 0.5)
        w = aspect_w_h * h
        proj_settings['w_projection'] = w
        proj_settings['h_projection'] = h
    else:
        _projection_update_in_progress = False
        return


    focus_mode = getattr(proj_settings, 'focus_mode', 'THROW_RATIO')
    if w > 0:
        if focus_mode == 'THROW_RATIO':
            proj_settings['throw_ratio'] = proj_settings.focus_distance / w
            update_throw_ratio(proj_settings, context)
        elif focus_mode == 'FOCUS_DISTANCE':
            proj_settings['focus_distance'] = proj_settings.throw_ratio * w
            update_focus_distance(proj_settings, context)

    _projection_update_in_progress = False


# Wrapper für Blender Property-Callbacks
def update_projection_by_width(proj_settings, context):
    update_projection_by_dimension(proj_settings, context, 'width')

def update_projection_by_height(proj_settings, context):
    update_projection_by_dimension(proj_settings, context, 'height')

def update_projection_by_diagonal(proj_settings, context):
    update_projection_by_dimension(proj_settings, context, 'diagonal')


def update_projector_width(proj_settings, context):
    projector = _get_projector_from_settings(proj_settings, context)
    if projector is None:
        return
    update_projector_dimensions(proj_settings, context)


def update_projector_height(proj_settings, context):
    projector = _get_projector_from_settings(proj_settings, context)
    if projector is None:
        return
    update_projector_dimensions(proj_settings, context)


def update_projector_depth(proj_settings, context):
    projector = _get_projector_from_settings(proj_settings, context)
    if projector is None:
        return
    update_projector_dimensions(proj_settings, context)


def update_projector_dimensions(proj_settings, context):
    projector = _get_projector_from_settings(proj_settings, context)
    if projector is None:
        return
    projector_cube = projector.children[get_child_ID_by_name(projector.children, 'Cube')]
    # Keep initialization behavior consistent with slider callbacks.
    
    projector_cube.dimensions = (
    proj_settings.projector_w,
    proj_settings.projector_h,
    proj_settings.projector_d,
)
    projector_cube.location[2] = projector_cube.dimensions[2] / 2


def update_resolution(proj_settings, context):
    projector = get_projector(context)
    nodes = projector.children[get_child_ID_by_type(projector.children, 'LIGHT')].data.node_tree.nodes[
        'Group'
    ].node_tree.nodes
    nodes['Image Texture'].image = bpy.data.images[f'_proj.tex.{proj_settings.resolution}']
    update_throw_ratio(proj_settings, context)
    update_pixel_grid(proj_settings, context)
    update_projection_helper(proj_settings, context)


def update_checker_color(proj_settings, context):
    projector = get_projector(context)
    nodes = get_projector(context).children[
        get_child_ID_by_type(projector.children, 'LIGHT')
    ].data.node_tree.nodes['Group'].node_tree.nodes
    c = proj_settings.projected_color
    nodes['Checker Texture'].inputs['Color2'].default_value = [c.r, c.g, c.b, 1]
    projector_cube = projector.children[get_child_ID_by_name(projector.children, 'Cube')]
    projector_cube.material_slots[0].material.diffuse_color = [c.r, c.g, c.b, 0.5]
    for i in range(2):
        projector_plane = projector.children[get_child_ID_by_name(projector.children, 'Plane_' + str(i))]
        projector_plane.material_slots[0].material.diffuse_color = [c.r, c.g, c.b, 0.5]


def update_power(proj_settings, context):
    projector = get_projector(context)
    spot = get_projector(context).children[get_child_ID_by_type(projector.children, 'LIGHT')]
    spot.data.energy = proj_settings['power']


def update_pixel_grid(proj_settings, context):
    projector = get_projector(context)
    root_tree = get_projector(context).children[get_child_ID_by_type(projector.children, 'LIGHT')].data.node_tree
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
    curve = projector.children[get_child_ID_by_name(projector.children, 'HelperLine')]

    pn = curve.data.splines[0].points

    throw_ratio = proj_settings.throw_ratio
    focus_distance = proj_settings.focus_distance
    factor = focus_distance * 1 / throw_ratio / 2

    w, h = get_resolution(proj_settings, context)
    h_shift = proj_settings.get('h_shift', 0.0) / 100
    h_shift_factor = h_shift / throw_ratio * focus_distance
    v_shift = proj_settings.get('v_shift', 0.0) / 100
    v_shift_factor = h / w * v_shift / throw_ratio * focus_distance

    pn[0].co.x = -factor + h_shift_factor
    pn[0].co.y = h / w * factor + v_shift_factor
    pn[0].co.z = -focus_distance

    pn[1].co.x = factor + h_shift_factor
    pn[1].co.y = h / w * factor + v_shift_factor
    pn[1].co.z = -focus_distance

    pn[2].co.x = factor + h_shift_factor
    pn[2].co.y = -(h / w * factor) + v_shift_factor
    pn[2].co.z = -focus_distance

    pn[3].co.x = -factor + h_shift_factor
    pn[3].co.y = -(h / w * factor) + v_shift_factor
    pn[3].co.z = -focus_distance

    pn[4].co.x = pn[0].co.x
    pn[4].co.y = pn[0].co.y
    pn[4].co.z = pn[0].co.z

    pn[5].co = (0.0, 0.0, 0.0, 0.0)
    pn[6].co = (pn[1].co.x, pn[1].co.y, pn[1].co.z, 0.0)
    pn[7].co = (0.0, 0.0, 0.0, 0.0)
    pn[8].co = (pn[2].co.x, pn[2].co.y, pn[2].co.z, 0.0)
    pn[9].co = (0.0, 0.0, 0.0, 0.0)
    pn[10].co = (pn[3].co.x, pn[3].co.y, pn[3].co.z, 0.0)
    pn[11].co = (0.0, 0.0, 0.0, 0.0)
    pn[12].co = (0.0, 0.0, 0.0, 0.0)
    pn[13].co = (0.0, 0.0, 0.0, 0.0)
    pn[14].co = (0.0, 0.0, 0.0, 0.0)
    pn[15].co = (0.0, 0.0, 0.0, 0.0)
    pn[16].co = (0.0, 0.0, 0.0, 0.0)

    for j in range(4):
        plane = projector.children[get_child_ID_by_name(projector.children, 'HelperPlane_' + str(j))]
        for i in range(4):
            if i < 2:
                plane.data.vertices[i].co.x = pn[i + j].co.x * 2
                plane.data.vertices[i].co.y = pn[i + j].co.y * 2
                plane.data.vertices[i].co.z = pn[i + j].co.z
            else:
                plane.data.vertices[i].co.x = 0
                plane.data.vertices[i].co.y = 0
                plane.data.vertices[i].co.z = 0

    proj_settings.w_projection = (pn[0].co - pn[1].co).length
    proj_settings.h_projection = (pn[1].co - pn[2].co).length
    proj_settings.d_projection = (pn[0].co - pn[2].co).length


def update_projector_visibility(context):
    projector = get_projector(context)
    projector.hide_viewport = False
    projector.hide_render = False


def update_helper_lines_visibility(proj_settings, context):
    projector = get_projector(context)

    helper_line = projector.children[get_child_ID_by_name(projector.children, 'HelperLine')]
    helper_line.hide_viewport = not proj_settings.show_helper_lines
    helper_line.hide_render = not proj_settings.show_helper_lines

    for i in range(4):
        helper_plane = projector.children[
            get_child_ID_by_name(projector.children, 'HelperPlane_' + str(i))
        ]
        helper_plane.hide_viewport = not proj_settings.show_helper_lines
        helper_plane.hide_render = not proj_settings.show_helper_lines


def update_projected_texture(proj_settings, context):
    projector = get_projectors(context, only_selected=True)[0]
    root_tree = projector.children[get_child_ID_by_type(projector.children, 'LIGHT')].data.node_tree
    group_tree = root_tree.nodes['Group'].node_tree
    group_output_node = group_tree.nodes['Group Output']
    group_node = root_tree.nodes['Group']
    emission_node = root_tree.nodes['Emission']

    case = proj_settings.projected_texture
    if case == Textures.CHECKER.value:
        mix_node = group_tree.nodes['Mix.001']
        group_tree.links.new(mix_node.outputs['Color'], group_output_node.inputs[1])
        root_tree.links.new(group_node.outputs[1], emission_node.inputs[0])
    elif case == Textures.COLOR_GRID.value:
        img_node = group_tree.nodes['Image Texture']
        group_tree.links.new(img_node.outputs[0], group_output_node.inputs[1])
        root_tree.links.new(group_node.outputs[1], emission_node.inputs[0])
    elif case == Textures.CUSTOM_TEXTURE.value:
        custom_tex_node = root_tree.nodes['Image Texture']
        root_tree.links.new(custom_tex_node.outputs[0], emission_node.inputs[0])


def init_projector(proj_settings, context):
        proj_settings.throw_ratio = 1.0
        proj_settings.power = 100.0
        proj_settings.v_shift = 0.0
        proj_settings.h_shift = 0.0
        proj_settings.focus_distance = 1.0
        proj_settings.projector_w = 0.52
        proj_settings.projector_h = 0.14
        proj_settings.projector_d = 0.48
        proj_settings.projected_texture = Textures.CHECKER.value
        proj_settings.projected_color = random_color()
        proj_settings.resolution = '1920x1080'
        proj_settings.use_custom_texture_res = True

        # Do not rely on Property update callback timing during creation.
        update_projector_width(proj_settings, context)
        update_projector_height(proj_settings, context)
        update_projector_depth(proj_settings, context)

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
        update_helper_lines_visibility(proj_settings, context)

        # Set dimensions and scale for Cube only once at the very end, after all property callbacks
        projector = _get_projector_from_settings(proj_settings, context)
        if projector is not None:
            projector_cube = projector.children[get_child_ID_by_name(projector.children, 'Cube')]
            projector_cube.scale = (1, 1, 1)
            projector_cube.dimensions = (
                proj_settings.projector_w,
                proj_settings.projector_h,
                proj_settings.projector_d,
            )
            projector_cube.location[2] = projector_cube.dimensions[2] / 2
            projector_cube.data.update()
            bpy.context.view_layer.update()
            print(f"[DEBUG] init_projector: dimensions={projector_cube.dimensions[:]}, scale={projector_cube.scale[:]}")
