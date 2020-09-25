import bpy
from bpy.types import Menu
from zpy import Is
from . add_mannequin import mannequin


class MACRO_MT_daz(Menu):
    bl_description = ""
    bl_label = "Rig Macros"

    def draw(self, context):
        layout = self.layout

        if not (self.rig(context) or self.mesh(context)):
            layout.label(text="No rigs selected", icon='ERROR')

    def rig(self, context):
        layout = self.layout

        rig = meta = rigify = False
        count = 0
        for daz in context.selected_objects:
            if not Is.armature(daz):
                continue
            # elif daz.data.get('rig_id') is not None:
            #     rigify = True
            # elif daz.data.rigify_layers:
            #     meta = True
            # rig = True
            count += 1
            if count >= 2:
                layout.operator('daz.merge_rigs')
                break

        for op in ('macro.daz_to_metarig', 'macro.daz_to_metarig_weights',
                   'macro.generate_rigify', 'macro.meta_from_rigify',
                   'macro.meta_to_rigify', 'macro.rigify_to_meta'):
            if eval(f'bpy.ops.{op}.poll()'):
                layout.operator(op)
                rig = True

        return (rig or (count >= 2))

        # layout.operator('daz.merge_rigs')
        # layout.operator('macro.daz_to_metarig')
        # if meta:
        #     layout.operator('macro.generate_rigify')
        #     layout.operator('macro.meta_to_rigify')
        # if rig:
        #     layout.operator('macro.rigify_to_meta')
        # if bpy.ops.macro.meta_from_rigify.poll():
        #     layout.operator('macro.meta_from_rigify')

        # # layout.separator(factor=1.0)
        # # layout.operator('macro.daz_rig_setup')
        # # layout.operator('macro.auto_rename_bones')
        # # layout.operator('macro.auto_rename_bones', text="Rename Bones (Undo)").revert = True

    def mesh(self, context):
        layout = self.layout

        obj = context.active_object
        if not (Is.mesh(obj) and Is.armature(obj.parent)):
            return False

        scn = context.scene
        if hasattr(scn, 'DazShowRigging'):
            layout.prop(scn, 'DazMannequinGroup', text="")
            idname = 'daz.add_mannequin_macro'
            # op = layout.operator(idname, text="Full Macro")
            layout.operator_menu_hold(idname, menu='MACRO_MT_add_mannequin_full',
                text="Add Mannequin (Full Macro)" + mannequin.head).macro = True
            layout.operator_menu_hold(idname, menu='MACRO_MT_add_mannequin_only',
                text="Add Mannequin" + mannequin.head)
            # op.head = 'SOLID'
            # op.macro = True

            # layout.operator(idname, text="Solid").head = 'SOLID'
            # layout.operator(idname, text="Jaw").head = 'JAW'
            # layout.operator(idname, text="Full").head = 'FULL'

        layout.operator('object.data_transfer_mannequin_preset', icon='OUTLINER_DATA_MESH')
        layout.operator('object.data_transfer_materials', icon='MATERIAL')

        return True


class MACRO_MT_add_mannequin_full(Menu):
    bl_description = ""
    bl_label = "Add Mannequin (Full Macro)..."

    def draw(self, context):
        layout = self.layout

        def operator(text, head):
            op = layout.operator('daz.add_mannequin_macro', text=text)
            op.head = head
            op.macro = True

        operator(text="Solid", head='SOLID')
        operator(text="Jaw", head='JAW')
        operator(text="Full", head='FULL')


class MACRO_MT_add_mannequin_only(Menu):
    bl_description = ""
    bl_label = "Add Mannequin..."

    def draw(self, context):
        layout = self.layout

        idname = 'daz.add_mannequin_macro'
        layout.operator(idname, text="Solid").head = 'SOLID'
        layout.operator(idname, text="Jaw").head = 'JAW'
        layout.operator(idname, text="Full").head = 'FULL'


def draw_menu(self, context):
    layout = self.layout
    layout.menu('MACRO_MT_daz')


def register():
    bpy.types.VIEW3D_MT_object.append(draw_menu)
    bpy.types.VIEW3D_MT_pose.append(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(draw_menu)
    bpy.types.VIEW3D_MT_pose.remove(draw_menu)
