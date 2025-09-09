import bpy
from . import tt_utils
# tt_utils = bpy.data.texts["tt_utils.py"].as_module()


class TurntableProperty(bpy.types.PropertyGroup):
    use_hdri: bpy.props.BoolProperty(name='HDRI')
    image_path_alert: bpy.props.BoolProperty()
    hdri_rotation_z: bpy.props.FloatProperty(name="Rotation", subtype='ANGLE')
    hdri_strength: bpy.props.FloatProperty(name='Strength', default=1.0)
    hdri_blur_bg: bpy.props.FloatProperty(name='Blur', min=0, max=1, subtype='FACTOR')
    
    image_path: bpy.props.StringProperty(
        name='Image path', subtype='DIR_PATH'
    )

    enum: bpy.props.EnumProperty(
        name='HDRI Image',
        items=tt_utils.get_image_items,
        update=tt_utils.create_or_update_hdri
    )

    tt_target: bpy.props.PointerProperty(
        name="Turntable Target", type=bpy.types.Object, update=tt_utils.update_target
    )

    tt_camera_distance: bpy.props.FloatProperty(
        name="Camera Distance", default=5.0, min=0.1, max=100.0, update=tt_utils.update_camera_distance
    )