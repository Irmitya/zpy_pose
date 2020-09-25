import bpy
from zpy import register_keymaps, keyframe, Get
km = register_keymaps()


class ANGLE_OT_flip_quat(bpy.types.Operator):
    bl_idname = 'zpy.flip_quats'
    bl_label = "Flip Quaternions"
    bl_description = "Reverse Quaternion direction of selected (fixes gimble lock)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.mode in ('OBJECT', 'POSE'):
            for src in Get.selected(context):
                if src.rotation_mode in ('QUATERNION', 'AXIS_ANGLE'):
                    return True

    def execute(self, context):
        for src in Get.selected(context):
            if src.rotation_mode in ('QUATERNION', 'AXIS_ANGLE'):
                src.rotation_quaternion *= -1

                for (i, r) in enumerate(src.rotation_axis_angle):
                    src.rotation_axis_angle[i] *= -1

                if keyframe.use_auto(context):
                    keyframe.rotation(context, src)

        return {'FINISHED'}


def register():
    args = dict(idname='zpy.flip_quats', type='F', alt=True)

    # Flip Quaternions
    km.add(**args, name='Pose')
    km.add(**args, name='Object Mode')


def unregister():
    km.remove()
