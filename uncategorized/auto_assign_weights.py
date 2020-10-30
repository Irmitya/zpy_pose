import bpy
from zpy import Get, Is, Set, utils


class POSE_OT_auto_weights(bpy.types.Operator):
    bl_description = "Macro to run auto-weights on bones (temporarily increase scale, to avoid bone-heat failure)"
    bl_idname = 'zpy.auto_bone_weights'
    bl_label = "Assign Automatic Weights"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        text = cls.bl_description
        if properties.normalize_active or properties.from_active:
            text += ".\n" "Limit the weights of the selected bones, to the range of the active bone's current weight"
        if properties.normalize_active:
            text += ".\n" "After assigning the weights, remove the selected bones' auto-weights from the active bone's"
        return text

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
        (rig, meshes) = self.get_rig_meshes(context)
        if not (rig and meshes):
            return {'CANCELLED'}

        use_mask = bool((self.from_active or self.normalize_active))
        active = context.object
        active_bone = context.active_pose_bone.bone
        mode = active.mode
        pose = rig.data.pose_position
        scale = rig.scale.copy()

        if use_mask:
            active_bone.select = False

        Set.mode(context, 'OBJECT')
        rig.data.pose_position = 'REST'
        rig.scale *= 50

        for mesh in meshes:
            mscale = mesh.scale.copy()
            mp = mesh.parent
            while mp and mp != rig:
                # Sort through mesh parent hierarchy to find if the rig is a parent somewhere in there
                mp = mp.parent
            if mp != rig:
                # The rig/parent is already scaled, so don't scale mesh again
                mesh.scale *= 50
            Set.active(context, mesh)
            Set.mode(context, 'WEIGHT_PAINT')

            vg = mesh.vertex_groups
            bone_group = vg.get(active_bone.name)
            do_bone = bool((use_mask and bone_group))
            mindex = vg.active_index

            bpy.ops.paint.weight_from_bones(type='AUTOMATIC')

            if do_bone:
                vg.active_index = mindex
                bpy.ops.object.vertex_group_invert()
                for b in context.selected_pose_bones:
                    utils.subtract_vertex_groups(mesh, active_bone.name, b.name)
                bpy.ops.object.vertex_group_invert()
                if self.normalize_active:
                    for b in context.selected_pose_bones:
                        utils.subtract_vertex_groups(mesh, b.name, active_bone.name)

            if (mindex != -1):
                vg.active_index = mindex

            Set.mode(context, 'OBJECT')
            mesh.scale = mscale

        Set.active(context, active)
        rig.scale = scale
        rig.data.pose_position = pose
        Set.mode(context, mode)

        if use_mask:
            active_bone.select = True

        if len(meshes) > 1:
            self.report({'INFO'}, f"Assigned weights to {len(meshes)} meshes")
        else:
            self.report({'INFO'}, f"Assigned weights to {list(meshes)[0].name}")

        return {'FINISHED'}

    def get_rig_meshes(self, context):
        """
        Find the selected rigs and meshes, attached together.
        If only a rig is selected, find all the meshes that use it.
        """

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

        return (rig, meshes)

    from_active: bpy.props.BoolProperty(
        name="From Active",
        description="Only assign weights used by the active bone",
        default=False,
        options={'SKIP_SAVE'},
    )

    normalize_active: bpy.props.BoolProperty(
        name="Normalize Active",
        description="Normalize the active bone with the selected bones",
        default=False,
        options={'SKIP_SAVE'},
    )


class WEIGHT_MT_assign_auto(bpy.types.Menu):
    bl_description = ""
    # bl_idname = 'WEIGHT_MT_assign_auto'
    bl_label = "Assign Automatic Weights"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator('zpy.auto_bone_weights', text="Assign Automatic Weights")
        layout.operator('zpy.auto_bone_weights', text="Assign Automatic Weights (Mask)").from_active = True
        layout.operator('zpy.auto_bone_weights', text="Assign Automatic Weights (Normalize)").normalize_active = True


def draw_menu(self, context):
    layout = self.layout
    layout.menu('WEIGHT_MT_assign_auto', icon='MOD_VERTEX_WEIGHT')


def register():
    bpy.types.VIEW3D_MT_paint_weight.append(draw_menu)
    bpy.types.VIEW3D_MT_pose.append(draw_menu)
    bpy.types.VIEW3D_MT_edit_armature.append(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_paint_weight.remove(draw_menu)
    bpy.types.VIEW3D_MT_pose.remove(draw_menu)
    bpy.types.VIEW3D_MT_edit_armature.remove(draw_menu)
