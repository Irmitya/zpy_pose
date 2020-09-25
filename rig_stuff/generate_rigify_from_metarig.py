import bpy
from zpy import Get, Set, Is, utils
from .metarig_to_rigify import meta_to_rigify


class MACRO_OT_generate_rigify(bpy.types.Operator):
    bl_description = "Generate Rigify rigs from Metarigs"
    bl_idname = 'macro.generate_rigify'
    bl_label = "Generate Rig"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        for rig in context.selected_objects:
            if None in cls.poll_parse(cls, context, rig):
                continue

            return True

    def poll_parse(self, context, rig):
        null = [None] * 2

        val = rig.get('daz_to_rigify')
        if not Is.armature(rig):
            return null
        elif val == 'metarig':
            meta = rig
            for rig in Get.objects(context):
                if rig.get('daz_to_rigify') == repr(meta):
                    break
            else:
                rig = meta.data.rigify_target_rig
                if rig is None:
                    return null
        elif val is None:
            if rig.data.rigify_layers:
                # Is a regular metarig
                meta = rig
            else:
                # Is a regular rig
                return null
        else:
            try:
                meta = eval(val)
                if meta is None:
                    return null
            except:
                return null
        return (meta, rig)

    def execute(self, context):
        def close_rigify(meta):
            """Close Rigify Layers panel by default"""
            text = meta.data.rigify_rig_ui
            for (index, line) in enumerate(text.lines):
                if (line.body == "class RigLayers(bpy.types.Panel):"):
                    text.cursor_set(index + 6)  # bl_category = 'Item'
                    text.write("    bl_options = {'DEFAULT_CLOSED'}\n")
                    return True

        for daz in context.selected_objects:
            (meta, daz) = self.poll_parse(context, daz)
            if None in (meta, daz):
                continue

            layers_extra = get_layers_extra(meta)

            Set.active(context, meta)
            bpy.ops.pose.rigify_generate()
            close_rigify(meta)

            rig = context.active_object
            meta_to_rigify(daz, rig)

            adjust_rigify(rig)
            set_layers_extra(rig, layers_extra)

        return {'FINISHED'}


