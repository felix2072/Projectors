import bpy
import os
import json

class PROJECTOR_OT_load_json(bpy.types.Operator):
    bl_idname = "projector.load_json"
    bl_label = "Load Projector from JSON"
    bl_description = "Lädt Werte aus einer JSON-Datei in den aktuellen Projector"

    filepath: bpy.props.StringProperty()

    def execute(self, context):
        selected_projectors = context.selected_objects
        if not selected_projectors:
            self.report({'WARNING'}, "No projector selected.")
            return {'CANCELLED'}
        projector = selected_projectors[0]
        proj_settings = projector.proj_settings
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for key, value in data.items():
                if hasattr(proj_settings, key):
                    try:
                        setattr(proj_settings, key, value)
                    except Exception:
                        pass
            self.report({'INFO'}, f"Loaded values from {os.path.basename(self.filepath)}.")
        except Exception as e:
            self.report({'ERROR'}, f"Fehler beim Laden: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

def register():
    bpy.utils.register_class(PROJECTOR_OT_load_json)

def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_load_json)
