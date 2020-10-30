import bpy
from zpy import Get, Is, New, Set, utils, register_keymaps, popup
km = register_keymaps()


class BBONE_OT_add_controllers(bpy.types.Operator):
    bl_description = "Add drivers and bone controllers for selected bbones"
    bl_idname = 'zpy.add_bbone_controllers'
    bl_label = "Add BBone Controllers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        txt = cls.bl_description + ".\n"
        if properties.controls == 'IN/OUT':
            return txt + "(Only add 2 end bones to control the bbone properties with drivers)"
        elif properties.controls == 'START/END':
            return txt + "(Only add 2 stretch bones as the bbone's custom handles)"

    @classmethod
    def poll(cls, context):
        if context.selected_pose_bones:
            for bone in context.selected_pose_bones:
                if not Is.linked(bone):
                    return True

    def __init__(self):
        self.hide_bones = dict()  # bones to queue for hiding
        self.bone_widgets = {'mch': [], 'start': [], 'end': [], 'head': [], 'in_out': []}
        self.warning = ""
        self.warnings = 0
        self.delayed_parenting = list()  # bones to queue for parenting (because of order of creation)
        self.center_bones = dict()

    def execute(self, context):
        (rigs, self.selected) = get_rig_bones(context)

        for rig in rigs:
            Set.mode(context, 'EDIT', rig)
            self.hide_bones[rig] = list()
            self.center_bones[rig] = list()
        for (rig, bones) in rigs.items():
            for bone in bones:
                self.edit_func(context, rig.data.edit_bones[bone.name])
        for (ebones, ebone, tbone) in self.delayed_parenting:
            ebones[ebone].parent = ebones[tbone]
        (do_mch, do_start_end, do_in_out) = self.do()
        if do_start_end:
            self.edit_mirror_center(context)

        if self.warning:
            self.report({'WARNING'}, self.warning)

        for rig in rigs:
            Set.mode(context, 'POSE', rig)
        for (rig, bones) in rigs.items():
            for bone in bones:
                self.pose_func(context, rig.pose.bones[bone.name])

        def widget(ctrl_type, wgt='Sphere', global_size=6, scale=(1, 1, 1), slide=None):
            from mathutils import Vector
            bpy.ops.bonewidget.create_widget(
                global_size=global_size,
                slide=Vector(slide) if slide else Vector(),
                scale=scale,
                bones='%r' % self.bone_widgets[ctrl_type],
                widget=wgt,
            )
        widget('mch', wgt='Box', global_size=1, scale=(0.75, 0.75, 1))
        # widget('start', slide=(0, -0.5, 0))
        widget('start', wgt='Blenrig - Box', global_size=3)
        # widget('end', slide=(0, 0.5, 0))
        widget('end', wgt='Blenrig - Box', global_size=3)
        widget('in_out', global_size=7.5, slide=(0, 0.5, 0))

        return {'FINISHED'}

    def do(self):
        if self.controls == 'ALL':
            do_mch = do_start_end = do_in_out = True
        elif self.controls == 'NO_MCH':
            do_mch = False
            do_start_end = do_in_out = True
        else:
            do_mch = (self.controls == 'MCH')
            do_start_end = (self.controls == 'START/END')
            do_in_out = (self.controls == 'IN/OUT')
        return (do_mch, do_start_end, do_in_out)

    def edit_func(self, context, bone):
        rig = Get.rig(context, bone.id_data)
        ebones = rig.data.edit_bones
        (do_mch, do_start_end, do_in_out) = self.do()

        def get_disconnected_parent(bone, first_loop=True):
            if ((bone is None) or (not bone.parent)):
                if first_loop:
                    return
                else:
                    return bone
            elif Is.connected(bone):
                # Keep going up the chain until it finds a disconnected bone
                return get_disconnected_parent(bone.parent, False)
            else:
                return bone.parent

        def reset(bone, edit_bone):
            attributes = [
                'head', 'head_radius', 'tail', 'tail_radius',
                'roll', 'matrix', 'layers', 'bbone_x', 'bbone_z',
                ]

            for atr in attributes:
                if hasattr(bone, atr):
                    setattr(bone, atr, getattr(edit_bone, atr))

        def edit(ebone, bbone_xz=1.0):
            reset(ebone, bone)
            ebone.bbone_x *= bbone_xz
            ebone.bbone_z *= bbone_xz
            ebone.use_deform = False
            ebone.inherit_scale = 'NONE'
            ebone.hide = True

        def edit_mch(ebone):
            edit(ebone, 1.25)
            ebone.parent = bone.parent
            ebone.inherit_scale = bone.inherit_scale
            # ebone.use_connect = bone.use_connect
            # bone.use_connect = False
            # bone.parent = ebone
            # for cbone in bone.children:
                # cbone.parent = ebone

        def edit_start(ebone):
            edit(ebone, 2.5)
            if do_mch:
                ebone.parent = bone_mch
            else:
                if Is.connected(bone):
                    ebone.parent = ebones.get(get_name(bone.parent, 'bbone_end'))
                if ebone.parent:
                    self.hide_bones[rig].append(ebone.name)
                    ebone.hide = True
                else:
                    ebone.parent = bone.parent
                if not do_in_out:
                    cbone = ebones.get(get_name(bone, 'bbone_in'))
                    if cbone:
                        cbone.parent = ebone
            for cbone in bone.children_recursive:
                if (bone.head != cbone.tail):
                    continue
                cbone_end = ebones.get(get_name(cbone, 'bbone_end'))
                if cbone_end:
                    cbone_end.parent = ebone
                    self.hide_bones[rig].append(cbone_end.name)
                    cbone_end.hide = True
            ebone.tail = utils.lerp(ebone.head, ebone.tail, 0.1)

        def edit_head(ebone):
            edit(ebone, 0.5)
            ebone.parent = bone_start
            ebone.tail = utils.lerp(ebone.head, ebone.tail, 0.1)
            ebone.translate(ebone.head - ebone.tail)
            bone.bbone_custom_handle_start = ebone
            self.hide_bones[rig].append(ebone.name)

        def edit_end(ebone):
            edit(ebone, 2.5)
            if do_mch:
                ebone.parent = bone_mch
            else:
                for tbone in bone.parent_recursive:
                    if (tbone.head != bone.tail):
                        continue
                    tobone_name = get_name(tbone, 'bbone_start')
                    tobone = ebones.get(tobone_name)
                    if tobone or ((tbone, rig) in self.selected):
                        self.hide_bones[rig].append(ebone.name)
                        ebone.hide = True
                        if tobone:
                            ebone.parent = tobone
                        else:
                            self.delayed_parenting.append(ebones, ebone.name, tobone_name)
                    else:
                        ebone.parent = tbone
                    break
                else:
                    ebone.parent = get_disconnected_parent(bone)
                if not do_in_out:
                    cbone = ebones.get(get_name(bone, 'bbone_out'))
                    if cbone:
                        cbone.parent = ebone
            for cbone in bone.children:
                if Is.connected(cbone):
                    cbone_start = ebones.get(get_name(cbone, 'bbone_start'))
                    if cbone_start:
                        cbone_start.parent = ebone
                        self.hide_bones[rig].append(cbone_start.name)
                        cbone_start.hide = True
            ebone.head = utils.lerp(ebone.head, ebone.tail, 0.9)
            ebone.translate(ebone.tail - ebone.head)
            bone.bbone_custom_handle_end = ebone

        def edit_in(ebone):
            edit(ebone, 2.0)
            if do_start_end:
                ebone.parent = bone_start
            else:
                ebone.parent = ebones.get(get_name(bone, 'bbone_start'), bone)
            (head, tail) = (ebone.head.copy(), ebone.tail.copy())
            ebone.head = utils.lerp(head, tail, 0.1)
            ebone.tail = utils.lerp(head, tail, 0.2)

        def edit_out(ebone):
            edit(ebone, 2.0)
            if do_start_end:
                ebone.parent = bone_end
            else:
                ebone.parent = ebones.get(get_name(bone, 'bbone_end'), bone)
            (head, tail) = (ebone.head.copy(), ebone.tail.copy())
            ebone.tail = utils.lerp(head, tail, 0.8)
            ebone.head = utils.lerp(head, tail, 0.9)
            ebone.align_roll(-bone.z_axis)
                # This bone is reversed, so the the roll needs to be flipped

        if (do_in_out and (not (do_mch or do_start_end)) and (bone.bbone_segments < 2)):
            # parenting to the bone will cause dependency loop, with drivers
            # if the bone isn't using bbones

            if not (ebones.get(get_name(bone, 'bbone_start'), ebones.get(get_name(bone, 'bbone_end')))):
                if self.warning:
                    self.warning = (
                        f"{bone.name} does not have Bendy Bone Segments;"
                        " this will cause a dependency cycle-loop with its drivers/controllers"
                    )
                else:
                    self.warning = (
                        f"{self.warnings + 1} bones don't have Bendy Bone Segments;"
                        " this will cause a dependency cycle-loop with their drivers/controllers"
                    )
                self.warnings += 1

        if do_start_end:
            bone.bbone_handle_type_start = bone.bbone_handle_type_end = 'ABSOLUTE'

        args = dict(context=context, armature=rig, overwrite=True)
        if do_mch:
            bone_mch = New.bone(**args, name=get_name(bone, 'bbone'), edit=edit_mch)
        if do_start_end:
            bone_start = New.bone(**args, name=get_name(bone, 'bbone_start'), edit=edit_start)
            bone_end = New.bone(**args, name=get_name(bone, 'bbone_end'), edit=edit_end)
            bone_head = New.bone(**args, name=get_name(bone, 'bbone_head'), edit=edit_head)
        if do_in_out:
            bone_in = New.bone(**args, name=get_name(bone, 'bbone_in'), edit=edit_in)
            bone_out = New.bone(**args, name=get_name(bone, 'bbone_out'), edit=edit_out)

    def edit_mirror_center(self, context):
        def get_bones(rig, bbone):
            ebones = rig.data.edit_bones
            ebone = ebones.get(get_name(bone, bbone))
            mebone = Get.mirror_bone(ebone)
            return (ebone, mebone)

        found = []
        for (bone, rig) in self.selected:
            if not (rig.pose.use_mirror_x or rig.data.use_mirror_x):
                continue
            mbone = Get.mirror_bone(bone)
            if mbone in found:
                continue
            else:
                found.append(bone)

            (ebone, mebone) = get_bones(rig, 'bbone_start')
            if not (ebone and mebone):
                continue

            if (ebone.parent == mebone.parent):
                # Connect heads
                if Is.connected(bone):
                    # The parent will already handle the symmetry
                    continue
                parent = ebone.parent
            else:
                (ebone, mebone) = get_bones(rig, 'bbone_end')
                if not (ebone and mebone):
                    continue

                # Find a mutual parent between the two bones
                parent = [*(x for x in ebone.parent_recursive if x in mebone.parent_recursive), None][0]

            distance = abs(sum(ebone.head) - sum(mebone.head)) / 2
            margin = utils.lerp(bone.bone.length, mbone.bone.length, 0.5) / bone.bone.bbone_segments
            if distance >= margin:
                # Bones too far apart
                continue

            (prefix, replace, suffix, number) = utils.flip_name(bone.name, only_split=True)
            center_name = prefix + suffix + number
            center = New.bone(context, rig, name=center_name, overwrite=True)

            attributes = [
                'head', 'head_radius', 'tail', 'tail_radius',
                'roll', 'matrix', 'layers', 'bbone_x', 'bbone_z',
                ]
            for atr in attributes:
                if hasattr(center, atr):
                    setattr(center, atr, utils.lerp(getattr(ebone, atr), getattr(mebone, atr), 0.5))
            center.use_deform = False
            center.inherit_scale = 'NONE'
            center.parent = parent
            center.hide = True

            ebone.parent = mebone.parent = center
            self.hide_bones[rig].extend((ebone.name, mebone.name))
            self.center_bones[rig].append(center.name)

    def pose_func(self, context, bone):
        rig = bone.id_data
        bones = rig.pose.bones

        (do_mch, do_start_end, do_in_out) = self.do()

        def add_driver(pbone, path, transform_type, name="var", **kargs):
            return New.driver(bone, path, target=pbone, transform_type=transform_type, name=name, **kargs)

        def pose(pbone):
            pbone.rotation_mode = 'XYZ'
            pbone.bone.hide = False

        def pose_mch(pbone):
            Set.select(bone, False)
            Set.select(pbone, True)
            rig.data.bones.active = pbone.bone

            mats = (pbone.matrix.copy(), bone.matrix.copy())
            (bone.matrix, pbone.matrix) = mats

            pbone.rotation_mode = bone.rotation_mode
            pbone.lock_location = bone.lock_location
            pbone.lock_rotation = bone.lock_rotation
            pbone.lock_rotation_w = bone.lock_rotation_w
            pbone.lock_rotations_4d = bone.lock_rotations_4d
            pbone.lock_scale = (True, False, True)
            pbone.custom_shape_transform = bone
            if not pbone.custom_shape:
                self.bone_widgets['mch'].append(pbone)
            con = bone.constraints.new('COPY_ROTATION')
            con.target = rig
            con.subtarget = pbone.name
            con = bone.constraints.new('COPY_SCALE')
            con.target = rig
            con.subtarget = pbone.name
            con.use_x = con.use_z = False

        def pose_start(pbone):
            pose(pbone)
            pbone.lock_scale = (True, True, True)
            if not pbone.custom_shape:
                self.bone_widgets['start'].append(pbone)
            if not Is.connected(bone):
                con = bone.constraints.new('COPY_LOCATION')
                con.target = rig
                con.subtarget = pbone.name
                # Using offset will cause the Stretch TO constraint to fail if the bone's parent is scaled.
                # con.use_offset = True
                # con.target_space = con.owner_space = 'LOCAL_WITH_PARENT'

        def pose_head(pbone):
            pose(pbone)
            pbone.bone.hide = True
            pbone.lock_scale = (True, True, True)

        def pose_end(pbone):
            pose(pbone)
            pbone.lock_scale = (True, True, True)
            if not pbone.custom_shape:
                self.bone_widgets['end'].append(pbone)
            con = bone.constraints.new('STRETCH_TO')
            con.target = rig
            con.subtarget = pbone.name

        def pose_in_out(pbone, in_out):
            pose(pbone)
            pbone.lock_location = (True, False, True)
            pbone.lock_scale = (False, True, False)
            if not pbone.custom_shape:
                self.bone_widgets['in_out'].append(pbone)
            length = bone.bone.length

            # add_driver(pbone, f'bbone_curve{in_out}x', 'ROT_Z', "rotation_Z", '-{name} * %s' % length)
            # if (in_out == 'in'):
                # add_driver(pbone, 'bbone_curveiny', 'ROT_X', "rotation_x", '{name} * %s' % length)
                # add_driver(pbone, 'bbone_rollin', 'ROT_Y', "rotation_y")
            # else:
                # add_driver(pbone, 'bbone_curveouty', 'ROT_X', "rotation_x", '-{name} * %s' % length)
                # add_driver(pbone, 'bbone_rollout', 'ROT_Y', "rotation_y", '-{name}')
            # add_driver(pbone, f'bbone_ease{in_out}', 'SCALE_Y', "scale_y", '{name} - 1')

            add_driver(pbone, f'bbone_curve{in_out}x', 'ROT_Z', "rotation_Z", frames=[(0, 0), (-1, length)], target_path='rotation_euler.z')
            add_driver(pbone, f'bbone_curve{in_out}y', 'ROT_X', "rotation_x", frames=[(0, 0), ((1, -1)[in_out == 'out'], length)], target_path='rotation_euler.x')
            add_driver(pbone, f'bbone_roll{in_out}', 'ROT_Y', "rotation_y", frames=[(0, 0), ((1, -1)[in_out == 'out'], 1)], target_path='rotation_euler.y')

            add_driver(pbone, f'bbone_scale{in_out}x', 'SCALE_X', "scale_X")
            add_driver(pbone, f'bbone_scale{in_out}y', 'SCALE_Z', "scale_Z")
            # add_driver(pbone, f'bbone_ease{in_out}', 'SCALE_Y', "scale_y", frames=[(1, 0), (2, 1)])
            add_driver(pbone, f'bbone_ease{in_out}', 'LOC_Y', "location_y", frames=[(0, 0), (length, 1)])

        def set_bone_groups():
            if do_mch:
                bg = Get.bone_group(rig, "BBone FK")
                if not bg:
                    bg = New.bone_group(rig, "BBone FK", True)
                bone_mch.bone_group = bg
            if do_start_end:
                bg = Get.bone_group(rig, "BBone Stretch")
                if not bg:
                    bg = New.bone_group(rig, "BBone Stretch", True)
                bone_start.bone_group = bone_end.bone_group = bg
                for name in self.center_bones[rig]:
                    rig.pose.bones[name].bone_group = bg
            if do_in_out:
                bg = Get.bone_group(rig, "BBone Curve")
                if not bg:
                    bg = New.bone_group(rig, "BBone Curve", True)
                bone_in.bone_group = bone_out.bone_group = bg
            if self.hide_bones.get(rig):
                bg = Get.bone_group(rig, "BBone Stretch [Hidden]")
                if not bg:
                    bg = New.bone_group(rig, "BBone Stretch [Hidden]", 'THEME20')
                for name in self.hide_bones[rig]:
                    rig.pose.bones[name].bone_group = bg

        def post_pose():
            for name in self.center_bones[rig]:
                pbone = rig.pose.bones[name]
                pose(pbone)
                if not pbone.custom_shape:
                    self.bone_widgets['start'].append(pbone)
            for name in self.hide_bones[rig]:
                rig.data.bones[name].hide = True

        if do_mch:
            bone_mch = bones[get_name(bone, 'bbone')]
        if do_start_end:
            bone_start = bones[get_name(bone, 'bbone_start')]
            bone_end = bones[get_name(bone, 'bbone_end')]
            bone_head = bones[get_name(bone, 'bbone_head')]
        if do_in_out:
            bone_in = bones[get_name(bone, 'bbone_in')]
            bone_out = bones[get_name(bone, 'bbone_out')]

        if do_mch:
            pose_mch(bone_mch)
        if do_start_end:
            pose_start(bone_start)
            pose_head(bone_head)
            pose_end(bone_end)
        if do_in_out:
            pose_in_out(bone_in, 'in')
            pose_in_out(bone_out, 'out')
        set_bone_groups()
        post_pose()

    controls: bpy.props.EnumProperty(
        items=[
            ('ALL', "All", "Add all bbone controllers"),
            ('MCH', "Mch", "Add FK control"),
            ('START/END', "Start / End", "Insert stretch bones as custom in/out bbone handles"),
            ('IN/OUT', "In / Out", "Add drivers and controls for the bones' bbone properties"),
            ('NO_MCH', "No Mch", "Add everything but FK control"),
        ],
        name="Mode",
        description="Control setup to add for controlling the selected bones",
        default='NO_MCH',
        options={'SKIP_SAVE'},
    )


