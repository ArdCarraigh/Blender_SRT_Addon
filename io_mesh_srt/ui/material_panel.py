# -*- coding: utf-8 -*-
# ui/material_panel.py

import bpy
import numpy as np
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, StringProperty
from io_mesh_srt.utils import GetCollection, importSRTTexture
    
class SPEEDTREE_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        coll = data
        ma = item.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon="MATERIAL")
            else:
                layout.label(text="", translate=False, icon="MATERIAL")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon="MATERIAL")
                            
class SpeedTreeMaterialPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_material_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Material'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
        if wm.SpeedTreeSubPanel == 'material':
            
            layout = self.layout
            obj = context.active_object
            if obj:
                if "SpeedTreeTag" in obj and obj.data.materials:
                    mat = obj.active_material
                    
                    row = layout.row()
                    row.template_list("SPEEDTREE_UL_materials", "", obj, "material_slots", obj, "active_material_index", rows=3)
            
                    row = layout.row(align=True)  
                    row.prop(wm, "BBranchesPresent", text = "Branches", toggle=True)
                    if wm.BBranchesPresent != mat["BBranchesPresent"]:
                        wm.BBranchesPresent = mat["BBranchesPresent"]
                    
                    row.prop(wm, "BFrondsPresent", text = "Fronds",toggle=True)
                    if wm.BFrondsPresent != mat["BFrondsPresent"]:
                        wm.BFrondsPresent = mat["BFrondsPresent"]
                    
                    row.prop(wm, "BLeavesPresent", text = "Leaves", toggle=True)
                    if wm.BLeavesPresent != mat["BLeavesPresent"]:
                        wm.BLeavesPresent = mat["BLeavesPresent"]
                        
                    row.prop(wm, "BFacingLeavesPresent", text = "Facing Leaves", toggle=True)
                    if wm.BFacingLeavesPresent != mat["BFacingLeavesPresent"]:
                        wm.BFacingLeavesPresent = mat["BFacingLeavesPresent"]
                        
                    row.prop(wm, "BRigidMeshesPresent", text = "Rigid Meshes", toggle=True)
                    if wm.BRigidMeshesPresent != mat["BRigidMeshesPresent"]:
                        wm.BRigidMeshesPresent = mat["BRigidMeshesPresent"]
                        
                    row = layout.row()
                    row.enabled = (wm.BFrondsPresent and not (wm.BBranchesPresent or wm.BLeavesPresent or wm.BFacingLeavesPresent or wm.BRigidMeshesPresent))
                    row.prop(wm, "BCaps", text="Is Caps")
                    if wm.BCaps != mat["BCaps"]:
                        wm.BCaps = mat["BCaps"]
                    if wm.BBranchesPresent or wm.BLeavesPresent or wm.BFacingLeavesPresent or wm.BRigidMeshesPresent:
                        wm.BCaps = False
                    
                    layout.separator()  
                    row = layout.row(align = True)
                    row.alignment = "CENTER"
                    row.scale_x = 1.44
                    row.scale_y = 1.4
                    row.prop_enum(wm, "SpeedTreeMaterialSubPanel", 'texture')
                    row.prop_enum(wm, "SpeedTreeMaterialSubPanel", 'colorset')
                    row.prop_enum(wm, "SpeedTreeMaterialSubPanel", 'other')
                        
        return
    
class SpeedTreeTexturePanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_texture_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_material_panel'
    bl_label = 'Textures'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
        if wm.SpeedTreeSubPanel == 'material' and wm.SpeedTreeMaterialSubPanel == 'texture':
            
            layout = self.layout
            obj = context.active_object
            if obj:
                if "SpeedTreeTag" in obj and obj.data.materials:
                    mat = obj.active_material
                    
                    #Diffuse
                    row = layout.row()
                    box = row.box()
                    box.label(text="Diffuse Texture")
                    box.prop(wm, "diffuseTexture", text="")
                    if wm.diffuseTexture != mat["diffuseTexture"]:
                        wm.diffuseTexture = mat["diffuseTexture"]
                        
                    box.prop(wm, "BDiffuseAlphaMaskIsOpaque", text = "Alpha Mask Opaque")
                    if wm.BDiffuseAlphaMaskIsOpaque != mat["BDiffuseAlphaMaskIsOpaque"]:
                        wm.BDiffuseAlphaMaskIsOpaque = mat["BDiffuseAlphaMaskIsOpaque"]
                                   
                    #Normal
                    row = layout.row()
                    box = row.box()
                    box.label(text="Normal Texture")
                    box.prop(wm, "normalTexture", text="")
                    if wm.normalTexture != mat["normalTexture"]:
                        wm.normalTexture = mat["normalTexture"]
                            
                    #Specular
                    row = layout.row()
                    box = row.box()
                    box.label(text="Specular Texture")
                    box.prop(wm, "specularTexture", text="")
                    if wm.specularTexture != mat["specularTexture"]:
                        wm.specularTexture = mat["specularTexture"]
                    
                    #Branch Seam
                    row = layout.row()
                    box = row.box()
                    box.label(text = "Branch Seam Smoothing")
                    box.enabled = (wm.BBranchesPresent and not (wm.BFrondsPresent or wm.BLeavesPresent or wm.BFacingLeavesPresent or wm.BRigidMeshesPresent))
                    box.prop(wm, "EBranchSeamSmoothing", text = "")
                    if wm.EBranchSeamSmoothing != mat["EBranchSeamSmoothing"]:
                        wm.EBranchSeamSmoothing = mat["EBranchSeamSmoothing"]
                         
                    box_row = box.row()
                    box_row.enabled = wm.EBranchSeamSmoothing in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "FBranchSeamWeight", text = "Branch Seam Weight")
                    if wm.FBranchSeamWeight != mat["FBranchSeamWeight"]:
                        wm.FBranchSeamWeight = mat["FBranchSeamWeight"]
                        
                    #Detail Layer
                    row = layout.row()
                    box = row.box()
                    box.label(text = "Detail Layer")
                    box.enabled = ((wm.BBranchesPresent and not (wm.BFrondsPresent or wm.BLeavesPresent or wm.BFacingLeavesPresent or wm.BRigidMeshesPresent)) or wm.BCaps)
                    box.prop(wm, "EDetailLayer", text = "")
                    if wm.EDetailLayer != mat["EDetailLayer"]:
                        wm.EDetailLayer = mat["EDetailLayer"]
                    
                    box_row = box.row()
                    box_row.label(text = "Detail Texture")
                    box_row = box.row()
                    box_row.enabled = wm.EDetailLayer in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "detailTexture", text="")
                    if wm.detailTexture != mat["detailTexture"]:
                        wm.detailTexture = mat["detailTexture"]
                        
                    box_row = box.row()
                    box_row.label(text = "Detail Normal Texture")
                    box_row = box.row()
                    box_row.enabled = wm.EDetailLayer in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "detailNormalTexture", text="")
                    if wm.detailNormalTexture != mat["detailNormalTexture"]:
                        wm.detailNormalTexture = mat["detailNormalTexture"]
                               
        return
    
class SpeedTreeColorSetPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_color_set_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_material_panel'
    bl_label = 'Color Set'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
        if wm.SpeedTreeSubPanel == 'material' and wm.SpeedTreeMaterialSubPanel == 'colorset':
            
            layout = self.layout
            obj = context.active_object
            if obj:
                if "SpeedTreeTag" in obj and obj.data.materials:
                    mat = obj.active_material
                    
                    # Diffuse Color
                    row = layout.row()
                    box = row.box()
                    box_row = box.row()
                    box_row.label(text="Diffuse Color")
                    box_row.prop(wm, "VDiffuseColor", text = "")
                    if any(np.array(wm.VDiffuseColor) != np.array(mat["VDiffuseColor"])):
                        wm.VDiffuseColor = mat["VDiffuseColor"]
                        
                    box.prop(wm, "FDiffuseScalar", text = "Diffuse Scalar")
                    if wm.FDiffuseScalar != mat["FDiffuseScalar"]:
                        wm.FDiffuseScalar = mat["FDiffuseScalar"]
                        
                    #Ambient Color
                    row = layout.row()
                    box = row.box()
                    box_row = box.row()
                    box_row.label(text="Ambient Color")
                    box_row.prop(wm, "VAmbientColor", text = '')
                    if any(np.array(wm.VAmbientColor) != np.array(mat["VAmbientColor"])):
                        wm.VAmbientColor = mat["VAmbientColor"]
                    
                    box_row = box.row()
                    box_row.label(text = "Ambient Contrast")
                    box_row = box.row()
                    box_row.prop(wm, "EAmbientContrast", text = "")
                    if wm.EAmbientContrast != mat["EAmbientContrast"]:
                        wm.EAmbientContrast = mat["EAmbientContrast"]
                    
                    box_row = box.row()
                    box_row.enabled = wm.EAmbientContrast in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "FAmbientContrastFactor", text = 'Ambient Contrast Factor')
                    if wm.FAmbientContrastFactor != mat["FAmbientContrastFactor"]:
                        wm.FAmbientContrastFactor = mat["FAmbientContrastFactor"]
                        
                    #Specular Color
                    row = layout.row()
                    box = row.box()
                    box.label(text='Specular')
                    box.prop(wm, "ESpecular", text = "")
                    if wm.ESpecular != mat["ESpecular"]:
                        wm.ESpecular = mat["ESpecular"]
                        
                    box_row = box.row()
                    box_row.label(text="Specular Color")
                    box_row.enabled = wm.ESpecular in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "VSpecularColor", text = '')
                    if any(np.array(wm.VSpecularColor) != np.array(mat["VSpecularColor"])):
                        wm.VSpecularColor = mat["VSpecularColor"]
                        
                    box_row = box.row()
                    box_row.enabled = wm.ESpecular in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "FShininess", text = 'Shininess')
                    if wm.FShininess != mat["FShininess"]:
                        wm.FShininess = mat["FShininess"]
                        
                    #Transmission Color
                    row = layout.row()
                    box = row.box()
                    box.label(text='Transmission')
                    box.prop(wm, "ETransmission", text = "")
                    if wm.ETransmission != mat["ETransmission"]:
                        wm.ETransmission = mat["ETransmission"]
                        
                    box_row = box.row()
                    box_row.label(text="Transmission Color")
                    box_row.enabled = wm.ETransmission in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "VTransmissionColor", text = '')
                    if any(np.array(wm.VTransmissionColor) != np.array(mat["VTransmissionColor"])):
                        wm.VTransmissionColor = mat["VTransmissionColor"]
                        
                    box_row = box.row()
                    box_row.enabled = wm.ETransmission in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "FTransmissionViewDependency", text = 'View Influence')
                    if wm.FTransmissionViewDependency != mat["FTransmissionViewDependency"]:
                        wm.FTransmissionViewDependency = mat["FTransmissionViewDependency"]
                        
                    box_row = box.row()
                    box_row.enabled = wm.ETransmission in ["OFF__X__ON", "ON"]
                    box_row.prop(wm, "FTransmissionShadowBrightness", text = 'Shadow Brightness')
                    if wm.FTransmissionShadowBrightness != mat["FTransmissionShadowBrightness"]:
                        wm.FTransmissionShadowBrightness = mat["FTransmissionShadowBrightness"]
                        
                    #Visibility
                    row = layout.row()
                    box = row.box()
                    box.label(text='Visibility')
                    box.prop(wm, "FAlphaScalar", text = "Alpha Scalar")
                    if wm.FAlphaScalar != mat["FAlphaScalar"]:
                        wm.FAlphaScalar = mat["FAlphaScalar"]
                    
                    box_row = box.row()
                    box_row.label(text="Culling Method")
                    box_row = box.row()
                    box_row.prop(wm, "EFaceCulling", text = "")
                    if wm.EFaceCulling != mat["EFaceCulling"]:
                        wm.EFaceCulling = mat["EFaceCulling"]
                            
        return
    
class SpeedTreeOthersPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_others_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_material_panel'
    bl_label = 'Others'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
        if wm.SpeedTreeSubPanel == 'material' and wm.SpeedTreeMaterialSubPanel == 'other':
            
            layout = self.layout
            obj = context.active_object
            if obj:
                if "SpeedTreeTag" in obj and obj.data.materials:
                    mat = obj.active_material
                    
                    #Supported
                    row = layout.row()
                    box = row.box()
                    box.label(text="Supported")
                    box.prop(wm, "BAmbientOcclusion", text = "Ambient Occlusion")
                    if wm.BAmbientOcclusion != mat["BAmbientOcclusion"]:
                        wm.BAmbientOcclusion = mat["BAmbientOcclusion"]
                        
                    box.prop(wm, "BCastsShadows", text = "Cast Shadow")
                    if wm.BCastsShadows != mat["BCastsShadows"]:
                        wm.BCastsShadows = mat["BCastsShadows"]
                        
                    #Not Supported
                    row = layout.row()
                    box = row.box()
                    box.label(text="Not Supported")
                    
                    box.prop(wm, "BBlending", text = "Blending")
                    if wm.BBlending != mat["BBlending"]:
                        wm.BBlending = mat["BBlending"]
                        
                    box.prop(wm, "BReceivesShadows", text = "Receive Shadow")
                    if wm.BReceivesShadows != mat["BReceivesShadows"]:
                        wm.BReceivesShadows = mat["BReceivesShadows"]
                        
                    box.prop(wm, "BShadowSmoothing", text = "Shadow Smoothing")
                    if wm.BShadowSmoothing != mat["BShadowSmoothing"]:
                        wm.BShadowSmoothing = mat["BShadowSmoothing"]
                    
                    box_row = box.row()
                    box_row.label(text="Fog Curve")    
                    box_row = box.row()
                    box_row.prop(wm, "EFogCurve", text = '')
                    if wm.EFogCurve!= mat["EFogCurve"]:
                        wm.EFogCurve = mat["EFogCurve"]
                    
                    box_row = box.row()
                    box_row.label(text="Fog Curve Style")  
                    box_row = box.row()
                    box_row.prop(wm, "EFogColorStyle", text = '')
                    if wm.EFogColorStyle!= mat["EFogColorStyle"]:
                        wm.EFogColorStyle = mat["EFogColorStyle"]
                    
                    box_row = box.row()
                    box_row.label(text="Wind LOD")      
                    box_row = box.row()
                    box_row.prop(wm, "EWindLod", text = '')
                    if wm.EWindLod!= mat["EWindLod"]:
                        wm.EWindLod = mat["EWindLod"]
 
                    box_row = box.row()
                    box_row.label(text="Ambient Image Lighting")
                    box_row = box.row()
                    box_row.prop(wm, "EAmbientImageLighting", text = '')
                    if wm.EAmbientImageLighting!= mat["EAmbientImageLighting"]:
                        wm.EAmbientImageLighting = mat["EAmbientImageLighting"]
                        
                    box_row = box.row()
                    box_row.label(text="Hue Variation")
                    box_row = box.row()
                    box_row.prop(wm, "EHueVariation", text = '')
                    if wm.EHueVariation!= mat["EHueVariation"]:
                        wm.EHueVariation = mat["EHueVariation"]   

        return

