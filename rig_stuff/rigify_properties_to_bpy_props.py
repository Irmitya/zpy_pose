# import bpy
# from bpy.props import BoolProperty
# from bpy.types import PoseBone


# def register():
#     def update_pole(self, context):
#         if "_parent" not in self.name:
#             return
#         name, lr = self.name.rsplit("_parent", 1)
#         bones = self.id_data.pose.bones

#         # self = bones.get(name + "_parent" + lr)
#         # ik = bones.get(name + "_ik" + lr)
#         pole = bones.get(name + "_ik_target" + lr)
#         line = bones.get("VIS_" + name + "_ik_pole" + lr)

#         if None in (pole, line):
#             return

#         pole.bone.hide = line.bone.hide = not self.pole_vector

#     PoseBone.pole_vector = BoolProperty(
#         name="Pole Vector",
#         description="Use a pole target control",
#         default=False,
#         options={'HIDDEN', 'ANIMATABLE'},
#         update=update_pole,
#     )


# def unregister():
#     del PoseBone.pole_vector
