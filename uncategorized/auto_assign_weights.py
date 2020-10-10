import bpy
from zpy import Get, Is, Set


class POSE_OT_auto_weights(bpy.types.Operator):
    bl_description = "Macro to run auto-weights on bones (temporarily increase scale, to avoid bone-heat failure)"
    bl_idname = 'zpy.auto_bone_weights'
    bl_label = "Assign Automatic Weights"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        ob = context.object

        if Is.armature(ob) and ob.mode in ('POSE', 'EDIT'):
            return Get.selected(context, ob)

        if not bpy.ops.paint.weight_from_bones.poll(context.copy()):
            return

        if Is.mesh(ob) and (ob.mode == 'WEIGHT_PAINT'):
            for mod in ob.modifiers:
                if (mod.type == 'ARMATURE') and (mod.object in Get.objects(context)[:]):
                    if mod.object.mode == 'POSE':
                        return True

    def execute(self, context):
        active = context.object
        if context.mode == 'PAINT_WEIGHT':
            meshes = {active}
            rig = None
            for mod in active.modifiers:
                if (mod.type == 'ARMATURE') and (mod.object in Get.objects(context)[:]):
                    rig = mod.object
                    if rig.mode == 'POSE':
                        break
            if not rig:
                self.report({'ERROR'}, "Can't find rig using the active mesh")
                return {'CANCELLED'}
        else:
            rig = active
            meshes = set()
            for ob in context.selected_objects:
                if Is.mesh(ob):
                    for mod in ob.modifiers:
                        if (mod.type == 'ARMATURE') and (mod.object == rig):
                            meshes.add(ob)

            if not meshes:
                for ob in Get.objects(context):
                    if not Is.visible(context, ob):
                        continue

                    for mod in ob.modifiers:
                        if (mod.type == 'ARMATURE') and (mod.object == rig):
                            meshes.add(ob)

            if not meshes:
                self.report({'ERROR'}, "Can't find mesh using the active rig")
                return {'CANCELLED'}

        mode = active.mode
        pose = rig.data.pose_position
        scale = rig.scale.copy()

        Set.mode(context, None, 'OBJECT')
        rig.data.pose_position = 'REST'
        rig.scale *= 50

        for mesh in meshes:
            mscale = mesh.scale.copy()
            mp = mesh.parent
            while mp and mp != rig:
                # Sort through mesh parent hierarchy to find if the rig is a parent somewhere in there
                mp = mp.parent
            if mp != rig:
                mesh.scale *= 50
            Set.active(context, mesh)
            Set.mode(context, None, 'WEIGHT_PAINT')

            bpy.ops.paint.weight_from_bones(type='AUTOMATIC')

            Set.mode(context, None, 'OBJECT')
            mesh.scale = mscale

        Set.active(context, active)
        rig.scale = scale
        rig.data.pose_position = pose
        Set.mode(context, None, mode)

        if len(meshes) > 1:
            self.report({'INFO'}, f"Assigned weights to {len(meshes)} meshes")
        else:
            self.report({'INFO'}, f"Assigned weights to {list(meshes)[0].name}")

        return {'FINISHED'}


def draw_menu(self, context):
    layout = self.layout
    layout.operator('zpy.auto_bone_weights')


def register():
    bpy.types.VIEW3D_MT_paint_weight.append(draw_menu)
    bpy.types.VIEW3D_MT_pose.append(draw_menu)
    bpy.types.VIEW3D_MT_edit_armature.append(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_paint_weight.remove(draw_menu)
    bpy.types.VIEW3D_MT_pose.remove(draw_menu)
    bpy.types.VIEW3D_MT_edit_armature.remove(draw_menu)
