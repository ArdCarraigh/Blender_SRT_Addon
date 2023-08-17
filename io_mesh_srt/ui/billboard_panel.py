# -*- coding: utf-8 -*-
# ui/billboard_panel.py

import bpy
import numpy as np
import re
from math import radians
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty, StringProperty
from io_mesh_srt.utils import GetCollection, selectOnly
from io_mesh_srt.tools.billboard_tools import generate_srt_billboards, generate_srt_horizontal_billboard, generate_srt_billboard_texture
if 'blender_dds_addon' in bpy.context.preferences.addons:
    from blender_dds_addon.ui.custom_properties import DDS_FMT_ITEMS

class SRTBillboardTextureGeneration(Operator):
    """Generate a Billboard Texture"""
    bl_idname = "speed_tree.srt_billboard_texture_generation"
    bl_label = "Generate a Billboard Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        dds_dxgi = None
        if wm.EBillboardTextureFormat == 'DDS':
            dds_dxgi = wm.EDxgiFormat
        generate_srt_billboard_texture(context, wm.IBillboardTextureResolution, wm.IBillboardTextureMargin, wm.IBillboardTextureDilation, wm.EBillboardTextureFormat, dds_dxgi, wm.BApplyBillboardTexture, wm.BUseCustomOutputBillboardTexture, wm.SOutputBillboardTexture)
        return {'FINISHED'}
    
class SpeedTreeBillboardsPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_billboards_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Billboards'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'billboard':
            
            layout = self.layout
            main_coll = GetCollection(make_active=False)
            bb_coll = None
            horiz_coll = None
            if main_coll:
                for col in main_coll.children:
                    if re.search("Vertical Billboards", col.name):
                        bb_coll = col
                    if re.search("Horizontal Billboard", col.name):
                        horiz_coll = col
                
                row = layout.row()
                row.prop(wm, "BUpdateBillboards", text = "Update Billboards")            
                row = layout.row()
                box = row.box()
                box_row = box.row()
                box_row.label(text="Vertical Billboards")
                box_row = box.row()
                box_row.enabled = wm.BUpdateBillboards
                box_row.prop(wm, "NNumBillboards", text = 'Number')
                if not bb_coll:
                    wm.NNumBillboards = 0
                elif not re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects])):
                    wm.NNumBillboards = 0
                else:
                    bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
                    obj = bb_coll.objects[bb_objects[0]]
                    verts = obj.data.vertices
                    bb_width = verts[2].co[0] - verts[0].co[0]
                    bb_top = verts[2].co[2]
                    bb_bottom = verts[0].co[2]
                    number_billboards = len(bb_objects)
                    ngroup = obj.modifiers[0].node_group
                    if wm.NNumBillboards != number_billboards:
                        wm.NNumBillboards = number_billboards
                            
                    box_row = box.row()
                    box_row.enabled = wm.NNumBillboards > 0 and wm.BUpdateBillboards
                    box_row.prop(wm, "FWidth", text = 'Width')
                    if wm.FWidth != bb_width:
                        wm.FWidth = bb_width
                    
                    box_row = box.row()
                    box_row.enabled = wm.NNumBillboards > 0 and wm.BUpdateBillboards
                    box_row.prop(wm, "FTopPos", text = 'Top')
                    if wm.FTopPos != bb_top:
                        wm.FTopPos = bb_top
                    
                    box_row = box.row()
                    box_row.enabled = wm.NNumBillboards > 0 and wm.BUpdateBillboards
                    box_row.prop(wm, "FBottomPos", text = 'Bottom')
                    if wm.FBottomPos != bb_bottom:
                        wm.FBottomPos = bb_bottom
                        
                    box_row = box.row()
                    box_row.enabled = wm.NNumBillboards > 0
                    box_row.prop(wm, "BCutout", text = 'Use Cutout')
                    if not re.findall('_cutout', str([x.name for x in bb_coll.objects])) or not ngroup.nodes['Cutout Diffuse UV'].outputs['Geometry'].links or not ngroup.nodes["Billboard Cutout"].inputs[0].default_value:
                        wm.BCutout = False
                    else:
                        wm.BCutout = True
                     
                row = layout.row()
                box = row.box()
                box_row = box.row()
                box_row.label(text="Horizontal Billboard")
                box_row = box.row()
                box_row.enabled = wm.BUpdateBillboards
                box_row.prop(wm, "BHorizontalBillboard", text = "Is Present")
                if not horiz_coll:
                    wm.BHorizontalBillboard = False
                elif not horiz_coll.objects:
                    wm.BHorizontalBillboard = False
                else:
                    wm.BHorizontalBillboard = True
                    obj = horiz_coll.objects[0]
                    verts = obj.data.vertices
                    bb_height = np.mean([verts[0].co[2], verts[2].co[2]])
                    bb_size = verts[2].co[0] - verts[0].co[0]
                    
                    box_row = box.row()
                    box_row.enabled = wm.BHorizontalBillboard and wm.BUpdateBillboards
                    box_row.prop(wm, "FHeight", text = 'Height')
                    if wm.FHeight != bb_height:
                        wm.FHeight = bb_height
                        
                    box_row = box.row()
                    box_row.enabled = wm.BHorizontalBillboard and wm.BUpdateBillboards
                    box_row.prop(wm, "FSize", text = 'Size')
                    if wm.FSize != bb_size:
                        wm.FSize = bb_size
                    
                if bb_coll or horiz_coll:
                    row = layout.row()
                    box = row.box()
                    box.enabled = wm.NNumBillboards > 0 or len(horiz_coll.objects) > 0
                    box_row = box.row()
                    box_row.label(text="Billboard Texture Generation")
                    box_row = box.row()
                    box_row.prop(wm, "IBillboardTextureResolution", text="Resolution")
                    box_row = box.row()
                    box_row.prop(wm, "IBillboardTextureMargin", text = "Margin")
                    box_row = box.row()
                    box_row.prop(wm, "IBillboardTextureDilation", text = "Dilation")
                    box_row = box.row()
                    box_row.prop(wm, "EBillboardTextureFormat", text="File Format")
                    if wm.EBillboardTextureFormat == 'DDS':
                        box_row = box.row()
                        box_row.prop(wm, "EDxgiFormat")
                    box_row = box.row()
                    box_row.prop(wm, "BApplyBillboardTexture", text="Apply Generated Textures")
                    box_row = box.row()
                    box_row.prop(wm, "BUseCustomOutputBillboardTexture", text="Use Custom Output Path")
                    box_row = box.row()
                    box_row.enabled = wm.BUseCustomOutputBillboardTexture
                    box_row.prop(wm, "SOutputBillboardTexture", text="Output Path")
                    box_row = box.row()
                    box_row.operator(SRTBillboardTextureGeneration.bl_idname, text = "Generate Texture", icon = "TEXTURE")
            
        return

