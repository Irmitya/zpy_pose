import bpy


class BONE_PT_curved_edit(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    bl_parent_id = 'BONE_PT_curved'
    bl_label = "Bendy Bones (Edit)"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode != 'EDIT_ARMATURE'

    def draw(self, context):
        # ob = context.object
        bone = context.bone
        # arm = context.armature
        # bone_list = "bones"

        # if ob and bone:
        #     bbone = ob.pose.bones[bone.name]
        # elif bone is None:
        #     bone = context.edit_bone
        #     bbone = bone
        #     bone_list = "edit_bones"
        # else:
        #     bbone = bone

        layout = self.layout
        layout.use_property_split = True

        topcol = layout.column()
        topcol.active = bone.bbone_segments > 1

        col = topcol.column(align=True)
        col.prop(bone, "bbone_easein", text="Ease In")
        col.prop(bone, "bbone_easeout", text="Out")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_curveinx", text="Curve In X")
        col.prop(bone, "bbone_curveiny", text="In Y")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_curveoutx", text="Curve Out X")
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
