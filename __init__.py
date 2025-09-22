import bpy
import bpy.utils.previews
from . import tt_utils, operator, LightControlPanel, TurntableProperty

# tt_utils = bpy.data.texts["tt_utils.py"].as_module()
# operator = bpy.data.texts["operator.py"].as_module()
# LightControlPanel = bpy.data.texts["LightControlPanel.py"].as_module()
# TurntableProperty = bpy.data.texts["TurntableProperty.py"].as_module()

bl_info = {
    "name": "Turntable Studio",
    "author": "Youjie + ChatGPT, wei_sheng",
    "version": (0, 18, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Turntable",
    "description": "Area lights(track to model),per-light intensity & color,camera distance,model rotation animation",
    "category": "3D View"
}


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
        
        row = layout.row()
        row.prop(sc, 'frame_end', text="Animation Frames")

        layout.label(text="Camera")
        layout.prop(sc.turntable, "tt_camera_distance", text="Distance")


# ---- register/unregister ----
classes = (TurntableStudioPanel, TurntableProperty.TurntableProperty,
           operator.OBJECT_OT_tt_apply_setup, operator.OBJECT_OT_tt_add_animation,
           operator.LIST_OT_light_list_add, operator.LIST_OT_light_list_delete,
           LightControlPanel.LightControlPanel, LightControlPanel.LIGHT_UL_list)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    pcoll = bpy.utils.previews.new()
    pcoll.image_dir = ""
    pcoll.hdri_previews = ()
    tt_utils.hdri_preview_collections["main"] = pcoll
    
    bpy.types.Scene.turntable = bpy.props.PointerProperty(type=TurntableProperty.TurntableProperty)
    bpy.types.Collection.light_list_index = bpy.props.IntProperty(update=tt_utils.sync_select_list)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for pcoll in tt_utils.hdri_preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    
    del bpy.types.Scene.turntable
    del bpy.types.Collection.light_list_index
    
    tt_utils.hdri_preview_collections.clear()
    

if __name__ == "__main__":
    register()
