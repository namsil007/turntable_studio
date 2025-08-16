
bl_info = {
    "name": "Turntable Studio v14",
    "author": "Youjie + ChatGPT",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Turntable",
    "description": "Area lights (track to model), per-light intensity & color, camera distance, model rotation animation, Apply Setup",
    "category": "3D View",
}

import bpy
import math
from mathutils import Vector

# ---- constant names ----
CAM_NAME = "Turntable_Camera"
KEY_NAME = "Key_Light"
FILL_NAME = "Fill_Light"
RIM_NAME = "Rim_Light"
COLLECTION_NAME = "Turntable_Studio"

# ---- utilities ----
def get_world_bounds_size(obj):
    try:
        verts = obj.data.vertices
        if len(verts) == 0:
            return obj.dimensions.x, obj.dimensions.y, obj.dimensions.z
        coords = [obj.matrix_world @ v.co for v in verts]
        min_x = min(v.x for v in coords); max_x = max(v.x for v in coords)
        min_y = min(v.y for v in coords); max_y = max(v.y for v in coords)
        min_z = min(v.z for v in coords); max_z = max(v.z for v in coords)
        return max_x - min_x, max_y - min_y, max_z - min_z
    except Exception:
        return obj.dimensions.x, obj.dimensions.y, obj.dimensions.z

