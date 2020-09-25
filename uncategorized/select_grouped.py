import bpy
from zpy import Is, Set, register_keymaps, popup
km = register_keymaps()


class POSE_OT_select_grouped_multi(bpy.types.Operator):
    bl_description = "Select all visible bones grouped by similar properties"
    bl_idname = 'zpy.select_grouped'
    bl_label = "Select Grouped"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if (context.mode == 'PAINT_WEIGHT'):
            for obj in context.selected_objects:
                if (obj.mode == 'POSE'):
                    return True
            return False

        return True


    def invoke(self, context, event):
        return popup.menu(context, draw_menu=self.draw_menu, title=self.bl_label)

    def draw_menu(self, ui, context):
        layout = ui.layout
        layout.operator(self.bl_idname, text="Layer").type = 'LAYER'
        if hasattr(bpy.types.PoseBone, 'layers_extra'):
            layout.operator(self.bl_idname, text="Pseudo Layers").type = 'PSEUDO_LAYERS'
        layout.operator(self.bl_idname, text="Group").type = 'GROUP'
        layout.operator(self.bl_idname, text="Keying Set").type = 'KEYINGSET'
        layout.operator(self.bl_idname, text="In Object").type = 'IN_OBJECT'

    def execute(self, context):
        if (self.type == 'IN_OBJECT'):
            rigs = set()
            for b in context.selected_pose_bones:
                rigs.add(b.id_data)
            for rig in rigs:
                for b in rig.data.bones:
                    if Is.visible(context, b) and (not b.hide_select):
                        Set.select(b, True)
                    elif not self.extend:
                        Set.select(b, False)
            return {'FINISHED'}
        elif (self.type == 'PSEUDO_LAYERS'):
            rigs = dict()
            for b in context.selected_pose_bones:
                rig = b.id_data
                if rig not in rigs:
                    rigs[rig] = list()
                try:
                    selected_layers = eval(b.layers_extra)
                    rigs[rig].extend(selected_layers)
                    rigs[rig] = list(set(rigs[rig]))
                except:
                    pass
            for (rig, selected_layers) in rigs.items():
                visible_layers = [i for i, l in enumerate(rig.data.layers_extra.layers) if l.visible]
                for b in rig.pose.bones:
                    try:
                        bone_layers = eval(b.layers_extra)
                    except:
                        continue

                    if Is.visible(context, b):
                        for b_layer in bone_layers:
                            if (b_layer in selected_layers) and (b_layer in visible_layers):
                                Set.select(b, True)
                                break
                        else:
                            if not self.extend:
                                Set.select(b, False)
                    elif not self.extend:
                        Set.select(b, False)
            return {'FINISHED'}

        if self.type == 'GROUP':
            active_group = set()
            for b in context.selected_pose_bones:
                rig = b.id_data
                if (rig not in active_group) and b.bone_group:
                    rig.pose.bone_groups.active = b.bone_group
                    active_group.add(rig)

        try:
            return bpy.ops.pose.select_grouped(
                type=self.type, extend=self.extend)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex).split('Error: ', 1)[-1])
            return {'CANCELLED'}

    extend: bpy.props.BoolProperty(
        name="Extend", default=True,
        description="Extend selection instead of deselecting everything first"
    )

    type: bpy.props.EnumProperty(
        items=[
            ('LAYER', "Layer", "Shared layers"), ('GROUP', "Group", "Shared group"),
            ('KEYINGSET', "Keying Set", "All bones affected by active Keying Set"),
            ('IN_OBJECT', "In Object", "All visible bones in objects of selected bones"),
            ('PSEUDO_LAYERS', "Pseudo Layers", "Pseudo Layers of selected bones"),
        ],
        name="Type",
        description="",
        # default=None,  # ('string' or {'set'})  from items
        # options=set({'SKIP_SAVE'}),
    )


def register():
    args = dict(idname=POSE_OT_select_grouped_multi, type='G', shift=True)
    km.add(**args, name='Pose')
    km.add(**args, name='Weight Paint')


def unregister():
    km.remove()
