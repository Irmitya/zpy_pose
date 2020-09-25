import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty
from bpy.types import Operator, Panel
from zpy import Is, Set, Get, utils, New


class mannequin:
    head = ""


class DAZ_OT_AddMannequin(Operator):
    bl_idname = "daz.add_mannequin_macro"
    bl_label = "Add Mannequins"
    bl_description = "Add mannequins to selected meshes"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        text = cls.bl_rna.bl_description
        if properties.macro:
            text += ",\nthen transfer vertex groups and materials" \
                    " and,\nfinally hide and instance the collection"
        return text

    @classmethod
    def poll(self, context):
        for obj in context.selected_objects:
            if Is.mesh(obj) and Is.armature(obj.parent):
                return True

    def execute(self, context):
        mannequin.head = f" ({self.head.title()})"

        objects = list()

        for obj in context.selected_objects:
            if Is.mesh(obj) and Is.armature(obj.parent):
                inst = self.convert(context, obj)
                objects.append(inst)

        for obj in reversed(objects):
            Set.active_select(context, obj, isolate=False)

        return {'FINISHED'}

    def convert(self, context, obj):
        scn = context.scene
        Set.active_select(context, obj, isolate=True)

        coll_instanced = False  # Whether or not to instance collection in full macro

        head = self.head
        group = obj.name + '-Mannequin'

        coll = bpy.data.collections.get(group)
        if coll:
            # Regenerating mannequin
            coll_instanced = True

            for ob in coll.objects.values():
                if Is.mesh(ob) and ob.DazMannequin:
                    bpy.data.objects.remove(ob)
        else:
            coll = bpy.data.collections.new(group)
            scn.collection.children.link(coll)

        # "temporarily" unhide collection if hidden
        in_view = Is.in_view(context, coll)
        if not in_view:
            Set.visible(context, coll, view_layer=True)
        visible = Is.visible(context, coll)
        if not visible:
            Set.visible(context, coll)

        # Add mannequin objects for current mesh
        self.generate(context, obj, obj.parent, coll)

        if self.macro:
            has_mann = False
            for ob in coll.objects.values():
                if Is.mesh(ob):
                    Set.select(ob)
                    has_mann = True

            if has_mann:
                bpy.ops.object.data_transfer_mannequin_preset()
                # if obj.data.materials:
                    # bpy.ops.object.data_transfer_materials()

            # Hide the collection and create an instancer of it
            # if coll:
                # # Set.visible(context, obj, value=False)
                # Set.visible(context, coll, value=False, view_layer=True)
                # if not coll_instanced:
                    # inst = New.object(context, name=coll.name)
                    # inst.instance_type = 'COLLECTION'
                    # inst.instance_collection = coll
                    # Set.empty_size(inst, 0)
                    # return inst

            for ob in coll.objects.values():
                Set.select(ob, value=False)

        if not visible:
            Set.visible(context, coll, False)
        if not in_view:
            Set.visible(context, coll, False, view_layer=True)

        return obj

    def generate(self, context, ob, rig, coll):
        scn = context.scene

        faceverts, vertfaces = self.getVertFaces(ob)
        majors = {}
        skip = []
        for vgrp in ob.vertex_groups:
            if vgrp.name in rig.data.bones:
                majors[vgrp.index] = []
            else:
                skip.append(vgrp.index)
        for v in ob.data.vertices:
            wmax = 1e-3
            vbest = None
            for g in v.groups:
                if g.weight > wmax and g.group not in skip:
                    wmax = g.weight
                    vbest = v
                    gbest = g.group
            if vbest is not None:
                majors[gbest].append(vbest)

        roots = [bone for bone in rig.data.bones if bone.parent is None]
        for bone in roots:
            self.remapBones(bone, ob.vertex_groups, majors, None)

        face_mats = dict()
        if ob.data.materials:
            for f in ob.data.polygons:
                face_mats[(f.area, *f.center, *f.normal)] = ob.material_slots[f.material_index].material

        nobs = []
        for vgrp in ob.vertex_groups:
            if (vgrp.name not in rig.pose.bones.keys() or
                vgrp.index not in majors.keys()):
                continue
            fnums = []
            for v in majors[vgrp.index]:
                for fn in vertfaces[v.index]:
                    fnums.append(fn)
            fnums = list(set(fnums))

            nverts = []
            nfaces = []
            for fn in fnums:
                f = ob.data.polygons[fn]
                nverts += f.vertices
                nfaces.append(f.vertices)
            if not nfaces:
                continue
            nverts = list(set(nverts))
            nverts.sort()

            bone = rig.pose.bones[vgrp.name]
            head = bone.bone.head_local
            # verts = [ob.data.vertices[vn].co - head for vn in nverts]
            verts = [ob.data.vertices[vn].co for vn in nverts]
            assoc = dict([(vn, n) for n, vn in enumerate(nverts)])
            faces = []
            for fverts in nfaces:
                faces.append([assoc[vn] for vn in fverts])

            name = ob.name[0:3] + "_" + vgrp.name
            me = bpy.data.meshes.new(name)
            me.from_pydata(verts, [], faces)
            nob = bpy.data.objects.new(name, me)
            coll.objects.link(nob)
            nob.DazMannequin = True
            # nob.location = head
            # nob.lock_location = nob.lock_rotation = nob.lock_scale = (True,True,True)
            nobs.append((nob, bone))

            if ob.data.materials:
                for b in me.polygons:
                    mat_i = face_mats.get((b.area, *b.center, *b.normal))
                    if mat_i is None:
                        # Add an empty material
                        if mat is None:
                            from random import random
                            mat = bpy.data.materials.new(ob.name + 'Mannequin')
                            mat.diffuse_color[0:3] = (random(), random(), random())
                            # for omat in ob.data.materials:
                                # mat.diffuse_color = omat.diffuse_color
                        if mat.name not in me.materials:
                            me.materials.append(mat)
                        continue

                    if mat_i.name not in me.materials:
                        me.materials.append(mat_i)
                    for (i, mat_c) in enumerate(nob.material_slots):
                        if mat_c.material == mat_i:
                            b.material_index = i
                            break
            else:
                if mat is None:
                    from random import random
                    mat = bpy.data.materials.new(ob.name + 'Mannequin')
                    mat.diffuse_color[0:3] = (random(), random(), random())
                    # for omat in ob.data.materials:
                        # mat.diffuse_color = omat.diffuse_color
                if mat.name not in me.materials:
                    me.materials.append(mat)

        utils.update(context)
        for (nob, bone) in nobs:
            mat = Get.matrix(nob)
            # pmat = nob.matrix_parent_inverse.copy()
            nob.parent = rig
            nob.parent_bone = bone.name
            nob.parent_type = 'BONE'
            # nob.matrix_parent_inverse = pmat
            Set.matrix(nob, mat)

            # mat = nob.matrix_world.copy()
            # nob.parent = rig
            # nob.parent_bone = bone.name
            # nob.parent_type = 'BONE'
            # nob.matrix_world = mat

    @staticmethod
    def getVertFaces(ob, verts=None, faces=None, faceverts=None):
        if verts is None:
            verts = range(len(ob.data.vertices))
        if faces is None:
            faces = range(len(ob.data.polygons))
        if faceverts is None:
            faceverts = [list(f.vertices) for f in ob.data.polygons]
        vertfaces = dict([(vn, []) for vn in verts])
        for fn in faces:
            for vn in faceverts[fn]:
                vertfaces[vn].append(fn)
        return faceverts, vertfaces

    def remapBones(self, bone, vgrps, majors, remap):
        special = {
            'SOLID': ["head"],
            'JAW': ["head", "lowerjaw", "leye", "reye"],
            'FULL': []
            }
        if bone.name.lower() in special[self.head]:
            if bone.name in vgrps.keys():
                remap = vgrps[bone.name].index
        elif remap is not None:
            if bone.name in vgrps.keys():
                gn = vgrps[bone.name].index
                if gn in majors.keys():
                    majors[remap] += majors[gn]
                    del majors[gn]

        for child in bone.children:
            self.remapBones(child, vgrps, majors, remap)

    head: EnumProperty(
        items=[
            ('SOLID', "Solid", "Solid head"),
            ('JAW', "Jaw", "Head with jaws and eyes"),
            ('FULL', "Full", "Head with all face bones"),
        ],
        name="",
        description="",
    )
    macro: BoolProperty(options={'SKIP_SAVE'})


