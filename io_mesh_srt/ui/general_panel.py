# -*- coding: utf-8 -*-
# ui/general_panel.py

import bpy
import re
from bpy.props import BoolProperty, EnumProperty, StringProperty, IntProperty, CollectionProperty
from io_mesh_srt.utils import GetCollection

class UserStringsListActions(bpy.types.Operator):
    """Move user strings up and down, add and remove"""
    bl_idname = "speed_tree.user_strings_list_action"
    bl_label = "List Actions"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}

    action: EnumProperty(
        options={'HIDDEN'},
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))
            
    user_string: EnumProperty(
        options={'HIDDEN'},
        default='BillboardRandomBranch',
        items=(
            ('BillboardRandomBranch', "BillboardRandomBranch", ""),
            ('BillboardRandomGrass', "BillboardRandomGrass", ""),
            ('BillboardRandomOff', "BillboardRandomOff", ""),
            ('BillboardRandomTrees', "BillboardRandomTrees", ""),
            ('EnvMaterialSettingsOff', "EnvMaterialSettingsOff", ""),
            ('InteractiveOn', "InteractiveOn", ""),
            ('PigmentFloodOff', "PigmentFloodOff", ""),
            ('RandomOff', "RandomOff", ""),
            ('TerrainNormalsOn', "TerrainNormalsOn", ""),
            ('Custom', "Custom String", "")))
            
    text: StringProperty(name = "Enter String", default = "")

    def execute(self, context):
        main_coll = GetCollection(make_active=False)
        wm = context.window_manager.speedtree
        idx = wm.PUserStringsIndex
        strings = main_coll["PUserStrings"]
        if not strings:
            strings = []

        try:
            item = strings[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(strings) - 1:
                item_next = strings[idx+1]
                strings[idx] = item_next
                strings[idx+1] = item
                wm.PUserStringsIndex += 1

            elif self.action == 'UP' and idx >= 1:
                item_prev = strings[idx-1]
                strings[idx] = item_prev
                strings[idx-1] = item
                wm.PUserStringsIndex -= 1

            elif self.action == 'REMOVE':
                if idx == len(strings) - 1:
                    wm.PUserStringsIndex -= 1
                strings.pop(idx)

        if self.action == 'ADD':
            if self.user_string != 'Custom':
                t = self.user_string
            else:
                t = self.text
            strings.append(t)
            wm.PUserStringsIndex = len(strings)-1
            
        main_coll["PUserStrings"] = strings
        self.user_string = 'BillboardRandomBranch'
            
        return {'FINISHED'}
    
    def invoke(self, context, event):
        if self.user_string != 'Custom':
            return self.execute(context)
        else:
            return bpy.context.window_manager.invoke_props_dialog(self)

def updatePUserString(self, context):
    wm = context.window_manager.speedtree
    main_coll = GetCollection(make_active=False) 
    if main_coll:
        strings = main_coll["PUserStrings"]
        strings[self.index] = self.name
        main_coll["PUserStrings"] = strings

class SPEEDTREE_PROP_UserStrings(bpy.types.PropertyGroup):
    name: StringProperty()
    index: IntProperty()

class SPEEDTREE_UL_UserStrings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "name", text="", emboss=False, icon="NONE")
        
class SpeedTreeGeneralSettings(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_settings_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree General Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
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
                box_row.label(text="User Strings")
                box_row = box.row()
                box_row.template_list("SPEEDTREE_UL_UserStrings", "", wm, "PUserStrings", wm, "PUserStringsIndex", rows=4)
                check = False
                length_wm_strings = len(wm.PUserStrings)
                length_coll_strings = len(main_coll["PUserStrings"])
                if length_wm_strings == length_coll_strings:
                    for i, string in enumerate(wm.PUserStrings):
                        if string.name != main_coll["PUserStrings"][i]:
                            check = True
                            break
                if length_wm_strings != length_coll_strings or check:
                    for i in reversed(range(length_wm_strings)):
                        wm.PUserStrings.remove(i)
                    for i, string in enumerate(main_coll["PUserStrings"]):
                        wm.PUserStrings.add()
                        wm.PUserStrings[-1].name = string
                        wm.PUserStrings[-1].index = i
                        
                col = box_row.column(align=True)
                col.operator_menu_enum(UserStringsListActions.bl_idname, property = "user_string", icon='ADD', text="").action = 'ADD'
                col.operator(UserStringsListActions.bl_idname, icon='REMOVE', text="").action = 'REMOVE'
                col.separator()
                col.operator(UserStringsListActions.bl_idname, icon='TRIA_UP', text="").action = 'UP'
                col.operator(UserStringsListActions.bl_idname, icon='TRIA_DOWN', text="").action = 'DOWN'
                
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
("PUserStringsIndex", IntProperty(
        name = "Index of the active user string",
        default = 0
    )),
("PUserStrings", CollectionProperty(
        type = SPEEDTREE_PROP_UserStrings
    )),
("ELightingModel", EnumProperty(
        name="Lighting Model",
        update = updateELightingModel,
        description="Set the lighting model to use with the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('DEFERRED', 'DEFERRED', "Set the lighting model deferred"),
            ('PER_VERTEX', "PER_VERTEX", "Set the lighting model per vertex"),
            ('PER_PIXEL', "PER_PIXEL", "Set the lighting model per pixel"))
    )),
("ELodMethod", EnumProperty(
        name="Lod Method",
        update = updateELodMethod,
        description="Set the lod transition method of the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('SMOOTH', "SMOOTH", "Enable smooth lod transition"),
            ('POP', "POP", "Enable immediate lod transition"))
    )),
("EShaderGenerationMode", EnumProperty(
        name="Shader Generation Mode",
        update = updateEShaderGenerationMode,
        description="Set the shader generation mode",
        items=(
            ('UNIFIED_SHADERS', "UNIFIED_SHADERS", "Set the shader generation mode to REDengine"),
            ('STANDARD', "STANDARD", "Set the shader generation mode to Standard"),
            ('UNREAL4', "UNREAL4", "Set the shader generation mode to Unreal Engine 4 !!! NOT SUPPORTED IN BLENDER !!!"))
    )),
("BUsedAsGrass", BoolProperty(
        name="Used as Grass",
        update = updateBUsedAsGrass,
        description="Set the mesh as grass. Requires no billboard, a single LOD and a single material"
    ))
]

CLASSES_General_Panel = [UserStringsListActions, SPEEDTREE_PROP_UserStrings, SPEEDTREE_UL_UserStrings, SpeedTreeGeneralSettings]