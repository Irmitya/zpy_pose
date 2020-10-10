import bpy
from . import add_bones, add_ik_chain, add_bbone_controllers


def draw_menu(self, context):
    if context.mode != 'POSE':
        return

    add_bones.draw_add_armature(self, context)
    add_bbone_controllers.draw_menu(self, context)
    add_ik_chain.draw_armature(self, context)

    self.layout.separator()


def register():
    bpy.types.VIEW3D_MT_armature_add.prepend(draw_menu)


def unregister():
    bpy.types.VIEW3D_MT_armature_add.remove(draw_menu)