def updateDiffuseTexture(self, context):
    mat = bpy.context.active_object.active_material
    mat["diffuseTexture"] = self.diffuseTexture
    image = importSRTTexture(self.diffuseTexture)                   
    nodes = mat.node_tree.nodes
    nodes["Diffuse Texture"].image = image
    nodes["Branch Seam Diffuse Texture"].image = image
    if image:
        nodes["Diffuse Texture"].image.colorspace_settings.name='sRGB'
        nodes["Branch Seam Diffuse Texture"].image.colorspace_settings.name='sRGB'
                
def updateNormalTexture(self, context):
    mat = bpy.context.active_object.active_material
    mat["normalTexture"] = self.normalTexture
    image = importSRTTexture(self.normalTexture)    
    nodes = mat.node_tree.nodes
    nodes["Normal Texture"].image = image
    nodes["Branch Seam Normal Texture"].image = image
    if image:
        nodes["Normal Texture"].image.colorspace_settings.name='Non-Color'
        nodes["Branch Seam Normal Texture"].image.colorspace_settings.name='Non-Color'
                
def updateDetailTexture(self, context):
    mat = bpy.context.active_object.active_material
    mat["detailTexture"] = self.detailTexture
    image = importSRTTexture(self.detailTexture)
    nodes = mat.node_tree.nodes
    nodes["Detail Texture"].image = image
    nodes["Branch Seam Detail Texture"].image = image
    if image:
        nodes["Detail Texture"].image.colorspace_settings.name='sRGB'
        nodes["Branch Seam Detail Texture"].image.colorspace_settings.name='sRGB'
                
def updateDetailNormalTexture(self, context):
    mat = bpy.context.active_object.active_material
    mat["detailNormalTexture"] = self.detailNormalTexture
    image = importSRTTexture(self.detailNormalTexture)
    nodes = mat.node_tree.nodes
    nodes["Detail Normal Texture"].image = image
    nodes["Branch Seam Detail Normal Texture"].image = image
    if image:
        nodes["Detail Normal Texture"].image.colorspace_settings.name='Non-Color'
        nodes["Branch Seam Detail Normal Texture"].image.colorspace_settings.name='Non-Color'
                
def updateSpecularTexture(self, context):
    mat = bpy.context.active_object.active_material
    mat["specularTexture"] = self.specularTexture
    image = importSRTTexture(self.specularTexture)
    nodes = mat.node_tree.nodes 
    nodes["Specular Texture"].image = image
    nodes["Branch Seam Specular Texture"].image = image
    if image:
        nodes["Specular Texture"].image.colorspace_settings.name='Non-Color'
        nodes["Branch Seam Specular Texture"].image.colorspace_settings.name='Non-Color'
    if self.specularTexture:
        nodes["Control Specular Texture"].inputs["Factor"].default_value = 0
        nodes["Control Transmission Texture"].inputs["Factor"].default_value = 0
    else:
        nodes["Control Specular Texture"].inputs["Factor"].default_value = 1
        nodes["Control Transmission Texture"].inputs["Factor"].default_value = 1
            
def updateVAmbientColor(self, context):
    mat = bpy.context.active_object.active_material
    mat["VAmbientColor"] = self.VAmbientColor
    mat.node_tree.nodes["Ambient Color"].outputs["Color"].default_value = self.VAmbientColor
            
def updateEAmbientContrast(self, context):
    mat = bpy.context.active_object.active_material
    mat["EAmbientContrast"] = self.EAmbientContrast
    nodes = mat.node_tree.nodes
    if self.EAmbientContrast == "OFF":
        nodes['Control Ambient Contrast'].inputs[1].default_value = 1
    else:
        nodes['Control Ambient Contrast'].inputs[1].default_value = 0
                
def updateFAmbientContrastFactor(self, context):
    mat = bpy.context.active_object.active_material
    mat["FAmbientContrastFactor"] = self.FAmbientContrastFactor
    mat.node_tree.nodes["Ambient Contrast Factor"].outputs["Value"].default_value = self.FAmbientContrastFactor
            
