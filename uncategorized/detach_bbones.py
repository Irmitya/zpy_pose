import bpy
from bpy.types import Operator
from zpy import Get


class BBONES_OT_detach_bbone(Operator):
    bl_idname = 'pose.detachbbone'
    bl_label = "Default Custom Handle"
    bl_description = "Set Custom Handles to default targets"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if (context.mode == 'POSE'):
            return context.selected_pose_bones
        elif (context.mode == 'EDIT_ARMATURE'):
            return context.selected_bones

    def __init__(self):
        self.selected = False

    def invoke(self, context, event):
        self.selected = event.alt
        return self.execute(context)

    def execute(self, context):
        if (context.mode == 'POSE'):
            if self.selected:
                bones = context.selected_pose_bones
            else:
                bones = [context.active_pose_bone]
        elif (context.mode == 'EDIT_ARMATURE'):
            if self.selected:
                bones = context.selected_bones
            else:
                bones = [context.active_bone]
        else:
            return {'CANCELLED'}

        default_auto = None

        for _bone in bones:
            if (context.mode == 'POSE'):
                bone = _bone.bone
                if _bone.child:
                    child = _bone.child.bone
                else:
                    # No bone connected, so try to find a substitute
                    child = self.get_closest_child(bone)
            elif (context.mode == 'EDIT_ARMATURE'):
                bone = _bone
                child = None
                if len(bone.children) == 1:
                    child = bone.children[0]
                elif bone.children:
                    for bone_child in bone.children:
                        if bone_child.use_connect:
                            if (child is not None):
                                child_dist = Get.distance(child.tail, bone.tail)
                                active_dist = Get.distance(bone_child.tail, bone.tail)
                                if (child_dist == active_dist):
                                    # both children tails same distance from bone
                                    # Just sort alphabetically
                                    child = sorted((b.name, b) for b in [child, bone_child])[0][1]
                                    continue
                                elif (child_dist < active_dist):
                                    # Previous is closes
                                    continue
                            child = bone_child
                    if child is None:
                        # No bone connected, so try to find a substitute
                        child = self.get_closest_child(bone)

            if default_auto is None:
                default_auto = 'AUTO' not in (bone.bbone_handle_type_start, bone.bbone_handle_type_end)

            if default_auto:
                bone.bbone_handle_type_start = bone.bbone_handle_type_end = 'AUTO'
                bone.bbone_custom_handle_end = bone.bbone_custom_handle_start = None
            else:
                if (bone.bbone_handle_type_start == 'AUTO'):
                    bone.bbone_handle_type_start = 'ABSOLUTE'
                if (bone.bbone_handle_type_end == 'AUTO'):
                    bone.bbone_handle_type_end = 'ABSOLUTE'

                bone.bbone_custom_handle_end = child\
                    if child else None
                bone.bbone_custom_handle_start = bone.parent\
                    if bone.parent else None

        return {'FINISHED'}

    @staticmethod
    def get_closest_child(bone):
        if len(bone.children) == 1:
            return bone.children[0]
        elif bone.children:
            # Multiple children, None connected; search by distance
            children = dict()
            for bone_child in bone.children:
                dist = Get.distance(bone_child.head, bone.tail)
                if dist not in children:
                    children[dist] = list()
                children[dist].append(bone_child)

            closest = children[sorted(children)[0]]
            if len(closest) == 1:
                return closest[0]
            else:
                # Multiple children same distance from bone; check tail distanxce
                children = dict()
                for bone_child in closest:
                    dist = Get.distance(bone_child.tail, bone.tail)
                    if dist not in children:
                        children[dist] = list()
                    children[dist].append(bone_child)
                closest = children[sorted(children)[0]]
                if len(closest) == 1:
                    return closest[0]
                else:
                    # All children tails same distance from bone
                    # Just sort alphabetically
                    return sorted((b.name, b) for b in closest)[0][1]


class BBONES_OT_attach(Operator):
    bl_description = "Attach selected bone as active bone's custom bbone handle"
    bl_idname = 'pose.attach_bbone'
    bl_label = "Set Custom Handle"
    bl_options = {'REGISTER', 'UNDO'}
    bl_undo_group = ""

    @classmethod
    def poll(self, context):
        if (context.mode == 'POSE'):
            return len(Get.selected_pose_bones(context)) > 1
        elif (context.mode == 'EDIT_ARMATURE'):
            return len([b for b in Get.selected_bones(context) if b.select]) > 1

    def execute(self, context):
        bb = None
        if (context.mode == 'POSE'):
            b = context.active_pose_bone
            for bone in context.selected_pose_bones:
                if (bone != b) and (bone.id_data == b.id_data):
                    b = b.bone
                    bb = bone.bone
                    break
        elif (context.mode == 'EDIT_ARMATURE'):
            b = context.active_bone
            for bone in [b for b in context.selected_bones if b.select]:
                if (bone != b) and (bone.id_data == b.id_data):
                    bb = bone
                    break

        if bb is None:
            self.report({'ERROR'}, "Must select two bones from the same object")
            return {'CANCELLED'}

        # b.use_bbone_custom_handles = True

        if self.end:
            if b.bbone_handle_type_end == 'AUTO':
                b.bbone_handle_type_end = 'ABSOLUTE'
            b.bbone_custom_handle_end = bb
        else:
            if b.bbone_handle_type_start == 'AUTO':
                b.bbone_handle_type_start = 'ABSOLUTE'
            b.bbone_custom_handle_start = bb

        return {'FINISHED'}

    end: bpy.props.BoolProperty(
        name="Out",
        description="Set as bone's custom end",
        default=False,
        options={'SKIP_SAVE'},
    )


def detach_bbone_button(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.operator('pose.attach_bbone', text="In").end = False
    row.operator('pose.detachbbone', text="Default")
    row.operator('pose.attach_bbone', text="Out").end = True


def register():
    bpy.types.BONE_PT_curved.append(detach_bbone_button)


def unregister():
    bpy.types.BONE_PT_curved.remove(detach_bbone_button)
