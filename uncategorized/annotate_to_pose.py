import bpy
from bpy_extras.view3d_utils import (location_3d_to_region_2d, region_2d_to_location_3d)
from mathutils import Color
from zpy import register_keymaps, Get, Is, New, utils, Set, keyframe
km = register_keymaps()


class POSE_OT_annotate_view(bpy.types.Operator):
    bl_description = "Make bones mimic the shape of an annoation"
    bl_idname = 'zpy.annotate_pose'
    bl_label = "Draw Pose"
    bl_options = {'UNDO_GROUPED'}
    bl_undo_group = "Annotation Draw"  # add it to the drawing's history

    @classmethod
    def description(cls, context, properties):
        return cls.bl_rna.description

    @classmethod
    def poll(cls, context):
        # selected = dict()

        # for b in context.selected_pose_bones:
            # if b.id_data not in selected:
                # selected[b.id_data] = list()
            # selected[b.id_data].append(b)

        # for (rig, bones) in selected.items():
            # if len(bones) >= 2:
                # return True

        # return False
        return context.selected_pose_bones

    # def invoke(self, context, event):
        # return self.execute(context)

    def execute(self, context):
        # selected = dict()

        # for b in context.selected_pose_bones:
            # if b.id_data not in selected:
                # selected[b.id_data] = list()
            # selected[b.id_data].append(b)

        # for (rig, bones) in selected.items():
            # if len(bones) >= 2:
                # Get.
                # self.selected = bones
                # break

        gp = context.annotation_data

        if gp is None:
            self.active_gp_layer = None
            bpy.ops.gpencil.annotation_add()
            gp = context.annotation_data
            gp.name = "Draw Pose"
        else:
            self.active_gp_layer = gp.layers.active
            bpy.ops.gpencil.layer_annotation_add()

        layer = gp.layers.active
        layer.info = 'TMP-Pose'
        layer.color = Color((1, 0, 0.5))
        layer.show_in_front = True
        # layer = gp.layers.new(name="Pose")
        # gp.layers.active = layer
        # gp.edit_line_color
        # gp.layers.active
        # gp.layers.remove()

        bpy.ops.gpencil.annotate('INVOKE_DEFAULT', mode='DRAW', wait_for_input=False)
        self.drawing = True

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not(self.drawing):
            return self.update_pose(context)

        if event.type in ('LEFTMOUSE', 'RET', 'NUMPAD_ENTER', 'SPACE'):
            self.drawing = False
            return {'PASS_THROUGH'}

        if event.type in ('RIGHTMOUSE', 'ESC'):
            return self.cancel(context)

        return {'PASS_THROUGH'}
        return {'RUNNING_MODAL'}

    def remove_annotation(self, context):
        gp = context.annotation_data

        if self.active_gp_layer is None:
            context.scene.grease_pencil = None
            if not gp.users:
                gp.name = "tmp-orphan-pose"

                # Can't remove from here because when undo, then draw again, it crashes
                # bpy.data.grease_pencils.remove(gp)
        else:
            gp.layers.remove(gp.layers[-1])
            gp.layers.active = self.active_gp_layer

        return

    def cancel(self, context):
        self.remove_annotation(context)
        return {'PASS_THROUGH', 'CANCELLED'}

    def update_pose(self, context):
        # for region in context.area.regions:
            # if region.type == 'WINDOW':
                # break
        # else:
            # return self.cancel(context)
        region = context.region
        rv3d = context.space_data.region_3d

        gp = context.annotation_data

        stroke = gp.layers.active.frames[0].strokes[0]

        for chain in Get.sorted_chains(context.selected_pose_bones):
            bone_chain = list()

            for bone in reversed(chain):
                bone_chain.insert(0, bone)
                if bone == chain[0]:
                    # Do location
                    pass
                    # continue  # or break; should do the same
                else:
                    pass

                    while bone.parent not in chain:
                        # Do unselected in betweens
                        bone = bone.parent
                        if not Is.visible(context, bone):
                            # Don't rotate hidden bones
                            continue

                        bone_chain.insert(0, bone)

            bcount = len(bone_chain) - 1
            gcount = len(stroke.points) - 1

            # if bcount:
                # while gcount > bcount * 3:
                    # # Split point count in half
                    # index = 0
                    # while index < len(stroke.points) - 1:
                    #     stroke.points.pop(index=index + 1)
                    #     index += 1
                    # print(bcount, gcount, '\t', index, len(stroke.points))

                    # gcount = len(stroke.points) - 1

            bone_mats = list()
            con_tmp = list()

            index = 0
            for bone in bone_chain:
                if index > bcount:
                    index = bcount

                point_index = utils.scale_range(index, 0, bcount, 0, gcount)
                point = stroke.points[int(point_index)]


                if index == 0:
                    if not(bone.parent):
                        bone = bone_chain[0]
                        point = stroke.points[0]

                        to_2d = location_3d_to_region_2d(region, rv3d, point.co)  # get 2d space of stroke
                        if to_2d:
                            to_3d = region_2d_to_location_3d(region, rv3d, to_2d, bone.head)  # keep depth of bone

                            empty = New.object(context, bone.name)
                            empty.empty_display_size = 0.25
                            empty.location = to_3d

                            con = bone.constraints.new('COPY_LOCATION')
                            con.target = empty
                            con_tmp.append((bone, con, empty))

                    if bcount == 0:
                        point = stroke.points[-1]
                    else:
                        # index += 1
                        point_index = utils.scale_range(0.5, 0, bcount, 0, gcount)
                        point = stroke.points[int(point_index)]

                to_2d = location_3d_to_region_2d(region, rv3d, point.co)  # get 2d space of stroke
                if to_2d:
                    to_3d = region_2d_to_location_3d(region, rv3d, to_2d, bone.tail)  # keep depth of bone

                    empty = New.object(context, bone.name)
                    empty.empty_display_size = 0.1
                    empty.location = to_3d

                    con = bone.constraints.new('DAMPED_TRACK')
                    con.target = empty
                    con_tmp.append((bone, con, empty))

                index += 1

            utils.update(context)
            for (bone, con, empty) in reversed(con_tmp):
                mat = Get.matrix_constraints(context, bone)
                # mat = Get.matrix(bone)
                bone_mats.append((bone, mat))

                bone.constraints.remove(con)
                Get.objects(context, link=True).unlink(empty)

            for (bone, mat) in bone_mats:
                Set.matrix(bone, mat)
                keyframe.keyingset(context, selected=[bone], skip_bones=True)

        self.remove_annotation(context)

        return {'FINISHED'}


def register():
    km.add(POSE_OT_annotate_view, name='Pose', type='LEFTMOUSE', value='PRESS', key_modifier='V')


def unregister():
    km.remove()
