import bpy


class POSE_OT_remove_unused_bone_groups(bpy.types.Operator):
    bl_description = "Remove unused bone groups from active object"
    bl_idname = 'pose.remove_unused_bone_groups'
    bl_label = "Remove Unused Bone Groups"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        rig = context.object
        return (rig and rig.type == 'ARMATURE' and rig.pose and rig.pose.bone_groups)

    def execute(self, context):
        rig = context.object
        groups = set(rig.pose.bone_groups)

        # Remove unused bone groups
        for pbone in rig.pose.bones:
            if pbone.bone_group in groups:
                groups.remove(pbone.bone_group)

        count = len(groups)
        while groups:
            rig.pose.bone_groups.remove(groups.pop())
        self.report({'INFO'}, f"Removed {count} unused bone groups")

        return {'FINISHED'}


def draw(self, context):
    layout = self.layout
    layout.operator('pose.remove_unused_bone_groups')


def register():
    bpy.types.DATA_MT_bone_group_context_menu.append(draw)


def unregister():
    bpy.types.DATA_MT_bone_group_context_menu.remove(draw)
