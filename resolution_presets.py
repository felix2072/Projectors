import json
import os

RESOLUTIONS_DIRNAME = 'resolutions'


def get_resolutions_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), RESOLUTIONS_DIRNAME)


def load_resolution_presets():
    """Read all resolution JSON presets (name, x, y) from the resolutions folder."""
    resolutions_dir = get_resolutions_dir()
    presets = []
    if not os.path.isdir(resolutions_dir):
        return presets
    for filename in sorted(os.listdir(resolutions_dir)):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(resolutions_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            presets.append({
                'name': data['name'],
                'x': int(data['x']),
                'y': int(data['y']),
            })
        except Exception:
            continue
    presets.sort(key=lambda p: (p['x'] * p['y'], p['x']))
    return presets


def get_resolution_items(self, context):
    """EnumProperty items callback: rebuilt from the JSON presets on every call, so new
    or edited files show up immediately without any reload."""
    items = []
    for preset in load_resolution_presets():
        identifier = f"{preset['x']}x{preset['y']}"
        label = f"{preset['name']} ({identifier})"
        # Number is derived from x/y (not list position), so a value already stored on
        # an object (e.g. saved in a .blend file) keeps resolving to the same resolution
        # even after presets are added, removed or reordered elsewhere in the list.
        number = preset['x'] * 100000 + preset['y']
        items.append((identifier, label, '', number))

    # Also expose the width/height currently being edited in the "Save Resolution" fields,
    # even before it's written to disk, so picking it as the active resolution works live.
    scene = getattr(context, 'scene', None)
    custom_x = getattr(scene, 'resolution_save_x', None)
    custom_y = getattr(scene, 'resolution_save_y', None)
    if custom_x and custom_y:
        custom_id = f'{custom_x}x{custom_y}'
        if not any(item[0] == custom_id for item in items):
            items.append((custom_id, f'Custom ({custom_id})', '', custom_x * 100000 + custom_y))

    if not items:
        items = [('1920x1080', '1080p (1920x1080)', '', 1920 * 100000 + 1080)]
    return items


def save_resolution_preset(name, width, height):
    """Save a resolution preset (name, x, y - no aspect ratio) into the resolutions folder."""
    resolutions_dir = get_resolutions_dir()
    os.makedirs(resolutions_dir, exist_ok=True)
    filepath = os.path.join(resolutions_dir, f'{int(width)}x{int(height)}.json')
    data = {'name': name.strip(), 'x': int(width), 'y': int(height)}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return filepath