class BBONE_OT_remove_controllers(bpy.types.Operator):
    bl_description = "Remove drivers and bone controllers for selected bbones"
    bl_idname = 'zpy.remove_bbone_controllers'
    bl_label = "Remove BBone Controllers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        bbones = ('bbone', 'bbone_start', 'bbone_end', 'bbone_head', 'bbone_in', 'bbone_out')
        if context.selected_pose_bones:
            for bone in context.selected_pose_bones:
                if Is.linked(bone):
                    continue
                for bb in bbones:
                    if get_name(bone, bb) in bone.id_data.pose.bones:
                        return True

    def __init__(self):
        self.widgets = set()
        self.bones = dict()

    def invoke(self, context, event):
        return popup.invoke_confirm(context, self, event)

    def execute(self, context):
        (rigs, __) = get_rig_bones(context)

        for (rig, bones) in rigs.items():
            for bone in bones:
                self.pose_func(context, rig.pose.bones[bone.name])

        for rig in rigs:
            Set.mode(context, 'EDIT', rig)

        # Reparent soon-to-be orphans
        for (pbone, rig) in self.bones.items():
            bone = rig.data.edit_bones[pbone.name]

            for parent in bone.parent_recursive:
                if (parent not in self.bones):
                    break
            else:
                parent = None

            for child in bone.children:
                if (child not in self.bones):
                    child.parent = parent

        # Remove the bbone constrollers
        for (pbone, rig) in self.bones.items():
            ebones = rig.data.edit_bones
            ebones.remove(ebones[pbone.name])

        for rig in rigs:
            Set.mode(context, 'POSE', rig)

            # remove unused groups
            groups = (
                rig.pose.bone_groups[bg] for bg in
                ("BBone FK", "BBone Stretch", "BBone Curve", "BBone Stretch [Hidden]")
                if rig.pose.bone_groups.get(bg)
            )
            for bg in list(groups):
                for bone in rig.pose.bones:
                    if bone.bone_group == bg:
                        break
                else:
                    rig.pose.bone_groups.remove(bg)

        # Remove unused widgets
        for wgt in self.widgets:
            if (wgt.users < 2):  # 1) mesh  2+) objects
                wgt_col = list(wgt.users_collection)
                bpy.data.objects.remove(wgt)
                for col in wgt_col:
                    if not col.all_objects:
                        bpy.data.collections.remove(col)

        return {'FINISHED'}

    def pose_func(self, context, bone):
        rig = bone.id_data
        bones = rig.pose.bones
        bbones = ('bbone', 'bbone_start', 'bbone_end', 'bbone_head', 'bbone_in', 'bbone_out')

        def parse(bbone):
            self.bones[bbone] = rig

            # Prep the widget for removal
            wgt = bbone.custom_shape
            if wgt:
                self.widgets.add(wgt)

            # Remove stretch constraints
            for con in list(bone.constraints):
                if (getattr(con, 'target', None) == rig) and (con.subtarget == bbone.name):
                    bone.constraints.remove(con)

            # Remove Custom Handle
            if bone.bbone_custom_handle_start == bbone:
                bone.bone.bbone_custom_handle_start = None
                bone.bone.bbone_handle_type_start = 'AUTO'
            if bone.bbone_custom_handle_end == bbone:
                bone.bone.bbone_custom_handle_end = None
                bone.bone.bbone_handle_type_end = 'AUTO'

        for bbone_name in bbones:
            bbone = bones.get(get_name(bone, bbone_name))
            if not bbone:
                continue

            parse(bbone)

            if bbone_name in ('bbone_start', 'bbone_end') and Get.mirror_bone(bbone):
                (prefix, replace, suffix, number) = utils.flip_name(bone.name, only_split=True)
                center_name = prefix + suffix + number
                center = bones.get(center_name)
                if center:
                    parse(center)

            # Remove BBone drivers
            if bbone_name in ('bbone_in', 'bbone_out'):
                in_out = bbone_name.split('_')[1]
                in_outs = (
                    f'bbone_curve{in_out}x', f'bbone_curve{in_out}y',
                    f'bbone_roll{in_out}', f'bbone_scale{in_out}x',
                    f'bbone_scale{in_out}y', f'bbone_ease{in_out}',
                )
                for bbone_in_out in in_outs:
                    Driver = Get.driver(bone, bbone_in_out)
                    try:
                        target = Driver.driver.variables[0].targets[0]
                    except:
                        continue
                    if (target.bone_target == bbone.name) and (target.id == rig):
                        bone.driver_remove(bbone_in_out)