def updateBAmbientOcclusion(self, context):
    mat = bpy.context.active_object.active_material
    mat["BAmbientOcclusion"] = self.BAmbientOcclusion
    mat.node_tree.nodes['Control Ambient Occlusion'].inputs[1].default_value = not self.BAmbientOcclusion
                
def updateVDiffuseColor(self, context):
    mat = bpy.context.active_object.active_material
    mat["VDiffuseColor"] = self.VDiffuseColor
    mat.node_tree.nodes["Diffuse Color"].outputs["Color"].default_value = self.VDiffuseColor
            
def updateFDiffuseScalar(self, context):
    mat = bpy.context.active_object.active_material
    mat["FDiffuseScalar"] = self.FDiffuseScalar
    mat.node_tree.nodes["Diffuse Scalar"].outputs["Value"].default_value = self.FDiffuseScalar
            
def updateBDiffuseAlphaMaskIsOpaque(self, context):
    mat = bpy.context.active_object.active_material
    mat["BDiffuseAlphaMaskIsOpaque"] = self.BDiffuseAlphaMaskIsOpaque
    mat.node_tree.nodes['Control Diffuse Mask Opaque'].inputs[1].default_value = self.BDiffuseAlphaMaskIsOpaque
                
def updateEDetailLayer(self, context):
    mat = bpy.context.active_object.active_material
    mat["EDetailLayer"] = self.EDetailLayer
    nodes = mat.node_tree.nodes
    if self.EDetailLayer == "OFF":
        nodes['Control Diffuse Detail Layer'].inputs[1].default_value = 1
        nodes['Control Normal Detail Layer'].inputs[1].default_value = 1
    else:
        nodes['Control Diffuse Detail Layer'].inputs[1].default_value = 0
        nodes['Control Normal Detail Layer'].inputs[1].default_value = 0
                
def updateESpecular(self, context):
    mat = bpy.context.active_object.active_material
    mat["ESpecular"] = self.ESpecular
    nodes = mat.node_tree.nodes
    if self.ESpecular == "OFF":
        nodes['Control Specular'].inputs[0].default_value = 1
        nodes['Control Shininess'].inputs[1].default_value = 1
    else:
        nodes['Control Specular'].inputs[0].default_value = 0
        nodes['Control Shininess'].inputs[1].default_value = 0
        if mat["specularTexture"]:
            nodes["Control Specular Texture"].inputs["Factor"].default_value = 0
        else:
            nodes["Control Specular Texture"].inputs["Factor"].default_value = 1
                
def updateFShininess(self, context):
    mat = bpy.context.active_object.active_material
    mat["FShininess"] = self.FShininess
    mat.node_tree.nodes["Shininess"].outputs["Value"].default_value = self.FShininess
            
def updateVSpecularColor(self, context):
    mat = bpy.context.active_object.active_material
    mat["VSpecularColor"] = self.VSpecularColor
    mat.node_tree.nodes["Specular Color"].outputs["Color"].default_value = self.VSpecularColor
            
def updateETransmission(self, context):
    mat = bpy.context.active_object.active_material
    mat["ETransmission"] = self.ETransmission
    nodes = mat.node_tree.nodes
    if self.ETransmission == "OFF":
        nodes['Control Transmission Seam Blending'].inputs[1].default_value = 1
        nodes['Control Transmission Mask'].inputs[0].default_value = 1
        nodes['Control Transmission Pre Final'].inputs[1].default_value = 1
    else:
        nodes['Control Transmission Seam Blending'].inputs[1].default_value = 0
        nodes['Control Transmission Mask'].inputs[0].default_value = 0
        nodes['Control Transmission Pre Final'].inputs[1].default_value = 0
        if mat["specularTexture"]:
            nodes["Control Transmission Texture"].inputs["Factor"].default_value = 0
        else:
            nodes["Control Transmission Texture"].inputs["Factor"].default_value = 1
                
def updateVTransmissionColor(self, context):
    mat = bpy.context.active_object.active_material
    mat["VTransmissionColor"] = self.VTransmissionColor
    mat.node_tree.nodes["Transmission Color"].outputs["Color"].default_value = self.VTransmissionColor
            
def updateFTransmissionShadowBrightness(self, context):
    mat = bpy.context.active_object.active_material
    mat["FTransmissionShadowBrightness"] = self.FTransmissionShadowBrightness
    mat.node_tree.nodes['Transmission Shadow Brightness'].outputs["Value"].default_value = self.FTransmissionShadowBrightness
            
def updateFTransmissionViewDependency(self, context):
    mat = bpy.context.active_object.active_material
    mat["FTransmissionViewDependency"] = self.FTransmissionViewDependency
    mat.node_tree.nodes["Transmission View Dependency"].inputs[0].default_value = 1 - self.FTransmissionViewDependency
            
def updateEBranchSeamSmoothing(self, context):
    mat = bpy.context.active_object.active_material
    mat["EBranchSeamSmoothing"] = self.EBranchSeamSmoothing
    nodes = mat.node_tree.nodes
    if self.EBranchSeamSmoothing == "OFF":
        nodes['Control Branch Seam Smoothing'].inputs[1].default_value = 1
    else:
        nodes['Control Branch Seam Smoothing'].inputs[1].default_value = 0
                