def ensure_collection(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

# ---- camera create/update ----
def create_or_update_camera(target, dist, height):
    cam = bpy.data.objects.get(CAM_NAME)
    col = ensure_collection(COLLECTION_NAME)
    if cam and cam.type == 'CAMERA':
        cam.location = target.location + Vector((0, -dist, height))
    else:
        cam_data = bpy.data.cameras.new(CAM_NAME + "_data")
        cam = bpy.data.objects.new(CAM_NAME, cam_data)
        bpy.context.collection.objects.link(cam)
    if cam.name not in col.objects:
        try:
            col.objects.link(cam)
        except Exception:
            pass
    track = None
    for c in cam.constraints:
        if c.type == 'TRACK_TO' and getattr(c, "name", "") == "Turntable_CamTrack":
            track = c
            break
    if not track:
        track = cam.constraints.new(type='TRACK_TO')
        track.name = "Turntable_CamTrack"
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    return cam

# ---- area light create/update ----
def create_or_update_area_light(name, data_name, target, offset, energy, color, size):
    col = ensure_collection(COLLECTION_NAME)
    light_obj = bpy.data.objects.get(name)
    if light_obj and light_obj.type == 'LIGHT':
        light_obj.data.type = 'AREA'
        try:
            light_obj.data.size = size
        except Exception:
            pass
    else:
        ldata = bpy.data.lights.new(data_name, type='AREA')
        try:
            ldata.size = size
        except Exception:
            pass
        light_obj = bpy.data.objects.new(name, ldata)
        bpy.context.collection.objects.link(light_obj)
    if light_obj.name not in col.objects:
        try:
            col.objects.link(light_obj)
        except Exception:
            pass
    light_obj.location = target.location + Vector(offset)
    light_obj.data.energy = energy
    light_obj.data.color = color
    tr = None
    for c in light_obj.constraints:
        if c.type == 'TRACK_TO' and getattr(c, "name", "") == "Turntable_LightTrack":
            tr = c
            break
    if not tr:
        tr = light_obj.constraints.new(type='TRACK_TO')
        tr.name = "Turntable_LightTrack"
    tr.target = target
    tr.track_axis = 'TRACK_NEGATIVE_Z'
    tr.up_axis = 'UP_Y'
    return light_obj

# ---- update callbacks (bound to scene props) ----
def update_camera_distance(self, context):
    cam = bpy.data.objects.get(CAM_NAME)
    target = context.scene.tt_target
    if cam and target:
        dir_vec = cam.location - target.location
        if dir_vec.length == 0:
            dir_vec = Vector((0, -1, 0))
        dir_vec.normalize()
        cam.location = target.location + dir_vec * context.scene.tt_camera_distance

def update_key_strength(self, context):
    obj = bpy.data.objects.get(KEY_NAME)
    if obj and obj.type == 'LIGHT':
        obj.data.energy = context.scene.tt_key_strength

def update_fill_strength(self, context):
    obj = bpy.data.objects.get(FILL_NAME)
    if obj and obj.type == 'LIGHT':
        obj.data.energy = context.scene.tt_fill_strength

def update_rim_strength(self, context):
    obj = bpy.data.objects.get(RIM_NAME)
    if obj and obj.type == 'LIGHT':
        obj.data.energy = context.scene.tt_rim_strength

def update_key_color(self, context):
    obj = bpy.data.objects.get(KEY_NAME)
    if obj and obj.type == 'LIGHT':
        obj.data.color = context.scene.tt_key_color

def update_fill_color(self, context):
    obj = bpy.data.objects.get(FILL_NAME)
    if obj and obj.type == 'LIGHT':
        obj.data.color = context.scene.tt_fill_color

def update_rim_color(self, context):
    obj = bpy.data.objects.get(RIM_NAME)
    if obj and obj.type == 'LIGHT':
        obj.data.color = context.scene.tt_rim_color

# when target changes, rebuild/relocate scene objects
def update_target(self, context):
    target = context.scene.tt_target
    if not target or target.type != 'MESH':
        return
    sx, sy, sz = get_world_bounds_size(target)
    max_s = max(sx, sy, sz, 0.001)
    default_dist = max_s * 2.5
    default_height = max_s * 0.8
    cam = create_or_update_camera(target, default_dist, default_height)
    context.scene.tt_camera_distance = (cam.location - target.location).length
    light_dist = max_s * 2.0
    create_or_update_area_light(KEY_NAME, "Key_Data", target, (light_dist, -light_dist, max_s), context.scene.tt_key_strength, context.scene.tt_key_color, max_s)
    create_or_update_area_light(FILL_NAME, "Fill_Data", target, (-light_dist, light_dist, max_s * 0.7), context.scene.tt_fill_strength, context.scene.tt_fill_color, max_s)
    create_or_update_area_light(RIM_NAME, "Rim_Data", target, (0, -light_dist * 1.3, max_s * 0.8), context.scene.tt_rim_strength, context.scene.tt_rim_color, max_s)
    if cam:
        bpy.context.scene.camera = cam

# ---- Operators ----
class OBJECT_OT_tt_apply_setup(bpy.types.Operator):
    bl_idname = "turntable.apply_setup"
    bl_label = "Apply Studio Setup"
    bl_description = "Apply or update turntable camera and area lights for the selected or specified target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sc = context.scene
        target = sc.tt_target if sc.tt_target else context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Please select a Mesh target or set Target in panel")
            return {'CANCELLED'}
        sc.tt_target = target
        sx, sy, sz = get_world_bounds_size(target)
        max_s = max(sx, sy, sz, 0.001)
        dist = max_s * 2.5
        height = max_s * 0.8
        light_dist = max_s * 2.0
        base_energy = max(500.0, max_s * 200.0)
        cam = create_or_update_camera(target, dist, height)
        create_or_update_area_light(KEY_NAME, "Key_Data", target, (light_dist, -light_dist, max_s), base_energy, (1.0,1.0,1.0), max_s)
        create_or_update_area_light(FILL_NAME, "Fill_Data", target, (-light_dist, light_dist, max_s * 0.7), base_energy * 0.7, (1.0,1.0,1.0), max_s)
        create_or_update_area_light(RIM_NAME, "Rim_Data", target, (0, -light_dist * 1.3, max_s * 0.8), base_energy * 0.5, (1.0,1.0,1.0), max_s)
        sc.tt_camera_distance = (cam.location - target.location).length
        sc.tt_key_strength = bpy.data.objects[KEY_NAME].data.energy
        sc.tt_fill_strength = bpy.data.objects[FILL_NAME].data.energy
        sc.tt_rim_strength = bpy.data.objects[RIM_NAME].data.energy
        sc.tt_key_color = bpy.data.objects[KEY_NAME].data.color[:]
        sc.tt_fill_color = bpy.data.objects[FILL_NAME].data.color[:]
        sc.tt_rim_color = bpy.data.objects[RIM_NAME].data.color[:]
        self.report({'INFO'}, "Turntable setup applied/updated")
        return {'FINISHED'}

class OBJECT_OT_tt_add_animation(bpy.types.Operator):
    bl_idname = "turntable.add_animation"
    bl_label = "Add Turntable Animation"
    bl_description = "Add 0->360° looping rotation keyframes on the target (Z axis)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.scene.tt_target if context.scene.tt_target else context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Please select a Mesh target or set Target in panel")
            return {'CANCELLED'}
        frames = context.scene.tt_anim_frames
        target.rotation_mode = 'XYZ'
        base = target.rotation_euler.z
        target.rotation_euler.z = base
        target.keyframe_insert(data_path="rotation_euler", frame=1, index=2)
        target.rotation_euler.z = base + 2 * math.pi
        target.keyframe_insert(data_path="rotation_euler", frame=frames, index=2)
        if target.animation_data and target.animation_data.action:
            for fc in target.animation_data.action.fcurves:
                if fc.data_path == "rotation_euler" and fc.array_index == 2:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'
                    has_cycles = any(m.type == 'CYCLES' for m in fc.modifiers)
                    if not has_cycles:
                        fc.modifiers.new(type='CYCLES')
        context.scene.frame_start = 1
        context.scene.frame_end = frames
        self.report({'INFO'}, f"Added rotation animation to {target.name} ({frames} frames)")
        return {'FINISHED'}

