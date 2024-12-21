# -*- coding: utf-8 -*-
# ui/vertex_panel.py

import bpy
import numpy as np
import bmesh
from bpy.props import FloatProperty, FloatVectorProperty, BoolProperty
from io_mesh_srt.utils import GetCollection
        
class SpeedTreeVertexPropertiesPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_vertex_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Vertex Properties'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
        if wm.SpeedTreeSubPanel == 'vertex':
            main_coll = GetCollection(make_active=False)
            if main_coll:
                
                layout = self.layout
                row = layout.row()
                check_lod = wm.previewLod
                if check_lod:
                    icon = 'PAUSE'
                    txt = 'Disable LOD Preview'
                else:
                    icon = "PLAY"
                    txt = 'Enable LOD Preview'
                row.prop(wm, "previewLod", text = txt, toggle = True, icon = icon)
                
                obj = context.active_object
                if obj:
                    if "SpeedTreeTag" in obj and obj["SpeedTreeTag"] == 1:
                        mesh = obj.data
                        check_edit = mesh.is_editmode
                        check_history = None
                        check_mat_facing = False
                        check_mat_leaves = False
                        if check_edit:
                            bm = bmesh.from_edit_mesh(mesh)
                            bm.verts.ensure_lookup_table()
                            check_history = bm.select_history.active
                            if check_history:
                                f_index = bm.select_history.active.link_faces[0].index
                                mat = mesh.materials[mesh.polygons[f_index].material_index]
                                check_mat_facing = 'BFacingLeavesPresent' in mat and mat['BFacingLeavesPresent']
                                check_mat_leaves = 'BLeavesPresent' in mat and mat['BLeavesPresent']
                        
                        row = layout.row()
                        box = row.box()
                        box_row = box.row()
                        box_row.label(text="Vertex LOD Position")
                        box_row = box.row()    
                        col = box_row.column()
                        col.enabled = check_lod and check_edit and check_history is not None 
                        col.prop(wm, "vertexLodPosition", text = "")
                                
                        row = layout.row()
                        box = row.box()
                        box_row = box.row()
                        box_row.label(text="Facing Leaves")
                        box_row = box.row()
                        box_row.enabled = check_mat_facing and check_edit and check_history is not None 
                        col = box_row.column()
                        col.prop(wm, "leafCardCornerTransform", text = "Leaf Card Corner Transform")
                        
                        box_row = box.row()
                        box_row.enabled = check_mat_facing and check_lod and check_edit and check_history is not None 
                        box_row.prop(wm, "leafCardLodScalar", text="Leaf Card LOD Scalar")
                        
                        row = layout.row()
                        box = row.box()
                        box_row = box.row()
                        box_row.label(text="Leaves")
                        box_row = box.row()
                        box_row.enabled = check_mat_leaves and check_edit and check_history is not None 
                        col = box_row.column()
                        col.prop(wm, "leafAnchorPoint", text = "Leaf Anchor Point")
                        
                        if check_edit and check_history is not None:
                            bm = bmesh.from_edit_mesh(mesh)
                            bm.verts.ensure_lookup_table()
                            v_index = check_history.index
                            
                            if check_mat_facing:
                                if wm.leafCardCornerTransform != bm.verts[v_index][bm.verts.layers.float_vector['leafCardCorner']]:
                                    wm.leafCardCornerTransform = bm.verts[v_index][bm.verts.layers.float_vector['leafCardCorner']]
                                    
                                if check_lod:
                                    if wm.leafCardLodScalar != bm.verts[v_index][bm.verts.layers.float['leafCardLodScalar']]:
                                        wm.leafCardLodScalar = bm.verts[v_index][bm.verts.layers.float['leafCardLodScalar']]
                                            
                            if check_mat_leaves:
                                if wm.leafAnchorPoint != bm.verts[v_index][bm.verts.layers.float_vector['leafAnchorPoint']]:
                                    wm.leafAnchorPoint = bm.verts[v_index][bm.verts.layers.float_vector['leafAnchorPoint']]
                            
                            if check_lod:
                                if wm.vertexLodPosition != mesh.vertices[v_index].co:
                                    wm.vertexLodPosition = mesh.vertices[v_index].co
                                    bm = bmesh.from_edit_mesh(mesh)
                                    bm.verts.ensure_lookup_table()
                                    bm.verts[v_index][bm.verts.layers.float_vector['vertexLodPosition']] = mesh.vertices[v_index].co
                                        
            return
        
