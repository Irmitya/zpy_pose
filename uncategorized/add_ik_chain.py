import bpy
from zpy import Get, Is, New, Set, Constraint, utils


mt = bpy.types.VIEW3D_MT_armature_add


def copy(target, src, attr):
    setattr(target, attr, getattr(src, attr))


def cls(cls):
    return [cls.head, cls.tail, cls.bone]


class CON_OT_add_ik_chain(bpy.types.Operator):
    bl_description = "Convert bone(s) to IK Chain + Stretch"
    bl_idname = 'zpy.add_ik_chain'
    bl_label = "Add IK Chain"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if cls.poll(context):
            return cls.bl_rna.description
        elif context.selected_pose_bones:
            return "Selected bones don't have 2 parents for IK chain"
        else:
            return "No bones selected"

    @classmethod
    def poll(cls, context):
        if context.mode == 'PAINT_WEIGHT': return
        for bone in Get.selected_pose_bones(context):
            if bone.parent and bone.parent.parent:
                return True

    def execute(self, context):
        wgt = utils.find_op('bonewidget.create_widget')
        # if wgt is None:
        #     def wgt(*nil, **null):
        #         return

        for bone in Get.selected_pose_bones(context):
            if not (bone.parent and bone.parent.parent):
                continue

            rig = bone.id_data
            bone_name = bone.name

            # Get and create bones for edit mode
            Set.mode(context, rig, 'EDIT')
            editbone = rig.data.edit_bones[bone_name]

            class fk:
                head = editbone.parent.parent
                tail = editbone.parent
                bone = editbone

            class ik:
                head = New.bone(context, rig, name="IK-" + fk.head.name)
                tail = New.bone(context, rig, name="IK-" + fk.tail.name)
                bone = New.bone(context, rig, name="IK-" + fk.bone.name)

            class stretch:
                head = New.bone(context, rig, name="IK-Stretch-" + fk.head.name)
                tail = New.bone(context, rig, name="IK-Stretch-" + fk.tail.name)
                bone = New.bone(context, rig, name="IK-Stretch-" + fk.bone.name)
            fk_names = [b.name for b in cls(fk)]
            ik_names = [b.name for b in cls(ik)]
            stretch_names = [b.name for b in cls(stretch)]

            # Set transforms for edit bones
            for k in (ik, stretch):
                for (b, f) in zip(cls(k), cls(fk)):
                    copy(b, f, 'bbone_x')
                    copy(b, f, 'bbone_z')
                    copy(b, f, 'matrix')
                    copy(b, f, 'tail')
            for b in cls(stretch):
                b.inherit_scale = 'NONE'
                b.length /= 3
            stretch.tail.head = fk.head.tail
            stretch.bone.head = fk.tail.tail
            ik.tail.tail = ik.bone.head

            # Set parenting
            ik.head.parent = fk.head.parent
            ik.tail.parent = ik.head
            # ik.bone.parent = fk.head.parent
            for (b, i) in zip(cls(stretch), cls(ik)):
                b.parent = i

            # Switch bones back to pose mode
            Set.mode(context, rig, 'POSE')
            bones = rig.pose.bones

            class fk:
                head = bones[fk_names[0]]
                tail = bones[fk_names[1]]
                bone = bones[fk_names[2]]

            class ik:
                head = bones[ik_names[0]]
                tail = bones[ik_names[1]]
                bone = bones[ik_names[2]]

            class stretch:
                head = bones[stretch_names[0]]
                tail = bones[stretch_names[1]]
                bone = bones[stretch_names[2]]
            # for k in ('fk', 'ik', 'stretch'):
                # for h in ('head', 'tail', 'bone'):
                #     exec(f"{k}.{h} = bones[{k}.{h}.name]")
                #     # fk.head = bones[fk.head.name]

            ik.head.ik_stretch = 0.10
            ik.tail.ik_stretch = 0.10

            # for (b, i) in zip(cls(ik), cls(fk)):
                # Set.matrix(b, Get.matrix(i))

            # Insert constraints
            cc = Constraint.new(context, add_relations=False, add_drivers=False)

            cc.type = 'IK'
            cc.add_constraint(context, ik.tail, ik.bone).chain_count = 2

            cc.type = 'COPY_TRANSFORMS'
            cc.add_constraint(context, fk.head, stretch.head)
            cc.add_constraint(context, fk.tail, stretch.tail)
            cc.add_constraint(context, fk.bone, stretch.bone)

            cc.type = 'STRETCH_TO'
            cc.add_constraint(context, fk.head, stretch.tail)
            cc.add_constraint(context, fk.tail, stretch.bone)

            fk.bone.bone.select = False
            ik.bone.bone.select = True
            if fk.bone.bone == rig.data.bones.active:
                rig.data.bones.active = ik.bone.bone

            # Hide bones
            fk.head.bone.hide = True
            ik.tail.bone.hide = True
            fk.tail.bone.hide = True
            fk.bone.bone.hide = True

            if not wgt:
                continue

            # wgt(cc, widget='Rigify - Arrows', slide=(0, 0, 0), rotate=(0, 0, 0), relative_size=True, global_size=1, scale=(1, 1, 1))
            cc = dict(selected_pose_bones=[ik.head])
            # wgt(cc, scale=(1.25, 1.50, 1), widget='Rigify - Arrows')
            wgt(cc, scale=(1, 1, 1), widget='Blenrig - IK Limb')

            cc = dict(selected_pose_bones=cls(stretch))
            wgt(cc, scale=(3,) * 3, widget='Sphere')

            cc = dict(selected_pose_bones=[ik.bone])
            if 'hand' in ik.bone.name.lower():
                wgt(cc, scale=(1, 1, 1), widget='Blenrig - Hand')
            elif 'foot' in ik.bone.name.lower():
                wgt(cc, scale=(1, 1, 1), widget='Blenrig - Foot')
            else:
                wgt(cc, scale=(1, 1, 1), widget='Cube')

        return {'FINISHED'}


def draw_armature(self, context):
    if context.mode != 'POSE':
        return
    layout = self.layout
    layout.operator('zpy.add_ik_chain', icon='CON_KINEMATIC')


def register():
    mt.prepend(draw_armature)


def unregister():
    mt.remove(draw_armature)