def updateFBranchSeamWeight(self, context):
    mat = bpy.context.active_object.active_material
    mat["FBranchSeamWeight"] = self.FBranchSeamWeight
    mat.node_tree.nodes["Branch Seam Weight"].outputs["Value"].default_value = self.FBranchSeamWeight
            
def updateEFaceCulling(self, context):
    mat = bpy.context.active_object.active_material
    mat["EFaceCulling"] = self.EFaceCulling
    if self.EFaceCulling == "BACK":
        mat.use_backface_culling = True
    else:
        mat.use_backface_culling = False
                
def updateBBlending(self, context):
    bpy.context.active_object.active_material["BBlending"] = self.BBlending
            
def updateEAmbientImageLighting(self, context):
    bpy.context.active_object.active_material["EAmbientImageLighting"] = self.EAmbientImageLighting
            
def updateEHueVariation(self, context):
    bpy.context.active_object.active_material["EHueVariation"] = self.EHueVariation
            
def updateEFogCurve(self, context):
    bpy.context.active_object.active_material["EFogCurve"] = self.EFogCurve
            
def updateEFogColorStyle(self, context):
    bpy.context.active_object.active_material["EFogColorStyle"] = self.EFogColorStyle
            
def updateBCastsShadows(self, context):
    mat = bpy.context.active_object.active_material
    mat["BCastsShadows"] = self.BCastsShadows
    mat.node_tree.nodes['Control Cast Shadows'].inputs[1].default_value = self.BCastsShadows
                
def updateBReceivesShadows(self, context):
    bpy.context.active_object.active_material["BReceivesShadows"] = self.BReceivesShadows
            
def updateBShadowSmoothing(self, context):
    bpy.context.active_object.active_material["BShadowSmoothing"] = self.BShadowSmoothing
    
def updateFAlphaScalar(self, context):
    mat = bpy.context.active_object.active_material
    mat["FAlphaScalar"] = self.FAlphaScalar
    mat.node_tree.nodes["Alpha Scalar"].outputs["Value"].default_value = self.FAlphaScalar
            
def updateEWindLod(self, context):
    bpy.context.active_object.active_material["EWindLod"] = self.EWindLod
            
def updateBBranchesPresent(self, context):
    bpy.context.active_object.active_material["BBranchesPresent"] = self.BBranchesPresent
        
def updateBFrondsPresent(self, context):
    bpy.context.active_object.active_material["BFrondsPresent"] = self.BFrondsPresent
            
def updateBLeavesPresent(self, context):
    bpy.context.active_object.active_material["BLeavesPresent"] = self.BLeavesPresent
            
def updateBFacingLeavesPresent(self, context):
    bpy.context.active_object.active_material["BFacingLeavesPresent"] = self.BFacingLeavesPresent
            
def updateBRigidMeshesPresent(self, context):
    bpy.context.active_object.active_material["BRigidMeshesPresent"] = self.BRigidMeshesPresent
    
def updateBCaps(self, context):
    mat = bpy.context.active_object.active_material
    nodes = mat.node_tree.nodes
    mat["BCaps"] = self.BCaps
    if self.BCaps:
        nodes["UV Map.002"].uv_map = "DiffuseUV"
        nodes["UV Map.003"].uv_map = "SeamDiffuseUV"
    else:
        nodes["UV Map.002"].uv_map = "DetailUV"
        nodes["UV Map.003"].uv_map = "SeamDetailUV"   
     
PROPS_Material_Panel = [
("diffuseTexture", StringProperty(
        subtype='FILE_PATH',
        default = '',
        update = updateDiffuseTexture,
        name="Diffuse Texture",
        description="Set the diffuse texture used by the selected material"
    )),
("normalTexture", StringProperty(
        subtype='FILE_PATH',
        default = '',
        update = updateNormalTexture,
        name="Normal Texture",
        description="Set the normal texture used by the selected material"
    )),
("detailTexture", StringProperty(
        subtype='FILE_PATH',
        default = '',
        update = updateDetailTexture,
        name="Detail Texture",
        description="Set the detail texture used by the selected material"
    )),
("detailNormalTexture", StringProperty(
        subtype='FILE_PATH',
        default = '',
        update = updateDetailNormalTexture,
        name="Detail Normal Texture",
        description="Set the detail normal texture used by the selected material"
    )),
("specularTexture", StringProperty(
        subtype='FILE_PATH',
        default = '',
        update = updateSpecularTexture,
        name="Specular Texture",
        description="Set the specular texture used by the selected material"
    )),
("VAmbientColor", FloatVectorProperty(
        name="Ambient Color",
        update = updateVAmbientColor,
        description="Set the ambient color of the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        subtype = 'COLOR',
        precision = 6,
        size = 4,
        min = 0,
        max = 1
    )),
("EAmbientContrast", EnumProperty(
        name="Ambient Contrast",
        update = updateEAmbientContrast,
        description="Darken the transitional area between the diffuse color and the ambient color !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('OFF', "OFF", "Disable ambient contrast"),
            ('OFF__X__ON', "OFF__X__ON", "Enable ambient contrast only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable ambient contrast"))
    )),