# ---- UI Panel (English) ----
class VIEW3D_PT_turntable_panel(bpy.types.Panel):
    bl_label = "Turntable Studio"
    bl_idname = "VIEW3D_PT_turntable_studio_v14"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Turntable'

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Target (select or set below)")
        layout.prop(sc, "tt_target", text="Target")
        row = layout.row()
        row.operator("turntable.apply_setup", icon='LIGHT_DATA')
        row.operator("turntable.add_animation", icon='ANIM')

        layout.prop(sc, "tt_anim_frames", text="Animation Frames")

        layout.separator()
        layout.label(text="Camera")
        layout.prop(sc, "tt_camera_distance", text="Distance")

        layout.separator()
        layout.label(text="Key Light")
        layout.prop(sc, "tt_key_strength", text="Brightness")
        layout.prop(sc, "tt_key_color", text="Color")

        layout.separator()
        layout.label(text="Fill Light")
        layout.prop(sc, "tt_fill_strength", text="Brightness")
        layout.prop(sc, "tt_fill_color", text="Color")

        layout.separator()
        layout.label(text="Rim Light")
        layout.prop(sc, "tt_rim_strength", text="Brightness")
        layout.prop(sc, "tt_rim_color", text="Color")

# ---- register/unregister ----
classes = (
    OBJECT_OT_tt_apply_setup,
    OBJECT_OT_tt_add_animation,
    VIEW3D_PT_turntable_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.tt_target = bpy.props.PointerProperty(
        name="Turntable Target",
        type=bpy.types.Object,
        update=update_target
    )
    bpy.types.Scene.tt_camera_distance = bpy.props.FloatProperty(
        name="Camera Distance",
        default=5.0, min=0.1, max=100.0, update=update_camera_distance
    )
    bpy.types.Scene.tt_key_strength = bpy.props.FloatProperty(
        name="Key Strength", default=1000.0, min=0.0, max=50000.0, update=update_key_strength
    )
    bpy.types.Scene.tt_fill_strength = bpy.props.FloatProperty(
        name="Fill Strength", default=700.0, min=0.0, max=50000.0, update=update_fill_strength
    )
    bpy.types.Scene.tt_rim_strength = bpy.props.FloatProperty(
        name="Rim Strength", default=500.0, min=0.0, max=50000.0, update=update_rim_strength
    )
    bpy.types.Scene.tt_key_color = bpy.props.FloatVectorProperty(
        name="Key Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0,1.0,1.0),
        update=update_key_color
    )
    bpy.types.Scene.tt_fill_color = bpy.props.FloatVectorProperty(
        name="Fill Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0,1.0,1.0),
        update=update_fill_color
    )
    bpy.types.Scene.tt_rim_color = bpy.props.FloatVectorProperty(
        name="Rim Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0,1.0,1.0),
        update=update_rim_color
    )
    bpy.types.Scene.tt_anim_frames = bpy.props.IntProperty(
        name="Animation Frames", default=250, min=4, max=10000
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for p in ("tt_target","tt_camera_distance","tt_key_strength","tt_fill_strength",
              "tt_rim_strength","tt_key_color","tt_fill_color","tt_rim_color","tt_anim_frames"):
        if hasattr(bpy.types.Scene, p):
            delattr(bpy.types.Scene, p)

if __name__ == "__main__":
    register()