class TRANSFER_DATA_OT_mesh(Operator):
    bl_description = "Transfer Mesh Data"
    bl_idname = 'object.data_transfer_mannequin_preset'
    bl_label = "Transfer Mesh Data"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 1

    def execute(self, context):
        active = obj = context.object
        transfer = bpy.ops.object.data_transfer

        if (not Is.mesh(obj)) or getattr(obj, 'DazMannequin', False):
            # redesignate obj
            obj = None

            for o in context.selected_objects:
                if Is.mesh(o) and (not getattr(o, 'DazMannequin', False)):
                    obj = o
                    Set.active(context, o)
                    break

        if not all((obj, obj.data.polygons, transfer.poll(context.copy()),)):
            self.report({'INFO'}, "Only Mannequins Selected")
            return {'CANCELLED'}

        mesh = obj.data

        if mesh.polygons[0].use_smooth:
            # only check one face, rather than all
            bpy.ops.object.shade_smooth()

        if mesh.use_auto_smooth:
            transfer(data_type='CUSTOM_NORMAL')
            for o in context.selected_objects:
                if Is.mesh(o):
                    o.data.use_auto_smooth = True

        if obj.vertex_groups:
            # Vertex groups add to file size, so don't keep them for everything
            transfer(data_type='VGROUP_WEIGHTS', layers_select_src='ALL', layers_select_dst='NAME')

        if mesh.vertex_colors:
            transfer(data_type='VCOL', layers_select_src='ALL', layers_select_dst='NAME')

        if mesh.uv_layers:
            transfer(data_type='UV', layers_select_src='ALL', layers_select_dst='NAME')

        Set.active(context, active)

        return {'FINISHED'}


