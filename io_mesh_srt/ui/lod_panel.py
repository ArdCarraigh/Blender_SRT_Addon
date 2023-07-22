# -*- coding: utf-8 -*-
# ui/lod_panel.py

import bpy
import numpy as np
from bpy.props import BoolProperty, FloatProperty
from io_mesh_srt.utils import GetCollection
    
class SpeedTreeLODPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_lod_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree LOD System'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'lod':
            
            layout = self.layout
            main_coll = GetCollection(make_active=False)      
            if main_coll:
                row = layout.row()
                box = row.box()
                box.label(text = 'LOD Profile')
                box_row = box.row()
                box_row.prop(wm, "m_f3dRange", text = "3D Range")
                if wm.m_f3dRange != main_coll['m_f3dRange']:
                    wm.m_f3dRange = main_coll['m_f3dRange']
                
                box_row = box.row()    
                box_row.prop(wm, "m_fHighDetail3dDistance", text = "High Detail 3D Distance")
                if wm.m_fHighDetail3dDistance != main_coll['m_fHighDetail3dDistance']:
                    wm.m_fHighDetail3dDistance = main_coll['m_fHighDetail3dDistance']
                
                box_row = box.row()  
                box_row.prop(wm, "m_fLowDetail3dDistance", text = "Low Detail 3D Distance")
                if wm.m_fLowDetail3dDistance != main_coll['m_fLowDetail3dDistance']:
                    wm.m_fLowDetail3dDistance = main_coll['m_fLowDetail3dDistance']
                
                box_row = box.row()   
                box_row.prop(wm, "m_fBillboardRange", text = "Billboard Range")
                if wm.m_fBillboardRange != main_coll['m_fBillboardRange']:
                    wm.m_fBillboardRange = main_coll['m_fBillboardRange']
                
                box_row = box.row()    
                box_row.prop(wm, "m_fBillboardStartDistance", text = "Billboard Start Distance")
                if wm.m_fBillboardStartDistance != main_coll['m_fBillboardStartDistance']:
                    wm.m_fBillboardStartDistance = main_coll['m_fBillboardStartDistance']
                
                box_row = box.row()
                box_row.prop(wm, "m_fBillboardFinalDistance", text = "Billboard End Distance")
                if wm.m_fBillboardFinalDistance != main_coll['m_fBillboardFinalDistance']:
                    wm.m_fBillboardFinalDistance = main_coll['m_fBillboardFinalDistance']
                    
            row = layout.row()
            box = row.box()
            box.prop(wm, "previewLod", text = 'Preview LOD')
        
        return
    
def updatem_f3dRange(self, context):
    main_coll = GetCollection(make_active=False)     
    if main_coll:
        main_coll["m_f3dRange"] = self.m_f3dRange
        
def updatem_fHighDetail3dDistance(self, context):
    main_coll = GetCollection(make_active=False)    
    if main_coll:
        main_coll["m_fHighDetail3dDistance"] = self.m_fHighDetail3dDistance
        
def updatem_fLowDetail3dDistance(self, context):
    main_coll = GetCollection(make_active=False)     
    if main_coll:
        main_coll["m_fLowDetail3dDistance"] = self.m_fLowDetail3dDistance
        
def updatem_fBillboardRange(self, context):
    main_coll = GetCollection(make_active=False)    
    if main_coll:
        main_coll["m_fBillboardRange"] = self.m_fBillboardRange
        
def updatem_fBillboardStartDistance(self, context):
    main_coll = GetCollection(make_active=False)  
    if main_coll:
        main_coll["m_fBillboardStartDistance"] = self.m_fBillboardStartDistance
        
def updatem_fBillboardFinalDistance(self, context):
    main_coll = GetCollection(make_active=False)     
    if main_coll:
        main_coll["m_fBillboardFinalDistance"] = self.m_fBillboardFinalDistance
            
def updateLodPreview(self, context):
    prev_mode = bpy.context.mode
    if bpy.data.objects:
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False) 
        
        for obj in bpy.data.objects:
            mesh = obj.data
            if "SpeedTreeTag" in mesh:
                if mesh["SpeedTreeTag"] == 1:
                    geom_nodes = obj.modifiers[0]
                    vector_math = geom_nodes.node_group.nodes["Vector Math"]
                    n_vert = len(mesh.vertices) * 3 
                    vert_array = np.zeros(n_vert)
                    lod_vert_array = np.zeros(n_vert)
                    if self.previewLod:
                        mesh.attributes["position"].data.foreach_get("vector", vert_array)
                        mesh.attributes['vertexPosition'].data.foreach_set("vector", vert_array)
                        mesh.attributes["vertexLodPosition"].data.foreach_get("vector", lod_vert_array)
                        mesh.attributes["position"].data.foreach_set("vector", lod_vert_array)
                        leaf_card_lod_scalar = geom_nodes.node_group.nodes['Leaf Card LOD Scalar']
                        geom_nodes.node_group.links.new(leaf_card_lod_scalar.outputs['Attribute'], vector_math.inputs[1])
                    else:
                        mesh.attributes["position"].data.foreach_get("vector", lod_vert_array)
                        mesh.attributes['vertexLodPosition'].data.foreach_set("vector", lod_vert_array)
                        mesh.attributes["vertexPosition"].data.foreach_get("vector", vert_array)
                        mesh.attributes["position"].data.foreach_set("vector", vert_array)
                        if vector_math.inputs[1].links:
                            geom_nodes.node_group.links.remove(vector_math.inputs[1].links[0])
                            
    if prev_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
     
PROPS_Lod_Panel = [
('m_f3dRange', FloatProperty(
        name="3D Range",
        description="Set the distance from which meshes are enabled",
        update = updatem_f3dRange,
        default = 0,
        min = 0,
        precision = 4
    )),
('m_fHighDetail3dDistance', FloatProperty(
        name="High Detail 3D Distance",
        description="Set the distance at which lod0 is no longer used",
        update = updatem_fHighDetail3dDistance,
        default = 10,
        min = 0,
        precision = 4
    )),
('m_fLowDetail3dDistance', FloatProperty(
        name="Low Detail 3D Distance",
        description="Set the distance at which lod2 gets used",
        update = updatem_fLowDetail3dDistance,
        default = 30,
        min = 0,
        precision = 4
    )),
('m_fBillboardRange', FloatProperty(
        name="Billboard Range",
        description="Set the distance from which billboard is enabled",
        update = updatem_fBillboardRange,
        default = 0,
        min = 0,
        precision = 4
    )),
('m_fBillboardStartDistance', FloatProperty(
        name="Billboard Start Distance",
        description="Set the distance at which billboard starts to get used",
        update = updatem_fBillboardStartDistance,
        default = 80,
        min = 0,
        precision = 4
    )), 
('m_fBillboardFinalDistance', FloatProperty(
        name="Billboard End Distance",
        description="Set the distance at which billboard disappears",
        update = updatem_fBillboardFinalDistance,
        default = 100,
        min = 0,
        precision = 4
    )),
("previewLod", BoolProperty(
        name="Preview LOD",
        update = updateLodPreview,
        description="Enable/disable LOD Previewing",
        default = False
    ))
]

CLASSES_Lod_Panel = [SpeedTreeLODPanel]