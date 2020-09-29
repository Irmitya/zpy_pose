import bpy
from bpy.props import EnumProperty, BoolProperty
from zpy import Get, Set, utils, register_keymaps
km = register_keymaps()


class POSE_OT_set_parent(bpy.types.Operator):
    bl_description = "Set the active bone as parent of the selected bones"
    bl_idname = 'zpy.set_parent'
    bl_label = "Make Parent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.mode == 'PAINT_WEIGHT': return
        return Get.selected_pose_bones(context)

    def execute(self, context):
        # TODO: Redo / Cleanup code
        class props:
            keep_matrix = True
            connect = False
            connect_child = False
            stretch = False

            if self.type == 'BONE':
                pass
            elif self.type == 'BONE_CONNECT':
                connect = True
            elif self.type == 'STRETCH':
                stretch = True
            elif self.type == 'STRETCH_CONNECT':
                stretch = True
                connect = True
            elif self.type == 'CHILD_CONNECT':
                connect_child = True

        ap = context.active_pose_bone
        bones = dict()
        matrices = {b: b.matrix.copy() for b in context.selected_pose_bones}

        for rig in context.selected_objects:
            if rig.mode != 'POSE':
                continue

            Set.mode(context, rig, 'EDIT')
            mirror = rig.data.use_mirror_x
            rig.data.use_mirror_x = False

            ab = context.active_bone
            edit_bones = Get.selected_edit_bones(context, rig)
            if ab and ab.parent in edit_bones:
                for eb in [*ab.parent_recursive, None]:
                    if eb in edit_bones:
                        # bones.append((rig, eb.name))
                        continue
                    ab.use_connect = False
                    ab.parent = eb
                    bones[ab.name] = rig
                    break
            for eb in edit_bones:
                if props.connect_child:
                    for bb in eb.children:
                        if bb in edit_bones:
                            eb.tail = bb.head
                            bb.use_connect = True
                else:
                    if eb == ab:    # or it'll delete itself
                        continue
                    eb.use_connect = False
                    if props.stretch:
                        eb.head = ab.tail
                    eb.parent = ab
                    bones[eb.name] = rig
                    if props.connect:
                        head = ab.tail - eb.head
                        tail = ab.tail - eb.tail
                        connects = []
                        for ebc in [*eb.children_recursive, eb]:
                            connects.append([ebc, ebc.use_connect])
                            ebc.use_connect = False
                        for ebc, c in connects:
                            ebc.translate(ab.tail - eb.head)
                        for ebc, c in connects:
                            ebc.use_connect = c
                        eb.use_connect = True

            rig.data.use_mirror_x = mirror
            Set.mode(context, rig, 'POSE')

        if props.keep_matrix:
            # ap.matrix = matrices[ap]
            # update()
            for b in bones:
                rig = bones[b]
                bone = rig.pose.bones.get(b)
                if bone is None:
                    print(f"{rig.name} can't find {b}",
                          *rig.pose.bones, sep='\n\t')
                    continue
                if bone == ap:
                    # Skip changing the active bone
                    continue
                if bone not in matrices:
                    print("Skip matrix,", bone.name)
                    continue
                Set.matrix(bone, matrices[bone])
                utils.update(context)

        return {'FINISHED'}

    bone_parent_types = [
        ('BONE', "Bone Parent", "", 'BONE_DATA', 1),
        ('BONE_CONNECT', "   Connected", "", 'LINKED', 2),
        ('STRETCH', "   Stretch", "", 'AUTOMERGE_OFF', 3),
        ('STRETCH_CONNECT', "   Stretch (Connected)", "", 'AUTOMERGE_ON', 4),
        ('CHILD_CONNECT', "   Parent to Child", "", 'OUTLINER_DATA_ARMATURE', 5),
    ]
    type: EnumProperty(
        items=bone_parent_types,
        name="Bone Type",
        description="Preset bone to insert",
        default='BONE',  # ('string' or {'set'})  from items
    )
    keep_matrix: BoolProperty(
        name="Keep Matrix", default=True, options={'SKIP_SAVE'},
        description="Keep the visual transforms of the child bones",
    )
    connect: BoolProperty(
        name="Connect", default=False, options={'SKIP_SAVE'},
    )
    connect_child: BoolProperty(
        name="Connect Child", default=False, options={'SKIP_SAVE'},
    )
    stretch: BoolProperty(
        name="Stretch", default=False, options={'SKIP_SAVE'},
    )


