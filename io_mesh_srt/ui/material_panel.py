# -*- coding: utf-8 -*-
# ui/material_panel.py

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, PointerProperty
    
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
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'material':
            
            layout = self.layout
            me = context.active_object
            if me:
                mesh = me.data
                if "SpeedTreeTag" in mesh:
                    if mesh.materials:
                        mat = me.active_material
                        row = layout.row()
                        row.template_list("SPEEDTREE_UL_materials", "", me, "material_slots", me, "active_material_index", rows=3)
                
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
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'material' and wm.SpeedTreeMaterialSubPanel == 'texture':
            
            layout = self.layout
            me = context.active_object
            if me:
                mesh = me.data
                if "SpeedTreeTag" in mesh:
                    if mesh.materials:
                        mat = me.active_material
                        nodes = mat.node_tree.nodes
                        
                        #Diffuse
                        row = layout.row()
                        box = row.box()
                        box.label(text="Diffuse Texture")
                        box.template_ID(wm, "diffuseTexture", new="image.new", open="image.open")
                        if wm.diffuseTexture != nodes["Diffuse Texture"].image:
                            wm.diffuseTexture = nodes["Diffuse Texture"].image
                            
                        box.prop(wm, "BDiffuseAlphaMaskIsOpaque", text = "Alpha Mask Opaque")
                        if mat.blend_method == 'OPAQUE':
                            wm.BDiffuseAlphaMaskIsOpaque = True
                        else:
                            wm.BDiffuseAlphaMaskIsOpaque = False
                                       
                        #Normal
                        row = layout.row()
                        box = row.box()
                        box.label(text="Normal Texture")
                        box.template_ID(wm, "normalTexture", new="image.new", open="image.open")
                        if wm.normalTexture != nodes["Normal Texture"].image:
                            wm.normalTexture = nodes["Normal Texture"].image
                                
                        #Specular
                        row = layout.row()
                        box = row.box()
                        box.label(text="Specular Texture")
                        box.template_ID(wm, "specularTexture", new="image.new", open="image.open")
                        if wm.specularTexture != nodes["Specular Texture"].image:
                            wm.specularTexture = nodes["Specular Texture"].image
                        
                        #Branch Seam
                        row = layout.row()
                        box = row.box()
                        box.label(text = "Branch Seam Smoothing")
                        box.enabled = wm.BBranchesPresent
                        box.prop(wm, "EBranchSeamSmoothing", text = "")
                        if wm.EBranchSeamSmoothing != mat["EBranchSeamSmoothing"]:
                            wm.EBranchSeamSmoothing = mat["EBranchSeamSmoothing"]
                        if len(nodes['Branch Seam Weight Mult'].outputs['Value'].links) != 10:
                            wm.EBranchSeamSmoothing = 'EFFECT_OFF'
                             
                        box_row = box.row()
                        box_row.enabled = wm.EBranchSeamSmoothing in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FBranchSeamWeight", text = "Branch Seam Weight")
                        if wm.FBranchSeamWeight != nodes["Branch Seam Weight"].outputs["Value"].default_value:
                            wm.FBranchSeamWeight = nodes["Branch Seam Weight"].outputs["Value"].default_value
                            
                        #Detail Layer
                        row = layout.row()
                        box = row.box()
                        box.label(text = "Detail Layer")
                        box.enabled = wm.BBranchesPresent
                        box.prop(wm, "EDetailLayer", text = "")
                        if wm.EDetailLayer != mat["EDetailLayer"]:
                            wm.EDetailLayer = mat["EDetailLayer"]
                        if not nodes['Mix Detail Diffuse'].inputs["Fac"].links or not nodes['Mix Detail Normal'].inputs["Fac"].links:
                            wm.EDetailLayer = 'EFFECT_OFF'
                        
                        box_row = box.row()
                        box_row.label(text = "Detail Texture")
                        box_row.enabled = wm.EDetailLayer in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.template_ID(wm, "detailTexture", new="image.new", open="image.open")
                        if wm.detailTexture != nodes["Detail Texture"].image:
                            wm.detailTexture = nodes["Detail Texture"].image
                            
                        box_row = box.row()
                        box_row.label(text = "Detail Normal Texture")
                        box_row.enabled = wm.EDetailLayer in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.template_ID(wm, "detailNormalTexture", new="image.new", open="image.open")
                        if wm.detailNormalTexture != nodes["Detail Normal Texture"].image:
                            wm.detailNormalTexture = nodes["Detail Normal Texture"].image
                               
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
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'material' and wm.SpeedTreeMaterialSubPanel == 'colorset':
            
            layout = self.layout
            me = context.active_object
            if me:
                mesh = me.data
                if "SpeedTreeTag" in mesh:
                    if mesh.materials:
                        mat = me.active_material
                        nodes = mat.node_tree.nodes
                        
                        # Diffuse Color
                        row = layout.row()
                        box = row.box()
                        box_row = box.row()
                        box_row.label(text="Diffuse Color")
                        box_row.prop(wm, "VDiffuseColor", text = "")
                        if wm.VDiffuseColor != nodes["Diffuse Color"].outputs["Color"].default_value:
                            wm.VDiffuseColor = nodes["Diffuse Color"].outputs["Color"].default_value
                            
                        box.prop(wm, "FDiffuseScalar", text = "Diffuse Scalar")
                        if wm.FDiffuseScalar != nodes["Diffuse Scalar"].outputs["Value"].default_value:
                            wm.FDiffuseScalar = nodes["Diffuse Scalar"].outputs["Value"].default_value
                            
                        #Ambient Color
                        row = layout.row()
                        box = row.box()
                        box.label(text='Ambient Contrast')
                        box.prop(wm, "EAmbientContrast", text = "")
                        if wm.EAmbientContrast != mat["EAmbientContrast"]:
                            wm.EAmbientContrast = mat["EAmbientContrast"]
                        if not nodes['Ambient Contrast'].inputs["Fac"].links:
                            wm.EAmbientContrast = 'EFFECT_OFF'
                        
                        box_row = box.row()
                        box_row.label(text="Ambient Color")
                        box_row.enabled = wm.EAmbientContrast in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "VAmbientColor", text = '')
                        if wm.VAmbientColor != nodes["Ambient Color"].outputs["Color"].default_value:
                            wm.VAmbientColor = nodes["Ambient Color"].outputs["Color"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.EAmbientContrast in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FAmbientContrastFactor", text = 'Ambient Contrast Factor')
                        if wm.FAmbientContrastFactor != nodes["Ambient Contrast Factor"].outputs["Value"].default_value:
                            wm.FAmbientContrastFactor = nodes["Ambient Contrast Factor"].outputs["Value"].default_value
                            
                        #Specular Color
                        row = layout.row()
                        box = row.box()
                        box.label(text='Specular')
                        box.prop(wm, "ESpecular", text = "")
                        if wm.ESpecular != mat["ESpecular"]:
                            wm.ESpecular = mat["ESpecular"]
                        if not nodes['Specular BSDF'].inputs['Roughness'].links or not nodes["Mix Specular Color"].inputs['Color2'].links:
                            wm.ESpecular = 'EFFECT_OFF'
                            
                        box_row = box.row()
                        box_row.label(text="Specular Color")
                        box_row.enabled = wm.ESpecular in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "VSpecularColor", text = '')
                        if wm.VSpecularColor!= nodes["Specular Color"].outputs["Color"].default_value:
                            wm.VSpecularColor = nodes["Specular Color"].outputs["Color"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.ESpecular in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FShininess", text = 'Shininess')
                        if wm.FShininess != nodes["Shininess"].outputs["Value"].default_value:
                            wm.FShininess = nodes["Shininess"].outputs["Value"].default_value
                            
                        #Transmission Color
                        row = layout.row()
                        box = row.box()
                        box.label(text='Transmission')
                        box.prop(wm, "ETransmission", text = "")
                        if wm.ETransmission != mat["ETransmission"]:
                            wm.ETransmission = mat["ETransmission"]
                        if not nodes["Mix Transmission Color"].inputs["Color2"].links or not nodes["Mix Shader Fresnel"].inputs["Fac"].links or not nodes["Mix Shadow Brightness"].inputs["Fac"].links:
                            wm.ETransmission = 'EFFECT_OFF'
                            
                        box_row = box.row()
                        box_row.label(text="Transmission Color")
                        box_row.enabled = wm.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "VTransmissionColor", text = '')
                        if wm.VTransmissionColor!= nodes["Transmission Color"].outputs["Color"].default_value:
                            wm.VTransmissionColor = nodes["Transmission Color"].outputs["Color"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FTransmissionViewDependency", text = 'View Influence')
                        if wm.FTransmissionViewDependency != nodes["Transmission View Dependency"].outputs["Value"].default_value:
                            wm.FTransmissionViewDependency = nodes["Transmission View Dependency"].outputs["Value"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FTransmissionShadowBrightness", text = 'Shadow Brightness')
                        if wm.FTransmissionShadowBrightness != nodes["Transmission Shadow Brightness"].outputs["Value"].default_value:
                            wm.FTransmissionShadowBrightness = nodes["Transmission Shadow Brightness"].outputs["Value"].default_value
                            
                        #Visibility
                        row = layout.row()
                        box = row.box()
                        box.label(text='Visibility')
                        box.prop(wm, "FAlphaScalar", text = "Alpha Scalar")
                        if wm.FAlphaScalar != nodes["Alpha Scalar"].outputs["Value"].default_value:
                            wm.FAlphaScalar = nodes["Alpha Scalar"].outputs["Value"].default_value
                        
                        box_row = box.row()
                        box_row.label(text="Culling Type")  
                        box.prop(wm, "EFaceCulling", text = "")
                        if wm.EFaceCulling != mat["EFaceCulling"]:
                            wm.EFaceCulling = mat["EFaceCulling"]
                        if mat.use_backface_culling:
                            wm.EFaceCulling = 'CULLTYPE_BACK'
                            
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
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'material' and wm.SpeedTreeMaterialSubPanel == 'other':
            
            layout = self.layout
            me = context.active_object
            if me:
                mesh = me.data
                if "SpeedTreeTag" in mesh:
                    if mesh.materials:
                        mat = me.active_material
                        nodes = mat.node_tree.nodes
                        
                        #Supported
                        row = layout.row()
                        box = row.box()
                        box.label(text="Supported")
                        box.prop(wm, "BAmbientOcclusion", text = "Ambient Occlusion")
                        if not nodes['Ambient Occlusion'].inputs["Color"].links:
                            wm.BAmbientOcclusion = False
                        else:
                            wm.BAmbientOcclusion = True
                            
                        box.prop(wm, "BCastsShadows", text = "Cast Shadow")
                        if mat.shadow_method != 'NONE':
                            wm.BCastsShadows = True
                        else:
                            wm.BCastsShadows = False
                            
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
                        box_row.prop(wm, "EFogCurve", text = '')
                        if wm.EFogCurve!= mat["EFogCurve"]:
                            wm.EFogCurve = mat["EFogCurve"]
                        
                        box_row = box.row()
                        box_row.prop(wm, "EFogColorStyle", text = '')
                        if wm.EFogColorStyle!= mat["EFogColorStyle"]:
                            wm.EFogColorStyle = mat["EFogColorStyle"]
                            
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
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        nodes = ob.active_material.node_tree.nodes
        nodes["Diffuse Texture"].image = self.diffuseTexture
        nodes["Branch Seam Diffuse Texture"].image = self.diffuseTexture
        if self.diffuseTexture:
            nodes["Diffuse Texture"].image.colorspace_settings.name='sRGB'
            nodes["Branch Seam Diffuse Texture"].image.colorspace_settings.name='sRGB'
                
def updateNormalTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        nodes = ob.active_material.node_tree.nodes
        nodes["Normal Texture"].image = self.normalTexture
        nodes["Branch Seam Normal Texture"].image = self.normalTexture
        if self.normalTexture:
            nodes["Normal Texture"].image.colorspace_settings.name='Non-Color'
            nodes["Branch Seam Normal Texture"].image.colorspace_settings.name='Non-Color'
                
def updateDetailTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        nodes = ob.active_material.node_tree.nodes
        nodes["Detail Texture"].image = self.detailTexture
        nodes["Branch Seam Detail Texture"].image = self.detailTexture
        if self.detailTexture:
            nodes["Detail Texture"].image.colorspace_settings.name='sRGB'
            nodes["Branch Seam Detail Texture"].image.colorspace_settings.name='sRGB'
                
def updateDetailNormalTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        nodes = ob.active_material.node_tree.nodes
        nodes["Detail Normal Texture"].image = self.detailNormalTexture
        nodes["Branch Seam Detail Normal Texture"].image = self.detailNormalTexture
        if self.detailNormalTexture:
            nodes["Detail Normal Texture"].image.colorspace_settings.name='Non-Color'
            nodes["Branch Seam Detail Normal Texture"].image.colorspace_settings.name='Non-Color'
                
def updateSpecularTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        nodes = ob.active_material.node_tree.nodes 
        nodes["Specular Texture"].image = self.specularTexture
        nodes["Branch Seam Specular Texture"].image = self.specularTexture
        if self.specularTexture:
            nodes["Specular Texture"].image.colorspace_settings.name='Non-Color'
            nodes["Branch Seam Specular Texture"].image.colorspace_settings.name='Non-Color'
            
def updateVAmbientColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Ambient Color"].outputs["Color"].default_value = self.VAmbientColor
            
def updateEAmbientContrast(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        mat["EAmbientContrast"] = self.EAmbientContrast
        tree = mat.node_tree
        links = tree.links
        nodes = tree.nodes
        input1 = nodes['Ambient Contrast'].inputs["Fac"]
        while input1.links:
            links.remove(input1.links[0])
        if self.EAmbientContrast in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
            links.new(nodes['Ambient Contrast Factor'].outputs["Value"], input1)
                
def updateFAmbientContrastFactor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Ambient Contrast Factor"].outputs["Value"].default_value = self.FAmbientContrastFactor
            
def updateBAmbientOcclusion(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        tree = mat.node_tree
        links = tree.links
        nodes = tree.nodes
        input1 = nodes["Ambient Occlusion"].inputs["Color"]
        while input1.links:
            links.remove(input1.links[0])
        if self.BAmbientOcclusion:
            links.new(nodes["Ambient Occlusion Attribute"].outputs["Fac"], input1)
                
def updateVDiffuseColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Diffuse Color"].outputs["Color"].default_value = self.VDiffuseColor
            
def updateFDiffuseScalar(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Diffuse Scalar"].outputs["Value"].default_value = self.FDiffuseScalar
            
def updateBDiffuseAlphaMaskIsOpaque(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if self.BDiffuseAlphaMaskIsOpaque:
            ob.active_material.blend_method = 'OPAQUE'
        else:
            ob.active_material.blend_method = 'CLIP'
                
def updateEDetailLayer(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        mat["EDetailLayer"] = self.EDetailLayer
        tree = mat.node_tree
        links = tree.links
        nodes = tree.nodes
        input1 = nodes['Mix Detail Diffuse'].inputs["Fac"]
        input2 = nodes['Mix Detail Normal'].inputs["Fac"]
        while input1.links or input2.links:
            links.remove(input1.links[0])
            links.remove(input2.links[0])
        if self.EDetailLayer in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
            links.new(nodes["Mix Detail Alpha Seam Blending"].outputs["Color"], input1)
            links.new(nodes['Mix Detail Normal Alpha Seam Blending'].outputs["Color"], input2)
                
def updateESpecular(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        mat["ESpecular"] = self.ESpecular
        tree = mat.node_tree
        links = tree.links
        nodes = tree.nodes
        input1 = nodes['Specular BSDF'].inputs['Roughness']
        input2 = nodes["Mix Specular Color"].inputs['Color2']
        while input1.links or input2.links:
            links.remove(input1.links[0])
            links.remove(input2.links[0])
        if self.ESpecular in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
            links.new(nodes["Invert Shininess"].outputs["Color"], input1)
            links.new(nodes['Specular Color'].outputs["Color"], input2)
                
def updateFShininess(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Shininess"].outputs["Value"].default_value = self.FShininess
            
def updateVSpecularColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Specular Color"].outputs["Color"].default_value = self.VSpecularColor
            
def updateETransmission(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        mat["ETransmission"] = self.ETransmission
        tree = mat.node_tree
        links = tree.links
        nodes = tree.nodes
        input1 = nodes["Mix Transmission Color"].inputs["Color2"]
        input2 = nodes["Mix Shader Fresnel"].inputs["Fac"]
        input3 = nodes["Mix Shadow Brightness"].inputs["Fac"]
        while input1.links or input2.links or input3.links:
            links.remove(input1.links[0])
            links.remove(input2.links[0])
            links.remove(input3.links[0])
        if self.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
            links.new(nodes["Transmission Color Brightness"].outputs["Color"], input1)
            links.new(nodes['Transmission Fresnel'].outputs["Fac"], input2)
            links.new(nodes['Transmission Shadow Brightness'].outputs["Value"], input3)
                
def updateVTransmissionColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Transmission Color"].outputs["Color"].default_value = self.VTransmissionColor
            
def updateFTransmissionShadowBrightness(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes['Transmission Shadow Brightness'].outputs["Value"].default_value = self.FTransmissionShadowBrightness
            
def updateFTransmissionViewDependency(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Transmission View Dependency"].outputs["Value"].default_value = self.FTransmissionViewDependency
            
def updateEBranchSeamSmoothing(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        mat["EBranchSeamSmoothing"] = self.EBranchSeamSmoothing
        tree = mat.node_tree
        links = tree.links
        nodes = tree.nodes
        weight_mult_output = nodes['Branch Seam Weight Mult'].outputs['Value']
        while weight_mult_output.links:
            links.remove(weight_mult_output.links[0])
        if self.EBranchSeamSmoothing in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
            links.new(weight_mult_output, nodes['Mix Diffuse Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Diffuse Alpha Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Normal Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Normal Alpha Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Detail Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Detail Alpha Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Detail Normal Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Detail Normal Alpha Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Specular Seam Blending'].inputs["Fac"])
            links.new(weight_mult_output, nodes['Mix Specular Alpha Seam Blending'].inputs["Fac"])
                
def updateFBranchSeamWeight(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Branch Seam Weight"].outputs["Value"].default_value = self.FBranchSeamWeight
            
def updateEFaceCulling(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        mat = ob.active_material
        mat["EFaceCulling"] = self.EFaceCulling
        if self.EFaceCulling == "CULLTYPE_BACK":
            mat.use_backface_culling = True
        else:
            mat.use_backface_culling = False
                
def updateBBlending(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BBlending"] = self.BBlending
            
def updateEAmbientImageLighting(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["EAmbientImageLighting"] = self.EAmbientImageLighting
            
def updateEHueVariation(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["EHueVariation"] = self.EHueVariation
            
def updateEFogCurve(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["EFogCurve"] = self.EFogCurve
            
def updateEFogColorStyle(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["EFogColorStyle"] = self.EFogColorStyle
            
def updateBCastsShadows(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if self.BCastsShadows:
            ob.active_material.shadow_method = 'CLIP'
        else:
            ob.active_material.shadow_method = 'NONE'
                
def updateBReceivesShadows(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BReceivesShadows"] = self.BReceivesShadows
            
def updateBShadowSmoothing(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BShadowSmoothing"] = self.BShadowSmoothing
    
def updateFAlphaScalar(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material.node_tree.nodes["Alpha Scalar"].outputs["Value"].default_value = self.FAlphaScalar
            
def updateEWindLod(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["EWindLod"] = self.EWindLod
            
def updateBBranchesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BBranchesPresent"] = self.BBranchesPresent
        
def updateBFrondsPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BFrondsPresent"] = self.BFrondsPresent
            
def updateBLeavesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BLeavesPresent"] = self.BLeavesPresent
            
def updateBFacingLeavesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BFacingLeavesPresent"] = self.BFacingLeavesPresent
            
def updateBRigidMeshesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        ob.active_material["BRigidMeshesPresent"] = self.BRigidMeshesPresent
     
PROPS_Material_Panel = [
("diffuseTexture", PointerProperty(
        type=bpy.types.Image,
        update = updateDiffuseTexture,
        name="Diffuse Texture",
        description="Set the diffuse texture used by the selected material"
    )),
("normalTexture", PointerProperty(
        type=bpy.types.Image,
        update = updateNormalTexture,
        name="Normal Texture",
        description="Set the normal texture used by the selected material"
    )),
("detailTexture", PointerProperty(
        type=bpy.types.Image,
        update = updateDetailTexture,
        name="Detail Texture",
        description="Set the detail texture used by the selected material"
    )),
("detailNormalTexture", PointerProperty(
        type=bpy.types.Image,
        update = updateDetailNormalTexture,
        name="Detail Normal Texture",
        description="Set the detail normal texture used by the selected material"
    )),
("specularTexture", PointerProperty(
        type=bpy.types.Image,
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
            ('EFFECT_OFF', "EFFECT_OFF", "Disable ambient contrast"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable ambient contrast only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable ambient contrast"))
    )),
("FAmbientContrastFactor", FloatProperty(
        name="Ambient Contrast Factor",
        update = updateFAmbientContrastFactor,
        description="Set the ambient contrast factor !!! NOT SUPPORTED IN BLENDER !!!",
        precision = 4
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
        precision = 4
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
            ('EFFECT_OFF', "EFFECT_OFF", "Disable detail layer"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable detail layer only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable detail layer"))
    )),
("ESpecular", EnumProperty(
        name="Specular",
        update = updateESpecular,
        description="Add a specular effect",
        items=(
            ('EFFECT_OFF', "EFFECT_OFF", "Disable specular"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable specular only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable specular"))
    )),
("FShininess", FloatProperty(
        name="Shininess",
        update = updateFShininess,
        description="Set the shininess",
        precision = 4
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
            ('EFFECT_OFF', "EFFECT_OFF", "Disable transmission"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable transmission only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable transmission"))
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
        precision = 4
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
            ('EFFECT_OFF', "EFFECT_OFF", "Disable branch seam smoothing"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable branch seam smoothing only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable branch seam smoothing"))
    )),
("FBranchSeamWeight", FloatProperty(
        name="Branch Seam Weight",
        update = updateFBranchSeamWeight,
        description="Adjust how “dense” the blend area is in the blend computation",
        precision = 4
    )),
("EFaceCulling", EnumProperty(
        name="Face Culling",
        update = updateEFaceCulling,
        description="Set the culling method of the selected material",
        items=(
            ('CULLTYPE_NONE', "CULLTYPE_NONE", "Disable face culling"),
            ('CULLTYPE_BACK', "CULLTYPE_BACK", "Enable backface culling"),
            ('CULLTYPE_FRONT', "CULLTYPE_FRONT", "Enable frontface culling !!! NOT SUPPORTED IN BLENDER !!!"))
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
            ('EFFECT_OFF', "EFFECT_OFF", "Disable ambient image lighting"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable ambient image lighting only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable ambient image lighting"))
    )),
("EHueVariation", EnumProperty(
        name="Hue Variation",
        update = updateEHueVariation,
        description="Add semi-random hues to individual instances of the selected material !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('EFFECT_OFF', "EFFECT_OFF", "Disable hue variation"),
            ('EFFECT_OFF_X_ON', "EFFECT_OFF_X_ON", "Enable hue variation only where needed? Considered ON in Blender"),
            ('EFFECT_ON', "EFFECT_ON", "Enable hue variation"))
    )),
("EFogCurve", EnumProperty(
        name="Fog Curve",
        update = updateEFogCurve,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('FOG_CURVE_NONE', "FOG_CURVE_NONE", "Disable fog curve"),
            ('FOG_CURVE_LINEAR', "FOG_CURVE_LINEAR", "Enable the linear fog curve"))
    )),
("EFogColorStyle", EnumProperty(
        name="Fog Color Style",
        update = updateEFogColorStyle,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('FOG_COLOR_TYPE_CONSTANT', "FOG_COLOR_TYPE_CONSTANT", "Make the fog color constant along the curve?"),
            ('FOG_COLOR_TYPE_DYNAMIC', "FOG_COLOR_TYPE_DYNAMIC", "Make the fog color dynamic along the curve?"))
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
        precision = 4
    )),
("EWindLod", EnumProperty(
        name="Wind Lod",
        update = updateEWindLod,
        description="No idea !!! NOT SUPPORTED IN BLENDER !!!",
        items=(
            ('WIND_LOD_NONE', "WIND_LOD_NONE", "No idea"),
            ('WIND_LOD_NONE_X_BRANCH', "WIND_LOD_NONE_X_BRANCH", "No idea"),
            ('WIND_LOD_GLOBAL', "WIND_LOD_GLOBAL", "No idea"),
            ('WIND_LOD_GLOBAL_X_BRANCH', 'WIND_LOD_GLOBAL_X_BRANCH', "No idea"),
            ('WIND_LOD_BRANCH_X_FULL', 'WIND_LOD_BRANCH_X_FULL', "No idea"),
            ('WIND_LOD_FULL', 'WIND_LOD_FULL', "No idea"))
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