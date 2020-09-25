import bpy
from zpy import utils


class Addon_Properties(bpy.types.AddonPreferences, utils.Preferences):
    bl_idname = __package__  # __name__

    def draw(self, context):
        layout = self.layout
        self.draw_keymaps(context)
