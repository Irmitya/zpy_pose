import bpy


class VIEW3D_BONE_PT_curved(bpy.types.Panel):
    bl_category = "Item"
    bl_label = "Bendy Bones"
    bl_options = {'DEFAULT_CLOSED'}
    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'

    @classmethod
    def poll(cls, context):
        return (context.active_bone or context.active_pose_bone)

    def draw(self, context):
        ob = context.object
        bone = context.active_bone
        bone_list = "bones"

        if (context.mode == 'EDIT_ARMATURE'):
            bbone = bone
        elif bone is None:
            bbone = context.active_pose_bone
            bone = bbone.bone
            ob = bbone.id_data
        else:
            bbone = ob.pose.bones[bone.name]

        arm = ob.data

        layout = self.layout
        layout.use_property_split = True

        layout.prop(bone, "bbone_segments", text="Segments")

        col = layout.column(align=True)
        col.prop(bone, "bbone_x", text="Display Size X")
        col.prop(bone, "bbone_z", text="Z")

        topcol = layout.column()
        topcol.active = bone.bbone_segments > 1

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_curveinx", text="Curve In X")
        col.prop(bbone, "bbone_curveiny", text="In Y")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_curveoutx", text="Curve Out X")
        col.prop(bbone, "bbone_curveouty", text="Out Y")

        col = topcol.column(align=True)
        col.prop(bbone, "bbone_rollin", text="Roll In")
        col.prop(bbone, "bbone_rollout", text="Out")
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

        col = topcol.column(align=True)
        col.prop(bone, "bbone_handle_type_start", text="Start Handle")

        col = col.column(align=True)
        col.active = (bone.bbone_handle_type_start != 'AUTO')
        col.prop_search(bone, "bbone_custom_handle_start", arm, bone_list, text="Custom")

        col = topcol.column(align=True)
        col.prop(bone, "bbone_handle_type_end", text="End Handle")

        col = col.column(align=True)
        col.active = (bone.bbone_handle_type_end != 'AUTO')
        col.prop_search(bone, "bbone_custom_handle_end", arm, bone_list, text="Custom")

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
        return (context.mode != 'EDIT_ARMATURE')

    def draw(self, context):
        bone = context.active_bone

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
