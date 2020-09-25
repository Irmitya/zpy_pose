import bpy
from zpy import New, Set, Is, utils
from mathutils import Vector, Color
from math import radians
from .daz_metarig_names import vg_names

# TODO: transfer weights and modifiers to the metarig
# instead of only after generating rigify


class MACRO_OT_daz_to_metarig(bpy.types.Operator):
    # bl_description = "Convert a Daz rig to a Rigify Metarig"
    bl_description = "Create a Metarig based on a Daz Rig"
    bl_idname = 'macro.daz_to_metarig'
    bl_label = "Convert Daz to Metarig"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        if context.mode not in ('POSE', 'OBJECT'):
            return False

        for daz in context.selected_objects:
            if not Is.armature(daz) or daz.data.rigify_layers or daz.data.get('rig_id') is not None:
                continue

            return True

    def execute(self, context):
        active_mode = context.mode
        daz_meta = list()

        for daz in context.selected_objects:
            if not Is.armature(daz) or daz.data.rigify_layers or daz.data.get('rig_id') is not None:
                continue

            # mode = daz.get('daz_to_rigify')
            # if mode in (None, 'daz') or mode.startswith('bpy'):
                # # Is a daz Rig
                # pass
            # else:
                # # Is a metarig
                # continue

            # Add armature object
            meta = New.armature(context, daz.name + "-metarig")
            meta.data.name = daz.data.name + "-metarig"
            # obj.location = Get.cursor(context).location
            meta.location = daz.location
            meta.data.rigify_rig_basename = daz.name + "-rig"
            Set.armature_display_type(meta, 'BBONE')

            # Create metarig
            Set.active_select(context, meta, False)
            Set.mode(context, daz, 'EDIT')
            Set.mode(context, meta, 'EDIT')
            daz_to_meta(daz, meta)
            bpy.ops.object.mode_set(mode=active_mode)
            Set.select(daz, False)

            # rig['daz_to_rigify'] = 'daz'
            daz['daz_to_rigify'] = repr(meta)
            meta['daz_to_rigify'] = 'metarig'
            # daz_meta.append((daz, meta))

        # for (daz, meta) in daz_meta:
            # Set.active(context, meta)
            # bpy.ops.pose.rigify_generate()
            # rig = context.active_object
            # meta_to_rigify(daz, rig)

        return {'FINISHED'}


