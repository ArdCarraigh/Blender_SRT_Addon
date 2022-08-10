# -*- coding: utf-8 -*-
# __init__.py

bl_info = {
    "name": "SRT JSON Importer/Exporter (.json)",
    "author": "Ard Carraigh",
    "version": (1, 0),
    "blender": (2, 92, 0),
    "location": "File > Import-Export",
    "description": "Import and export srt .json dump meshes",
    "wiki_url": "https://github.com/ArdCarraigh/Blender_SRT_JSON_Addon",
    "tracker_url": "https://github.com/ArdCarraigh/Blender_SRT_JSON_Addon/issues",
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
from io_scene_srt_json.tools import add_srt_sphere
from io_scene_srt_json.tools.add_srt_sphere import add_srt_sphere
from io_scene_srt_json.tools import add_srt_connection
from io_scene_srt_json.tools.add_srt_connection import add_srt_connection

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
    
class AddSRTCollisionSphere(Operator, AddObjectHelper):
    """Create a new Collision Sphere"""
    bl_idname = "speed_tree.add_srt_collision_sphere"
    bl_label = "Add Collision Sphere"
    bl_options = {'REGISTER', 'UNDO'}

    radius: FloatProperty(
        name="Radius",
        default = 0.15,
        description="Set the radius of the sphere",
    )
    location: FloatVectorProperty(
        name="Location",
        default=(0.0, 0.0, 0.0),
        description="Set the location of the sphere",
    )

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        add_srt_sphere(context, self.radius, self.location)
        return {'FINISHED'}
    
class AddSRTSphereConnection(Operator):
    """Create a new Connection"""
    bl_idname = "speed_tree.add_srt_sphere_connection"
    bl_label = "Add Sphere Connection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        add_srt_connection(context)
        return {'FINISHED'}
    
class SpeedTreeMenu(bpy.types.Menu):
    bl_label = "SpeedTree"
    bl_idname = "VIEW3D_MT_object_SpeedTree_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator(AddSRTCollisionSphere.bl_idname, text = "Add Collision Sphere", icon='MESH_UVSPHERE')
        layout.operator(AddSRTSphereConnection.bl_idname, text = "Add Sphere Connection", icon='MESH_CAPSULE')

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSrtJson.bl_idname, text="SRT JSON (.json)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportSrtJson.bl_idname, text="SRT JSON (.json)")
    
def draw_item(self, context):
    layout = self.layout
    layout.separator()
    layout.menu(SpeedTreeMenu.bl_idname)

def register():
    bpy.utils.register_class(ImportSrtJson)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.utils.register_class(ExportSrtJson)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    bpy.utils.register_class(AddSRTCollisionSphere)
    bpy.utils.register_class(AddSRTSphereConnection)
    
    bpy.utils.register_class(SpeedTreeMenu)
    bpy.types.VIEW3D_MT_object.append(draw_item)

def unregister():
    bpy.utils.unregister_class(ImportSrtJson)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(exportSrtJson)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    bpy.utils.unregister_class(AddSRTCollisionSphere)
    bpy.utils.unregister_class(AddSRTSphereConnection)
    
    bpy.utils.unregister_class(SpeedTreeMenu)
    bpy.types.VIEW3D_MT_object.remove(draw_item)

if __name__ == "__main__":
    register()
    
    # test call
    bpy.ops.export.srt_json('INVOKE_DEFAULT')
