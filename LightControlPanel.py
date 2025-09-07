import bpy
from . import tt_utils
# tt_utils = bpy.data.texts["tt_utils.py"].as_module()


class Light_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item.data, 'color', text='', icon="BLANK1")
            layout.prop(item, 'name', text='', emboss=False)
            layout.prop(item.data, 'energy', text='', emboss=False, slider=True)
            layout.prop(item, 'hide_viewport', text='', emboss=False, icon='HIDE_OFF')


class LIST_OT_light_list_add(bpy.types.Operator):
    bl_idname = "scene.light_list_add"
    bl_label = "Add"
    
    def execute(self, context):
        sc = context.scene
        col = bpy.data.collections['Light']
        light_data = bpy.data.lights.new('Light', 'AREA')
        light = bpy.data.objects.new('Light', light_data)
        target = sc.turntable.tt_target
        
        sx, sy, sz = tt_utils.get_world_bounds_size(target)
        max_s = max(sx, sy, sz, 0.001)
        
        tt_utils.create_or_update_area_light(light.name, light_data.name, target, (0, 0, max_s), light_data.energy, light_data.color, max_s)
        
        return{'FINISHED'}


class LIST_OT_light_list_delete(bpy.types.Operator):
    bl_idname = "scene.light_list_delete"
    bl_label = "Delete"
    
    def execute(self, context):
        col = bpy.data.collections['Light']
        light = col.objects[col.light_list_index]
        light_data = light.data
        
        col.objects.unlink(light)
        bpy.data.objects.remove(light)
        bpy.data.lights.remove(light_data)
        return{'FINISHED'}


class LightControlPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_light_control"
    bl_label = "Light List"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "VIEW3D_PT_turntable_studio"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        collection = bpy.data.collections.get('Light')
        
        layout.label(text='Light Control', icon="LIGHT")
        if collection:
            row = layout.row(align=True)
            row.template_list("Light_UL_list", "", collection, 'objects', collection, 'light_list_index', rows=3)
            col = row.column(align=True)
            col.operator('scene.light_list_add', text='', icon='ADD')
            col.operator('scene.light_list_delete', text='', icon='REMOVE')