class POSE_MT_set_parent(bpy.types.Menu):
    bl_description = POSE_OT_set_parent.bl_description
    bl_label = "Set Parent To"

    @classmethod
    def poll(self, context):
        return context.object

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_DEFAULT'

        col = layout.column(align=True)

        if POSE_OT_set_parent.poll(context):
            col.operator_enum(POSE_OT_set_parent.bl_idname, 'type')
            col.separator()

        for (type, text, description, icon, no) in self.get_types(context):
            op = col.operator('object.parent_set', text=text, icon=icon)
            op.type = type
            if type == 'OBJECT':
                op.keep_transform = bool(text == 'Object (Keep Transform)')

    def get_types(self, context):
        class has:
            mesh = False
            gpencil = False
        active = context.active_object
        for o in context.selected_editable_objects:
            if (o == active):
                continue
            if (o.type == 'MESH'):
                has.mesh = True
            if (o.type == 'GPENCIL'):
                has.gpencil = True

        types = [
            ("OBJECT", "Object", "", 'OBJECT_DATA', 1),
            ("OBJECT", "Object (Keep Transforms)", "", 'OUTLINER_OB_EMPTY', 1),

            *[a for a in [
                ("ARMATURE", "Armature Deform", "", 'OUTLINER_OB_ARMATURE', 2),
                ("ARMATURE_NAME", "   With Empty Groups", "", 'POSE_HLT', 3),
                *[a for a in [
                    ("ARMATURE_AUTO", "   With Automatic Weights", "", 'OUTLINER_DATA_ARMATURE', 4),
                    ] if (has.mesh or has.gpencil)],
                ("ARMATURE_ENVELOPE", "   With Envelope Weights", "", 'MOD_ARMATURE', 5),
                ("BONE", "Bone", "", 'BONE_DATA', 6),
                ("BONE_RELATIVE", "Bone Relative", "", 'CONSTRAINT_BONE', 7),
                ] if (active.type == 'ARMATURE')],
            *[a for a in [
                ("CURVE", "Curve Deform", "", 'OUTLINER_OB_CURVE', 8),
                ("FOLLOW", "Follow Path", "", 'ANIM', 9),
                ("PATH_CONST", "Path Constraint", "", 'CURVE_PATH', 10),
                ] if (active.type == 'CURVE')],
            *[a for a in [
                ("LATTICE", "Lattice Deform", "", 'MOD_LATTICE', 11),
                ] if (active.type == 'LATTICE')],
            # # /* vertex parenting */
            # if (OB_TYPE_SUPPORT_PARVERT(parent.type)):
            *[a for a in [
                ("VERTEX", "Vertex", "", 'VERTEXSEL', 12),
                ("VERTEX_TRI", "Vertex (Triangle)", "", 'MOD_TRIANGULATE', 13),
                ] if (hasattr(active.data, 'vertices'))],
            ]

        "This part is supposed to find out whether or not xmirror is enabled, for whatever it does :p"
        # static bool parent_set_poll_property(const bContext *UNUSED(C), wmOperator *op, const PropertyRNA *prop)
        # {
            # const char *prop_id = RNA_property_identifier(prop);

            # /* Only show XMirror for PAR_ARMATURE_ENVELOPE and PAR_ARMATURE_AUTO! */
            # if (STREQ(prop_id, "xmirror")) {
                # const int type = RNA_enum_get(op->ptr, "type");
                # if (ELEM(type, PAR_ARMATURE_ENVELOPE, PAR_ARMATURE_AUTO))
                    # return true;
                # else
                    # return false;
            # }

            # return true;
        # }

        return types


def register():
    args = dict(idname='wm.call_menu', type='P', value='PRESS', ctrl=True)
    for n in ('Pose', 'Object Mode'):
        km.add(name=n, **args).name = 'POSE_MT_set_parent'


def unregister():
    km.remove()
