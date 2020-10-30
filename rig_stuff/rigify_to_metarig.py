
import bpy
from zpy import Get, Is, Set, utils


class MACRO_OT_rigify_to_meta(bpy.types.Operator):
    bl_description = "Set the metarig back as the deform rig (for adding bones/weights)"
    bl_idname = 'macro.rigify_to_meta'
    bl_label = "Convert Rigify to Meta"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        for rig in context.selected_objects:
            (rig, meta) = self.poll_parse(self, context, rig)
            if None in (rig, meta):
                continue

            return True

    def poll_parse(self, context, rig):
        null = [None] * 2
        if (not Is.armature(rig)):
            return null
        if (rig.data.get('rig_id') is None):
            meta = rig
            rig = meta.data.rigify_target_rig
            if rig is None:
                return null
        else:
            for meta in Get.objects(context):
                if Is.armature(meta) and meta.data.rigify_target_rig == rig:
                    break
            else:
                return null

        return (rig, meta)

    def execute(self, context):
        active = Get.active(context)
        mode = context.mode
        pose = list()

        for rig in context.selected_objects:
            (rig, meta) = self.poll_parse(context, rig)
            if None in (rig, meta):
                continue

            rigify_to_meta(rig, meta)
            pose.append((meta, rig))
        else:
            if mode == 'POSE':
                Set.mode(context, 'OBJECT')
            for (meta, rig) in pose:
                Set.select(rig, False)
                Set.select(meta, True)
                if rig == active:
                    Set.active(context, meta)
            if mode == 'POSE':
                Set.mode(context, 'POSE')

        return {'FINISHED'}


def rigify_to_meta(rigify, metarig):
    """Retarget Rigify meshes to Metarig"""

    pose = (metarig.data.pose_position, rigify.data.pose_position)
    (metarig.data.pose_position, rigify.data.pose_position) = ('REST', 'REST')
    utils.update(bpy.context)

    for obj in bpy.data.objects:
        if Is.curve(obj) and obj.name.startswith(rigify.name + '-MCH-'):
            # Splines from angavrilov's spline rig
            continue
        for mod in obj.modifiers:
            if hasattr(mod, 'object') and mod.object == rigify:
                mod.object = metarig
                metafy_vgroups(rigify, obj, metarig)

        if (obj.parent == rigify):
            rigify_bone = obj.parent_bone

            if rigify_bone:
                if rigify_bone.startswith('DEF-'):
                    meta_bone = rigify_bone[4:]
                else:
                    meta_bone = rigify_bone

                if meta_bone in metarig.data.bones:
                    mat = Get.matrix(obj)
                    # pmat = obj.matrix_parent_inverse.copy()
                    obj.parent = metarig
                    obj.parent_bone = meta_bone
                    # obj.matrix_parent_inverse = pmat
                    Set.matrix(obj, mat)
            else:
                obj.parent = metarig

        if Is.mesh(obj):
            meshes = {obj.data}
            if hasattr(obj, 'variants'):
                # The LoDs store the mesh datas and drivers without an object
                for layer in obj.variants.layers:
                    if layer.mesh:
                        meshes.add(layer.mesh)
                    for lod in layer.lods:
                        meshes.add(lod.mesh)

            for mesh in meshes:
                if mesh:
                    rigify_drivers(rigify, metarig, mesh.shape_keys)
    for mat in bpy.data.materials:
        rigify_drivers(rigify, metarig, mat)
        rigify_drivers(rigify, metarig, mat.node_tree)

    (metarig.data.pose_position, rigify.data.pose_position) = pose


def metafy_vgroups(rigify, obj, metarig):
    """Rename Rigify DEF Vertex Groups to Metarig Vertex Groups"""

    scanned_placeholders = False

    count = 0
    total = len(rigify.data.bones.keys())
    for (i, rigify_bone) in enumerate(rigify.data.bones.keys()):
        if not rigify_bone.startswith('DEF-'):
            # Not a DEF group, so...
            continue

        meta_bone = rigify_bone[4:]
        if obj.vertex_groups.get(meta_bone):
            # Both DEF and regular name in vertex groups
            continue

        if (meta_bone not in metarig.data.bones):
            # DEF bone like the arms/legs but don't have a placeholder bone for it
            if scanned_placeholders:
                continue
            else:
                add_placeholder_bones(rigify, obj, metarig)
                scanned_placeholders = True
                if (meta_bone not in metarig.data.bones):
                    continue

        perc = round(((i + 1) / total * 100))
        print(f"\rTransferring weights ({obj.name}): {count}/{total} ({perc}%)", end="")

        utils.merge_vertex_groups(obj, meta_bone, rigify_bone, remove=True)
        count += 1
    else:
        # print(f"\rTransferred {count}/{total} bone weights.", " " * 80)
        print(f"\rTransferred {count}/{total} bone weights in {obj.name}", " " * 20)


def rigify_drivers(rigify, metarig, data):
    """Transfer drivers from rigify to metarig"""

    anim = getattr(data, 'animation_data', None)
    if anim is None:
        return

    bones = metarig.pose.bones

    for driver in anim.drivers:
        for var in driver.driver.variables:
            for target in var.targets:
                if target.id == rigify:
                    target.id = metarig

                    if target.bone_target.startswith(('DEF-', 'ORG-')):
                        name = target.bone_target[4:]
                    else:
                        name = target.bone_target

                    if name in bones:
                        target.bone_target = name


def add_placeholder_bones(rigify, obj, metarig):
    context = bpy.context

    rigify_mode = rigify.mode
    meta_mode = metarig.mode
    Set.mode(context, 'EDIT', metarig)
    Set.mode(context, 'EDIT', rigify)

    for rigify_bone in rigify.data.edit_bones.keys():
        if not rigify_bone.startswith('DEF-'):
            # Not a DEF group, so...
            continue

        meta_bone = rigify_bone[4:]
        if obj.vertex_groups.get(meta_bone):
            # Both DEF and regular name in vertex groups
            continue

        if (meta_bone in metarig.data.edit_bones):
            continue

        rbone = rigify.data.edit_bones[rigify_bone]
        mbone = metarig.data.edit_bones.new(meta_bone)
        for attr in (
            # 'bbone_curveinx', 'bbone_curveiny',
            # 'bbone_curveoutx', 'bbone_curveouty',
            # 'bbone_custom_handle_end', 'bbone_custom_handle_start',
            # 'bbone_easein', 'bbone_easeout',
            # 'bbone_handle_type_end', 'bbone_handle_type_start',
            # 'bbone_rollin', 'bbone_rollout',
            # 'bbone_scaleinx', 'bbone_scaleiny',
            # 'bbone_scaleoutx', 'bbone_scaleouty',
            # 'bbone_segments',
            'bbone_x', 'bbone_z',
            'envelope_distance', 'envelope_weight',
            'head', 'head_radius', 'tail', 'tail_radius',
            'roll',
            'inherit_scale', 'use_inherit_rotation', 'use_inherit_scale',
            'use_endroll_as_inroll',
            'use_envelope_multiply',
            'use_local_location',
            'use_relative_parent',
            ):
            setattr(mbone, attr, getattr(rbone, attr))
        if rbone.parent:
            mbone.parent = metarig.data.edit_bones.get(rbone.parent.name[4:])
            if mbone.parent:
                mbone.layers = mbone.parent.layers

    Set.mode(context, meta_mode, metarig)
    Set.mode(context, rigify_mode, rigify)