def adjust_rigify(rig):
    # Disable other layers
    for (layer, on) in enumerate(rig.data.layers):
        if on:
            para_set = True
            for bone in rig.pose.bones:
                para = bone.rigify_parameters
                # Limbs
                if para.fk_layers_extra and para.fk_layers[layer]:
                    break
                if para.tweak_layers_extra and para.tweak_layers[layer]:
                    break

                # Face
                if para.primary_layers_extra and para.primary_layers[layer]:
                    break
                if para.secondary_layers_extra and para.secondary_layers[layer]:
                    break

                # agavrilov's IK Knee/Elbow
                if para.ik_mid_layers_extra and para.ik_mid_layers[layer]:
                    break
            else:
                para_set = False
            if para_set:
                rig.data.layers[layer] = False

    bone = None

    def get(name):
        nonlocal bone
        bone = rig.pose.bones.get(name)
        return bone

    # # Convert Rigify to constraints_extra
    # for name, sub in (
            # ('hand_ik.L', 'DEF-hand.L'), ('hand_ik.R', 'DEF-hand.R'),
            # ('foot_ik.L', 'DEF-foot.L'), ('foot_ik.R', 'DEF-foot.R'),
            # ):
        # if get(name):
            # bone.base_src.is_duplicate = True
            # bone.base_src.target = rig.name
            # bone.base_src.target_self = True
            # bone.base_src.subtarget = sub

    # Rearrange face bone layers
    if get('ORG-face'):
        secondary = bone.rigify_parameters.secondary_layers
        for name in (
                'teeth.B', 'teeth.T', 'nose_master',
                'master_eye.L', 'master_eye.R', 'ear.L', 'ear.R',
                ):
            if get(name):
                bone.bone.layers = secondary

    # Disable translation of bones that shouldn't be moved
    locs_lr = (
        'palm', 'palm.01'
        # 'shoulder',
        'thumb.01_master', 'f_index.01_master', 'f_middle.01_master', 'f_ring.01_master', 'f_pinky.01_master',  # Rigify Fingere
        'toe1.01_master', 'toe2.01_master', 'toe3.01_master', 'toe4.01_master', 'toe5.01_master',  # Rigify Toes

        'thumb.01', 'f_index.01', 'f_middle.01', 'f_ring.01', 'f_pinky.01',  # Regular Finger
        'toe1.01', 'toe2.01', 'toe3.01', 'toe4.01', 'toe5.01',  # Regular Toes
    )
    locs = (
        'neck', 'head',
        *(x + '.L' for x in locs_lr), *(x + '.R' for x in locs_lr),
        )
    for name in locs:
        if get(name):
            bone.lock_location = (True, True, True)

    # Disable tweak controls on IK pole-limbs
    for name in ('upper_arm_ik.L', 'upper_arm_ik.R', 'thigh_ik.L', 'thigh_ik.R'):
        # They use 10% IK stretch, which will cause the scale to unintentionally change
        if get(name):
            bone.lock_location = (True, True, True)
            bone.lock_scale = (True, True, True)

    # Disable pole-axis locking. Can't see any good reason they're locked in the first place
    for name in ('upper_arm_ik.L', 'upper_arm_ik.R', 'thigh_ik.L', 'thigh_ik.R'):
        if get(name):
            bone.lock_rotation = (False, False, False)

    # Disable side-to-side and twisting (just do toe stand)
    for name in ('foot_heel_ik.L', 'foot_heel_ik.R'):
        if get(name):
            bone.lock_rotation = (False, True, True)

    # if get('DEF-spine.003'):
        # # Chest's deformation bone. When the neck rotates, this distorts badly
        # bone.bone.bbone_segments = 1
        # if get('DEF-spine.002'):
            # bone.bone.bbone_easeout = 0

    def fix_toe_roll():
        """
        The Toe controller bone may have a bad automated roll, so recalculate it
        """
        mode = Get.mode(rig)
        Set.mode(bpy.context, rig, 'EDIT')
        bones = rig.data.edit_bones

        ebones = bpy.context.selected_bones
        for ebone in ebones:
            ebone.select = False

        bone = tweak = None

        def get(name):
            nonlocal bone, tweak
            bone = bones.get(name)
            tweak = bones.get(name.replace('_master', ''))
            return (bone and tweak)

        def roll(name):
            if get(name):
                bone.select = True
                bones.active = tweak
                bpy.ops.armature.calculate_roll(type='ACTIVE')
                bone.select = False

        for lr in ('L', 'R'):
            for ind in range(1, 6):
                roll(f'toe{ind}.01_master.{lr}')
            roll(f'thumb.01_master.{lr}')
            roll(f'f_index.01_master.{lr}')
            roll(f'f_middle.01_master.{lr}')
            roll(f'f_ring.01_master.{lr}')
            roll(f'f_pinky.01_master.{lr}')

        for ebone in ebones:
            ebone.select = True

        Set.mode(bpy.context, rig, mode)
    fix_toe_roll()

    # Fix default pole location
    def fix_poles():
        def op(**args):
            eval('bpy.ops.pose.rigify_limb_toggle_pole_' + rig.data["rig_id"])(
                dict(active_object=rig), 'INVOKE_DEFAULT', **args
            )
        poles = dict()

        def getmat(bone, active):
            """Helper function for visual transform copy,
            gets the active transform in bone space
            """
            obj_bone = bone.id_data
            obj_active = active.id_data
            data_bone = obj_bone.data.bones[bone.name]
            # all matrices are in armature space unless commented otherwise
            active_to_selected = obj_bone.matrix_world.inverted() @ obj_active.matrix_world
            active_matrix = active_to_selected @ active.matrix
            otherloc = active_matrix  # final 4x4 mat of target, location.
            bonemat_local = data_bone.matrix_local.copy()  # self rest matrix
            if data_bone.parent:
                parentposemat = obj_bone.pose.bones[data_bone.parent.name].matrix.copy()
                parentbonemat = data_bone.parent.matrix_local.copy()
            else:
                parentposemat = parentbonemat = Matrix()
            if parentbonemat == parentposemat or not data_bone.use_inherit_rotation:
                newmat = bonemat_local.inverted() @ otherloc
            else:
                bonemat = parentbonemat.inverted() @ bonemat_local

                newmat = bonemat.inverted() @ parentposemat.inverted() @ otherloc
            return newmat

        def rotcopy(item, mat):
            """Copy rotation to item from matrix mat depending on item.rotation_mode"""
            if item.rotation_mode == 'QUATERNION':
                item.rotation_quaternion = mat.to_3x3().to_quaternion()
            elif item.rotation_mode == 'AXIS_ANGLE':
                rot = mat.to_3x3().to_quaternion().to_axis_angle()    # returns (Vector((x, y, z)), w)
                axis_angle = rot[1], rot[0][0], rot[0][1], rot[0][2]  # convert to w, x, y, z
                item.rotation_axis_angle = axis_angle
            else:
                item.rotation_euler = mat.to_3x3().to_euler(item.rotation_mode)

        def get_pole(pole, line):
            from math import radians
            from mathutils import Matrix

            bone["pole_vector"] = 0
            pole = get(pole)
            line = get(line)

            # lock rotation/scale, since bone only suppose to be moved
            pole.rotation_mode = 'XYZ'
            pole.lock_rotation_w = True
            pole.lock_rotation = (True, True, True)
            pole.lock_scale = (True, True, True)

            utils.update(bpy.context)
            mat = getmat(pole, line) @ Matrix.Rotation(radians(180), 4, 'X')
            rotcopy(pole, mat)
            utils.update(bpy.context)
            poles[pole.name] = Get.matrix(pole)
            rotcopy(pole, Matrix())

            pole.location = (0, 0, 0)

        if get('thigh_parent.L'):
            op(prop_bone="thigh_parent.L", ik_bones="[\"thigh_ik.L\", \"MCH-shin_ik.L\", \"MCH-thigh_ik_target.L\"]", ctrl_bones="[\"thigh_ik.L\", \"foot_ik.L\", \"thigh_ik_target.L\"]", extra_ctrls="[\"foot_ik_pivot.L\", \"foot_heel_ik.L\", \"foot_spin_ik.L\"]")
            get_pole('thigh_ik_target.L', 'VIS_thigh_ik_pole.L')
        if get('thigh_parent.R'):
            op(prop_bone="thigh_parent.R", ik_bones="[\"thigh_ik.R\", \"MCH-shin_ik.R\", \"MCH-thigh_ik_target.R\"]", ctrl_bones="[\"thigh_ik.R\", \"foot_ik.R\", \"thigh_ik_target.R\"]", extra_ctrls="[\"foot_ik_pivot.R\", \"foot_heel_ik.R\", \"foot_spin_ik.R\"]")
            get_pole('thigh_ik_target.R', 'VIS_thigh_ik_pole.R')
        if get('upper_arm_parent.L'):
            op(prop_bone="upper_arm_parent.L", ik_bones="[\"upper_arm_ik.L\", \"MCH-forearm_ik.L\", \"MCH-upper_arm_ik_target.L\"]", ctrl_bones="[\"upper_arm_ik.L\", \"hand_ik.L\", \"upper_arm_ik_target.L\"]", extra_ctrls="[\"hand_ik_pivot.L\", \"hand_ik_wrist.L\"]")
            get_pole('upper_arm_ik_target.L', 'VIS_upper_arm_ik_pole.L')
        if get('upper_arm_parent.R'):
            op(prop_bone="upper_arm_parent.R", ik_bones="[\"upper_arm_ik.R\", \"MCH-forearm_ik.R\", \"MCH-upper_arm_ik_target.R\"]", ctrl_bones="[\"upper_arm_ik.R\", \"hand_ik.R\", \"upper_arm_ik_target.R\"]", extra_ctrls="[\"hand_ik_pivot.R\", \"hand_ik_wrist.R\"]")
            get_pole('upper_arm_ik_target.R', 'VIS_upper_arm_ik_pole.R')
        if poles:
            utils.update(bpy.context)
            mode = Get.mode(rig)
            Set.mode(bpy.context, rig, 'EDIT')
            for (name, mat) in poles.items():
                edit_bone = rig.data.edit_bones[name]
                Set.matrix(edit_bone, mat)
            Set.mode(bpy.context, rig, mode)
    fix_poles()

    # # Adjust the influence of the default Copy Rotation constraint
    # appendages = (
        # 'thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky',
        # 'toe1', 'toe2', 'toe3', 'toe4', 'toe5',
    # )
    # for ap in appendages:
        # for lr in ('L', 'R'):
            # if get(f'{ap}.02.{lr}') and bone.constraints:
                # try:
                    # bone.constraints[0].influence = 0.25
                # except AttributeError:
                    # pass
            # # Lower the influence of the finger/toe tip
            # # if get(f'{ap}.03.{lr}') and bone.constraints:
                # # bone.constraints[0].influence = 0.75

    if get('torso'):
        # Set head to follow like neck
        if ('head_follow' in bone):
            bone["head_follow"] = 0.5
            bone['_RNA_UI']['head_follow']['default'] = 0.5

        if ('fk_hips' in bone):
            bone["fk_hips"] = 0.5
            bone['_RNA_UI']['fk_hips']['default'] = 0.5

    # Remove empty Rotation from 'limbs.simple_tentacle'
    for bone in rig.pose.bones:
        if bone.bone.use_deform or not bone.parent:
            continue
        con = bone.constraints.get('Copy Rotation')
        if con and (con.target == rig) and (con.subtarget == bone.parent.name):
            if not any((con.use_x, con.use_y, con.use_z)):
                bone.constraints.remove(con)
                con = None  # Just remove from memory, just because


