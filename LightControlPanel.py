import bpy
from . import tt_utils
# tt_utils = bpy.data.texts["tt_utils.py"].as_module()


class LIGHT_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item.data, 'color', text='', icon="BLANK1")
            layout.prop(item, 'name', text='', emboss=False)
            layout.prop(item.data, 'energy', text='', emboss=False, slider=True)
            layout.prop(item, 'hide_viewport', text='', emboss=False, icon='HIDE_OFF')


class LightControlPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_light_control"
    bl_label = "Light Setting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "VIEW3D_PT_turntable_studio"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        collection = bpy.data.collections.get(tt_utils.LIGHT_COLLECTION)
        
        if collection:
            layout.label(text='Light Control', icon="LIGHT")
            row = layout.row(align=True)
            row.template_list("LIGHT_UL_list", "", collection, 'objects', collection, 'light_list_index', rows=3)
            col = row.column(align=True)
            col.operator('scene.light_list_add', text='', icon='ADD')
            col.operator('scene.light_list_delete', text='', icon='REMOVE')
        
        if scene.turntable.use_hdri:    
            layout.label(text='HDRI Control', icon='WORLD')
            layout.prop(scene.turntable, 'image_path', text='', placeholder='選擇HDRI資料夾')
        
        if scene.turntable.image_path and scene.turntable.use_hdri:
            box = layout.box()
            box.template_icon_view(scene.turntable, 'enum', show_labels=True)
            box.prop(scene.turntable, 'hdri_rotation_z')
            box.prop(scene.turntable, 'hdri_strength')
            box.prop(scene.turntable, 'hdri_blur_bg')
