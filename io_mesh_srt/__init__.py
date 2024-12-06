# -*- coding: utf-8 -*-
# __init__.py

bl_info = {
    "name": "SRT Importer/Exporter (.srt/.json)",
    "author": "Ard Carraigh",
    "version": (4, 1),
    "blender": (4, 3, 0),
    "location": "File > Import-Export",
    "description": "Import and export .srt and .json SpeedTree meshes",
    "doc_url": "https://github.com/ArdCarraigh/Blender_SRT_Addon",
    "tracker_url": "https://github.com/ArdCarraigh/Blender_SRT_Addon/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, IntProperty, PointerProperty
from bpy.types import Operator, PropertyGroup
from io_mesh_srt.import_srt_json import read_srt_json
from io_mesh_srt.export_srt_json import write_srt_json 
from io_mesh_srt.ui.main_panel import CLASSES_Main_Panel, PROPS_Main_Panel
from io_mesh_srt.ui.general_panel import CLASSES_General_Panel, PROPS_General_Panel
from io_mesh_srt.ui.lod_panel import CLASSES_Lod_Panel, PROPS_Lod_Panel
from io_mesh_srt.ui.vertex_panel import CLASSES_Vertex_Panel, PROPS_Vertex_Panel
from io_mesh_srt.ui.collision_panel import CLASSES_Collision_Panel, PROPS_Collision_Panel
from io_mesh_srt.ui.billboard_panel import CLASSES_Billboard_Panel, PROPS_Billboard_Panel
from io_mesh_srt.ui.material_panel import CLASSES_Material_Panel, PROPS_Material_Panel

class ImportSrtJson(Operator, ImportHelper):
    """Load a SRT file"""
    bl_idname = "import.srt_json"
    bl_label = "Import SRT"

    # ImportHelper mixin class uses this
    filename_ext = ".srt"

    filter_glob: StringProperty(
        default="*.json;*.srt",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
                
    def execute(self, context):
        
        # Should work from all modes
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        
        read_srt_json(context, self.filepath)
        
        return {'FINISHED'}
    
class ExportSrtJson(Operator, ExportHelper):
    """Write a SRT file"""
    bl_idname = "export.srt_json"
    bl_label = "Export SRT"

    # ExportHelper mixin class uses this
    filename_ext = ".srt"

    filter_glob: StringProperty(
        default="*.srt",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    def execute(self, context):
        
        # Should work from all modes
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        
        write_srt_json(context, self.filepath)
        
        return {'FINISHED'}
    
class SpeedTreeProperties(PropertyGroup):
    placeholder: IntProperty(name="Placeholder")
    
PROPS = [*PROPS_Main_Panel, *PROPS_General_Panel, *PROPS_Lod_Panel, *PROPS_Vertex_Panel, *PROPS_Collision_Panel, *PROPS_Billboard_Panel, *PROPS_Material_Panel]
CLASSES = [ImportSrtJson, ExportSrtJson, SpeedTreeProperties, *CLASSES_Main_Panel, *CLASSES_General_Panel, *CLASSES_Lod_Panel, *CLASSES_Vertex_Panel, *CLASSES_Collision_Panel, *CLASSES_Billboard_Panel, *CLASSES_Material_Panel]
    
# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSrtJson.bl_idname, text="SRT (.srt/.json)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportSrtJson.bl_idname, text="SRT (.srt)")

def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    for klass in CLASSES:
        bpy.utils.register_class(klass)
        
    setattr(bpy.types.WindowManager, "speedtree", SpeedTreeProperties)
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.WindowManager.speedtree, prop_name, prop_value)
    bpy.types.WindowManager.speedtree = PointerProperty(type=SpeedTreeProperties)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    for klass in CLASSES:
        bpy.utils.unregister_class(klass)

    delattr(bpy.types.WindowManager, "speedtree")