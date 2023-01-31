from . import quickmirror
from . import displayas

bl_info = {
    "name": "Allsorts",
    "author": "Alister Sanders <alister@sugol.org>",
    "version": (0, 0, 0, 1),
    "description": "Assortment of utilities",
    "blender": (3, 3, 0),
}

mods = [quickmirror, displayas]

def register():
    for mod in mods:
        mod.register()

def unregister():
    for mod in mods:
        mod.unregister()

if __name__ == "__main__":
    register()