def updateVertexLodPosition(self, context):
    mesh = bpy.context.active_object.data
    bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    count = len(mesh.vertices)
    sel = np.zeros(count, dtype=bool)
    mesh.vertices.foreach_get('select', sel)
    v_index = list(sel).index(True)
    mesh.attributes['vertexLodPosition'].data[v_index].vector = self.vertexLodPosition
    mesh.vertices[v_index].co = self.vertexLodPosition
    bpy.ops.object.mode_set(mode='EDIT', toggle = False)
    
def updateLeafCorner(self, context):
    mesh = bpy.context.active_object.data
    bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    count = len(mesh.vertices)
    sel = np.zeros(count, dtype=bool)
    mesh.vertices.foreach_get('select', sel)
    v_index = list(sel).index(True)
    mesh.attributes['leafCardCorner'].data[v_index].vector = self.leafCardCornerTransform
    bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateLeafCardScalar(self, context):
    mesh = bpy.context.active_object.data
    bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    count = len(mesh.vertices)
    sel = np.zeros(count, dtype=bool)
    mesh.vertices.foreach_get('select', sel)
    v_index = list(sel).index(True)
    mesh.attributes['leafCardLodScalar'].data[v_index].value = self.leafCardLodScalar
    bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateLeafAnchorPoint(self, context):
    mesh = bpy.context.active_object.data
    bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    count = len(mesh.vertices)
    sel = np.zeros(count, dtype=bool)
    mesh.vertices.foreach_get('select', sel)
    v_index = list(sel).index(True)
    mesh.attributes['leafAnchorPoint'].data[v_index].vector = self.leafAnchorPoint
    bpy.ops.object.mode_set(mode='EDIT', toggle = False)
    
def updateLodPreview(self, context):
    prev_mode = bpy.context.mode
    if bpy.data.objects:
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False) 
        
        for obj in bpy.data.objects:
            if "SpeedTreeTag" in obj and obj["SpeedTreeTag"] == 1:
                mesh = obj.data
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
                            
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
                            
    if prev_mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
     
PROPS_Vertex_Panel = [
("vertexLodPosition", FloatVectorProperty(
        name="Vertex LOD Position",
        update = updateVertexLodPosition,
        description="Set the LOD position of the selected vertex",
        subtype = 'COORDINATES',
        precision = 6
    )),
("leafCardCornerTransform", FloatVectorProperty(
        name="Leaf Card Corner Transform",
        update = updateLeafCorner,
        description="Set the transform of the leaf card corner of the selected vertex",
        subtype = 'COORDINATES',
        precision = 6
    )),
("leafCardLodScalar", FloatProperty(
        name="Leaf Card Lod Scalar",
        update = updateLeafCardScalar,
        description="Set the leaf card lod system scalar of the selected vertex",
        precision = 6
    )),
("leafAnchorPoint", FloatVectorProperty(
        name="Leaf Anchor Point",
        update = updateLeafAnchorPoint,
        description="Set the anchor point of the selected vertex",
        subtype = 'COORDINATES',
        precision = 6
    )),
("previewLod", BoolProperty(
        name="Preview LOD",
        update = updateLodPreview,
        description="Enable/disable LOD Previewing",
        default = False
    ))
]

CLASSES_Vertex_Panel = [SpeedTreeVertexPropertiesPanel]