def daz_to_meta(daz, obj):
    Set.select(daz)
    Set.select(obj)

    arm = obj.data

 # Rigify Groups
    for i in range(6):
        arm.rigify_colors.add()

    arm.rigify_colors[0].name = "Root"
    arm.rigify_colors[0].active = Color((0.5490196347236633, 1.0, 1.0))
    arm.rigify_colors[0].normal = Color((0.4352940022945404, 0.18431399762630463, 0.4156860113143921))
    arm.rigify_colors[0].select = Color((0.31372547149658203, 0.7843138575553894, 1.0))
    arm.rigify_colors[0].standard_colors_lock = True
    arm.rigify_colors[1].name = "IK"
    arm.rigify_colors[1].active = Color((0.5490196347236633, 1.0, 1.0))
    arm.rigify_colors[1].normal = Color((0.6039220094680786, 0.0, 0.0))
    arm.rigify_colors[1].select = Color((0.31372547149658203, 0.7843138575553894, 1.0))
    arm.rigify_colors[1].standard_colors_lock = True
    arm.rigify_colors[2].name = "Special"
    arm.rigify_colors[2].active = Color((0.5490196347236633, 1.0, 1.0))
    arm.rigify_colors[2].normal = Color((0.9568629860877991, 0.7882350087165833, 0.04705899953842163))
    arm.rigify_colors[2].select = Color((0.31372547149658203, 0.7843138575553894, 1.0))
    arm.rigify_colors[2].standard_colors_lock = True
    arm.rigify_colors[3].name = "Tweak"
    arm.rigify_colors[3].active = Color((0.5490196347236633, 1.0, 1.0))
    arm.rigify_colors[3].normal = Color((0.03921600058674812, 0.21176500618457794, 0.5803920030593872))
    arm.rigify_colors[3].select = Color((0.31372547149658203, 0.7843138575553894, 1.0))
    arm.rigify_colors[3].standard_colors_lock = True
    arm.rigify_colors[4].name = "FK"
    arm.rigify_colors[4].active = Color((0.5490196347236633, 1.0, 1.0))
    arm.rigify_colors[4].normal = Color((0.11764699965715408, 0.5686269998550415, 0.035294000059366226))
    arm.rigify_colors[4].select = Color((0.31372547149658203, 0.7843138575553894, 1.0))
    arm.rigify_colors[4].standard_colors_lock = True
    arm.rigify_colors[5].name = "Extra"
    arm.rigify_colors[5].active = Color((0.5490196347236633, 1.0, 1.0))
    arm.rigify_colors[5].normal = Color((0.9686279892921448, 0.2509799897670746, 0.09411799907684326))
    arm.rigify_colors[5].select = Color((0.31372547149658203, 0.7843138575553894, 1.0))
    arm.rigify_colors[5].standard_colors_lock = True

 # Rigify Layers
    layer = arm.rigify_layers.add()
    layer.name = "Face"
    layer.row = 1
    layer.selset = False
    layer.group = 5
    layer = arm.rigify_layers.add()
    layer.name = "Face (Primary)"
    layer.row = 2
    layer.selset = False
    layer.group = 2
    layer = arm.rigify_layers.add()
    layer.name = "Face (Secondary)"
    layer.row = 2
    layer.selset = False
    layer.group = 3

    layer = arm.rigify_layers.add()
    layer.name = "Torso"
    layer.row = 3
    layer.selset = False
    layer.group = 3
    # layer = arm.rigify_layers.add()
    # layer.name = "Torso (FK)"
    # layer.row = 4
    # layer.selset = False
    # layer.group = 5
    layer = arm.rigify_layers.add()
    layer.name = "Torso (Tweak)"
    layer.row = 4
    layer.selset = False
    layer.group = 4

    layer = arm.rigify_layers.add()
    layer.name = "Fingers"
    layer.row = 5
    layer.selset = False
    layer.group = 6
    layer = arm.rigify_layers.add()
    layer.name = "Fingers (Detail)"
    layer.row = 6
    layer.selset = False
    layer.group = 5

    layer = arm.rigify_layers.add()
    layer.name = "Toes"
    layer.row = 5
    layer.selset = False
    layer.group = 6
    layer = arm.rigify_layers.add()
    layer.name = "Toes (Detail)"
    layer.row = 6
    layer.selset = False
    layer.group = 5

    layer = arm.rigify_layers.add()
    layer.name = "Arm.L (IK)"
    layer.row = 7
    layer.selset = False
    layer.group = 2
    layer = arm.rigify_layers.add()
    layer.name = "Arm.L (FK)"
    layer.row = 8
    layer.selset = False
    layer.group = 5
    layer = arm.rigify_layers.add()
    layer.name = "Arm.L (Tweak)"
    layer.row = 9
    layer.selset = False
    layer.group = 4

    layer = arm.rigify_layers.add()
    layer.name = "Arm.R (IK)"
    layer.row = 7
    layer.selset = False
    layer.group = 2
    layer = arm.rigify_layers.add()
    layer.name = "Arm.R (FK)"
    layer.row = 8
    layer.selset = False
    layer.group = 5
    layer = arm.rigify_layers.add()
    layer.name = "Arm.R (Tweak)"
    layer.row = 9
    layer.selset = False
    layer.group = 4

    layer = arm.rigify_layers.add()
    layer.name = "Leg.L (IK)"
    layer.row = 10
    layer.selset = False
    layer.group = 2
    layer = arm.rigify_layers.add()
    layer.name = "Leg.L (FK)"
    layer.row = 11
    layer.selset = False
    layer.group = 5
    layer = arm.rigify_layers.add()
    layer.name = "Leg.L (Tweak)"
    layer.row = 12
    layer.selset = False
    layer.group = 4

    layer = arm.rigify_layers.add()
    layer.name = "Leg.R (IK)"
    layer.row = 10
    layer.selset = False
    layer.group = 2
    layer = arm.rigify_layers.add()
    layer.name = "Leg.R (FK)"
    layer.row = 11
    layer.selset = False
    layer.group = 5
    layer = arm.rigify_layers.add()
    layer.name = "Leg.R (Tweak)"
    layer.row = 12
    layer.selset = False
    layer.group = 4

    while len(arm.rigify_layers) < 28:
        layer = arm.rigify_layers.add()
        layer.name = ""
        layer.row = 1
        layer.selset = False
        layer.group = 0

    layer = arm.rigify_layers.add()
    layer.name = "Root"
    layer.row = 28
    layer.selset = False
    layer.group = 1

    layers = {l.name: utils.layer(i) for i, l in enumerate(arm.rigify_layers)}

 #####################################
 # Generate bones
 #####################################
    dbones = daz.data.edit_bones  # Original Daz rig
    bones = obj.data.edit_bones  # Metarig
    head = tail = None
    bone = None

    def get(*names):
        nonlocal head, tail
        head = dbones.get(names[0])
        tail = dbones.get(names[-1])
        return (head and tail)

    # Set.active(bpy.context, daz)
    roll_bone = bones.new('_tmp_bone_for_rolls_')
    bones.active = roll_bone
    ebones = bpy.context.selected_bones
    # ebones = bpy.context.selected_editable_bones
    for ebone in ebones:
        ebone.select = False

    def roll(head, tail, roll=0.000):
        bone.select = True
        roll_bone.head = head
        roll_bone.tail = tail
        roll_bone.roll = roll
        bpy.ops.armature.calculate_roll(type='ACTIVE')
        bone.select = False

  # Torso
   # Spine
    if get('pelvis'):
        bone = bones.new('spine')
        # bone.head = dbones['hip'].tail
        bone.head = head.tail  # pelvis is flipped
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0467
        bone.use_connect = False
    if get('pelvis', 'abdomenUpper'):
        bone = bones.new('spine.001')
        bone.head = head.head  # pelvis is flipped
        bone.tail = tail.head
        bone.roll = tail.roll
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0467
        bone.tail_radius = 0.0594
        bone.use_connect = True
        bone.parent = bones.get('spine')
    if get('abdomenUpper', 'chestLower'):
        bone = bones.new('spine.001.2')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0467
        bone.tail_radius = 0.0594
        bone.use_connect = True
        bone.parent = bones.get('spine.001')
    if get('chestLower', 'chestUpper'):
        bone = bones.new('spine.002')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0594
        bone.tail_radius = 0.0633
        bone.use_connect = True
        bone.parent = bones.get('spine.001.2', bones.get('spine.001'))
    if get('chestUpper'):
        bone = bones.new('spine.003')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0633
        bone.tail_radius = 0.0251
        bone.use_connect = True
        bone.parent = bones.get('spine.002')
   # Neck/Head
    if get('chestUpper', 'neckUpper'):
        bone = bones.new('spine.004')
            # bone.head = dbones['chestUpper'].tail
        bone.head = head.tail
            # bone.head = dbones['neckLower'].head
        bone.tail = tail.head
        bone.roll = head.roll
            # bone.tail = dbones['neckLower'].tail
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0346
        bone.head_radius = 0.0251
        bone.tail_radius = 0.0251
        bone.use_connect = False  # New default
            # bone.use_connect = True
        bone.parent = bones.get('spine.003')
    if get('neckUpper', 'head'):
        bone = bones.new('spine.005')
        bone.head = head.head
            # bone.head = dbones['neckLower'].tail
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0251
        bone.tail_radius = 0.0175
        bone.use_connect = True
        bone.parent = bones.get('spine.004')
    if get('head'):
        bone = bones.new('spine.006')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.length = 0.19830000400543213
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0390
        bone.head_radius = 0.0175
        bone.tail_radius = 0.0087
        bone.use_connect = True
        bone.parent = bones.get('spine.005')
   # Hip Deformers

    # Default metarig position for spine.head
    vector_spine = Vector((0.0000, 0.0552, 1.0099))
    spine = bones.get('spine')
    if spine:
        # Offset of the default position and the new position
        dif = Vector((
            abs(x - y) * (1 if x < y else -1)
            for x, y in zip(vector_spine, spine.head)
        ))
        bone = bones.new('pelvis.L')
        bone.head = Vector((0.0000, 0.0552, 1.0099)) + dif
        bone.tail = Vector((0.1112, -0.0451, 1.1533)) + dif
        # xx bone.roll = -1.0756
        roll((0.0000, 0.0552, 1.0099), (0.1112, -0.0451, 1.1533), -1.0756)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = spine

        bone = bones.new('pelvis.R')
        bone.head = Vector((-0.0000, 0.0552, 1.0099)) + dif
        bone.tail = Vector((-0.1112, -0.0451, 1.1533)) + dif
        # xx bone.roll = 1.0756
        roll((-0.0000, 0.0552, 1.0099), (-0.1112, -0.0451, 1.1533), 1.0756)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = spine

        bone = bones.new('MCH-butt.L')
        bone.use_deform = False
        bone.head = Vector((0.1000, 0.0820, 1.0258)) + dif
        bone.tail = Vector((0.1000, 0.1516, 1.0258)) + dif
        # xx bone.roll = 0.0000
        roll((0.1000, 0.0820, 1.0258), (0.1000, 0.2212, 1.0258), 0.0000)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        # bone.parent = spine
        bone = bones.new('butt.L')
        bone.head = Vector((0.1000, 0.0820, 1.0258)) + dif
        bone.tail = Vector((0.1000, 0.2212, 1.0258)) + dif
        # xx bone.roll = 0.0000
        roll((0.1000, 0.0820, 1.0258), (0.1000, 0.2212, 1.0258), 0.0000)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones['MCH-butt.L']

        bone = bones.new('MCH-butt.R')
        bone.use_deform = False
        bone.head = Vector((-0.1000, 0.0820, 1.0258)) + dif
        bone.tail = Vector((-0.1000, 0.1516, 1.0258)) + dif
        # xx bone.roll = -0.0000
        roll((-0.1000, 0.0820, 1.0258), (-0.1000, 0.2212, 1.0258), 0.0000)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        # bone.parent = spine
        bone = bones.new('butt.R')
        bone.head = Vector((-0.1000, 0.0820, 1.0258)) + dif
        bone.tail = Vector((-0.1000, 0.2212, 1.0258)) + dif
        # xx bone.roll = -0.0000
        roll((-0.1000, 0.0820, 1.0258), (-0.1000, 0.2212, 1.0258), 0.0000)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones['MCH-butt.R']
   # Chest
    if get('lPectoral'):
        bone = bones.new('breast.L')
        bone.head = head.head
        bone.tail = tail.tail
        # bone.roll = head.roll + radians(44)
        roll((0.1184, 0.0485, 1.4596), (0.1184, -0.0907, 1.4596), 0.0000)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0504
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones.get('spine.003')
    if get('rPectoral'):
        bone = bones.new('breast.R')
        bone.head = head.head
        bone.tail = tail.tail
        # bone.roll = head.roll - radians(44)
        roll((-0.1184, 0.0485, 1.4596), (-0.1184, -0.0907, 1.4596), 0.0000)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0504
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones.get('spine.003')
  # Arms
   # Upper
    if get('lCollar'):
        bone = bones.new('shoulder.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.0004
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones.get('spine.00')
    if get('rCollar'):
        bone = bones.new('shoulder.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.0004
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones.get('spine.003')

    if get('lShldrBend', 'lForearmBend'):
        bone = bones.new('upper_arm.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 2.0724
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0317
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0268
        bone.use_connect = False
        bone.parent = bones.get('shoulder.L')
    if get('rShldrBend', 'rForearmBend'):
        bone = bones.new('upper_arm.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -2.0724
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0317
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0268
        bone.use_connect = False
        bone.parent = bones.get('shoulder.R')

    if get('lForearmBend', 'lHand'):
        bone = bones.new('forearm.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 2.1535
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0244
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0090
        bone.use_connect = True
        bone.parent = bones.get('upper_arm.L')
        pre = (bone, head, tail)
        if get('lForearmTwist', 'lHand'):
            bone = bones.new('forearm.L.001')
            bone.head = head.head
            bone.tail = tail.head
            bone.roll = head.roll
            # xx bone.roll = 2.1535
            roll(head.head, head.tail, head.roll)
            bone.envelope_distance = 0.0244
            bone.head_radius = 0.0268
            bone.tail_radius = 0.0090
            bone.use_connect = True
            bone.parent = pre[0]
    if get('rForearmBend', 'rHand'):
        bone = bones.new('forearm.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -2.1535
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0244
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0090
        bone.use_connect = True
        bone.parent = bones.get('upper_arm.R')
        pre = (bone, head, tail)
        if get('rForearmTwist', 'rHand'):
            bone = bones.new('forearm.R.001')
            bone.head = head.head
            bone.tail = tail.head
            bone.roll = head.roll
            # xx bone.roll = -2.1535
            roll(head.head, head.tail, head.roll)
            bone.envelope_distance = 0.0244
            bone.head_radius = 0.0268
            bone.tail_radius = 0.0090
            bone.use_connect = True
            bone.parent = pre[0]
   # Hands
    if get('lHand'):
        bone = bones.new('hand.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll - radians(90)
        # xx bone.roll = 2.2103
        bone.envelope_distance = 0.0244
        bone.head_radius = 0.0090
        bone.tail_radius = 0.0134
        bone.use_connect = True
        bone.parent = bones.get('forearm.L')
    if get('rHand'):
        bone = bones.new('hand.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll + radians(90)
        # xx bone.roll = -2.2103
        bone.envelope_distance = 0.0244
        bone.head_radius = 0.0090
        bone.tail_radius = 0.0134
        bone.use_connect = True
        bone.parent = bones.get('forearm.R')

    if get('lCarpal1'):
        bone = bones.new('palm.01.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -2.4928
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.L')
    if get('rCarpal1'):
        bone = bones.new('palm.01.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.4928
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.R')
    if get('lCarpal2'):
        bone = bones.new('palm.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -2.5274
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.L')
    if get('rCarpal2'):
        bone = bones.new('palm.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.5274
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.R')
    if get('lCarpal3'):
        bone = bones.new('palm.03.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -2.5843
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.L')
    if get('rCarpal3'):
        bone = bones.new('palm.03.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.5843
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.R')
    if get('lCarpal4'):
        bone = bones.new('palm.04.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -2.5155
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.L')
    if get('rCarpal4'):
        bone = bones.new('palm.04.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.5155
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = False
        bone.parent = bones.get('hand.R')
  # Fingers
   # Thumb
    if get('lThumb1'):
        bone = bones.new('thumb.01.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.1587
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.01.L')
    if get('rThumb1'):
        bone = bones.new('thumb.01.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.1587
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.01.R')
    if get('lThumb2'):
        bone = bones.new('thumb.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.4798
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('thumb.01.L')
    if get('rThumb2'):
        bone = bones.new('thumb.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.4798
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('thumb.01.R')
    if get('lThumb3'):
        bone = bones.new('thumb.03.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.5826
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('thumb.02.L')
    if get('rThumb3'):
        bone = bones.new('thumb.03.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.5826
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('thumb.02.R')
   # Index
    if get('lIndex1'):
        bone = bones.new('f_index.01.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -2.0315
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.01.L')
    if get('rIndex1'):
        bone = bones.new('f_index.01.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.0315
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.01.R')
    if get('lIndex2'):
        bone = bones.new('f_index.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.8799
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_index.01.L')
    if get('rIndex2'):
        bone = bones.new('f_index.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.8799
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_index.01.R')
    if get('lIndex3'):
        bone = bones.new('f_index.03.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.6760
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_index.02.L')
    if get('rIndex3'):
        bone = bones.new('f_index.03.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.6760
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_index.02.R')
   # Middle
    if get('lMid1'):
        bone = bones.new('f_middle.01.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -2.0067
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.02.L')
    if get('rMid1'):
        bone = bones.new('f_middle.01.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.0067
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.02.R')
    if get('lMid2'):
        bone = bones.new('f_middle.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.8283
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_middle.01.L')
    if get('rMid2'):
        bone = bones.new('f_middle.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.8283
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_middle.01.R')
    if get('lMid3'):
        bone = bones.new('f_middle.03.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.7483
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_middle.02.L')
    if get('rMid3'):
        bone = bones.new('f_middle.03.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.7483
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_middle.02.R')
   # Ring
    if get('lRing1'):
        bone = bones.new('f_ring.01.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.9749
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.04.L')
    if get('rRing1'):
        bone = bones.new('f_ring.01.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 2.0082
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.03.R')
    if get('lRing2'):
        bone = bones.new('f_ring.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.8946
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_ring.01.L')
    if get('rRing2'):
        bone = bones.new('f_ring.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.8946
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_ring.01.R')
    if get('lRing3'):
        bone = bones.new('f_ring.03.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.6582
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_ring.02.L')
    if get('rRing3'):
        bone = bones.new('f_ring.03.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.6582
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_ring.02.R')
   # Pinky
    if get('lPinky1'):
        bone = bones.new('f_pinky.01.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.9749
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.04.L')
    if get('rPinky1'):
        bone = bones.new('f_pinky.01.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.9749
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = False
        bone.parent = bones.get('palm.04.R')
    if get('lPinky2'):
        bone = bones.new('f_pinky.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.9059
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_pinky.01.L')
    if get('rPinky2'):
        bone = bones.new('f_pinky.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.9059
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0072
        bone.use_connect = True
        bone.parent = bones.get('f_pinky.01.R')
    if get('lPinky3'):
        bone = bones.new('f_pinky.03.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -1.7639
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_pinky.02.L')
    if get('rPinky3'):
        bone = bones.new('f_pinky.03.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 1.7639
        bone.envelope_distance = 0.0034
        bone.head_radius = 0.0072
        bone.tail_radius = 0.0036
        bone.use_connect = True
        bone.parent = bones.get('f_pinky.02.R')
  # Legs
   # Upper
    if get('lThighBend', 'lShin'):
        bone = bones.new('thigh.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0290
        bone.use_connect = False
        bone.parent = bones.get('spine')
        pre = (bone, head, tail)
        if get('lThighTwist', 'lShin'):
            bone = bones.new('thigh.L.001')
            bone.head = head.head
            bone.tail = tail.head
            bone.roll = head.roll
            # xx bone.roll = 0.0000
            roll(head.head, head.tail, head.roll)
            bone.envelope_distance = 0.0527
            bone.head_radius = 0.0268
            bone.tail_radius = 0.0290
            bone.use_connect = False
            bone.parent = pre[0]
    if get('rThighBend', 'rShin'):
        bone = bones.new('thigh.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -0.0000
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0290
        bone.use_connect = False
        bone.parent = bones.get('spine')
        pre = (bone, head, tail)
        if get('rThighBend', 'rShin'):
            bone = bones.new('thigh.R.001')
            bone.head = head.head
            bone.tail = tail.head
            bone.roll = head.roll
            # xx bone.roll = -0.0000
            roll(head.head, head.tail, head.roll)
            bone.envelope_distance = 0.0527
            bone.head_radius = 0.0268
            bone.tail_radius = 0.0290
            bone.use_connect = False
            bone.parent = pre[0]

    if get('lShin', 'lFoot'):
        bone = bones.new('shin.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.0000
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0290
        bone.tail_radius = 0.0139
        bone.use_connect = True
        bone.parent = bones.get('thigh.L')
    if get('rShin', 'rFoot'):
        bone = bones.new('shin.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -0.0000
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0290
        bone.tail_radius = 0.0139
        bone.use_connect = True
        bone.parent = bones.get('thigh.R')
   # Foot
    if get('lFoot', 'lToe'):
        bone = bones.new('foot.L')
        bone.head = head.head
        bone.tail = tail.head
        # bone.roll = head.roll - radians(2)
        # roll((0.0980, 0.0162, 0.0852), (0.0980, -0.0934, 0.0167), 0.0000)
        roll(head.head, head.tail, head.roll)
        # bone.roll += radians(180)
        bone.envelope_distance = 0.0094
        bone.head_radius = 0.0139
        bone.tail_radius = 0.0139
        bone.use_connect = True
        bone.parent = bones.get('shin.L')
    if get('rFoot', 'rToe'):
        bone = bones.new('foot.R')
        bone.head = head.head
        bone.tail = tail.head
        # bone.roll = head.roll + radians(2)
        # roll((-0.0980, 0.0162, 0.0852), (-0.0980, -0.0934, 0.0167), 0.0000)
        roll(head.head, head.tail, head.roll)
        # bone.roll += radians(180)
        bone.envelope_distance = 0.0094
        bone.head_radius = 0.0139
        bone.tail_radius = 0.0139
        bone.use_connect = True
        bone.parent = bones.get('shin.R')
    if get('lHeel'):
        bone = bones.new('heel.02.L')
        bone.use_deform = False
        bone.head = 0.0600, 0.0459, 0.0000
        bone.tail = 0.1400, 0.0459, 0.0000
        dist = abs(bone.head[0] - bone.tail[0]) / 2
        tail = head.tail
        bone.head[0] = tail[0] - dist
        bone.tail[0] = tail[0] + dist
        bone.head[1:] = tail[1:]
        bone.tail[1:] = tail[1:]
        # xx bone.roll = 0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones.get('foot.L')
    if get('rHeel'):
        bone = bones.new('heel.02.R')
        bone.use_deform = False
        bone.head = -0.0600, 0.0459, 0.0000
        bone.tail = -0.1400, 0.0459, 0.0000
        dist = -abs(bone.head[0] - bone.tail[0]) / 2
        tail = head.tail
        bone.head[0] = tail[0] - dist
        bone.tail[0] = tail[0] + dist
        bone.head[1:] = tail[1:]
        bone.tail[1:] = tail[1:]
        # xx bone.roll = -0.0000
        bone.envelope_distance = 0.0527
        bone.head_radius = 0.0268
        bone.tail_radius = 0.0134
        bone.use_connect = False
        bone.parent = bones.get('foot.R')
  # Toes
   # Master
    if get('lToe'):
        bone = bones.new('toe.L')
        bone.head = head.head
        bone.tail = tail.tail
        # bone.roll = head.roll + radians(176)
        roll((0.0980, -0.0934, 0.0167), (0.0980, -0.1606, 0.0167), 0.0000)
        bone.envelope_distance = 0.0094
        bone.head_radius = 0.0139
        bone.tail_radius = 0.0070
        bone.use_connect = True
        bone.parent = bones.get('foot.L')
    if get('rToe'):
        bone = bones.new('toe.R')
        bone.head = head.head
        bone.tail = tail.tail
        # bone.roll = head.roll - radians(176)
        roll((-0.0980, -0.0934, 0.0167), (-0.0980, -0.1606, 0.0167), 0.0000)
        bone.envelope_distance = 0.0094
        bone.head_radius = 0.0139
        bone.tail_radius = 0.0070
        bone.use_connect = True
        bone.parent = bones.get('foot.R')
   # Big
    if get('lBigToe', 'lBigToe_2'):
        bone = bones.new('toe1.01.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 5.3752
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0070
        bone.head_radius = 0.0064
        bone.tail_radius = 0.0058
        bone.use_connect = False
        bone.parent = bones.get('toe.L')
    if get('rBigToe', 'rBigToe_2'):
        bone = bones.new('toe1.01.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -5.3752
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0070
        bone.head_radius = 0.0064
        bone.tail_radius = 0.0058
        bone.use_connect = False
        bone.parent = bones.get('toe.R')
    if get('lBigToe_2'):
        bone = bones.new('toe1.02.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 6.6350
        bone.envelope_distance = 0.0063
        bone.head_radius = 0.0058
        bone.tail_radius = 0.0051
        bone.use_connect = True
        bone.parent = bones.get('toe1.01.L')
    if get('rBigToe_2'):
        bone = bones.new('toe1.02.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -6.6350
        bone.envelope_distance = 0.0063
        bone.head_radius = 0.0058
        bone.tail_radius = 0.0051
        bone.use_connect = True
        bone.parent = bones.get('toe1.01.R')
   # Long
    if get('lSmallToe1', 'lSmallToe1_2'):
        bone = bones.new('toe2.01.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -6.4991
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0054
        bone.head_radius = 0.0050
        bone.tail_radius = 0.0048
        bone.use_connect = False
        bone.parent = bones.get('toe.L')
    if get('rSmallToe1', 'rSmallToe1_2'):
        bone = bones.new('toe2.01.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 6.4991
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0054
        bone.head_radius = 0.0050
        bone.tail_radius = 0.0048
        bone.use_connect = False
        bone.parent = bones.get('toe.R')
    if get('lSmallToe1_2'):
        bone = bones.new('toe2.02.L')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = 6.5326
        bone.envelope_distance = 0.0051
        bone.head_radius = 0.0048
        bone.tail_radius = 0.0048
        bone.use_connect = True
        bone.parent = bones.get('toe2.01.L')
    if get('rSmallToe1_2'):
        bone = bones.new('toe2.02.R')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = -6.5326
        bone.envelope_distance = 0.0051
        bone.head_radius = 0.0048
        bone.tail_radius = 0.0048
        bone.use_connect = True
        bone.parent = bones.get('toe2.01.R')
    if get('lSmallToe1_2'):
        bone = bones.new('toe2.03.L')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.0917
        bone.envelope_distance = 0.0052
        bone.head_radius = 0.0048
        bone.tail_radius = 0.0024
        bone.use_connect = True
        bone.parent = bones.get('toe2.02.L')
    if get('rSmallToe1_2'):
        bone = bones.new('toe2.03.R')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.0917
        bone.envelope_distance = 0.0052
        bone.head_radius = 0.0048
        bone.tail_radius = 0.0024
        bone.use_connect = True
        bone.parent = bones.get('toe2.02.R')
   # Middle
    if get('lSmallToe2', 'lSmallToe2_2'):
        bone = bones.new('toe3.01.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 0.8805
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0044
        bone.head_radius = 0.0041
        bone.tail_radius = 0.0045
        bone.use_connect = False
        bone.parent = bones.get('toe.L')
    if get('rSmallToe2', 'rSmallToe2_2'):
        bone = bones.new('toe3.01.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -0.8805
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0044
        bone.head_radius = 0.0041
        bone.tail_radius = 0.0045
        bone.use_connect = False
        bone.parent = bones.get('toe.R')
    if get('lSmallToe2_2'):
        bone = bones.new('toe3.02.L')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = -0.1698
        bone.envelope_distance = 0.0049
        bone.head_radius = 0.0045
        bone.tail_radius = 0.0054
        bone.use_connect = True
        bone.parent = bones.get('toe3.01.L')
    if get('rSmallToe2_2'):
        bone = bones.new('toe3.02.R')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = 0.1698
        bone.envelope_distance = 0.0049
        bone.head_radius = 0.0045
        bone.tail_radius = 0.0054
        bone.use_connect = True
        bone.parent = bones.get('toe3.01.R')
    if get('lSmallToe2_2'):
        bone = bones.new('toe3.03.L')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.1821
        bone.envelope_distance = 0.0058
        bone.head_radius = 0.0054
        bone.tail_radius = 0.0027
        bone.use_connect = True
        bone.parent = bones.get('toe3.02.L')
    if get('rSmallToe2_2'):
        bone = bones.new('toe3.03.R')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.1821
        bone.envelope_distance = 0.0058
        bone.head_radius = 0.0054
        bone.tail_radius = 0.0027
        bone.use_connect = True
        bone.parent = bones.get('toe3.02.R')
   # Ring
    if get('lSmallToe3', 'lSmallToe3_2'):
        bone = bones.new('toe4.01.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 2.3067
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0044
        bone.head_radius = 0.0041
        bone.tail_radius = 0.0037
        bone.use_connect = False
        bone.parent = bones.get('toe.L')
    if get('rSmallToe3', 'rSmallToe3_2'):
        bone = bones.new('toe4.01.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -2.3067
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0044
        bone.head_radius = 0.0041
        bone.tail_radius = 0.0037
        bone.use_connect = False
        bone.parent = bones.get('toe.R')
    if get('lSmallToe3_2'):
        bone = bones.new('toe4.02.L')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = 5.9125
        bone.envelope_distance = 0.0040
        bone.head_radius = 0.0037
        bone.tail_radius = 0.0049
        bone.use_connect = True
        bone.parent = bones.get('toe4.01.L')
    if get('rSmallToe3_2'):
        bone = bones.new('toe4.02.R')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = -5.9125
        bone.envelope_distance = 0.0040
        bone.head_radius = 0.0037
        bone.tail_radius = 0.0049
        bone.use_connect = True
        bone.parent = bones.get('toe4.01.R')
    if get('lSmallToe3_2'):
        bone = bones.new('toe4.03.L')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.2863
        bone.envelope_distance = 0.0054
        bone.head_radius = 0.0049
        bone.tail_radius = 0.0025
        bone.use_connect = True
        bone.parent = bones.get('toe4.02.L')
    if get('rSmallToe3_2'):
        bone = bones.new('toe4.03.R')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.2863
        bone.envelope_distance = 0.0054
        bone.head_radius = 0.0049
        bone.tail_radius = 0.0025
        bone.use_connect = True
        bone.parent = bones.get('toe4.02.R')
   # Pinky
    if get('lSmallToe4', 'lSmallToe4_2'):
        bone = bones.new('toe5.01.L')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = -4.4536
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0059
        bone.head_radius = 0.0054
        bone.tail_radius = 0.0038
        bone.use_connect = False
        bone.parent = bones.get('toe.L')
    if get('rSmallToe4', 'rSmallToe4_2'):
        bone = bones.new('toe5.01.R')
        bone.head = head.head
        bone.tail = tail.head
        bone.roll = head.roll
        # xx bone.roll = 4.4536
        roll(head.head, head.tail, head.roll)
        bone.envelope_distance = 0.0059
        bone.head_radius = 0.0054
        bone.tail_radius = 0.0038
        bone.use_connect = False
        bone.parent = bones.get('toe.R')
    if get('lSmallToe4_2'):
        bone = bones.new('toe5.02.L')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = 5.7951
        bone.envelope_distance = 0.0041
        bone.head_radius = 0.0038
        bone.tail_radius = 0.0060
        bone.use_connect = True
        bone.parent = bones.get('toe5.01.L')
    if get('rSmallToe4_2'):
        bone = bones.new('toe5.02.R')
        bone.head = head.head
        bone.tail = tail.center
        bone.roll = head.roll
        # xx bone.roll = -5.7951
        bone.envelope_distance = 0.0041
        bone.head_radius = 0.0038
        bone.tail_radius = 0.0060
        bone.use_connect = True
        bone.parent = bones.get('toe5.01.R')
    if get('lSmallToe4_2'):
        bone = bones.new('toe5.03.L')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = -0.2291
        bone.envelope_distance = 0.0065
        bone.head_radius = 0.0060
        bone.tail_radius = 0.0030
        bone.use_connect = True
        bone.parent = bones.get('toe5.02.L')
    if get('rSmallToe4_2'):
        bone = bones.new('toe5.03.R')
        bone.head = head.center
        bone.tail = tail.tail
        bone.roll = head.roll
        # xx bone.roll = 0.2291
        bone.envelope_distance = 0.0065
        bone.head_radius = 0.0060
        bone.tail_radius = 0.0030
        bone.use_connect = True
        bone.parent = bones.get('toe5.02.R')

  # Penis

    if get('Shaft 1'):
        bone = bones.new('shaft.01')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('root', bones.get('spine'))
    if get('Shaft 2'):
        bone = bones.new('shaft.02')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('shaft.01')
        if bone.parent:
            bone.head = bone.parent.tail
            bone.use_connect = True
    if get('Shaft 3'):
        bone = bones.new('shaft.03')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('shaft.02')
        if bone.parent:
            bone.head = bone.parent.tail
            bone.use_connect = True
    if get('Shaft 4'):
        bone = bones.new('shaft.04')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('shaft.03')
        if bone.parent:
            bone.head = bone.parent.tail
            bone.use_connect = True
    if get('Shaft5') or get('Shaft 5'):
        bone = bones.new('shaft.05')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('shaft.04')
        if bone.parent:
            bone.head = bone.parent.tail
            bone.use_connect = True
    if get('Shaft 6'):
        bone = bones.new('shaft.06')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('shaft.05')
        if bone.parent:
            bone.head = bone.parent.tail
            bone.use_connect = True
    if get('Shaft 7'):
        bone = bones.new('shaft.07')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('shaft.06')
        if bone.parent:
            bone.head = bone.parent.tail
            bone.use_connect = True

    if get('Scortum'):  # or get('BallsRoot'):
        bone = bones.new('scrotum')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('root', bones.get('spine'))
    if get('Left Testicle'):  # or get('Ball.L'):
        bone = bones.new('testicle.L')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('scrotum')
    if get('Right Testicle'):  # or get('Ball.R'):
        bone = bones.new('testicle.R')
        bone.head = head.head
        bone.tail = tail.tail
        bone.roll = head.roll
        bone.parent = bones.get('scrotum')

  # Delete temp roll bone
    for ebone in ebones:
        ebone.select = True
    bones.remove(roll_bone)

  # Other Bones
    other_bones = set(dbones.keys()).difference(vg_names.keys())
    if other_bones:
        layer = arm.rigify_layers[21]
        layer.name = "Other"
        layer.row = 13
        layer.selset = False
        layer.group = 6

        layers['Other'] = utils.layer(21)
    for name in other_bones:
        dbone = dbones[name]
        bone = bones.new(name)
        bone.head = dbone.head
        bone.tail = dbone.tail
        bone.roll = dbone.roll
        bone.envelope_distance = dbone.envelope_distance
        bone.head_radius = dbone.head_radius
        bone.tail_radius = dbone.tail_radius

    for name in other_bones:
        dbone = dbones[name]
        bone = bones[name]
        dparent = dbone.parent
        if not dparent:
            continue
        if dparent.name in other_bones:
            bone.parent = bones[dparent.name]
        elif dparent.name in vg_names:
            pname = vg_names[dparent.name]
            if pname:  # "DEF-_______"
                bone.parent = bones.get(pname[4:])
        bone.use_connect = (bone.parent and dbone.use_connect)

  # Set default bbone sizes
    for bone in bones:
        bone.bbone_x = bone.bbone_z = bone.length * 0.05

 #####################################
 # Set Pose Defaults
 #####################################
  # Update Pose Bones
    bpy.ops.object.mode_set(mode='OBJECT')

    dbones = daz.pose.bones  # Original Daz rig
    bones = obj.pose.bones  # Metarig
    pbone = None

    def get(name):
        nonlocal pbone
        pbone = bones.get(name)
        return (pbone)

  # Torso
   # Spine
    if get('spine'):
        pbone.rigify_type = 'spines.blenrig_spine'
            # pbone.rigify_type = 'spines.basic_spine'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.tweak_layers = layers['Torso (Tweak)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.fk_layers = layers['Torso (Tweak)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_custom_pivot = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_custom_hips_pivot = True
        except AttributeError:
            pass
    if get('spine.001'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
    if get('spine.001.2'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
    if get('spine.002'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
    if get('spine.003'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
   # Neck/Head
    if get('spine.004'):
        pbone.rigify_type = 'spines.super_head'
            # pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.connect_chain = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Torso (Tweak)']
        except AttributeError:
            pass
    if get('spine.005'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
    if get('spine.006'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Torso']
   # Hip deformers
    if get('pelvis.L'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.make_control = False
        except AttributeError:
            pass
    if get('pelvis.R'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.make_control = False
        except AttributeError:
            pass

    if get('butt.L'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
    if get('MCH-butt.L'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.make_control = False
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_widget = False
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_deform = False
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.relink_constraints = True
        except AttributeError:
            pass
        try:
            con = pbone.constraints.new(type='ARMATURE')
            con.use_deform_preserve_volume = True
            target = con.targets.new()
            target.target = obj
            target.subtarget = 'spine'
            target.weight = 0.5
            target = con.targets.new()
            target.target = obj
            target.subtarget = 'thigh.L'
            target.weight = 0.5
        except:
            pass
    if get('butt.R'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
    if get('MCH-butt.R'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.make_control = False
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_widget = False
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_deform = False
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.relink_constraints = True
        except AttributeError:
            pass
        try:
            con = pbone.constraints.new(type='ARMATURE')
            con.use_deform_preserve_volume = True
            target = con.targets.new()
            target.target = obj
            target.subtarget = 'spine'
            target.weight = 0.5
            target = con.targets.new()
            target.target = obj
            target.subtarget = 'thigh.R'
            target.weight = 0.5
        except:
            pass
   # Chest
    if get('breast.L'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']

    if get('breast.R'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
  # Arms
    if get('shoulder.L'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.make_widget = False
        except AttributeError:
            pass
    if get('shoulder.R'):
        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Torso']
        try:
            pbone.rigify_parameters.make_widget = False
        except AttributeError:
            pass

    if get('upper_arm.L'):
        pbone.rigify_type = 'limbs.super_limb'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Arm.L (IK)']
        try:
            pbone.rigify_parameters.fk_layers = layers['Arm.L (FK)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Arm.L (Tweak)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.rotation_axis = "x"
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_custom_pivot = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_ik_wrist_pivot = True
        except AttributeError:
            pass
    if get('upper_arm.R'):
        pbone.rigify_type = 'limbs.super_limb'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Arm.R (IK)']
        try:
            pbone.rigify_parameters.fk_layers = layers['Arm.R (FK)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Arm.R (Tweak)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.rotation_axis = "x"
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_custom_pivot = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_ik_wrist_pivot = True
        except AttributeError:
            pass

    if get('forearm.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Arm.L (IK)']
    if get('forearm.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Arm.R (IK)']
  # Hands
    if get('hand.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Arm.L (IK)']
    if get('hand.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Arm.R (IK)']

    if get('palm.01.L'):
        pbone.rigify_type = 'limbs.super_palm'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']
        try:
            pbone.rigify_parameters.palm_both_sides = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.palm_rotation_axis = "X"
        except AttributeError:
            pass
    if get('palm.01.R'):
        pbone.rigify_type = 'limbs.super_palm'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']
        try:
            pbone.rigify_parameters.palm_both_sides = True
        except AttributeError:
            pass

    if get('palm.02.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']
    if get('palm.02.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']

    if get('palm.03.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']
    if get('palm.03.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']

    if get('palm.04.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']
    if get('palm.04.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'YXZ'
        pbone.bone.layers = layers['Fingers']
  # Fingers

    def set_finger(pbone, head=False):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        if head:
            pbone.lock_rotation = (False, True, False)
        else:
            pbone.lock_rotation = (False, True, True)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Fingers']

    def rig_finger(pbone):
        # # pbone.rigify_type = 'basic.copy_chain'
        # pbone.rigify_type = 'limbs.simple_tentacle'
        pbone.rigify_type = 'limbs.super_finger'
        # try:
            # pbone.rigify_parameters.roll_alignment = 'manual'
        # except AttributeError:
            # pass
        # try:
            # pbone.rigify_parameters.copy_rotation_axes = (True, False, False)
        # except AttributeError:
            # pass
        try:
            pbone.rigify_parameters.primary_rotation_axis = 'X'
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_extra_ik_control = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_extra_layers = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Fingers (Detail)']
        except AttributeError:
            pass

    if get('thumb.01.L'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
        pbone.lock_rotation = (False, False, False)
    if get('thumb.01.R'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
        pbone.lock_rotation = (False, False, False)
    if get('f_index.01.L'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_index.01.R'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_middle.01.L'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_middle.01.R'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_ring.01.L'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_ring.01.R'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_pinky.01.L'):
        set_finger(pbone, head=True)
        rig_finger(pbone)
    if get('f_pinky.01.R'):
        set_finger(pbone, head=True)
        rig_finger(pbone)

    if get('thumb.02.L'):
        set_finger(pbone)
    if get('thumb.02.R'):
        set_finger(pbone)
    if get('f_index.02.L'):
        set_finger(pbone)
    if get('f_index.02.R'):
        set_finger(pbone)
    if get('f_middle.02.L'):
        set_finger(pbone)
    if get('f_middle.02.R'):
        set_finger(pbone)
    if get('f_ring.02.L'):
        set_finger(pbone)
    if get('f_ring.02.R'):
        set_finger(pbone)
    if get('f_pinky.02.L'):
        set_finger(pbone)
    if get('f_pinky.02.R'):
        set_finger(pbone)

    if get('thumb.03.L'):
        set_finger(pbone)
    if get('thumb.03.R'):
        set_finger(pbone)
    if get('f_index.03.L'):
        set_finger(pbone)
    if get('f_index.03.R'):
        set_finger(pbone)
    if get('f_middle.03.L'):
        set_finger(pbone)
    if get('f_middle.03.R'):
        set_finger(pbone)
    if get('f_ring.03.L'):
        set_finger(pbone)
    if get('f_ring.03.R'):
        set_finger(pbone)
    if get('f_pinky.03.L'):
        set_finger(pbone)
    if get('f_pinky.03.R'):
        set_finger(pbone)
  # Legs
    if get('thigh.L'):
        pbone.rigify_type = 'limbs.super_limb'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.L (IK)']
        try:
            pbone.rigify_parameters.limb_type = "leg"
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.fk_layers = layers['Leg.L (FK)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Leg.L (Tweak)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.rotation_axis = "x"
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_custom_pivot = True
        except AttributeError:
            pass
    if get('thigh.R'):
        pbone.rigify_type = 'limbs.super_limb'
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.R (IK)']
        try:
            pbone.rigify_parameters.fk_layers = layers['Leg.R (FK)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Leg.R (Tweak)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.limb_type = "leg"
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.rotation_axis = "x"
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.make_custom_pivot = True
        except AttributeError:
            pass

    if get('shin.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.L (IK)']
    if get('shin.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.R (IK)']

    if get('foot.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.L (IK)']
    if get('foot.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.R (IK)']

    if get('heel.02.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.L (IK)']
    if get('heel.02.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.R (IK)']

    if get('toe.L'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.L (IK)']
    if get('toe.R'):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Leg.R (IK)']
  # Toes

    def set_toe(pbone, head=False):
        pbone.rigify_type = ''
        pbone.lock_location = (False, False, False)
        if head:
            pbone.lock_rotation = (False, True, False)
        else:
            pbone.lock_rotation = (False, True, True)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'
        pbone.bone.layers = layers['Toes']

    def rig_toe(pbone):
        # # pbone.rigify_type = 'basic.copy_chain'
        # pbone.rigify_type = 'limbs.simple_tentacle'
        pbone.rigify_type = 'limbs.super_finger'

        # try:
            # pbone.rigify_parameters.roll_alignment = 'manual'
        # except AttributeError:
            # pass
        # try:
            # pbone.rigify_parameters.copy_rotation_axes = (True, False, False)
        # except AttributeError:
            # pass
        try:
            pbone.rigify_parameters.tweak_extra_layers = True
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_layers = layers['Toes (Detail)']
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.primary_rotation_axis = 'X'
        except AttributeError:
            pass

    if get('toe1.01.L'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe1.01.R'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe2.01.L'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe2.01.R'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe3.01.L'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe3.01.R'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe4.01.L'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe4.01.R'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe5.01.L'):
        set_toe(pbone, head=True)
        rig_toe(pbone)
    if get('toe5.01.R'):
        set_toe(pbone, head=True)
        rig_toe(pbone)

    if get('toe1.02.L'):
        set_toe(pbone)
    if get('toe1.02.R'):
        set_toe(pbone)
    if get('toe2.02.L'):
        set_toe(pbone)
    if get('toe2.02.R'):
        set_toe(pbone)
    if get('toe3.02.L'):
        set_toe(pbone)
    if get('toe3.02.R'):
        set_toe(pbone)
    if get('toe4.02.L'):
        set_toe(pbone)
    if get('toe4.02.R'):
        set_toe(pbone)
    if get('toe5.02.L'):
        set_toe(pbone)
    if get('toe5.02.R'):
        set_toe(pbone)

    if get('toe2.03.L'):
        set_toe(pbone)
    if get('toe2.03.R'):
        set_toe(pbone)
    if get('toe3.03.L'):
        set_toe(pbone)
    if get('toe3.03.R'):
        set_toe(pbone)
    if get('toe4.03.L'):
        set_toe(pbone)
    if get('toe4.03.R'):
        set_toe(pbone)
    if get('toe5.03.L'):
        set_toe(pbone)
    if get('toe5.03.R'):
        set_toe(pbone)

  # Penis
    if get('shaft.01') or get('Shaft 1') or get('shaftRoot'):
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'

        pbone.rigify_type = 'limbs.simple_tentacle'
        try:
            pbone.rigify_parameters.roll_alignment = 'manual'
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.copy_rotation_axes = (False, False, False)
        except AttributeError:
            pass
        try:
            pbone.rigify_parameters.tweak_extra_layers = True
        except AttributeError:
            pass
        # try:
        #     pbone.rigify_parameters.tweak_layers = layers['Toes (Tweak)']
        # except AttributeError:
        #     pass

    def balls(pbone):
        pbone.lock_location = (False, False, False)
        pbone.lock_rotation = (False, False, False)
        pbone.lock_rotation_w = False
        pbone.lock_scale = (False, False, False)
        pbone.rotation_mode = 'QUATERNION'

        pbone.rigify_type = 'basic.super_copy'

    if get('scrotum') or get('BallsRoot'):
        balls(pbone)
    if get('testicle.L') or get('Ball.L'):
        balls(pbone)
    if get('testicle.R') or get('Ball.R'):
        balls(pbone)

  # Other Bones
    for name in other_bones:
        dbone = dbones[name]
        pbone = bones[name]

        pbone.rigify_type = 'basic.super_copy'
        pbone.lock_location = dbone.lock_location
        pbone.lock_rotation = dbone.lock_rotation
        pbone.lock_rotation_w = dbone.lock_rotation_w
        pbone.lock_scale = dbone.lock_scale
        pbone.rotation_mode = dbone.rotation_mode
        pbone.bone.layers = layers['Other']
        try:
            pbone.rigify_parameters.make_widget = False
        except AttributeError:
            pass

 #####################################
 # Exit
 #####################################
    bpy.ops.object.mode_set(mode='EDIT')
    used_layers = [False] * 32
    for bone in arm.edit_bones:
        bone.inherit_scale = 'ALIGNED'
        for (i, l) in enumerate(bone.layers):
            if l:
                used_layers[i] = True
        if bone.name in other_bones:
            bone.select = True
            bone.select_head = True
            bone.select_tail = True
        else:
            bone.select = True
            bone.select_head = True
            bone.select_tail = True
            arm.edit_bones.active = bone

    arm.layers = used_layers
    # arm.layers = utils.layer(0, 3, 5, 7, 9, 12, 15, 18)
    # arm.layers[21] = bool(other_bones)
