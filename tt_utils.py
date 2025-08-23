import bpy
from mathutils import Vector
from pathlib import Path

# ---- constant names ----
CAM_NAME = "Turntable_Camera"
KEY_NAME = "Key_Light"
FILL_NAME = "Fill_Light"
RIM_NAME = "Rim_Light"
COLLECTION_NAME = "Turntable_Studio"


# ---- utilities ----
def get_world_bounds_size(obj):
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
        col.objects.link(cam)
        cam.location = target.location + Vector((0, -dist, height))
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
        col.objects.link(light_obj)
        light_obj.data.energy = energy
        light_obj.data.color = color
    if light_obj.name not in col.objects:
        try:
            col.objects.link(light_obj)
        except Exception:
            pass
    light_obj.location = target.location + Vector(offset)
    #    light_obj.data.energy = energy
    #    light_obj.data.color = color
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
    target = context.scene.turntable.tt_target
    if cam and target:
        dir_vec = cam.location - target.location
        if dir_vec.length == 0:
            dir_vec = Vector((0, -1, 0))
        dir_vec.normalize()
        cam.location = target.location + dir_vec * context.scene.turntable.tt_camera_distance


# when target changes, rebuild/relocate scene objects
def update_target(self, context):
    target = context.scene.turntable.tt_target
    if not target or target.type != 'MESH':
        return
    sx, sy, sz = get_world_bounds_size(target)
    max_s = max(sx, sy, sz, 0.001)
    default_dist = max_s * 2.5
    default_height = max_s * 0.8
    cam = create_or_update_camera(target, default_dist, default_height)
    context.scene.turntable.tt_camera_distance = (cam.location - target.location).length
    light_dist = max_s * 2.0
    create_or_update_area_light(KEY_NAME, "Key_Data", target, (light_dist, -light_dist, max_s),
                                1000, (1.0, 1.0, 1.0), max_s)
    create_or_update_area_light(FILL_NAME, "Fill_Data", target, (-light_dist, light_dist, max_s * 0.7),
                                700, (1.0, 1.0, 1.0), max_s)
    create_or_update_area_light(RIM_NAME, "Rim_Data", target, (0, -light_dist * 1.3, max_s * 0.8),
                                500, (1.0, 1.0, 1.0), max_s)
    if cam:
        bpy.context.scene.camera = cam


def create_or_update_hdri(self, context):
    sc = bpy.context.scene
    if not sc.turntable.use_hdri:
        return

    env_node = sc.world.node_tree.nodes.get('Environment Texture')
    bg_node = sc.world.node_tree.nodes['Background']
    image_name = f"{sc.turntable.enum}.exr"
    image_in_data = bpy.data.images.get(image_name)

    if image_in_data:
        image = image_in_data
    else:
        image_path = Path(sc.turntable.image_path) / image_name
        image = bpy.data.images.load(str(image_path))

    if env_node:
        env_node.image = image
        env_node.image.colorspace_settings.name = 'Linear Rec.709'
    else:
        env_node = sc.world.node_tree.nodes.new('ShaderNodeTexEnvironment')
        map_node = sc.world.node_tree.nodes.new('ShaderNodeMapping')
        texcod_node = sc.world.node_tree.nodes.new('ShaderNodeTexCoord')
        env_node.image = image
        env_node.image.colorspace_settings.name = 'Linear Rec.709'
        sc.world.node_tree.links.new(bg_node.inputs[0], env_node.outputs[0])
        sc.world.node_tree.links.new(env_node.inputs[0], map_node.outputs[0])
        sc.world.node_tree.links.new(map_node.inputs[0], texcod_node.outputs[0])

        fcs = map_node.inputs['Rotation'].driver_add('default_value', 2)
        fcs.driver.type = 'AVERAGE'
        var = fcs.driver.variables.new()
        target0 = var.targets[0]
        target0.id_type = 'SCENE'
        target0.id = sc
        target0.data_path = 'turntable.hdri_rotation_z'


def get_image_items(self, context):
    image_path = Path(context.scene.turntable.image_path)
    items = []
    for image in image_path.iterdir():
        item = (image.stem, image.stem, '')
        items.append(item)
    return items
