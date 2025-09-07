import bpy
from . import tt_utils
from . import operator
from . import LightControlPanel

# tt_utils = bpy.data.texts["tt_utils.py"].as_module()
# operator = bpy.data.texts["operator.py"].as_module()
# LightControlPanel = bpy.data.texts["LightControlPanel.py"].as_module()

bl_info = {
    "name": "Turntable Studio",
    "author": "Youjie + ChatGPT, wei_sheng",
    "version": (0, 17, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Turntable",
    "description": "Area lights(track to model),per-light intensity & color,camera distance,model rotation animation",
    "category": "3D View"
}


class TurntableProperty(bpy.types.PropertyGroup):
    use_hdri: bpy.props.BoolProperty(name='HDRI')
    hdri_rotation_z: bpy.props.FloatProperty(name="Rotation", subtype='ANGLE')
    hdri_strength : bpy.props.FloatProperty(name='Strength', default=1.0)
    hdri_blur_bg : bpy.props.FloatProperty(name='Blur', min=0, max=1, subtype='FACTOR')
    image_path: bpy.props.StringProperty(name='Image path', subtype='DIR_PATH')

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


# ---- UI Panel (English) ----
class TurntableStudioPanel(bpy.types.Panel):
    bl_label = "Turntable Studio"
    bl_idname = "VIEW3D_PT_turntable_studio"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Turntable'

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Target (select or set below)")
        layout.prop(sc.turntable, "tt_target", text="Target")
        row = layout.row()
        row.prop(sc.turntable, 'use_hdri', toggle=True)
        row.operator("turntable.apply_setup", icon='LIGHT_DATA')
        row.operator("turntable.add_animation", icon='ANIM')

        layout.prop(sc, 'frame_end', text="Animation Frames")

        if sc.turntable.use_hdri:
            layout.prop(sc.turntable, 'image_path', text='')
            layout.prop(sc.turntable, 'enum', text='')
            layout.prop(sc.turntable, 'hdri_rotation_z')
            layout.prop(sc.turntable, 'hdri_strength')
            layout.prop(sc.turntable, 'hdri_blur_bg')

        layout.separator()
        layout.label(text="Camera")
        layout.prop(sc.turntable, "tt_camera_distance", text="Distance")


# ---- register/unregister ----
classes = (TurntableStudioPanel, TurntableProperty,
           operator.OBJECT_OT_tt_apply_setup, operator.OBJECT_OT_tt_add_animation,
           LightControlPanel.LightControlPanel, LightControlPanel.Light_UL_list,
           LightControlPanel.LIST_OT_light_list_add, LightControlPanel.LIST_OT_light_list_delete)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.turntable = bpy.props.PointerProperty(type=TurntableProperty)
    bpy.types.Collection.light_list_index = bpy.props.IntProperty(update=tt_utils.sync_select_list)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.turntable
    del bpy.types.Collection.light_list_index


if __name__ == "__main__":
    register()
