import bpy
import math
from . import tt_utils
# tt_utils = bpy.data.texts["tt_utils.py"].as_module()


# ---- Operators ----
class OBJECT_OT_tt_apply_setup(bpy.types.Operator):
    bl_idname = "turntable.apply_setup"
    bl_label = "Apply Studio Setup"
    bl_description = "Apply or update turntable camera and area lights for the selected or specified target"
    bl_options = {'REGISTER', 'UNDO'}
    
    @staticmethod
    def execute(self, context):
        sc = context.scene
        target = sc.turntable.tt_target if sc.turntable.tt_target else context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Please select a Mesh target or set Target in panel")
            return {'CANCELLED'}
        sc.turntable.tt_target = target
        sx, sy, sz = tt_utils.get_world_bounds_size(target)
        max_s = max(sx, sy, sz, 0.001)
        dist = max_s * 2.5
        height = max_s * 0.8
        light_dist = max_s * 2.0
        base_energy = max(500.0, max_s * 200.0)
        cam = tt_utils.create_or_update_camera(target, dist, height)
        tt_utils.create_or_update_area_light(tt_utils.KEY_NAME, "Key_Data", target, (light_dist, -light_dist, max_s), base_energy,
                                    (1.0, 1.0, 1.0), max_s)
        tt_utils.create_or_update_area_light(tt_utils.FILL_NAME, "Fill_Data", target, (-light_dist, light_dist, max_s * 0.7),
                                    base_energy * 0.7, (1.0, 1.0, 1.0), max_s)
        tt_utils.create_or_update_area_light(tt_utils.RIM_NAME, "Rim_Data", target, (0, -light_dist * 1.3, max_s * 0.8),
                                    base_energy * 0.5, (1.0, 1.0, 1.0), max_s)
        
        if sc.turntable.image_path and sc.turntable.use_hdri:
            tt_utils.create_or_update_hdri(self, context)
        
        self.report({'INFO'}, "Turntable setup applied/updated")
        return {'FINISHED'}


class OBJECT_OT_tt_add_animation(bpy.types.Operator):
    bl_idname = "turntable.add_animation"
    bl_label = "Add Turntable Animation"
    bl_description = "Add 0->360° looping rotation keyframes on the target (Z axis)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.scene.turntable.tt_target if context.scene.turntable.tt_target else context.active_object
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "Please select a Mesh target or set Target in panel")
            return {'CANCELLED'}
        if target.animation_data:
            target.animation_data_clear()
            frames = context.scene.frame_end
            target.rotation_mode = 'XYZ'
            base = target.rotation_euler.z
            target.keyframe_insert(data_path="rotation_euler", frame=1, index=2)
            target.rotation_euler.z = base + 2 * math.pi
            target.keyframe_insert(data_path="rotation_euler", frame=frames, index=2)
            act = target.animation_data.action
        else:
            frames = context.scene.frame_end
            target.rotation_mode = 'XYZ'
            base = target.rotation_euler.z
            target.keyframe_insert(data_path="rotation_euler", frame=1, index=2)
            target.rotation_euler.z = base + 2 * math.pi
            target.keyframe_insert(data_path="rotation_euler", frame=frames, index=2)
            act = target.animation_data.action
        for fc in act.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
        self.report({'INFO'}, f"Added rotation animation to {target.name} ({frames} frames)")
        return {'FINISHED'}


# ---- Light List Operators ----
class LIST_OT_light_list_add(bpy.types.Operator):
    bl_idname = "scene.light_list_add"
    bl_label = "Add"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def execute(self, context):
        sc = context.scene

        light_data = bpy.data.lights.new('Light', 'AREA')
        light = bpy.data.objects.new('Light', light_data)
        target = sc.turntable.tt_target

        sx, sy, sz = tt_utils.get_world_bounds_size(target)
        max_s = max(sx, sy, sz, 0.001)

        tt_utils.create_or_update_area_light(light.name, light_data.name, target, (0, 0, max_s), light_data.energy,
                                             light_data.color, max_s)

        return {'FINISHED'}


class LIST_OT_light_list_delete(bpy.types.Operator):
    bl_idname = "scene.light_list_delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        col = bpy.data.collections.get(tt_utils.LIGHT_COLLECTION)
        return col.objects.values()

    @staticmethod
    def execute(self, context):
        col = bpy.data.collections.get(tt_utils.LIGHT_COLLECTION)

        light = col.objects[col.light_list_index]
        light_data = light.data

        col.objects.unlink(light)
        bpy.data.objects.remove(light)
        bpy.data.lights.remove(light_data)

        index = col.light_list_index
        col.light_list_index = min(max(0, index - 1), len(col.objects))

        return {'FINISHED'}
