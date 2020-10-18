import bpy
from bpy.props import EnumProperty
from bpy.types import Operator, Menu
from zpy import Get, Set, Is, utils


class MERGE_OT_vgroups(Operator):
    bl_description = ""
    bl_idname = 'zpy.merge_vertex_groups'
    bl_label = "Merge Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return

    @classmethod
    def poll(cls, context):
        if context.mode not in ('POSE', 'PAINT_WEIGHT'):
            return
        return len(Get.selected_pose_bones(context)) > 1

    def execute(self, context):
        rig = context.active_object
        active = None

        if context.mode == 'PAINT_WEIGHT':
            for obj in context.selected_objects:
                if obj.type == 'ARMATURE':
                    active = rig
                    rig = obj
                    Set.active(context, rig)

        # if rig.type =='ARMATURE' and context.mode != 'EDIT_ARMATURE':

        meshes = self.get_meshes(context, rig)

        bone1 = context.active_pose_bone
        # bone2 = context.selected_pose_bones[1]
        for bone2 in context.selected_pose_bones:
            if bone2 == bone1:
                continue
            found = None

            for mesh in meshes:
                utils.merge_vertex_groups(mesh, bone1.name, bone2.name,
                    # If remove is False, and the bone stayed, it would be equivalent to transferring only partial weights
                    remove=(self.mode == 'remove'))
                found = True

            # if found:
                # if self.mode == 'hide':
                #     bone2.hide = True
                # elif self.mode == 'show':
                #     bone2.hide = False
                # elif self.mode == 'remove':
            if (found and self.mode == 'remove'):
                for ch in bone2.id_data.children:
                    if (ch.parent_type == 'BONE') and (ch.parent_bone == bone2.name):
                        mat = Get.matrix(ch)
                        ch.parent_bone = bone1.name
                        Set.matrix(ch, mat)
                name2 = bone2.name
                Set.mode(context, None, mode='EDIT')
                bone2 = rig.data.edit_bones[name2]
                rig.data.edit_bones.remove(bone2)
                Set.mode(context, None, mode='POSE')

        if active:
            Set.active(context, active)

        return {'FINISHED'}

    def get_meshes(self, context, rig):
        meshes = set()

        for ob in context.selected_objects:
            if Is.mesh(ob):
                for mod in ob.modifiers:
                    if (mod.type == 'ARMATURE') and (mod.object == rig):
                        meshes.add(ob)

        if not meshes:
            for ob in bpy.data.objects:
                if not Is.mesh(ob):
                    continue

                for modifier in ob.modifiers:
                    if (modifier.type == 'ARMATURE') and (modifier.object == rig):
                        meshes.add(ob)

        return meshes

    mode: EnumProperty(
        items=[
            # ('hide', "Hide", "Description"),
            # ('show', "Show", "Description"),
            ('keep', "Keep", "Transfer weights from selected bones and keep them all"),
            ('remove', "Remove", "Remove selected bones and merge to active"),
        ],
        name="",
        description="Keep or remove the selected bones after transferring their weights to the active bone",
    )


class SUBTRACT_OT_vgroups(Operator):
    bl_description = "Remove influence of the active bone's vertex group from select bones' vertex groups"
    bl_idname = 'zpy.subtract_vertex_groups'
    bl_label = "Subtract Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if properties.target == 'active':
            txt = "Remove influence of the selected bone's vertex groups from active bone's vertex group" + \
            "\n(Decrease strength of active bone)"
        # elif properties.target == 'selected':
            # txt = "Remove influence of the active bone's vertex group from select bones' vertex groups"
        else:
            txt = cls.bl_description + "\n(Increase strength of active bone)"

        return txt

    @classmethod
    def poll(cls, context):
        if context.mode not in ('POSE', 'PAINT_WEIGHT'):
            return
        return len(Get.selected_pose_bones(context)) > 1

    def execute(self, context):
        objs = self.get_objs(context)
        active_bone = context.active_pose_bone
        selected_bones = [b for b in Get.selected_pose_bones(context) if b != active_bone]

        for ob in objs:
            for b in selected_bones:
                if self.target == 'selected':
                    utils.subtract_vertex_groups(ob, active_bone.name, b.name)
                elif self.target == 'active':
                    utils.subtract_vertex_groups(ob, b.name, active_bone.name)

        return {'FINISHED'}

    def get_objs(self, context):
        if context.mode == 'PAINT_WEIGHT':
            objs = [context.object]
        else:
            objs = list()

            rig = context.active_pose_bone.id_data
            for ob in context.selected_objects:
                if Is.mesh(ob):
                    for mod in ob.modifiers:
                        if (mod.type == 'ARMATURE') and (mod.object == rig):
                            objs.append(ob)

            if not objs:
                for b in context.selected_pose_bones:
                    for mesh in bpy.data.objects:
                        if mesh.type != 'MESH':
                            continue

                        for modifier in mesh.modifiers:
                            if modifier.type == 'ARMATURE' and modifier.object == b.id_data:
                                if mesh not in objs:
                                    objs.append(mesh)

        return objs

    target: EnumProperty(
        items=[
            ('selected', "From Selected", "Remove vertex group influence from the selected bones, based on the active bone"),
            ('active', "From Active", "Remove vertex group influence from the active bone, based on the selected bones"),
        ],
        name="Target",
        description="Bone(s) to maintain influence of",
        default=None,  # ('string' or {'set'})  from items
        options={'SKIP_SAVE'},
    )


def draw_menu(self, context):
    layout = self.layout
    layout.menu('POSE_MT_merge_vg', text="Merge Vertex Groups", icon='NONE')


class POSE_MT_merge_vg(Menu):
    bl_description = ""
    # bl_idname = 'POSE_MT_merge_vg'
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout

        # layout.operator('zpy.merge_vertex_groups', text="Keep Bones (Show)").mode = 'show'
        # layout.operator('zpy.merge_vertex_groups', text="Keep Bones (Hide)").mode = 'hide'
        layout.operator('zpy.merge_vertex_groups', text="Keep Bones").mode = 'keep'
        layout.operator('zpy.merge_vertex_groups', text="Remove Bones").mode = 'remove'
        layout.separator()
        layout.operator('zpy.subtract_vertex_groups', text="Subtract Vertex Groups (from active)").target = 'active'
        layout.operator('zpy.subtract_vertex_groups', text="Subtract Vertex Groups (from selected)").target = 'selected'


def register():
    bpy.types.VIEW3D_MT_pose.append(draw_menu)
    bpy.types.VIEW3D_MT_paint_weight.append(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_pose.remove(draw_menu)
    bpy.types.VIEW3D_MT_paint_weight.remove(draw_menu)