("FAmbientContrastFactor", FloatProperty(
        name="Ambient Contrast Factor",
        update = updateFAmbientContrastFactor,
        description="Set the ambient contrast factor !!! NOT SUPPORTED IN BLENDER !!!",
        precision = 4,
        min = 0,
        max = 1
    )),
("BAmbientOcclusion", BoolProperty(
        name="Ambient Occlusion",
        update = updateBAmbientOcclusion,
        description="Enable/disable ambient occlusion"
    )),
("VDiffuseColor", FloatVectorProperty(
        name="Diffuse Color",
        update = updateVDiffuseColor,
        description="Set the diffuse color of the selected material",
        subtype = 'COLOR',
        precision = 6,
        size = 4,
        min = 0,
        max = 1
    )),
("FDiffuseScalar", FloatProperty(
        name="Diffuse Scalar",
        update = updateFDiffuseScalar,
        description="Set the diffuse scalar",
        precision = 4,
        min = 0,
        max = 100
    )),
("BDiffuseAlphaMaskIsOpaque", BoolProperty(
        name="Diffuse Alpha Mask Opaque",
        update = updateBDiffuseAlphaMaskIsOpaque,
        description="Enable/disable the diffuse alpha mask"
    )),
("EDetailLayer", EnumProperty(
        name="Detail Layer",
        update = updateEDetailLayer,
        description="Add a detail texture layer",
        items=(
            ('OFF', "OFF", "Disable detail layer"),
            ('OFF__X__ON', "OFF__X__ON", "Enable detail layer only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable detail layer"))
    )),
("ESpecular", EnumProperty(
        name="Specular",
        update = updateESpecular,
        description="Add a specular effect",
        items=(
            ('OFF', "OFF", "Disable specular"),
            ('OFF__X__ON', "OFF__X__ON", "Enable specular only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable specular"))
    )),
("FShininess", FloatProperty(
        name="Shininess",
        update = updateFShininess,
        description="Set the shininess",
        precision = 4,
        min = 0,
        max = 1
    )),
("VSpecularColor", FloatVectorProperty(
        name="Specular Color",
        update = updateVSpecularColor,
        description="Set the specular color of the selected material",
        subtype = 'COLOR',
        precision = 6,
        size = 4,
        min = 0,
        max = 1
    )),
("ETransmission", EnumProperty(
        name="Transmission",
        update = updateETransmission,
        description="Add a transmission effect",
        items=(
            ('OFF', "OFF", "Disable transmission"),
            ('OFF__X__ON', "OFF__X__ON", "Enable transmission only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable transmission"))
    )),
("VTransmissionColor", FloatVectorProperty(
        name="Transmission Color",
        update = updateVTransmissionColor,
        description="Set the transmission color of the selected material",
        subtype = 'COLOR',
        precision = 6,
        size = 4,
        min = 0,
        max = 1
    )),
("FTransmissionShadowBrightness", FloatProperty(
        name="Transmission Shadow Brightness",
        update = updateFTransmissionShadowBrightness,
        description="Allow for the brightening of shadows where transmission occurs",
        precision = 4,
        min = 0,
        max = 1
    )),
("FTransmissionViewDependency", FloatProperty(
        name="Transmission View Dependency",
        update = updateFTransmissionViewDependency,
        description="Make the transmission dependent on the viewer's direction",
        precision = 4,
        min = 0,
        max = 1
    )),
("EBranchSeamSmoothing", EnumProperty(
        name="Branch Seam Smoothing",
        update = updateEBranchSeamSmoothing,
        description="Enable/disable branch seam smoothing",
        items=(
            ('OFF', "OFF", "Disable branch seam smoothing"),
            ('OFF__X__ON', "OFF__X__ON", "Enable branch seam smoothing only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable branch seam smoothing"))
    )),
("FBranchSeamWeight", FloatProperty(
        name="Branch Seam Weight",
        update = updateFBranchSeamWeight,
        description="Adjust how “dense” the blend area is in the blend computation",
        precision = 4,
        min = 0,
        max = 99.9999
    )),
("EFaceCulling", EnumProperty(
        name="Face Culling",
        update = updateEFaceCulling,
        description="Set the culling method of the selected material",
        items=(
            ('NONE', "NONE", "Disable face culling"),
            ('BACK', "BACK", "Enable backface culling"),
            ('FRONT', "FRONT", "Enable frontface culling !!! NOT SUPPORTED IN BLENDER !!!"))
    )),
