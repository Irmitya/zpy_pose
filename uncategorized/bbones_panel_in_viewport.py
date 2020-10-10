import bpy
from zpy import Is


class VIEW3D_BONE_PT_curved(bpy.types.Panel):
    bl_category = "Item"
    bl_label = "Bendy Bones"
    bl_options = {'DEFAULT_CLOSED'}
    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'

    @classmethod
    def poll(cls, context):
        bone = context.active_bone
        bbone = context.active_pose_bone

        if (bone and Is.linked(bone) and bone.bbone_segments == 1):
            return

        return (bone or bbone)

    def draw(self, context):
        arm = context.object.data
        bone = context.active_bone
        bbone = context.active_pose_bone

        if bbone is None:
            bbone = bone
        elif bone is None:
            arm = bbone.id_data.data
            bone = bbone.bone

        linked = Is.linked(bbone)

        layout = self.layout
        layout.use_property_split = True

        if not linked:
            layout.prop(bone, "bbone_segments", text="Segments")

            col = layout.column(align=True)
            col.prop(bone, "bbone_x", text="Display Size X")
            col.prop(bone, "bbone_z", text="Z")

        topcol = layout.column()
        topcol.active = bone.bbone_segments > 1

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_curveinx", text="Curve In X")
        col.prop(bbone, "bbone_curveoutx", text="Out X")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_curveiny", text="Curve In Y")
        col.prop(bbone, "bbone_curveouty", text="Out Y")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_rollin", text="Roll In")
        col.prop(bbone, "bbone_rollout", text="Out")
        if not linked:
            col.prop(bone, "use_endroll_as_inroll")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_scaleinx", text="Scale In X")
        col.prop(bbone, "bbone_scaleiny", text="In Y")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_scaleoutx", text="Scale Out X")
        col.prop(bbone, "bbone_scaleouty", text="Out Y")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_easein", text="Ease In")
        col.prop(bbone, "bbone_easeout", text="Out")

        if not linked:
            col = topcol.column(align=True)
            col.prop(bone, "bbone_handle_type_start", text="Start Handle")

            col = col.column(align=True)
            col.active = (bone.bbone_handle_type_start != 'AUTO')
            col.prop_search(bone, "bbone_custom_handle_start", arm, "bones", text="Custom")

            col = topcol.column(align=True)
            col.prop(bone, "bbone_handle_type_end", text="End Handle")

            col = col.column(align=True)
            col.active = (bone.bbone_handle_type_end != 'AUTO')
            col.prop_search(bone, "bbone_custom_handle_end", arm, "bones", text="Custom")

            # Detach BBones
            row = layout.row(align=True)
            row.operator('pose.attach_bbone', text="In").end = False
            row.operator('pose.detachbbone', text="Default")
            row.operator('pose.attach_bbone', text="Out").end = True


class VIEW3D_BONE_PT_curved_edit(bpy.types.Panel):
    bl_category = "Item"
    bl_label = "Bendy Bones (Edit)"
    bl_options = {'DEFAULT_CLOSED'}
    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_parent_id = 'VIEW3D_BONE_PT_curved'

    @classmethod
    def poll(cls, context):
        bone = context.active_bone
        bbone = context.active_pose_bone
        if bbone and not bone:
            bone = bbone.bone

        return (context.mode != 'EDIT_ARMATURE') and bone and not Is.linked(bone)

    def draw(self, context):
        bone = context.active_bone
        bbone = context.active_pose_bone
        if bbone and not bone:
            bone = bbone.bone

        layout = self.layout
        layout.use_property_split = True

        topcol = layout.column()
        topcol.active = bone.bbone_segments > 1

        col = topcol.column(align=True)
        col.prop(bone, "bbone_easein", text="Ease In")
        col.prop(bone, "bbone_easeout", text="Out")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_curveinx", text="Curve In X")
        col.prop(bone, "bbone_curveoutx", text="Out X")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_curveiny", text="Curve In Y")
        col.prop(bone, "bbone_curveouty", text="Out Y")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_rollin", text="Roll In")
        col.prop(bone, "bbone_rollout", text="Out")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_scaleinx", text="Scale In X")
        col.prop(bone, "bbone_scaleiny", text="In Y")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_scaleoutx", text="Scale Out X")
        col.prop(bone, "bbone_scaleouty", text="Out Y")
