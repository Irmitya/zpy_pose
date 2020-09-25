import bpy
from zpy import Get, Set, Is
from .metarig_to_rigify import meta_to_rigify


class MACRO_OT_daz_to_metarig_weights(bpy.types.Operator):
    bl_description = "Transfer Daz meshes and weights to Metarig"
    bl_idname = 'macro.daz_to_metarig_weights'
    bl_label = "Transfer Daz to Metarig"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        for rig in context.selected_objects:
            if None in self.poll_parse(self, context, rig):
                continue

            return True

    def poll_parse(self, context, rig):
        null = [None] * 3

        if not Is.armature(rig):
            return null

        val = rig.get('daz_to_rigify')
        if val == 'metarig':
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
        for daz in context.selected_objects:
            (meta, daz) = self.poll_parse(context, daz)
            if None in (meta, daz):
                continue

            deform_daz_to_meta(daz, meta)

        return {'FINISHED'}


def deform_daz_to_meta(daz, metarig):
    """Retarget Daz meshes to Metarig"""

    for obj in bpy.data.objects:
        if obj.parent == daz:
            obj.parent = metarig

        for mod in obj.modifiers:
            if hasattr(mod, 'object') and mod.object == daz:
                mod.object = metarig
                vgroups_daz_to_meta(daz, obj)


def vgroups_daz_to_meta(daz, obj):
    """Rename Daz Vertex Groups to Metarig Vertex Groups"""

    keep = (
        # 'abdomenLower', 'abdomenUpper',
        # 'lFoot', 'lMetatarsals', 'lHeel',
        # 'rFoot', 'rMetatarsals', 'rHeel',
    )

    count = 0
    total = len(daz.data.bones.keys())
    # for (daz_bone, rigify) in vg_names.items():
    for (i, daz_bone) in enumerate(daz.data.bones.keys()):
        meta_bone = vg_names.get(daz_bone, False)

        if not meta_bone:
            # Daz bone not registered with conversion in dict
            continue

        if meta_bone.startswith('DEF-'):
            meta_bone = meta_bone[4:]

        perc = round(((i + 1) / total * 100))
        # print(f"\rTransferring weights ({perc}%): {daz_bone} > {meta_bone}", end=" " * 80)
        print(f"\rTransferring weights ({obj.name}): {count}/{total} ({perc}%)", end="")

        utils.merge_vertex_groups(obj, meta_bone, daz_bone, remove=daz_bone not in keep)
        count += 1
    else:
        # print(f"\rTransferred {count}/{total} bone weights.", " " * 80)
        print(f"\rTransferred {count}/{total} bone weights in {obj.name}", " " * 20)
