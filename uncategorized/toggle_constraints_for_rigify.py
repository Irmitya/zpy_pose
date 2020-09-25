import bpy


rigify_ui = getattr(bpy.types, 'DATA_PT_rigify_buttons', None)
constraints_cache = list()


def draw(self, context):
    layout = self.layout

    wm = context.window_manager
    arm = getattr(context.object, 'data', None)

    if hasattr(arm, 'rigify_generate_mode'):
        rgm = arm.rigify_generate_mode
    elif hasattr(wm, 'rigify_generate_mode'):
        rgm = wm.rigify_generate_mode
    else:
        rgm = None

    if rgm != 'overwrite':
        return

    row = layout.row()
    row.active = False
    lab = ("Disable Constraints", "Re-enable Constraints")[bool(constraints_cache)]
    row.operator('pose.rigify_tmp_toggle_constraints', text=lab)


class RIGIFY_OT_toggle_constraints(bpy.types.Operator):
    bl_description = (
        "Enable/Disable constraints from other bones/objects, targetting "
        "the active rigify rig.\nRemoves excessive delay when re-generating "
        "a rig, when external bones/objects have constraints targetting it"
    )
    bl_idname = 'pose.rigify_tmp_toggle_constraints'
    bl_label = "Toggle Constraints to Rigify"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        arm = getattr(context.object, 'data', None)

        if hasattr(arm, 'rigify_target_rig'):
            rig = arm.rigify_target_rig
        elif hasattr(wm, 'rigify_target_rig'):
            name = wm.rigify_target_rig
            if not name:
                name = 'rig'
            rig = bpy.data.objects.get(name)
        else:
            rig = None

        return rig

    def execute(self, context):
        wm = context.window_manager
        arm = context.object.data
        if hasattr(arm, 'rigify_target_rig'):
            rig = arm.rigify_target_rig
        elif hasattr(wm, 'rigify_target_rig'):
            name = wm.rigify_target_rig
            if not name:
                name = 'rig'
            rig = bpy.data.objects.get(name)
        else:
            rig = None

        if not rig:
            return

        #---------------------------------
        # First run, so disable constraints
        if not constraints_cache:
            _items = [o for o in bpy.data.objects if o != rig]
            _items.extend([b for o in _items for b in getattr(o.pose, 'bones', [])])
            for _src in _items:
                for _c in _src.constraints:
                    if getattr(_c, 'target', None) == rig:
                        constraints_cache.append(_c)
                        _c.target = None
                    if hasattr(_c, 'targets'):
                        for _t in _c.targets:
                            if _t.target == rig:
                                constraints_cache.append(_t)
                                _t.target = None
        #---------------------------------
        # Restore Constraints
        else:
            for _c in constraints_cache:
                _c.target = rig
            constraints_cache.clear()

        return {'FINISHED'}


def register():
    if not rigify_ui: return
    rigify_ui.append(draw)


def unregister():
    if not rigify_ui: return
    rigify_ui.remove(draw)
