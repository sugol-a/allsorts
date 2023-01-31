import math

import bpy
import blf
import mathutils
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import Menu
from bpy_extras import view3d_utils

keymaps = []

def axis_name(axis):
    if axis[0]:
        return "X"
    elif axis[1]:
        return "Y"
    elif axis[2]:
        return "Z"
    else:
        return None

class QuickMirrorOperator(bpy.types.Operator):
    bl_idname = "allsorts.quick_mirror"
    bl_label = "Quick mirror"
    bl_description = "Quickly mirrors the active mesh"
    bl_options = {'REGISTER',}
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.cleanup_handlers()
            context.active_object.modifiers.remove(self.mirror_mod)
            return {'CANCELLED'}
        elif event.type in {"LEFTMOUSE", "ENTER"}:
            self.cleanup_handlers()
            return {'FINISHED'}
        elif event.type == "A":
            self.cleanup_handlers()
            bpy.ops.object.modifier_apply(modifier=self.mirror_mod.name)
            return {'FINISHED'}
        
        if event.type == "MOUSEMOVE":
            self.mouse_pos = [event.mouse_region_x, event.mouse_region_y]
            
            obj = context.active_object
            region = context.region
            region3d = context.space_data.region_3d
            
            view = view3d_utils.region_2d_to_vector_3d(region, region3d, self.mouse_pos)
            location_3d = view3d_utils.region_2d_to_location_3d(region, region3d, self.mouse_pos, view)
            
            # Convert to object-local coords
            location_3d = (obj.matrix_world.inverted() @ location_3d).normalized()
            
            # Find the most closely-aligned axis to the mouse world position
            align = [
              (mathutils.Vector((1, 0, 0)).dot(location_3d), [True, False, False]),
              (mathutils.Vector((0, 1, 0)).dot(location_3d), [False, True, False]),
              (mathutils.Vector((0, 0, 1)).dot(location_3d), [False, False, True])
            ]
            
            dot, axis = sorted(align, key=lambda x: math.fabs(x[0]), reverse=True)[0]

            self.axis_name = axis_name(axis)
            self.mirror_mod.use_axis = axis
        elif event.type == "WHEELUPMOUSE":
            bpy.ops.object.modifier_move_up(modifier=self.mirror_mod.name)
        elif event.type == "WHEELDOWNMOUSE":
            bpy.ops.object.modifier_move_down(modifier=self.mirror_mod.name)
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if context.area.type == "VIEW_3D" and context.active_object.type == "MESH":
            args = (context,)
            self._draw_info_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_info, args, "WINDOW", "POST_PIXEL")
            self._draw_plane_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_plane, args, 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)

            self.axis_name = None
            self.mirror_mod = context.active_object.modifiers.get("Allsorts.QuickMirror")
            
            if not self.mirror_mod:
                self.mirror_mod = context.active_object.modifiers.new(name="Allsorts.QuickMirror", type="MIRROR")

            self.mirror_mod.use_axis = [False, False, False]

            # Set up shit for the plane indicator            
            coords = ((-2, -2, 0), (+2, -2, 0),
                      (-2, +2, 0), (+2, +2, 0))

            indices = ((0, 1, 2), (1, 2, 3))
            
            self.plane_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            self.plane_batch = batch_for_shader(self.plane_shader, 'TRIS', {"pos": coords}, indices=indices)
            
            return {'RUNNING_MODAL'}
        else:
            return {'FINISHED'}

    def draw_info(self, context):
        blf.color(0, 1.0, 1.0, 1.0, 1.0)
        blf.shadow(0, 5, 0, 0, 0, 1)
        blf.position(0, self.mouse_pos[0] + 16, self.mouse_pos[1] + 16, 0)
        blf.size(0, 16, 72)
        blf.draw(0, "Quick mirror")

        blf.color(0, 1.0, 1.0, 1.0, 1.0)
        blf.shadow(0, 5, 0, 0, 0, 1)
        blf.size(0, 12, 72)
        blf.position(0, self.mouse_pos[0] + 16, self.mouse_pos[1] + 36, 0)
        blf.draw(0, f"Axis: {self.axis_name}")
        
        blf.color(0, 1, 1, 1, 1)
        blf.shadow(0, 5, 0, 0, 0, 1)
        blf.size(0, 12, 72)
        blf.position(0, self.mouse_pos[0] + 16, self.mouse_pos[1] + 52, 0)
        blf.draw(0, f"[C]lip: {self.clip}")
        
    def draw_plane(self, context):
        self.plane_shader.bind()
        self.plane_shader.uniform_float("color", (0.2, 0.5, 0.8, 0.25))
        
        # Face the plane in the correct direction
        gpu.matrix.push()

        rotation = mathutils.Matrix.Identity(4)
        if self.axis_name == "X":
            rotation = mathutils.Matrix.Rotation(math.radians(90), 4, "Y")
        elif self.axis_name == "Y":
            rotation = mathutils.Matrix.Rotation(math.radians(90), 4, "X")

        gpu.matrix.multiply_matrix(context.object.matrix_basis)
        gpu.matrix.multiply_matrix(rotation)
        
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.depth_mask_set(True)
        gpu.state.blend_set("ALPHA")
        self.plane_batch.draw(self.plane_shader)
        gpu.state.depth_mask_set(False)
        gpu.state.blend_set("NONE")
        
        gpu.matrix.pop()
        
    def cleanup_handlers(self):
        bpy.types.SpaceView3D.draw_handler_remove(self._draw_info_handler, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(self._draw_plane_handler, "WINDOW")
        
def menu(self, context):
    self.layout.operator(ModalDrawOperator.bl_idname, text="Quick Mirror")

def add_hotkey():
    wm = bpy.context.window_manager
    keyconf = wm.keyconfigs.addon

    km = keyconf.keymaps.new(name="Object Mode", space_type="EMPTY")
    km_item = km.keymap_items.new(
        DisplayAsPieMenuOperator.bl_idname,
        "Q", "PRESS", ctrl=False, shift=False, alt=True)

def remove_hotkey():
    for km, km_item in keymaps:
        km.keymap_items.remove(km_item)

    keymaps.clear()

def register():
    bpy.utils.register_class(QuickMirrorOperator)
    bpy.types.VIEW3D_MT_view.append(menu)
    
def unregister():
    bpy.utils.unregister_class(QuickMirrorOperator)
    bpy.types.VIEW3D_MT_view.append(menu)
