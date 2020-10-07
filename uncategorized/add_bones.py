import bpy
from mathutils import Vector
from zpy import Get, Set, Is, utils, register_keymaps
km = register_keymaps()


class POSE_OT_add_bone(bpy.types.Operator):
    bl_description = "Add bone to object, from pose mode"
    bl_idname = 'zpy.add_bone'
    bl_label = "Add Bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        objects = [context.active_object] + \
                  [o for o in context.selected_editable_objects
                   if o != context.active_object]

        any_polled = False

        for rig in objects:
            if not Is.armature(rig) or not Set.mode(context, rig, 'EDIT'):
                # object can't go into (armature) edit mode
                continue

            # Place driver search here to avoid scanning all datas, if nothing's being added
            if (not any_polled) and (self.type == 'MCH'):
                self.mch_driver_targets = list()
                # self.mch_driver_targets = self.get_drivers(objects)

            any_polled = True

            if self.type == 'BONE':
                self.add_bones_bone(context, rig)
                break  # Only add one bone, to the active rig or first applicable
            elif self.type == 'ROOT':
                self.add_bones_root(context, rig)
            elif self.type == 'DUPLI':
                self.add_bones_dupli(context, rig)
            elif self.type == 'VIS':
                self.add_bones_vis(context, rig)
            elif self.type == 'MCH':
                self.add_bones_mch(context, rig)
            elif self.type == 'MCH_PARENT':
                self.add_bones_mch(context, rig, mch_parent=True)
            elif self.type == 'IK':
                self.add_bones_ik(context, rig)
            elif self.type == 'STRETCH':
                self.add_bones_stretch(context, rig)
            elif self.type == 'STRETCH_TAIL':
                self.add_bones_stretch_tail(context, rig)

        if any_polled and (self.type == 'DUPLI'):
            bpy.ops.transform.translate('INVOKE_DEFAULT')

        return {'FINISHED'}

    def add_bones(self, context, rig):
        add_type = self.type

    # region: Add Bone Defaults

    def add_bones_bone(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        bone = rig.data.edit_bones.new('Bone')
        bone.parent = root

        bone.translate(
            Vector(utils.multiply_list(
                Get.cursor(context).location,
                rig.matrix_world.inverted().to_scale(),  # Get the transforms for the unscaled rig
            )) - rig.matrix_world.to_translation()
        )

        # Use the original bone size (unscaled by the rig)
        bone.tail = bone.head + Vector(utils.multiply_list(
            Vector((0, 0, 0.1)),
            rig.matrix_world.inverted().to_scale(),
        )) - rig.matrix_world.to_translation()

        bone = str(bone.name)

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        bone = rig.data.bones[bone]
        rig.data.bones.active = bone
        Set.select(bone)

    def add_bones_root(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        new_root = not bool(root)
        if root is None:
            root = rig.data.edit_bones.new('root')
            root.tail = Vector((0, 1, 0))
            root.bbone_x = 0.5
            root.bbone_z = 0.01
            root.layers = self.layer(27)
        for eb in rig.data.edit_bones:
            if eb.parent is None:
                eb.use_connect = False
                eb.parent = root
        root = str(root.name)

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        root = rig.pose.bones[root]

        if new_root:
            self.widget(root, 'Blenrig - Root')
        rig.data.bones.active = root.bone
        rig.data.layers[27] = True

    def add_bones_dupli(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        pose_bones = []

        for bone_name in prev_bones:
            prev = rig.data.edit_bones[bone_name]

            bone = rig.data.edit_bones.new(prev.name)
            pose_bones.append([bone.name, prev.name])
            self.reset(bone, prev)

            bone.parent = prev.parent
            bone.use_deform = prev.use_deform

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        for (bone, prev) in pose_bones:
            bone = rig.pose.bones[bone]
            prev = rig.pose.bones[prev]
            rig.data.bones.active = bone.bone
            bone.custom_shape = prev.custom_shape
            bone.custom_shape_transform = prev.custom_shape_transform
            bone.bone.show_wire = prev.bone.show_wire
            bone.matrix = prev.matrix
            bone.bone_group = prev.bone_group
            for lock in ['location', 'rotations_4d', 'rotation_w', 'rotation', 'scale']:
                setattr(bone, 'lock_' + lock, getattr(prev, 'lock_' + lock))

    def add_bones_vis(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        pose_bones = []

        for bone_name in prev_bones:
            prev = rig.data.edit_bones[bone_name]

            bone = rig.data.edit_bones.new(self.mirror_name(prev.name, 'VIS'))
            pose_bones.append([bone.name, prev.name])
            self.reset(bone, prev)

            bone.use_deform = False

            bone.parent = prev

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        for bone, prev in pose_bones:
            bone = rig.pose.bones[bone]
            prev = rig.pose.bones[prev]
            # rig.data.bones.active = bone.bone
            bone.custom_shape = prev.custom_shape
            bone.custom_shape_transform = prev.custom_shape_transform

            bone.bone.show_wire = True
            prev.custom_shape = None

            bone.bone.hide_select = True

            bone.matrix = prev.matrix

            driver = bone.bone.driver_add('hide')
            var = driver.driver.variables.new()
            var.name = 'var'
            driver.driver.expression = 'not var'
            var.type = 'SINGLE_PROP'
            vt = var.targets[0]
            vt.id = rig

            # vt.bone_target = target.name
            # vt.transform_space = 'LOCAL_SPACE'
            # vt.transform_type = transform
            # # if transform == 'SINGLE_PROP':

            vt.data_path = prev.bone.path_from_id('select')

    def add_bones_mch(self, context, rig, mch_parent=False):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        pose_bones = []

        # Get MCH Prefix
        parent_name = context.scene.mch_bone
        if parent_name == "":
            parent_name = "MCH-parent_"

        for bone_name in prev_bones:
            prev = rig.data.edit_bones[bone_name]

            # Replace bone prefixes with MCH instead of inserting keeping both
            name = parent_name + (prev.name.replace("DEF-", "", 1)).replace("CTRL-", "", 1)

            bone = rig.data.edit_bones.new(name)
            pose_bones.append([bone.name, prev.name])
            self.reset(bone, prev)

            bone.use_deform = False
            bone.use_connect = prev.use_connect
            bone.parent = prev.parent

            prev.use_connect = False
            prev.parent = bone
            # prev.select = False
            # prev.hide = True
            if not mch_parent:
                for c in prev.children:
                    c.parent = bone

            Set.select(bone, False)

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        for bone, prev in pose_bones:
            bone = rig.pose.bones[bone]
            prev = rig.pose.bones[prev]
            rig.data.bones.active = bone.bone
            # self.widget(bone, 'Box')
            ...

            # Retarget drivers
            if not mch_parent:
                for tar in self.mch_driver_targets:
                    if (tar.id is rig) and (tar.bone_target == prev.name):
                        tar.bone_target = bone.name

    def add_bones_ik(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        pose_bones = []

        for bone_name in prev_bones:
            prev = rig.data.edit_bones[bone_name]

            bone = rig.data.edit_bones.new(self.mirror_name(prev.name, 'IK'))
            pose_bones.append([bone.name, prev.name])
            self.reset(bone, prev)

            bone.parent = root
            bone.use_deform = False

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        for bone, prev in pose_bones:
            bone = rig.pose.bones[bone]
            prev = rig.pose.bones[prev]
            rig.data.bones.active = bone.bone
            bone.custom_shape_transform = prev
            self.widget(bone, 'Circle', slide=(0, 0.5, 1))

            bone['IK_FK'] = prev.name
            prev['IK_FK'] = prev.name

            bone['IK_IK'] = bone.name
            prev['IK_IK'] = bone.name

            bone.rotation_mode = 'QUATERNION'
            bone.matrix = prev.matrix

            # for ct in ['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE']:
                # con = deform.constraints.new(ct)
                # con.name = 'DEF-'+con.name
                # con.target = rig
                # con.subtarget = stretch.name
                # con.target_space = 'LOCAL'
                # con.owner_space = 'LOCAL'
                # con.use_offset = True
                # con.show_expanded = False
            # con				=	deform.constraints.new('STRETCH_TO')
            # con.name = 'DEF-'+con.name
            # con.target		=	rig
            # con.subtarget = tail.name
            # con.rest_length = deform.bone.length
            # con.head_tail = 0

            if prev.bone_group:
                bone.bone_group = self.bgroup(rig, 'IK-' + prev.bone_group.name)
            else:
                bone.bone_group = self.bgroup(rig, 'IK')
                prev.bone_group = self.bgroup(rig, 'FK')

    def add_bones_stretch(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        pose_bones = []

        for bone_name in prev_bones:
            prev = rig.data.edit_bones[bone_name]

            bone = rig.data.edit_bones.new(self.mirror_name(prev.name, 'STR'))
            head = prev.parent.name if (prev.parent and prev.use_connect) else ''
            tail = [*[c.name for c in prev.children if c.use_connect], ''][0]

            pose_bones.append([bone.name, [prev.name, head, tail]])
            self.reset(bone, prev)

            bone.parent = prev.parent
            bone.use_deform = False

            # use_tip = True
            # child = None
            # if edit_bone.children:
                # for i in edit_bone.children:
                    # if i.use_connect:
                        # if child is not None:
                            # child = False
                            # break
                        # child = i
                # if child in [None, False]:
                    # for i in edit_bone.children:
                        # if i.head == edit_bone.tail:
                            # if child not in [None, False]:
                                # child = False
                                # break
                            # child = i
            # if child:
                # tail = rig.data.edit_bones.get('STR-'+child.name)
                # if tail is None:
                    # tail	=	rig.data.edit_bones.new('STR-'+child.name)
                    # tail.parent		=	child
                    # tail.use_deform	=	False
                    # self.reset(tail, edit_bone=child)
                # else:
                    # use_tip = False
            # else:  # create bone tip
                # tail			=	rig.data.edit_bones.new('STR_TAIL-'+bone.name)
                # tail.parent		=	edit_bone
                # tail.use_deform	=	False
                # self.reset(tail)
                # th = Vector(tail.tail-tail.head)
                # tail.tail += th
                # tail.head += th
            ...

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        for bone, prev in pose_bones:
            prev, head, tail = prev
            bone = rig.pose.bones[bone]
            prev = rig.pose.bones[prev]

            head = rig.pose.bones.get(head, None)
            if head:
                prev.bone.bbone_custom_handle_start = head.bone
            tail = rig.pose.bones.get(tail, None)
            if tail:
                prev.bone.bbone_custom_handle_end = tail.bone

            rig.data.bones.active = bone.bone
            bone.custom_shape_transform = prev
            self.widget(bone, 'Sphere', scale=(0, 1.5, 0))

            # bone['IK_FK'] = prev.name
            # prev['IK_IK'] = bone.name
            bone.rotation_mode = prev.rotation_mode
            bone.lock_rotation[0] = True
            bone.lock_rotation[2] = True
            # i['IK_Deform'] = deform.name
            # i['IK_Stretch'] = stretch.name
            # i['IK_Tail'] = tail.name
            bone.matrix = prev.matrix

            if prev.bone_group:
                bone.bone_group = self.bgroup(rig, 'STR-' + prev.bone_group.name)
            else:
                bone.bone_group = self.bgroup(rig, 'STR')
                prev.bone_group = self.bgroup(rig, 'FK')

    def add_bones_stretch_tail(self, context, rig):
        # Add bones then set their defaults
        root = self.get_root(rig)
        prev_bones = self.get_prev_bones(rig)
        pose_bones = []

        for bone_name in prev_bones:
            prev = rig.data.edit_bones[bone_name]

            bone = rig.data.edit_bones.new(self.mirror_name(prev.name, 'STRT'))
            pose_bones.append([bone.name, prev.name])
            self.reset(bone, prev)

            bone.parent = prev.parent
            bone.use_deform = False

        # Switch back to Pose mode and setup pose bones
        Set.mode(context, rig, 'POSE')

        for bone, prev in pose_bones:
            bone = rig.pose.bones[bone]

    # endregion

    # region: Functions
    @staticmethod
    def bgroup(rig, name=''):
        bgroups = rig.pose.bone_groups
        if name in bgroups:
            group = bgroups[name]
        else:
            group = bgroups.new(name=name)
        return group

    @staticmethod
    def get_drivers(objects):
        # Find drivers targeting any of the rigs
        targets = list()

        data_blocks = (
            'cache_files', 'cameras', 'curves', 'grease_pencils', 'hairs',
            'lattices', 'lightprobes', 'lights', 'linestyles', 'masks',
            'materials', 'meshes', 'metaballs', 'movieclips', 'node_groups',
            'objects', 'particles', 'pointclouds', 'scenes', 'shape_keys',
            'simulations', 'speakers', 'textures', 'volumes', 'worlds',
        )

        def find_driver(ob):
            anim = ob.animation_data
            if anim:
                for drv in anim.drivers:
                    for var in drv.driver.variables:
                        for tar in var.targets:
                            if (tar.id in objects) and getattr(tar, 'bone_target', str()):
                                targets.append(tar)

        for block in data_blocks:
            for data in getattr(bpy.data, block):
                find_driver(data)

        return targets

    @staticmethod
    def get_prev_bones(rig):
        prev_bones = []

        for b in rig.data.bones:
            if b.select:
                prev_bones.append(b.name)
            Set.select(b, False)
            Set.select(rig.data.edit_bones[b.name], False)

        return prev_bones

    @staticmethod
    def get_root(rig):
        bones = rig.data.edit_bones
        return bones.get('root', bones.get('Root', None))

    @staticmethod
    def layer(*ins, max=32):
        layers = [False] * max
        for i in ins:
            layers[i] = True
        return tuple(layers)

    @staticmethod
    def reset(src, edit_bone):
        attributes = [
            'head', 'head_radius',
            'tail', 'tail_radius',
            'roll',
            'matrix',
            'layers',
            'bbone_curveinx', 'bbone_curveiny',
            'bbone_curveoutx', 'bbone_curveouty',
            'bbone_easein', 'bbone_easeout',
            'bbone_rollin', 'bbone_rollout',
            'bbone_scalein', 'bbone_scaleinx', 'bbone_scaleoutx',
            'bbone_scaleout', 'bbone_scaleiny', 'bbone_scaleouty',
            'bbone_segments',
            'bbone_x', 'bbone_z',
            'envelope_weight', 'envelope_distance', 'use_envelope_multiply',

            # 'use_connect',
            # 'use_cyclic_offset',
            # 'use_deform',
            # 'use_endroll_as_inroll',
            # 'use_inherit_rotation',
            # 'use_inherit_scale',
            # 'use_local_location',
            # 'use_relative_parent',

            ]
        for atr in attributes:
            if hasattr(src, atr):
                setattr(src, atr, getattr(edit_bone, atr))

    @staticmethod
    def mirror_name(name, txt):
        suf = ''
        if len(name) > 2:
            if name[-2] == '.' and name[-1] in ('L', 'R', 'M'):
                suf = name[:-2]
        return "%s-%s%s" % (name, txt, suf)

    @staticmethod
    def widget(bone, wgt, slide=Vector(), size=1, scale=(1, 1, 1)):
        bpy.ops.bonewidget.create_widget(global_size=size, slide=slide, scale=scale, bones='[%r]' % bone, widget=wgt)
        # try:
        #     wgt = wgts[wgt]
        # except:
        #     wgt = wgts[context.scene.widget_list]
        # # createWidget(bone=bone, widget=wgt, relative=True, size=size, scale=[1, 1, 1], slide=slide)
        # createWidget(
            # bone,
            # wgts[context.scene.widget_list],
            # True,
            # size,
            # [1, 1, 1],
            # slide,
            # Vector()
            # )

        # # ----  Widget Creation ----
        # if self.type in {'ROOT', 'IK', 'STRETCH'}:
            # try:
            #     from zpy__mods.boneWidget.functions.mainFunctions import createWidget
            #     from zpy__mods.boneWidget.functions.jsonFunctions import readWidgets
            #     wgts = readWidgets()
            # except:
            #     self.report({'ERROR'}, "Bone Widget addon not found; Can't run for this type")
            #     return {'CANCELLED'}
        # def createWidget(bone, widget, relative, size, scale, slide):
            # import numpy
            # C = bpy.context
            # D = bpy.data

            # if bone.custom_shape_transform:
                # matrixBone = bone.custom_shape_transform
            # else:
                # matrixBone = bone

            # if bone.custom_shape:
                # bone.custom_shape.name = bone.custom_shape.name + "_old"
                # bone.custom_shape.data.name = bone.custom_shape.data.name + "_old"
                # if C.scene.objects.get(bone.custom_shape.name):
                    # C.scene.objects.unlink(bone.custom_shape)

            # newData = D.meshes.new(bone.name)

            # if relative is True:
                # boneLength = 1
            # else:
                # boneLength = (1 / bone.bone.length)

            # newData.from_pydata(
                # numpy.array(widget['vertices']) * [size * scale[0] * boneLength, size * scale[2] * boneLength, size * scale[1] * boneLength] + [0, slide, 0],
                # widget['edges'],
                # widget['faces']
                # )
            # newData.update(calc_edges=True)

            # newObject = D.objects.new('WGT-%s' % bone.name, newData)

            # newObject.data = newData
            # newObject.name = 'WGT-%s' % bone.name
            # C.scene.objects.link(newObject)
            # newObject.matrix_local = matrixBone.bone.matrix_local
            # newObject.scale = [matrixBone.bone.length, matrixBone.bone.length, matrixBone.bone.length]
            # update()

            # bone.custom_shape = newObject
            # bone.bone.show_wire = True
            # newObject.layers = [*[False] * 19, *[True] * 1]

        # def readWidgets():
            # wgts = {}

            # import os
            # import json
            # # jsonFile = os.path.join(os.path.dirname(os.path.dirname(__file__)),'widgets.json')
            # jsonFile = os.path.join(__file__.rsplit(__package__)[0] + 'boneWidget\\\\', 'widgets.json')
            # if os.path.exists(jsonFile):
                # f = open(jsonFile, 'r')
                # wgts = json.load(f)

            # return (wgts)

    # endregion: functions

    type_items = [
        ('BONE', "Bone", "Insert default bone", 'BONE_DATA', 1),
        ('DUPLI', "    Duplicate", "Insert copy of selected bones", 'GHOST_ENABLED', 3),
        ('VIS', "    Visual", "Insert copy of selected bones for visual display", 'RESTRICT_VIEW_OFF', 4),
        ('ROOT', "Root", "Insert root bone", 'GRID', 2),
        ('IK', "IK", "Insert IK bone controller", 'PHYSICS', 5),
        ('STRETCH', "Stretch", "Insert stretch bones", 'FULLSCREEN_ENTER', 6),
        ('STRETCH_TAIL', "Stretch (Tail)", "Insert stretch bones", 'FULLSCREEN_ENTER', 7),
        ('MCH', "MCH Replace", "Insert bone controller (selected are DEF bones)", 'GROUP_BONE', 8),
        ('MCH_PARENT', "MCH Parent", "Insert bone controller (create new parent at selected)", 'GROUP_BONE', 9),
    ]
    type: bpy.props.EnumProperty(
        items=type_items,
        name="Bone Type",
        description="Preset bone to insert",
        default='BONE',  # ('string' or {'set'})  from items
    )


def draw_add_armature(self, context):
    if context.mode != 'POSE':
        return

    layout = self.layout
    layout.operator_context = 'EXEC_DEFAULT'

    col = layout.column(align=True)

    col.operator_enum(POSE_OT_add_bone.bl_idname, 'type')

    # Strings can't be in the same block in menus
    mch = context.scene.mch_bone
    # icon = 'COLLAPSEMENU'
    icon = 'TEXT'

    if mch:
        col.prop(context.scene, 'mch_bone', text="", icon=icon)
    else:
        row = col.column(align=True)
        row.scale_y = 0.1
        row.row(align=True).prop(context.scene, 'mch_bone', text="")
        col.label(text="Prefix:  MCH-parent_", icon=icon)

    col.separator()

    col.label(text="Pose Library")
    # op = col.operator('poselib.browse_interactive', text="Browse Poses...")
    # op = col.operator('poselib.mixcurrpose', text="Apply Pose Library Pose")
    # op = col.operator('poselib.mixedposepaste', text="Paste Mixed Pose")
    # col.prop(context.scene, 'posemixinfluence',
    #             text="Mix Influence", icon='ARROW_LEFTRIGHT')

    col.separator()

    # op = col.operator('poselib.pose_add', text="Add Pose...")
    # op = col.operator('poselib.pose_rename', text="Rename Pose...")
    # op = col.operator('poselib.pose_remove', text="Remove Pose...")
    layout.separator()


def register():
    km.add(POSE_OT_add_bone, name='Pose', type='D', shift=True).type = 'DUPLI'
    bpy.types.VIEW3D_MT_armature_add.prepend(draw_add_armature)

    def mch_update(self, context):
        if not context.scene.mch_bone.startswith('Prefix:  '):
            context.scene.mch_bone = "Prefix:  " + context.scene.mch_bone
        # if not context.scene.mch_bone:
            # context.scene.mch_bone = "MCH-parent_"
    bpy.types.Scene.mch_bone = bpy.props.StringProperty(
        default="Prefix:  MCH-parent_",
        update=mch_update
    )


def unregister():
    km.remove()
    bpy.types.VIEW3D_MT_armature_add.remove(draw_add_armature)

    del (bpy.types.Scene.mch_bone)
