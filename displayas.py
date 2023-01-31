import bpy
from bpy.types import Menu

keymaps = []

class DisplayAsPieMenu(Menu):
    bl_label = "Display As"
    
    def draw(self, context):
        layout = self.layout
        prefs = context.preferences
        inputs = prefs.inputs
        
        pie = layout.menu_pie()
        pie.prop(context.active_object, "display_type", expand=True)
        
class DisplayAsPieMenuOperator(bpy.types.Operator):
    bl_idname = "allsorts.displayas_menu"
    bl_label = "Display As"
    bl_description = "Summons 'Display As' pie menu"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="DisplayAsPieMenu")
        return {'FINISHED'}

def add_hotkey():
    wm = bpy.context.window_manager
    keyconf = wm.keyconfigs.addon
    
    km = keyconf.keymaps.new(name="Object Mode", space_type="EMPTY")
    km_item = km.keymap_items.new(
        DisplayAsPieMenuOperator.bl_idname,
        "A", "PRESS", ctrl=False, shift=True, alt=True)
    
def remove_hotkey():
    for km, km_item in keymaps:
        km.keymap_items.remove(km_item)
    
    keymaps.clear()

def register():
    bpy.utils.register_class(DisplayAsPieMenu)
    bpy.utils.register_class(DisplayAsPieMenuOperator)
    add_hotkey()

def unregister():
    bpy.utils.unregister_class(DisplayAsPieMenu)
    bpy.utils.unregister_class(DisplayAsPieMenuOperator)
    remove_hotkey()