class TRANSFER_DATA_OT_materials(Operator):
    bl_description = "Transfer Materials"
    bl_idname = 'object.data_transfer_materials'
    bl_label = "Transfer Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 1

    def execute(self, context):
        active = obj = context.object

        if (not Is.mesh(obj)) or getattr(obj, 'DazMannequin', False):
            obj = None

            for o in context.selected_objects:
                if Is.mesh(o) and (not getattr(o, 'DazMannequin', False)):
                    obj = o
                    Set.active(context, obj)
                    break

        if not (obj and obj.data.polygons):
            self.report({'INFO'}, "Only Mannequins Selected")
            return {'CANCELLED'}
        elif not obj.data.materials:
            self.report({'INFO'}, "Mesh doesn't have any materials to transfer")
            return {'CANCELLED'}

        def getface(f, o):
            r = self.Round
            area = round(f.area, r)
            center = utils.multiply_matrix(o.matrix_world, f.center)
            center = tuple([round(a, r) for a in center])
            return (area, center)

        mesh = obj.data
        # obj_faces = {
            # # getface(f, obj): obj.material_slots[f.material_index].material
            # getface(f, obj): mesh.materials[f.material_index]
            # for f in mesh.polygons
        # }

        obj_faces = dict()
        count = 0
        total = len(mesh.polygons)
        for (i, f) in enumerate(mesh.polygons):
            perc = round(((i + 1) / total * 100))
            log = f"\rGetting face ids ({obj.name}): {count}/{total} ({perc}%)"
            print(log + " [old_mats]", end="")

            obj_faces[getface(f, obj)] = mesh.materials[f.material_index]
            count += 1

        count_obj = 0
        total_obj = len(context.selected_objects) - 1
        for (i, o) in enumerate(context.selected_objects):
            if (o == obj) or (not Is.mesh(o)):
                continue
            omesh = o.data

            perc_obj = round(((i + 1) / total_obj * 100))
            log = f"\rTransferring materials ({o.name}): {count_obj}/{total_obj} ({perc_obj}%)"

            print(log + " [old_mats]", end="")
            old_mats = {i: m for i, m in enumerate(omesh.materials)}

            print(log + " [for face in mesh.polygons]", end="")
            # count = 0
            # total = len(omesh.polygons)
            for face in omesh.polygons:
                mat_i = obj_faces.get(getface(face, o))
                if mat_i is None:
                    # old_mats.pop(face.material_index)
                    continue

                if mat_i.name not in omesh.materials:
                    omesh.materials.append(mat_i)

                for (i, mat) in enumerate(o.material_slots):
                    if mat.material == mat_i:
                        face.material_index = i
                        if i in old_mats:
                            old_mats.pop(face.material_index)
                        break

            print(log + " [for i in old_mats]", end="")
            for i in reversed(list(old_mats)):
                o.data.materials.pop(index=i)

            count_obj += 1
        else:
            print(f"\rTransferred {count_obj}/{total_obj} materials from {obj.name}", " " * 20)

        Set.active(context, active)

        return {'FINISHED'}

    Round: IntProperty(
        default=2,
        description="Accuracy of face matching (only adjust if transfer is bad)"
    )
