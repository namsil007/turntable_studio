import bpy
from mathutils import Vector
from pathlib import Path

# ---- constant names ----
CAM_NAME = "Turntable_Camera"
KEY_NAME = "Key_Light"
FILL_NAME = "Fill_Light"
RIM_NAME = "Rim_Light"
COLLECTION_NAME = "Turntable_Studio"
LIGHT_COLLECTION = "Turntable_Light"


# ---- utilities ----
def get_world_bounds_size(obj):
    return obj.dimensions.x, obj.dimensions.y, obj.dimensions.z


def ensure_collection(name):
    scene_col = bpy.context.scene.collection
    col = bpy.data.collections.get(name)
    col_light = bpy.data.collections.get(LIGHT_COLLECTION)

    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)

    if not col_light:
        col_light = bpy.data.collections.new(LIGHT_COLLECTION)
        col.children.link(col_light)

    if not col.children.get(LIGHT_COLLECTION):
        col.children.link(col_light)

    if scene_col.children.get(LIGHT_COLLECTION):
        scene_col.children.unlink(col_light)
    return col, col_light


def sync_select_list(self, context):    
    col = bpy.data.collections.get(LIGHT_COLLECTION)
    obj = col.objects[col.light_list_index]
    
    for ob in col.objects:
        ob.select_set(False)    
    
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


# ---- camera create/update ----
def create_or_update_camera(target, dist, height):
    cam = bpy.data.objects.get(CAM_NAME)
    col, col_light = ensure_collection(COLLECTION_NAME)
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
    col, col_light = ensure_collection(COLLECTION_NAME)
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
        col_light.objects.link(light_obj)
        light_obj.data.energy = energy
        light_obj.data.color = color
    if light_obj.name not in col_light.objects:
        try:
            col_light.objects.link(light_obj)
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


def create_blur_node():
    lib_path = Path(__file__).parent / 'asset' / 'blur_node.blend'
    blur_node_group = bpy.data.node_groups.get('BlurNode')

    if not blur_node_group:
        with bpy.data.libraries.load(str(lib_path)) as (data_from, data_to):
            data_to.node_groups = data_from.node_groups

    blur_node_group = bpy.data.node_groups['BlurNode']
    blur_node = bpy.context.scene.world.node_tree.nodes.get('BlurNode')
    if not blur_node:
        blur_node = bpy.context.scene.world.node_tree.nodes.new('ShaderNodeGroup')
        blur_node.node_tree = blur_node_group
        blur_node.name = 'BlurNode'
    return blur_node


def add_driver(node_inputs, data_path, index=None):
    sc = bpy.context.scene
    if index:
        fcs = node_inputs.driver_add('default_value', index)
    else:
        fcs = node_inputs.driver_add('default_value')
    fcs.driver.type = 'AVERAGE'
    var = fcs.driver.variables.new()
    target0 = var.targets[0]
    target0.id_type = 'SCENE'
    target0.id = sc
    target0.data_path = data_path


def create_or_update_hdri(self, context):
    sc = bpy.context.scene

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
        blur_node = create_blur_node()

        env_node.image = image
        env_node.image.colorspace_settings.name = 'Linear Rec.709'
        sc.world.node_tree.links.new(bg_node.inputs[0], env_node.outputs[0])
        sc.world.node_tree.links.new(env_node.inputs[0], blur_node.outputs[0])
        sc.world.node_tree.links.new(blur_node.inputs[1], map_node.outputs[0])
        sc.world.node_tree.links.new(map_node.inputs[0], texcod_node.outputs[0])

        add_driver(map_node.inputs['Rotation'], 'turntable.hdri_rotation_z', 2)
        add_driver(blur_node.inputs['Factor'], 'turntable.hdri_blur_bg')
        add_driver(bg_node.inputs['Strength'], 'turntable.hdri_strength')


def get_image_items(self, context):
    image_path = Path(context.scene.turntable.image_path)
    items = []
    for image in image_path.iterdir():
        item = (image.stem, image.stem, '')
        items.append(item)
    return items
