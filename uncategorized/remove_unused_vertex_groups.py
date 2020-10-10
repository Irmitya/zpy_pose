import bpy
# Addon by CodemanX  https://blenderartists.org/t/batch-delete-vertex-groups-script/449881/3
# (probably) their actual code differs a lot from mine, so not sure if editted their code, or just coincidence


class VGROUP_OT_remove_unused(bpy.types.Operator):
    bl_description = "Remove unused vertex groups from the active mesh"
    bl_idname = 'mesh.remove_unused_vertex_groups'
    bl_label = "Remove Unused Vertex Groups"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @classmethod
    def poll(cls, context):
        return True

    def __init__(self):
        self.selected = list()

    def invoke(self, context, event):
        if event.alt:
            self.selected = [*{context.object, *context.selected_objects}]
        return self.execute(context)

    def execute(self, context):
        if not self.selected:
            self.selected = [context.object]

        for ob in self.selected:
            if not getattr(ob, 'type', None) == 'MESH':
                continue
            used_groups = set()

            # Used groups from weight paint
            for (id, vert) in enumerate(ob.data.vertices):
                for vg in vert.groups:
                    vgi = vg.group
                    used_groups.add(vgi)

            # Used groups from modifiers
            for mod in ob.modifiers:
                vg = getattr(mod, 'vertex_group', None)
                if vg:
                    vgi = ob.vertex_groups[vg].index
                    used_groups.add(vgi)

            # Used groups from shape keys
            if ob.data.shape_keys:
                for key in ob.data.shape_keys.key_blocks:
                    if key.vertex_group:
                        vg = ob.vertex_groups.get(key.vertex_group)
                        if vg:
                            used_groups.add(vg.index)

            # No search for constraints
            """
            Could do one for the object, and maybe all it's bones
            But that would still disregard every other object
            """

            for vg in list(reversed(ob.vertex_groups)):
                if vg.index not in used_groups:
                    ob.vertex_groups.remove(vg)

        return {'FINISHED'}


def draw_menu(self, context):
    layout = self.layout
    layout.operator('mesh.remove_unused_vertex_groups', icon='CANCEL')


def register():
    bpy.types.MESH_MT_vertex_group_context_menu.append(draw_menu)


def unregister():
    bpy.types.MESH_MT_vertex_group_context_menu.remove(draw_menu)
