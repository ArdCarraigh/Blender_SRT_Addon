# -*- coding: utf-8 -*-
# __init__.py

bl_info = {
    "name": "SRT JSON Importer/Exporter (.json)",
    "author": "Ard Carraigh",
    "version": (1, 0),
    "blender": (2, 92, 0),
    "location": "File > Import-Export",
    "description": "Import and export srt .json dump meshes",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty
from bpy.types import Operator
from io_scene_srt_json import import_srt_json
from io_scene_srt_json.import_srt_json import read_srt_json
from io_scene_srt_json import export_srt_json
from io_scene_srt_json.export_srt_json import write_srt_json

class ImportSrtJson(Operator, ImportHelper):
    """Load a SRT JSON dump file"""
    bl_idname = "import.srt_json"  # important since its how bpy.ops.import.apx is constructed
    bl_label = "Import SRT JSON"

    # ImportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
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
        
        my_areas = bpy.context.workspace.screens[0].areas
        my_shading = 'MATERIAL'  # 'WIREFRAME' 'SOLID' 'MATERIAL' 'RENDERED'
        for area in my_areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = my_shading
        
        return {'FINISHED'}
    
class ExportSrtJson(Operator, ExportHelper):
    """Write a SRT JSON dump file"""
    bl_idname = "export.srt_json"  # important since its how bpy.ops.export.apx is constructed
    bl_label = "Export Srt JSON"

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    randomType: EnumProperty(
        name="Billboard Randomisation",
        description="Choose a billboard randomisation method",
        items=(
            ('BillboardRandomOff', "Random Off", "Disable billboard randomisation"),
            ('BillboardRandomTrees', "Random Trees", "Randomise tree billboard"),
            ('OFF', "No billboard", "Disable billboard entirely") 
        ),
        default='BillboardRandomOff',
    )
    
    terrainNormals: BoolProperty(
        name="Terrain Normals",
        description="Enable terrain normals",
        default=False
    )
    
    lodDist_Range3D: FloatProperty(
        name="3D Range",
        description="Set the distance from which meshes enabled",
        default = 0,
        min = 1,
        max = 200
    )
    
    lodDist_HighDetail3D: FloatProperty(
        name="High Detail 3D Distance",
        description="Set the distance at which lod0 is no longer used",
        default = 10,
        min = 1,
        max = 200
    )
    
    lodDist_LowDetail3D: FloatProperty(
        name="Low Detail 3D Distance",
        description="Set the distance at which lod2 gets used",
        default = 30,
        min = 1,
        max = 200
    )
    
    lodDist_RangeBillboard: FloatProperty(
        name="Billboard Range",
        description="Set the distance from which billboard is enabled",
        default = 0,
        min = 1,
        max = 200
    )
    
    lodDist_StartBillboard: FloatProperty(
        name="Billboard Start Distance",
        description="Set the distance at which billboard starts to get used",
        default = 80,
        min = 1,
        max = 200
    )
    
    lodDist_EndBillboard: FloatProperty(
        name="Billboard End Distance",
        description="Set the distance at which billboard disappears",
        default = 90,
        min = 1,
        max = 200
    )
    grass: BoolProperty(
        name="Used as grass",
        description="Check to define the exported asset as grass",
        default=False
    )
    
    def draw(self, context):
        layout = self.layout

        sections = ["User Options", "Level Of Detail"]

        section_options = {
            "User Options": ["randomType", "terrainNormals", "grass"],
            "Level Of Detail": ["lodDist_Range3D", "lodDist_HighDetail3D", "lodDist_LowDetail3D",
             "lodDist_RangeBillboard", "lodDist_StartBillboard", "lodDist_EndBillboard"]
        }

        section_icons = {
            "User Options": "WORLD", "Level Of Detail": "WORLD"
        }

        for section in sections:
            row = layout.row()
            box = row.box()
            box.label(text=section, icon=section_icons[section])
            for prop in section_options[section]:
                box.prop(self, prop)

    def execute(self, context):
        
        # Should work from all modes
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        
        write_srt_json(context, self.filepath, self.randomType, self.terrainNormals, self.lodDist_Range3D,
        self.lodDist_HighDetail3D, self.lodDist_LowDetail3D, self.lodDist_RangeBillboard,
        self.lodDist_StartBillboard, self.lodDist_EndBillboard, self.grass)
        
        return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSrtJson.bl_idname, text="SRT JSON (.json)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportSrtJson.bl_idname, text="SRT JSON (.json)")

def register():
    bpy.utils.register_class(ImportSrtJson)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ExportSrtJson)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ImportSrtJson)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(exportSrtJson)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
    
    # test call
    bpy.ops.export.srt_json('INVOKE_DEFAULT')
