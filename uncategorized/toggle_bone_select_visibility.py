import bpy
from zpy import Is


class BONE_OT_toggle_selects(bpy.types.Operator):
    bl_description = "Toggle selectability for selected bones"
    bl_idname = 'zpy.toggle_bone_selects'
    bl_label = "Toggle Bone Selectability"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.selected_bones or context.selected_pose_bones

    def execute(self, context):
        if context.visible_pose_bones:
            selected_bones = [b.bone for b in context.selected_pose_bones]
        else:
            selected_bones = list(context.selected_bones)

        for bone in selected_bones:
            if self.enable:
                bone.hide_select = True
            else:
                bone.hide_select = not bone.hide_select

        return {'FINISHED'}

    enable: bpy.props.BoolProperty(options={'SKIP_SAVE'})


class BONE_OT_select_disabled(bpy.types.Operator):
    bl_description = "Select bones that have their selection disabled"
    bl_idname = 'zpy.select_locked_bones'
    bl_label = "Select Locked Bones"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return context.visible_bones or context.visible_pose_bones

    def invoke(self, context, event):
        if event.shift:
            self.extend = True
        return self.execute(context)

    def execute(self, context):
        if context.visible_pose_bones:
            is_pose = True
            visible_bones = [b.bone for b in context.visible_pose_bones]
        else:
            is_pose = False
            visible_bones = list(context.visible_bones)

        armatures = list()
        bones = list()
        for bone in visible_bones:
            if not self.extend:
                bone.select = bone.select_head = bone.select_tail = False
            arm = bone.id_data
            if arm in armatures:
                continue
            armatures.append(arm)
            if is_pose:
                arm.bones.active = None
            else:
                arm.edit_bones.active = None

        for arm in armatures:
            if is_pose:
                bones = arm.bones
            else:
                bones = arm.edit_bones

            for bone in bones:
                if bone.hide_select and Is.visible(context, bone):
                    bone.select = True
                    bones.active = bone

        return {'FINISHED'}

    extend: bpy.props.BoolProperty(options={'SKIP_SAVE'})


def draw_toggle(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    layout.operator('zpy.toggle_bone_selects', text="Selectability", icon='RESTRICT_SELECT_OFF')
    layout.operator('zpy.select_locked_bones', icon='VIS_SEL_11')


def draw_enable(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    layout.operator('zpy.toggle_bone_selects', text="Selectability", icon='RESTRICT_SELECT_OFF').enable = True
    layout.operator('zpy.select_locked_bones', icon='VIS_SEL_11')


def register():
    bpy.types.VIEW3D_MT_bone_options_toggle.append(draw_toggle)
    bpy.types.VIEW3D_MT_bone_options_enable.append(draw_enable)


def unregister():
    bpy.types.VIEW3D_MT_bone_options_toggle.remove(draw_toggle)
    bpy.types.VIEW3D_MT_bone_options_enable.remove(draw_enable)
