"""
When loading a file, reload custom properties/groups/constraints
for proxy rigs. Like protected layers, except allowing you to retain new constraints
"""
import bpy
from bpy.app.handlers import persistent, load_post
from zpy import Is, Get


@persistent
def reload_proxies(scn):
    for rig in bpy.data.objects:
        if not (Is.armature(rig) and not rig.library and rig.data.library):
            continue
        for src in bpy.data.objects:
            if (src.data == rig.data) and (src.library == rig.data.library):
                break
        else:
            # Can't find the original linked rig
            continue

        copy_custom(src, rig)
        copy_groups(src.pose.bone_groups, rig.pose.bone_groups)
        for pbone in rig.pose.bones:
            sbone = src.pose.bones.get(pbone.name)
            if not sbone:
                # Rig is proxy that was made local, incorrectly/incompletely
                continue
            elif (True, True) in zip(rig.data.layers_protected, pbone.bone.layers):
                # Bone is in a protected layer, so properties are locked and auto-reset
                continue

            if sbone.bone_group:
                try:
                    pbone.bone_group = Get.bone_group(rig, name=sbone.bone_group.name)
                except:
                    print(pbone, sbone)
            copy_constraints(sbone, pbone)
            copy_custom(sbone, pbone)
        copy_drivers(src, rig)


def copy_groups(sgroups, rgroups):
    for sg in sgroups.values():
        if (sg.name not in rgroups):
            rgroups.new(name=sg.name)
        rg = rgroups[sg.name]

        rg.color_set = sg.color_set
        rg.colors.active = sg.colors.active
        rg.colors.normal = sg.colors.normal
        rg.colors.select = sg.colors.select


def copy_constraints(sbone, pbone):
    for scon in sbone.constraints.values():
        if (scon.name not in pbone.constraints):
            pbone.constraints.new(scon.type).name = scon.name

        # Reset constraint properties
        pcon = pbone.constraints[scon.name]
        generic_copy(scon, pcon)

        if (pcon.type == 'ARMATURE'):
            pcon.targets.clear()
            for old_tar in scon.targets:
                new_tar = pcon.targets.new()
                generic_copy(old_tar, new_tar)

                new_tar.target = old_tar.target
                new_tar.subtarget = old_tar.subtarget
                new_tar.weight = old_tar.weight


def generic_copy(source, target, string=""):
    """Copy attributes from source to target that have string in them"""
    for attr in dir(source):
        if attr.find(string) > -1:
            try:
                setattr(target, attr, getattr(source, attr))
            except:
                pass


def copy_custom(sbone, pbone):
    rna = '_RNA_UI'
    bl_rna = pbone.bl_rna.properties.keys()

    for attr in sbone.keys():
        if (attr == rna):
            if (rna not in pbone.keys()):
                pbone[rna] = dict()
            for (attr, value) in sbone[rna].items():
                pbone[rna][attr] = value
        else:
            if (attr in pbone.keys()):
                # property already in bone
                if attr in bl_rna:
                    if pbone.bl_rna.properties[attr].is_library_editable:
                        # Property defined as bpy.props from addon and as editable
                        continue
                elif pbone.is_property_overridable_library(f'["{attr}"]'):
                    # manually added property and set it to be editable
                    continue

            pbone[attr] = sbone[attr]


def copy_drivers(src, rig):
    sdrivers = getattr(src.animation_data, 'drivers', None)
    if not sdrivers:
        return
    rdrivers = rig.animation_data_create().drivers

    for sdrv in sdrivers.values():
        while rdrivers.find(sdrv.data_path, index=sdrv.array_index):
            rdrv = rdrivers.find(sdrv.data_path, index=sdrv.array_index)
            rdrivers.remove(rdrv)

        rdrv = rdrivers.from_existing(src_driver=sdrv)


def register():
    load_post.append(reload_proxies)


def unregister():
    load_post.remove(reload_proxies)