("BBlending", BoolProperty(
        name="Blending",
        update = updateBBlending,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!"
    )),
("EAmbientImageLighting", EnumProperty(
        name="Ambient Image Lighting",
        update = updateEAmbientImageLighting,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('OFF', "OFF", "Disable ambient image lighting"),
            ('OFF__X__ON', "OFF__X__ON", "Enable ambient image lighting only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable ambient image lighting"))
    )),
("EHueVariation", EnumProperty(
        name="Hue Variation",
        update = updateEHueVariation,
        description="Add semi-random hues to individual instances of the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('OFF', "OFF", "Disable hue variation"),
            ('OFF__X__ON', "OFF__X__ON", "Enable hue variation only where needed? Considered ON in Blender"),
            ('ON', "ON", "Enable hue variation"))
    )),
("EFogCurve", EnumProperty(
        name="Fog Curve",
        update = updateEFogCurve,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('NONE', "NONE", "Disable fog curve"),
            ('LINEAR', "LINEAR", "Enable the linear fog curve"))
    )),
("EFogColorStyle", EnumProperty(
        name="Fog Color Style",
        update = updateEFogColorStyle,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('CONSTANT', "CONSTANT", "Make the fog color constant along the curve?"),
            ('DYNAMIC', "DYNAMIC", "Make the fog color dynamic along the curve?"))
    )),
("BCastsShadows", BoolProperty(
        name="Casts Shadows",
        update = updateBCastsShadows,
        description="Allow/disallow the selected material to cast shadows"
    )),
("BReceivesShadows", BoolProperty(
        name="Receives Shadows",
        update = updateBReceivesShadows,
        description="Allow/disallow the selected material to receive shadows !!! NOT SUPPORTED IN BLENDER !!!"
    )),
("BShadowSmoothing", BoolProperty(
        name="Shadow Smoothing",
        update = updateBShadowSmoothing,
        description="Enable/disable shadow smoothing !!! NOT SUPPORTED IN BLENDER !!!"
    )),
("FAlphaScalar", FloatProperty(
        name="Alpha Scalar",
        update = updateFAlphaScalar,
        description="Set the alpha scalar",
        precision = 4,
        min = 0,
        max = 100
    )),
("EWindLod", EnumProperty(
        name="Wind Lod",
        update = updateEWindLod,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('NONE', "NONE", "No idea"),
            ('CROSSFADE_NONE_TO_BRANCH', "CROSSFADE_NONE_TO_BRANCH", "No idea"),
            ('BRANCH', "BRANCH", "No idea"),
            ('CROSSFADE_BRANCH_TO_FULL', 'CROSSFADE_BRANCH_TO_FULL', "No idea"),
            ('FULL', 'FULL', "No idea"),
            ('GLOBAL', "GLOBAL", "No idea"),
            ('CROSSFADE_GLOBAL_TO_BRANCH', 'CROSSFADE_GLOBAL_TO_BRANCH', "No idea"),
            ('CROSSFADE_GLOBAL_TO_FULL', 'CROSSFADE_GLOBAL_TO_FULL', "No idea"))
    )),
("BBranchesPresent", BoolProperty(
        name="Branches Present",
        update = updateBBranchesPresent,
        description="Indicate presence of branches geometry"
    )),
("BFrondsPresent", BoolProperty(
        name="Fronds Present",
        update = updateBFrondsPresent,
        description="Indicate presence of fronds geometry"
    )),
("BLeavesPresent", BoolProperty(
        name="Leaves Present",
        update = updateBLeavesPresent,
        description="Indicate presence of leaves geometry"
    )),
("BFacingLeavesPresent", BoolProperty(
        name="Facing Leaves Present",
        update = updateBFacingLeavesPresent,
        description="Indicate presence of facing leaves geometry"
    )),
("BRigidMeshesPresent", BoolProperty(
        name="Rigid Meshes Present",
        update = updateBRigidMeshesPresent,
        description="Indicate presence of rigid meshes geometry"
    )),
("BCaps", BoolProperty(
        name="Caps",
        update = updateBCaps,
        description="Indicate whether to consider as cap geometry. In essence, it allows fronds geometry to use a detail texture"
    )),
('SpeedTreeMaterialSubPanel', EnumProperty(
        name="SpeedTree Material SubPanel",
        description="Set the active SpeedTree material subpanel",
        items=(
            ('texture', "Textures", "Show the texture SpeedTree material subpanel", 'TEXTURE', 0),
            ('colorset', "Color Set", "Show the color set SpeedTree material subpanel", 'COLOR', 1),
            ('other', "Others", "Show the other SpeedTree material subpanel",'TOOL_SETTINGS', 2)
        ),
        default='texture'
    ))
]

CLASSES_Material_Panel = [SPEEDTREE_UL_materials, SpeedTreeMaterialPanel, SpeedTreeTexturePanel, SpeedTreeColorSetPanel, SpeedTreeOthersPanel]