import bpy
from zpy import register_keymaps, Get, Set, Is, utils
km = register_keymaps()


def connect(bone=None, split=None, bone2=None):
    parent = (bone.parent, bone2)[bool(bone2)]
    length = bone.parent.length
    parent.tail = bone.head

    if split:
        parent.length = length
    # elif not bone2:
        # bone.use_connect = True


class POSE_OT_fill_bone_gaps(bpy.types.Operator):
    bl_description = "Fill and connect gaps for disconnected bones"
    bl_idname = 'zpy.fill_gaps'
    bl_label = "Fill Bone Gaps"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.mode == 'PAINT_WEIGHT': return
        return Get.selected_pose_bones(context) or Get.selected_bones(context)

    def execute(self, context):
        # active = Get.active(context)

        for rig in context.selected_editable_objects:
            if not Is.armature(rig):
                continue

            mode = rig.mode

            if not Set.mode(context, 'EDIT', rig):
                Set.mode(context, mode, rig)
                continue
            mirror = rig.data.use_mirror_x
            rig.data.use_mirror_x = False

            # Set.active(context, rig)
            bones = Get.selected_edit_bones(context, rig)

            links = []  # empty list
            for bone in bones:
                if bone.parent and not Is.connected(bone):  # prevent root-error
                    link = rig.data.edit_bones.new('COR-%s<>%s' % (bone.parent.name, bone.name))
                    link.tail = bone.head
                    link.head = bone.parent.tail

                    link.layers = bone.layers
                    # link.layers = utils.layer(30)

                    # # layer 28 = IK
                    # # Layer 32 = Gap<>fillers
                    # if (rig.data.rigify_layers):
                        # link.layers	=	[True if index in (31,) else False for index, layer in enumerate(range(32))]

                    link.use_deform = False
                    link.parent = bone.parent
                    bone.parent = link
                    connect(link)
                    connect(bone)
                    link.use_connect = True
                    bone.use_connect = True

                    # bpy.ops.object.mode_set(mode='POSE');bpy.ops.object.mode_set(mode='EDIT');
                    links.append(link.name)
                    # bone = rig.pose.bones[link.name]
                    # bone.lock_ik_x = True
                    # bone.lock_ik_y = True
                    # bone.lock_ik_z = True

                    '''def gap(bone):
                        #bpy.ops.object.mode_set(mode='POSE');
                        bone = C.active_object.pose.bones[bone]
                        bone.lock_ik_x=True;	bone.lock_ik_y=True;	bone.lock_ik_z=True;
                        #bpy.ops.object.mode_set(mode='EDIT');
                    try:
                        bone.lock_ik_x=True;	bone.lock_ik_y=True;	bone.lock_ik_z=True;
                        link = link.name
                    except: continue
                    '''
                elif Is.connected(bone):
                    bone.use_connect = True
                else:  # root-ctrl-bone
                    continue
                    "or this will create a parent for a 'root' bone"
                    link = rig.data.edit_bones.new('COR-%s<>%s' % (bone.name, bone.name))
                    link.tail = bone.tail
                    link.head = bone.head

                    link.layers = utils.layer(30)

                    # link.layers = bone.layers
                    link.use_deform = False
                    link.show_wire = True
                    bone.parent = link

                    links.append(link.name)

            rig.data.use_mirror_x = mirror
            Set.mode(context, 'POSE', rig)

            for link in links:
                link = rig.pose.bones.get(link, None)
                if link is None:
                    # if bone's head+tail are the same, it'll cancel itself out
                    continue
                links = link.name.replace('COR-', '', 1).split('<>')
                # linked = rig.pose.bones.get(links[1], None)

                if self.lock_ik:
                    link.ik_stiffness_x = 1
                    link.ik_stiffness_y = 1
                    link.ik_stiffness_z = 1
                    if (links[0] != links[1]):  # Parent <x> Child
                        link.lock_ik_x = True
                        link.lock_ik_y = True
                        link.lock_ik_z = True
                        link.lock_location = [True, True, True]
                        link.lock_rotation_w = True
                        link.lock_rotation = [True, True, True]
                        link.lock_scale = [True, True, True]
                    else:  # Original bone was copied for a control bone
                        print("Original bone was copied for a control bone")
                        # try:
                            # linked.lock_ik_x=True;	linked.lock_ik_y=True;	linked.lock_ik_z=True;
                            # linked.ik_stiffness_x=1;	linked.ik_stiffness_y=1;	linked.ik_stiffness_z=1;
                            # if not 'WGT-hips' in bpy.data.objects:
                                # bpy.context.scene.quickrig.create_wgt = 'hips'
                                # bpy.ops.quickrig.create_widgets()
                            # widget = bpy.data.objects['WGT-hips']
                            # link.custom_shape = widget
                            # #have the bone follow the original	#link.custom_shape_transform = rig.pose.bones[links[1]]
                            # link.use_custom_shape_bone_size = False
                            # con = widget.constraints.new('COPY_TRANSFORMS')
                            # con.target = rig;	con.subtarget = link.name;
                            # widget.layers[9] = True;	layers = 0
                            # for layer in widget.layers:
                                # if layers != 9:	layer = False
                        # except:	pass
                        ...

                def bgroup(name):
                    bgroups = rig.pose.bone_groups
                    if name in bgroups:
                        group = bgroups[name]
                    else:
                        group = bgroups.new(name=name)
                        group.color_set = 'CUSTOM'
                        black = ((0.0, 0.0, 0.0))
                        select = ((0.1, 0.7, 0.9))
                        c = group.colors
                        c.active, c.normal, c.select = black, black, select
                    return group

                link.bone_group = bgroup('<>')

            Set.mode(context, mode, rig)
        # if active:
            # Set.active(context, active)
        return {'FINISHED'}

    lock_ik: bpy.props.BoolProperty(
        name="Lock IK",
        description="Lock the fill bones during IK."
        "\nDisable to allow  bone to pseudo disconnect during IK",
        default=True
    )


def register():
    # Fill Bone Gaps
    args = dict(idname=POSE_OT_fill_bone_gaps, type='F', value='PRESS', ctrl=True)
    km.add(name='Pose', **args)  # Pose Mode is needed separate in 2.8
    km.add(name='Armature', **args)


def unregister():
    km.remove()
