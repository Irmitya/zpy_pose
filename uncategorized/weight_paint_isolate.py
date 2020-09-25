from zpy import register_keymaps, Get
import bpy
km = register_keymaps()


class MESH_OT_lock_weights(bpy.types.Operator):
    bl_description = "Lock all vertex groups except for those of the selected bones"
    bl_idname = 'object.vertex_group_isolate_bones'
    bl_label = "Lock by Selected Bones"
    # bl_options = {'REGISTER', 'UNDO'}

    global Auto_normalize, Locks
    Auto_normalize = None
    Locks = {}

    # DATA_PT_vertex_groups
    # MESH_MT_vertex_group_specials

    @classmethod
    def description(cls, context, properties):
        if not Locks:
            return
        elif Get.selected_pose_bones(context, force=True):
            return "Toggle locked weights to the selected bones"
        else:
            return "Reset locked weights to normal"

    @classmethod
    def poll(self, context):
        return (context.mode == 'PAINT_WEIGHT')

    def execute(self, context):
        global Auto_normalize, Locks
        ts = context.scene.tool_settings
        pbones = Get.selected_pose_bones(context, force=True)
        mode = self.mode
        obj = context.object
            # 2.8 doesn't do multi-object weight paint

        if Auto_normalize is None:
            # first run
            Auto_normalize = ts.use_auto_normalize
                # Without auto normalize, locks essentially do nothing

        if self.mode in ['None', 'DEFAULT']:
            # In case op called without invoke
            # Allow op to be called to only run in one mode regardless as to selection
            self.mode = 'None'
            mode = ('RESET', 'SET')[bool(pbones)]

        if mode == 'SET':
            bones = [b.name for b in pbones]

            toggled = 0
            for vg in obj.vertex_groups:
                if (obj.name, vg.name) not in Locks:
                    # store initial value
                    Locks[obj.name, vg.name] = vg.lock_weight
                if vg.name in bones:
                    vg.lock_weight = False
                    toggled += 1
                else:
                    vg.lock_weight = True

            report = f"{toggled}/{len(obj.vertex_groups)} " \
                "Bone Weight Groups Locked"

            ts.use_auto_normalize = True
        else:
            for vg in obj.vertex_groups:
                vg.lock_weight = Locks.get((obj.name, vg.name), vg.lock_weight)
            report = f"Reset {len(Locks)} Vertex Group Locks"

            # reset first run value
            ts.use_auto_normalize = Auto_normalize
            Auto_normalize = None
            Locks = {}

        self.report({'INFO'}, report)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout.column(True)

        row = layout.row(True)
        row.prop_enum(self, 'mode', 'SET', "Set", icon='LOCKED')
        row.prop_enum(self, 'mode', 'RESET', "Reset", icon='UNLOCKED')

        layout.prop_enum(self, 'mode', 'DEFAULT', "", icon='FILE_REFRESH')

    mode: bpy.props.EnumProperty(
        items=[
            ('SET', "Set Locks", "Enable locks on vertex groups"),
            ('RESET', "Reset Locks", "Reset locks on vertex groups"),
            ('DEFAULT', "Set/Reset Locks", "Enable locks on vertex groups if bones are selected, otherwise reset them"),
            ('None', "", ""),  # hidden, use default
            ],
        name="Toggle Locks Mode",
        # description="Enable / Disable Locks on vertex groups",
        default='DEFAULT',  # ('string' or {'set'})  from items
        # options={},  # Enumerator in ['HIDDEN', 'SKIP_SAVE'].
    )


def draw_menu(self, context):
    w_menu = getattr(self, 'bl_idname', None) == 'VIEW3D_MT_pose_context_menu'
    # self.bl_label == 'Pose Context Menu'

    if w_menu and context.mode != 'PAINT_WEIGHT':
        return

    if not Locks:
        name = "Lock by Selected Bones"
    elif Get.selected_pose_bones(context, force=True):
        name = "Toggle Locks to Selected Bones"
    else:
        name = "Reset Weight Locks"

    layout = self.layout
    layout.operator('object.vertex_group_isolate_bones', text=name, icon='PINNED')
    if w_menu:
        layout.separator()


# Mesh > Vertex Groups > Dropdown menu
# properties = bpy.types.MESH_MT_vertex_group_specials  # 2.7
properties = bpy.types.MESH_MT_vertex_group_context_menu  # 2.8


# Bone weights isolator
def register():
    km.add(MESH_OT_lock_weights, 'Weight Paint', type='Q', value='PRESS', shift=True)
    properties.append(draw_menu)
    bpy.types.VIEW3D_MT_paint_weight.append(draw_menu)
    bpy.types.VIEW3D_MT_pose_context_menu.prepend(draw_menu)


def unregister():
    km.remove()
    properties.remove(draw_menu)
    bpy.types.VIEW3D_MT_paint_weight.remove(draw_menu)
    bpy.types.VIEW3D_MT_pose_context_menu.remove(draw_menu)