def get_layers_extra(meta):
    rig = meta.data.rigify_target_rig
    if (rig is None) or (not rig.data.layers_extra.layers):
        # Rig hasn't been generated before, or never assigned it Pseudo Layers
        return

    layers_extra = {bone.name: bone.layers_extra for bone in rig.pose.bones}
    layers_extra[('Visible', 'layers')] = rig.data.layers[:]
    # layers_extra[('rig', 'ui')] = meta.data.rigify_rig_ui
    return layers_extra


def set_layers_extra(rig, layers_extra):
    if layers_extra is None:
        return

    layers = rig.data.layers_extra.layers

    # new = None
    # if layers:
        # new_index = layers[-1].column + 1
    # else:
        # new_index = 0

    for bone in rig.pose.bones:
        bone_layers = layers_extra.get(bone.name)
        if bone_layers:
            bone.layers_extra = bone_layers
        # else:
            # Add newly created bones to an empty pseudo-layer for futher sorting
            # if new is None:
                # new = layers.add()
                # new.name = "(New Bones)"
                # new.column = new_index
            # bone.layers_extra = f'[{new_index}]'

    for layer in layers:
        layer.visible = layer.visible
    rig.data.layers[:] = layers_extra[('Visible', 'layers')]

    # text = layers_extra[('rig', 'ui')]
    # for line in reversed(text.lines):
        # if line.body.startswith('register()'):
            # line.body = '# ' + line.body
            # break
