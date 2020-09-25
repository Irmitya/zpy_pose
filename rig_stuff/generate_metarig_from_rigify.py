import bpy
from zpy import Is, Get, Set, New, utils


class MACRO_OT_meta_from_rigify(bpy.types.Operator):
    bl_description = "Regenerate metarigs based on ORG bones in a Rigify rig"
    bl_idname = 'macro.meta_from_rigify'
    bl_label = "Generate Meta from Rigify"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        for rig in context.selected_objects:
            if (not Is.armature(rig)) or (rig.data.get('rig_id') is None):
                continue
            return True

    def execute(self, context):
        # active = Get.active(context)
        mode = context.mode
        # pose = list()

        for rig in context.selected_objects:
            if (not Is.armature(rig)) or (rig.data.get('rig_id') is None):
                continue

            meta = New.object(context, name="metarig", data=rig.data.copy())
            meta.data.animation_data_clear()
            metafy_rigify(context, meta)
            # pose.append(meta, rig)
        else:
            if context.mode != mode:
                bpy.ops.object.mode_set(mode=mode)
            # if mode == 'POSE':
            #     Set.mode(context, None, 'OBJECT')
            # for (meta, rig) in pose:
            #     Set.select(rig, True)
            #     Set.select(meta, False)
            #     if meta == active:
            #         Set.active(context, rig)
            # if mode == 'POSE':
            #     Set.mode(context, None, 'POSE')

        return {'FINISHED'}


def metafy_rigify(context, rig):
    """Isolate Org bones in rig, then mimic the likely original bone layers"""

    Set.mode(context, rig, 'EDIT')

    bones = rig.data.edit_bones
    for bone in bones.values():
        bone.inherit_scale = 'ALIGNED'
        if bone.name.startswith('ORG-'):
            bone.layers = utils.layer(0)
        else:
            bones.remove(bone)

    Set.mode(context, rig, 'POSE')

    for bone in rig.pose.bones:
        bone.lock_rotation_w = False
        for index in range(3):
            bone.lock_location[index] = False
            bone.lock_rotation[index] = False
            bone.lock_scale[index] = False

    rig.data.layers = utils.layer(0)
