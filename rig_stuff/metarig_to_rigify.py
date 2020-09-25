import bpy
from zpy import Is, Get, Set, utils
from .daz_metarig_names import vg_names


class MACRO_OT_meta_to_rigify(bpy.types.Operator):
    bl_description = "Convert metarigs to a Rigify rig without regenerating it"
    bl_idname = 'macro.meta_to_rigify'
    bl_label = "Convert Meta to Rigify"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        for rig in context.selected_objects:
            (meta, rig) = self.poll_parse(self, context, rig)
            if None in (meta, rig):
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

        return meta, rig

    def execute(self, context):
        active = Get.active(context)
        mode = context.mode
        pose = list()

        for rig in context.selected_objects:
            (meta, rig) = self.poll_parse(context, rig)
            if None in (meta, rig):
                continue

            meta_to_rigify(meta, rig)
            pose.append((meta, rig))
        else:
            if mode == 'POSE':
                Set.mode(context, None, 'OBJECT')
            for (meta, rig) in pose:
                Set.select(rig, True)
                Set.select(meta, False)
                if meta == active:
                    Set.active(context, rig)
            if mode == 'POSE':
                Set.mode(context, None, 'POSE')

        return {'FINISHED'}


def meta_to_rigify(metarig, rigify):
    """Retarget Metarig meshes to Rigify rig"""

    pose = (metarig.data.pose_position, rigify.data.pose_position)
    (metarig.data.pose_position, rigify.data.pose_position) = ('REST', 'REST')
    utils.update(bpy.context)

    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if hasattr(mod, 'object') and mod.object == metarig:
                mod.object = rigify
                rigify_vgroups(metarig, rigify, obj)

        if obj.parent == metarig:
            if obj.parent_bone:
                rigify_bone = vg_names.get(obj.parent_bone, False)
                if rigify_bone is False:
                    rigify_bone = 'DEF-' + obj.parent_bone
                if rigify_bone and rigify_bone in rigify.data.bones:
                    mat = Get.matrix(obj)
                    # pmat = obj.matrix_parent_inverse.copy()
                    obj.parent = rigify
                    obj.parent_bone = rigify_bone
                    # obj.matrix_parent_inverse = pmat
                    Set.matrix(obj, mat)
            else:
                obj.parent = rigify

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
                    rigify_drivers(metarig, rigify, mesh.shape_keys)
    for mat in bpy.data.materials:
        rigify_drivers(metarig, rigify, mat)
        rigify_drivers(metarig, rigify, mat.node_tree)

    (metarig.data.pose_position, rigify.data.pose_position) = pose


def rigify_vgroups(metarig, rigify, obj):
    """Rename Daz Vertex Groups to Rigify Vertex Groups"""

    keep = (
        # 'abdomenLower', 'abdomenUpper',
        # 'lFoot', 'lMetatarsals', 'lHeel',
        # 'rFoot', 'rMetatarsals', 'rHeel',
    )

    count = 0
    total = len(metarig.data.bones.keys())
    # for (meta_bone, rigify) in vg_names.items():
    for (i, meta_bone) in enumerate(metarig.data.bones.keys()):
        rigify_bone = vg_names.get(meta_bone, False)

        if rigify_bone is False:
            rigify_bone = 'DEF-' + meta_bone
        elif rigify_bone is None:
            # In case I insert None in the vg_names entries
            # Or False and None can be merged, and always insert as DEF
            continue

        if (rigify_bone not in rigify.data.bones):
            # DEF bone not found in rig; Maybe used Raw Copy
            continue

        perc = round(((i + 1) / total * 100))
        # print(f"\rTransferring weights ({perc}%): {meta_bone} > {rigify_bone}", end=" " * 80)
        print(f"\rTransferring weights ({obj.name}): {count}/{total} ({perc}%)", end="")

        utils.merge_vertex_groups(obj, rigify_bone, meta_bone, remove=meta_bone not in keep)
        count += 1
    else:
        # print(f"\rTransferred {count}/{total} bone weights.", " " * 80)
        print(f"\rTransferred {count}/{total} bone weights in {obj.name}", " " * 20)


def rigify_drivers(metarig, rigify, data):
    """Transfer drivers from metarig to rigify"""

    anim = getattr(data, 'animation_data', None)
    if anim is None:
        return

    bones = rigify.pose.bones

    for driver in anim.drivers:
        for var in driver.driver.variables:
            for target in var.targets:
                if target.id == metarig:
                    target.id = rigify

                    obone = bones.get('ORG-' + target.bone_target)
                    dbone = bones.get('DEF-' + target.bone_target)

                    if obone and obone.constraints:
                        # Org bones normally use copy_transforms constraint
                        # Which works the Local Space drivers
                        target.bone_target = obone.name
                    elif dbone and dbone.constraints:
                        target.bone_target = dbone.name
                    else:
                        # There's probably a bone with the same name, as a constroller
                        pass
