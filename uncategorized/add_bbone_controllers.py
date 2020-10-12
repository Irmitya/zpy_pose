import bpy
from zpy import Get, New, Set, utils


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
        else:
            return txt + "Note: intended for disconnected bones"\
                ".\nResults in bone chains are functional but not as good"

    @classmethod
    def poll(cls, context):
        return context.selected_pose_bones

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        for bone in context.selected_pose_bones:
            self.func(context, bone)

        return {'FINISHED'}

    def func(self, context, bone):
        rig = bone.id_data
        ebones = rig.data.edit_bones
        hide_bones = list()  # bones to queue for hiding

        if self.controls == 'ALL':
            do_mch = do_start_end = do_in_out = True
        elif self.controls == 'NO_MCH':
            do_mch = False
            do_start_end = do_in_out = True
        else:
            do_mch = (self.controls == 'MCH')
            do_start_end = (self.controls == 'START/END')
            do_in_out = (self.controls == 'IN/OUT')
            if do_in_out and (bone.bone.bbone_segments < 2):
                # parenting to the bone will cause dependency loop, with drivers
                # if the bone isn't using bbones
                return

        def get_disconnected_parent(bone):
            if ((bone is None) or (not bone.parent)):
                return
            elif bone.use_connect:
                # Keep going up the chain until it finds a disconnected bone
                return get_disconnected_parent(bone.parent)
            else:
                return bone.parent

        def get_name(bone, bbone):
            bn = bone.name
            (prefix, replace, suffix, number) = utils.flip_name(bn, only_split=True)

            if bn == bn.title():
                bbone = bbone.title()
            elif bn == bn.upper():
                bbone = bbone.upper()

            if prefix and replace:
                return f"{prefix[:-1]}.{bbone}{prefix[-1]}{replace}{suffix}{number}"
            elif suffix or number:
                return f"{prefix}{replace}{suffix}.{bbone}{number}"
            else:
                return f"{bn}.{bbone}"

        def reset(bone, edit_bone):
            attributes = [
                'head', 'head_radius', 'tail', 'tail_radius',
                'roll', 'matrix', 'layers', 'bbone_x', 'bbone_z',
                ]

            for atr in attributes:
                if hasattr(bone, atr):
                    setattr(bone, atr, getattr(edit_bone, atr))

        def edit(ebone, bbone_xz=1.0):
            abone = ebones[bone.name]
            reset(ebone, abone)
            ebone.bbone_x *= bbone_xz
            ebone.bbone_z *= bbone_xz
            ebone.use_deform = False
            ebone.inherit_scale = 'NONE'

        def edit_mch(ebone):
            edit(ebone, 1.25)
            abone = ebones[bone.name]
            ebone.parent = abone.parent
            ebone.inherit_scale = abone.inherit_scale
            # ebone.use_connect = abone.use_connect
            # abone.use_connect = False
            # abone.parent = ebone
            # for cbone in abone.children:
                # cbone.parent = ebone

        def edit_start(ebone):
            edit(ebone, 2.5)
            bbone = ebones[bone.name]
            if do_mch:
                ebone.parent = ebones[bone_mch.name]
            else:
                if bbone.parent and bbone.use_connect:
                    ebone.parent = ebones.get(get_name(bbone.parent, 'bbone_end'))
                if ebone.parent:
                    hide_bones.append(ebone.name)
                else:
                    ebone.parent = get_disconnected_parent(bbone)
                if not do_in_out:
                    cbone = ebones.get(get_name(bbone, 'bbone_in'))
                    if cbone:
                        cbone.parent = ebone
            ebone.tail = utils.lerp(ebone.head, ebone.tail, 0.1)

        def edit_head(ebone):
            edit(ebone, 0.5)
            ebone.parent = ebones[bone_start.name]
            ebone.tail = utils.lerp(ebone.head, ebone.tail, 0.1)
            ebone.translate(ebone.head - ebone.tail)
            ebones[bone.name].bbone_custom_handle_start = ebone

        def edit_end(ebone):
            edit(ebone, 2.5)
            bbone = ebones[bone.name]
            if do_mch:
                ebone.parent = ebones[bone_mch.name]
            else:
                ebone.parent = get_disconnected_parent(bbone)
                if not do_in_out:
                    cbone = ebones.get(get_name(bbone, 'bbone_out'))
                    if cbone:
                        cbone.parent = ebone
            for cbone in bbone.children:
                if cbone.use_connect:
                    cbone_start = ebones.get(get_name(cbone, 'bbone_start'))
                    if cbone_start:
                        cbone_start.parent = ebone
                        hide_bones.append(cbone_start.name)
            ebone.head = utils.lerp(ebone.head, ebone.tail, 0.9)
            ebone.translate(ebone.tail - ebone.head)
            bbone.bbone_custom_handle_end = ebone

        def edit_in(ebone):
            edit(ebone, 2.0)
            if do_start_end:
                ebone.parent = ebones[bone_start.name]
            else:
                ebone.parent = ebones.get(get_name(bone, 'bbone_start'), ebones[bone.name])
            (head, tail) = (ebone.head.copy(), ebone.tail.copy())
            ebone.head = utils.lerp(head, tail, 0.1)
            ebone.tail = utils.lerp(head, tail, 0.2)

        def edit_out(ebone):
            edit(ebone, 2.0)
            if do_start_end:
                ebone.parent = ebones[bone_end.name]
            else:
                ebone.parent = ebones.get(get_name(bone, 'bbone_end'), ebones[bone.name])
            (head, tail) = (ebone.head.copy(), ebone.tail.copy())
            ebone.tail = utils.lerp(head, tail, 0.8)
            ebone.head = utils.lerp(head, tail, 0.9)
            ebone.align_roll(-ebones[bone.name].z_axis)
                # This bone is reversed, so the the roll needs to be flipped

        def add_driver(pbone, path, transform_type, name="var", expression="", frames=[]):
            if Get.driver(pbone, path):
                bone.driver_remove(path)

            Driver = bone.driver_add(path)

            while Driver.keyframe_points:
                Driver.keyframe_points.remove(Driver.keyframe_points[0])

            if frames:
                Driver.extrapolation = 'LINEAR'
                while Driver.modifiers:
                    Driver.modifiers.remove(Driver.modifiers[0])
                Driver.keyframe_points.add(len(frames))
                for key, co in zip(Driver.keyframe_points[:], frames):
                    key.interpolation = 'LINEAR'
                    key.co = co

            driver = Driver.driver
            if expression:
                driver.expression = expression.replace('{name}', name)
                driver.type = 'SCRIPTED'
            else:
                driver.expression = name
                driver.type = 'AVERAGE'
            while driver.variables:
                driver.variables.remove(driver.variables[0])
            var = driver.variables.new()
            var.name = name
            var.type = 'TRANSFORMS'
            target = var.targets[0]
            target.id = rig
            target.bone_target = pbone.name
            target.rotation_mode = 'AUTO'
            target.transform_space = 'LOCAL_SPACE'
            target.transform_type = transform_type

            return Driver

        def pose(pbone):
            pbone.rotation_mode = 'XYZ'

        def pose_mch(pbone):
            Set.select(bone, False)
            Set.select(pbone, True)
            rig.data.bones.active = pbone.bone

            pbone.rotation_mode = bone.rotation_mode
            pbone.lock_location = bone.lock_location
            pbone.lock_rotation = bone.lock_rotation
            pbone.lock_rotation_w = bone.lock_rotation_w
            pbone.lock_rotations_4d = bone.lock_rotations_4d
            pbone.lock_scale = (True, False, True)
            pbone.custom_shape_transform = bone
            widget(pbone, wgt='Box', global_size=1, scale=(0.75, 0.75, 1))
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
            # widget(pbone, slide=(0, -0.5, 0))
            widget(pbone, wgt='Blenrig - Box', global_size=3)
            if not (bone.parent and bone.bone.use_connect):
                con = bone.constraints.new('COPY_LOCATION')
                con.target = rig
                con.subtarget = pbone.name
                # Using offset will cause the Stretch TO constraint to fail if the bone's parent is scaled.
                # con.use_offset = True
                # con.target_space = con.owner_space = 'LOCAL_WITH_PARENT'

        def pose_head(pbone):
            pose(pbone)
            pbone.bone.hide = True
            pbone.lock_location = (True, True, True)
            pbone.lock_rotation = (True, True, True)
            pbone.lock_rotation_w = True
            pbone.lock_scale = (True, True, True)

        def pose_end(pbone):
            pose(pbone)
            pbone.lock_scale = (True, True, True)
            # widget(pbone, slide=(0, 0.5, 0))
            widget(pbone, wgt='Blenrig - Box', global_size=3)
            con = bone.constraints.new('STRETCH_TO')
            con.target = rig
            con.subtarget = pbone.name

        def pose_in_out(pbone, in_out):
            pose(pbone)
            pbone.lock_location = (True, False, True)
            pbone.lock_scale = (False, True, False)
            widget(pbone, global_size=7.5, slide=(0, 0.5, 0))
            length = bone.bone.length

            # add_driver(pbone, f'bbone_curve{in_out}x', 'ROT_Z', "rotation_Z", '-{name} * %s' % length)
            # if (in_out == 'in'):
                # add_driver(pbone, 'bbone_curveiny', 'ROT_X', "rotation_x", '{name} * %s' % length)
                # add_driver(pbone, 'bbone_rollin', 'ROT_Y', "rotation_y")
            # else:
                # add_driver(pbone, 'bbone_curveouty', 'ROT_X', "rotation_x", '-{name} * %s' % length)
                # add_driver(pbone, 'bbone_rollout', 'ROT_Y', "rotation_y", '-{name}')
            # add_driver(pbone, f'bbone_ease{in_out}', 'SCALE_Y', "scale_y", '{name} - 1')

            add_driver(pbone, f'bbone_curve{in_out}x', 'ROT_Z', "rotation_Z", frames=[(0, 0), (-1, length)])
            add_driver(pbone, f'bbone_curve{in_out}y', 'ROT_X', "rotation_x", frames=[(0, 0), ((1, -1)[in_out == 'out'], length)])
            add_driver(pbone, f'bbone_roll{in_out}', 'ROT_Y', "rotation_y", frames=[(0, 0), ((1, -1)[in_out == 'out'], 1)])

            add_driver(pbone, f'bbone_scale{in_out}x', 'SCALE_X', "scale_X")
            add_driver(pbone, f'bbone_scale{in_out}y', 'SCALE_Z', "scale_Z")
            # add_driver(pbone, f'bbone_ease{in_out}', 'SCALE_Y', "scale_y", frames=[(1, 0), (2, 1)])
            add_driver(pbone, f'bbone_ease{in_out}', 'LOC_Y', "location_y", frames=[(0, 0), (length, 1)])

        def widget(pbone, wgt='Sphere', global_size=6, scale=(1, 1, 1), slide=None):
            from mathutils import Vector
            bpy.ops.bonewidget.create_widget(
                global_size=global_size,
                slide=Vector(slide) if slide else Vector(),
                scale=scale,
                bones='[%r]' % pbone,
                widget=wgt,
            )

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
            if do_in_out:
                bg = Get.bone_group(rig, "BBone Curve")
                if not bg:
                    bg = New.bone_group(rig, "BBone Curve", True)
                bone_in.bone_group = bone_out.bone_group = bg
            if hide_bones:
                bg = Get.bone_group(rig, "BBone Stretch [Hidden]")
                if not bg:
                    bg = New.bone_group(rig, "BBone Stretch [Hidden]", 'THEME20')
                for name in hide_bones:
                    rig.pose.bones[name].bone_group = bg
                    rig.data.bones[name].hide = True

        if do_start_end:
            bone.bone.bbone_handle_type_start = bone.bone.bbone_handle_type_end = 'ABSOLUTE'

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
        default='ALL',
        options={'SKIP_SAVE'},
    )


def draw_menu(self, context):
    self.layout.operator('zpy.add_bbone_controllers', icon='IPO_BEZIER')
    self.layout.operator('zpy.add_bbone_controllers', text="    (in/out)", icon='IPO_BEZIER').controls = 'IN/OUT'
    self.layout.operator('zpy.add_bbone_controllers', text="    (start/end)", icon='IPO_BEZIER').controls = 'START/END'
    self.layout.operator('zpy.add_bbone_controllers', text="    (no MCH)", icon='IPO_BEZIER').controls = 'NO_MCH'