def get_name(bone, bbone):
    bn = bone.name
    (prefix, replace, suffix, number) = utils.flip_name(bn, only_split=True)

    if bn == bn.title():
        bbone = bbone.title()
    elif bn == bn.upper():
        bbone = bbone.upper()

    if prefix and replace:
        return f"{prefix}.{bbone}{replace}{suffix}{number}"
    elif (suffix or number) and (bn != utils.flip_name(bn)):
        return f"{prefix}{replace}{suffix}.{bbone}{number}"
    else:
        return f"{bn}.{bbone}"


def get_rig_bones(context):
    rigs = dict()  # rig object with a list of selected and mirrored bones
    selected = list()  # remember selected and non-selected mirror bones

    for bone in context.selected_pose_bones:
        rig = bone.id_data
        if Is.linked(rig):
            continue
        if rig not in rigs:
            rigs[rig] = list()

        if (bone not in rigs[rig]):
            rigs[rig].append(bone)
            selected.append((bone, rig))
            if (rig.pose.use_mirror_x or rig.data.use_mirror_x):
                mirror = Get.mirror_bone(bone)
                if mirror and (mirror not in rigs[rig]):
                    rigs[rig].append(mirror)
                    selected.append((mirror, rig))

    return (rigs, selected)


def draw_menu(self, context):
    layout = self.layout
    layout.operator('zpy.add_bbone_controllers', icon='IPO_BEZIER')
    layout.operator('zpy.add_bbone_controllers', text="    (start/end)", icon='IPO_BEZIER').controls = 'START/END'
    layout.operator('zpy.add_bbone_controllers', text="    (in/out)", icon='IPO_BEZIER').controls = 'IN/OUT'
    layout.operator('zpy.add_bbone_controllers', text="    (with FK)", icon='IPO_BEZIER').controls = 'ALL'


def register():
    args = dict(idname=BBONE_OT_remove_controllers, name='Pose', type='X')
    km.add(**args)
    km.add(**args, shift=True)


def unregister():
    km.remove()