def updateVerticalBillboards(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_objects = None
        bb_coll = GetCollection("Vertical Billboards", make_active=False)
        if bb_coll: 
            bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            
        if not bb_coll or not bb_objects:
            generate_srt_billboards(context, self.NNumBillboards, self.FWidth, self.FBottomPos, self.FTopPos)
            
        else:
            if self.NNumBillboards:
                n_bb = len(bb_objects)
                while n_bb < self.NNumBillboards:
                    selectOnly(bb_coll.objects[bb_objects[0]])
                    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
                    bpy.context.active_object.name = "Mesh_billboard"+str(n_bb)
                    bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
                    n_bb = len(bb_objects)
                    
                while n_bb > self.NNumBillboards:
                    bpy.data.objects.remove(bb_coll.objects[bb_objects[-1]], do_unlink=True)
                    bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
                    n_bb = len(bb_objects)
                
                angle_diff = 360/n_bb 
                for i, name in enumerate(bb_objects):
                    bb_coll.objects[name].rotation_euler[2] = radians(90 + angle_diff * i)
                    
            else:
                bpy.data.collections.remove(bb_coll, do_unlink=True)
        
def updateFWidth(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_coll = GetCollection("Vertical Billboards", make_active=False)
        if bb_coll:
            right = self.FWidth * 0.5
            left = -right
            pos_array = np.zeros(12)
            bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            for name in bb_objects:
                attrib_data = bb_coll.objects[name].data.attributes["position"].data
                attrib_data.foreach_get("vector", pos_array)
                pos_array[[0,9]] = left
                pos_array[[3,6]] = right
                attrib_data.foreach_set("vector", pos_array)
                attrib_data[0].vector = attrib_data[0].vector #Update the mesh
        
def updateFTopPos(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_coll = GetCollection("Vertical Billboards", make_active=False)
        if bb_coll:
            pos_array = np.zeros(12)
            bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            for name in bb_objects:
                attrib_data = bb_coll.objects[name].data.attributes["position"].data
                attrib_data.foreach_get("vector", pos_array)
                pos_array[[8,11]] = self.FTopPos
                attrib_data.foreach_set("vector", pos_array)
                attrib_data[0].vector = attrib_data[0].vector #Update the mesh
            
def updateFBottomPos(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_coll = GetCollection("Vertical Billboards", make_active=False)
        if bb_coll:
            pos_array = np.zeros(12)
            bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            for name in bb_objects:
                attrib_data = bb_coll.objects[name].data.attributes["position"].data
                attrib_data.foreach_get("vector", pos_array)
                pos_array[[2,5]] = self.FBottomPos
                attrib_data.foreach_set("vector", pos_array)
                attrib_data[0].vector = attrib_data[0].vector #Update the mesh
                
def updateBCutout(self, context):
    bb_coll = GetCollection("Vertical Billboards", make_active=False)
                
    if bb_coll:
        bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
        if bb_objects:
            ngroup = bb_coll.objects[bb_objects[0]].modifiers[0].node_group
            if self.BCutout:
                if not re.findall('_cutout', str([x.name for x in bb_coll.objects])):
                    obj = bb_coll.objects[bb_objects[0]]
                    selectOnly(obj)
                    bpy.ops.object.duplicate()
                    obj.name = 'Mesh_cutout'
                    obj.modifiers.remove(obj.modifiers[0])
                    
                ngroup.nodes["Billboard Cutout"].inputs[0].default_value = bb_coll.objects[re.findall(r"Mesh_cutout\.?\d*", str([x.name for x in bb_coll.objects]))[0]]
                ngroup.links.new(ngroup.nodes["Cutout Diffuse UV"].outputs['Geometry'], ngroup.nodes["Group Output"].inputs['Geometry'])
                
            else:
                ngroup.nodes["Billboard Cutout"].inputs[0].default_value = None
                ngroup.links.new(ngroup.nodes["Group Input"].outputs['Geometry'], ngroup.nodes["Group Output"].inputs['Geometry'])
            
def updateBHorizontalBillboard(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_coll = GetCollection("Horizontal Billboard", make_active=False)
                    
        if self.BHorizontalBillboard:
            if not bb_coll:
                generate_srt_horizontal_billboard(context, self.FHeight, self.FSize)
            else:
                if not bb_coll.objects:
                    generate_srt_horizontal_billboard(context, self.FHeight, self.FSize)
        else:
            if bb_coll:
                bpy.data.collections.remove(bb_coll, do_unlink=True)
                
def updateFHeight(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_coll = GetCollection("Horizontal Billboard", make_active=False)
        if bb_coll and bb_coll.objects:
            pos_array = np.zeros(12)
            bb_object = bb_coll.objects[0]
            attrib_data = bb_object.data.attributes["position"].data
            attrib_data.foreach_get("vector", pos_array)
            pos_array[[2,5,8,11]] = self.FHeight
            attrib_data.foreach_set("vector", pos_array)
            attrib_data[0].vector = attrib_data[0].vector #Update the mesh
            
def updateFSize(self, context):
    if context.window_manager.BUpdateBillboards:
        bb_coll = GetCollection("Horizontal Billboard", make_active=False)
        right = self.FSize * 0.5
        left = -right
        if bb_coll and bb_coll.objects:
            pos_array = np.zeros(12)
            bb_object = bb_coll.objects[0]
            attrib_data = bb_object.data.attributes["position"].data
            attrib_data.foreach_get("vector", pos_array)
            pos_array[[0,1,4,9]] = left
            pos_array[[3,6,7,10]] = right
            attrib_data.foreach_set("vector", pos_array)
            attrib_data[0].vector = attrib_data[0].vector #Update the mesh
    
     
PROPS_Billboard_Panel = [
("NNumBillboards", IntProperty(
        name = "Number of Vertical Billboards",
        update = updateVerticalBillboards,
        default = 0,
        min = 0
    )),
("FWidth", FloatProperty(
        name = "Width of Vertical Billboards",
        update = updateFWidth,
        default = 0,
        precision = 4,
        min = 0,
        subtype="DISTANCE"
    )),
("FTopPos", FloatProperty(
        name = "Top Position of Vertical Billboards",
        update = updateFTopPos,
        default = 0,
        precision = 4,
        subtype="DISTANCE"
    )),
("FBottomPos", FloatProperty(
        name = "Bottom Position of Vertical Billboards",
        update = updateFBottomPos,
        default = 0,
        precision = 4,
        subtype="DISTANCE"
    )),
("BCutout", BoolProperty(
        name = "Enable/disable Billboard cutout",
        update = updateBCutout,
        default = False
    )),
("BHorizontalBillboard", BoolProperty(
        name = "Enable/disable Horizontal Billboard",
        update = updateBHorizontalBillboard,
        default = False
    )),
("FHeight", FloatProperty(
        name = "Height of Horizontal Billboard",
        update = updateFHeight,
        default = 0,
        precision = 4,
        subtype="DISTANCE"
    )),
("FSize", FloatProperty(
        name = "Edge Length of Horizontal Billboard",
        update = updateFSize,
        default = 0,
        precision = 4,
        min = 0,
        subtype="DISTANCE"
    )),
("BUpdateBillboards", BoolProperty(
        name = "Enable/disable Billboards Updating",
        default = False
    )),
("IBillboardTextureResolution", IntProperty(
        name = "X Resolution of the Generated Billboard Textures",
        default = 1024,
        subtype="PIXEL"
    )),
("IBillboardTextureMargin", IntProperty(
        name = "UV Islands Margin",
        description = "Set the space between UV islands",
        default = 4,
        min = 0,
        subtype="PIXEL"
    )),
("IBillboardTextureDilation", IntProperty(
        name = "Texture Dilation",
        description = "Set the number of steps (in pixels) each billboard texture should be dilated by",
        default = 4,
        min = 0,
        subtype="PIXEL"
    )),
("EBillboardTextureFormat", EnumProperty(
        name = "Generated Billboard Texture Format",
        description = "Set the format of the generated billboard textures",
        default = 'PNG' if 'blender_dds_addon' not in bpy.context.preferences.addons else 'DDS',
        items =(
            ('PNG', "PNG", "Set the format of the generated billboard textures to PNG"),
            ('TARGA', "TGA", "Set the format of the generated billboard textures to TGA/Targa")) if 'blender_dds_addon' not in bpy.context.preferences.addons else
            (
            ('PNG', "PNG", "Set the format of the generated billboard textures to PNG"),
            ('TARGA', "TGA", "Set the format of the generated billboard textures to TGA/Targa"),
            ('DDS', "DDS", "Set the format of the generated billboard textures to DDS"))
    )), 
("BApplyBillboardTexture", BoolProperty(
        name = "Apply Generated Billboard Textures",
        default = True
    )),
("BUseCustomOutputBillboardTexture", BoolProperty(
        name = "Use Custom Path",
        description = "Enable/disable the custom path for the generated billboard textures",
        default = False
    )),
("SOutputBillboardTexture", StringProperty(
        name = "Path to the Generated Billboard Textures",
        subtype='DIR_PATH',
        default = "/tmp/",
        description="Path where the generated billboard textures should be saved"
    )),
("EDxgiFormat", EnumProperty(
        name='DXGI format',
        items=DDS_FMT_ITEMS if 'blender_dds_addon' in bpy.context.preferences.addons else None,
        description="DXGI format for DDS",
        default='BC3_UNORM'
    ))
]

CLASSES_Billboard_Panel = [SRTBillboardTextureGeneration, SpeedTreeBillboardsPanel]