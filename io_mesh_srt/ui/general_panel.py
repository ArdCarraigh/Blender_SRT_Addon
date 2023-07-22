# -*- coding: utf-8 -*-
# ui/general_panel.py

import bpy
import re
from bpy.props import BoolProperty, EnumProperty
from io_mesh_srt.utils import GetCollection
        
class SpeedTreeGeneralSettings(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_settings_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree General Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'general':
            
            layout = self.layout
            main_coll = GetCollection(make_active=False)
            if main_coll:
                bb_coll = None
                horiz_coll = None
                nLod = 0
                nMat = 0
                for col in main_coll.children:
                    if re.search("Vertical Billboards", col.name):
                        bb_coll = col
                    if re.search("Horizontal Billboard", col.name):
                        horiz_coll = col
                    if re.search("LOD", col.name):
                        nLod += 1
                        if 'LOD0' in col.name:
                            for obj in col.objects:
                                for mat in obj.data.materials:
                                    nMat += 1
                        
                row = layout.row()
                box = row.box()
                box_row = box.row()
                box_row.label(text="User Settings")
                box_row = box.row()
                box_row.prop(wm, "EBillboardRandomType", text = '')
                if wm.EBillboardRandomType != main_coll["EBillboardRandomType"]:
                    wm.EBillboardRandomType = main_coll["EBillboardRandomType"]
                if not bb_coll and not horiz_coll:
                    wm.EBillboardRandomType = 'NoBillboard'
                box_row.enabled = not not bb_coll or not not horiz_coll
                
                box_row = box.row()
                box_row.prop(wm, 'ETerrainNormals', text = '')
                if wm.ETerrainNormals != main_coll["ETerrainNormals"]:
                    wm.ETerrainNormals = main_coll["ETerrainNormals"]
                
                row = layout.row()
                box = row.box()
                box_row = box.row()
                box_row.label(text="Shader Settings")
                box_row = box.row()
                box_row.prop(wm, "ELightingModel", text = '')
                if wm.ELightingModel != main_coll["ELightingModel"]:
                    wm.ELightingModel = main_coll["ELightingModel"]
                    
                box_row = box.row()
                box_row.prop(wm, "ELodMethod", text = '')
                if wm.ELodMethod != main_coll["ELodMethod"]:
                    wm.ELodMethod = main_coll["ELodMethod"]
                    
                box_row = box.row()
                box_row.prop(wm, "EShaderGenerationMode", text = '')
                if wm.EShaderGenerationMode != main_coll["EShaderGenerationMode"]:
                    wm.EShaderGenerationMode = main_coll["EShaderGenerationMode"]
                
                box_row = box.row()
                box_row.prop(wm, "BUsedAsGrass", text = "Used As Grass")
                if wm.BUsedAsGrass != main_coll["BUsedAsGrass"]:
                    wm.BUsedAsGrass = main_coll["BUsedAsGrass"]
                if bb_coll or horiz_coll or nLod != 1 or nMat != 1:
                    wm.BUsedAsGrass = False
                box_row.enabled = not bb_coll and not horiz_coll and nLod == 1 and nMat == 1
                
        return

def updateEBillboardRandomType(self, context):
    main_coll = GetCollection(make_active=False)
    if main_coll:
        main_coll["EBillboardRandomType"] = self.EBillboardRandomType
        
def updateETerrainNormals(self, context):
    main_coll = GetCollection(make_active=False) 
    if main_coll:
        main_coll["ETerrainNormals"] = self.ETerrainNormals
        
def updateELightingModel(self, context):
    main_coll = GetCollection(make_active=False) 
    if main_coll:
        main_coll["ELightingModel"] = self.ELightingModel
        
def updateELodMethod(self, context):
    main_coll = GetCollection(make_active=False) 
    if main_coll:
        main_coll["ELodMethod"] = self.ELodMethod
            
def updateEShaderGenerationMode(self, context):
    main_coll = GetCollection(make_active=False)  
    if main_coll:
        main_coll["EShaderGenerationMode"] = self.EShaderGenerationMode
            
def updateBUsedAsGrass(self, context):
    main_coll = GetCollection(make_active=False)   
    if main_coll:
        main_coll["BUsedAsGrass"] = self.BUsedAsGrass
     
PROPS_General_Panel = [
('EBillboardRandomType', EnumProperty(
        name="Billboard Randomisation",
        description="Set the billboard randomisation method",
        update = updateEBillboardRandomType,
        items=(
            ('BillboardRandomOff', "BillboardRandomOff", "Disable billboard randomisation"),
            ('BillboardRandomTrees', "BillboardRandomTrees", "Randomise tree billboards??"),
            ('BillboardRandomBranch', "BillboardRandomBranch", "Randomise branch billboards??"),
            ('NoBillboard', "NoBillboard", "NoBillboard") 
        ),
        default='NoBillboard'
    )),
('ETerrainNormals', EnumProperty(
        name="Terrain Normals",
        description="Enable terrain normals",
        update = updateETerrainNormals,
        items=(
            ('TerrainNormalsOn', "TerrainNormalsOn", "Enable terrain normals"),
            ('TerrainNormalsOff', "TerrainNormalsOff", "Disable terrain normals")
        ),
        default='TerrainNormalsOff'
    )),
("ELightingModel", EnumProperty(
        name="Lighting Model",
        update = updateELightingModel,
        description="Set the lighting model to use with the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('LIGHTING_MODEL_DEFERRED', 'LIGHTING_MODEL_DEFERRED', "Set the lighting model deferred"),
            ('LIGHTING_MODEL_PER_VERTEX', "LIGHTING_MODEL_PER_VERTEX", "Set the lighting model per vertex"),
            ('LIGHTING_MODEL_PER_PIXEL', "LIGHTING_MODEL_PER_PIXEL", "Set the lighting model per pixel"))
    )),
("ELodMethod", EnumProperty(
        name="Lod Method",
        update = updateELodMethod,
        description="Set the lod transition method of the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('LOD_METHOD_SMOOTH', "LOD_METHOD_SMOOTH", "Enable smooth lod transition"),
            ('LOD_METHOD_POP', "LOD_METHOD_POP", "Enable immediate lod transition"))
    )),
("EShaderGenerationMode", EnumProperty(
        name="Shader Generation Mode",
        update = updateEShaderGenerationMode,
        description="Set the shader generation mode",
        items=(
            ('SHADER_GEN_MODE_UNIFIED_SHADERS', "SHADER_GEN_MODE_UNIFIED_SHADERS", "Set the shader generation mode to REDengine"),
            ('SHADER_GEN_MODE_STANDARD', "SHADER_GEN_MODE_STANDARD", "Set the shader generation mode to Standard"),
            ('SHADER_GEN_MODE_UNREAL_ENGINE_4', "SHADER_GEN_MODE_UNREAL_ENGINE_4", "Set the shader generation mode to Unreal Engine 4 !!! NOT SUPPORTED IN BLENDER !!!"))
    )),
("BUsedAsGrass", BoolProperty(
        name="Used as Grass",
        update = updateBUsedAsGrass,
        description="Set the mesh as grass. Require no billboard, a single LOD and a single material"
    ))
]

CLASSES_General_Panel = [SpeedTreeGeneralSettings]