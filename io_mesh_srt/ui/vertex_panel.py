# -*- coding: utf-8 -*-
# ui/vertex_panel.py

import bpy
import numpy as np
import bmesh
from bpy.props import FloatProperty, FloatVectorProperty
        
class SpeedTreeVertexPropertiesPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_vertex_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Vertex Properties'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'vertex':
            
            layout = self.layout
            layout.label(text = "Vertex LOD Position (requires previewing LOD)")
            if wm.previewLod:
                me = context.active_object
                if me:
                    mesh = me.data
                    if "SpeedTreeTag" in mesh:
                        if mesh["SpeedTreeTag"] == 1:
                            if mesh.is_editmode:
                                bm = bmesh.from_edit_mesh(mesh)
                                bm.verts.ensure_lookup_table()
                                if bm.select_history.active is not None:
                                    v_index = bm.select_history.active.index
                                    row = layout.row()
                                    col = row.column()
                                    col.prop(wm, "vertexLodPosition", text = "")
                                    if wm.vertexLodPosition != mesh.vertices[v_index].co:
                                        wm.vertexLodPosition = mesh.vertices[v_index].co
                                        bm = bmesh.from_edit_mesh(mesh)
                                        bm.verts.ensure_lookup_table()
                                        bm.verts[v_index][bm.verts.layers.float_vector['vertexLodPosition']] = mesh.vertices[v_index].co
                                    
        return
    
class SpeedTreeFacingLeavesPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_facing_leaves_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_vertex_panel'
    bl_label = 'Facing Leaves'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'vertex':
            
            layout = self.layout
            me = context.active_object
            if me:
                mesh = me.data
                if "SpeedTreeTag" in mesh:
                    if mesh["SpeedTreeTag"] == 1:
                        if mesh.is_editmode:
                            bm = bmesh.from_edit_mesh(mesh)
                            bm.verts.ensure_lookup_table()
                            if bm.select_history.active is not None:
                                v_index = bm.select_history.active.index
                                f_index = bm.select_history.active.link_faces[0].index
                                mat = mesh.materials[mesh.polygons[f_index].material_index]
                                if mat['BFacingLeavesPresent']:
                                    layout.label(text = "Facing Leaves")
                                    row = layout.row()
                                    col = row.column()
                                    col.prop(wm, "leafCardCornerTransform", text = "Leaf Card Corner Transform")
                                    if wm.leafCardCornerTransform != bm.verts[v_index][bm.verts.layers.float_vector['leafCardCorner']]:
                                        wm.leafCardCornerTransform = bm.verts[v_index][bm.verts.layers.float_vector['leafCardCorner']]
                                        
                                    if wm.previewLod:
                                        row = layout.row()
                                        row.label(text="Leaf Card LOD Scalar")
                                        row = layout.row()
                                        row.prop(wm, "leafCardLodScalar", text="")
                                        if wm.leafCardLodScalar != bm.verts[v_index][bm.verts.layers.float['leafCardLodScalar']]:
                                            wm.leafCardLodScalar = bm.verts[v_index][bm.verts.layers.float['leafCardLodScalar']]
                        
class SpeedTreeLeavesPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_leaves_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_vertex_panel'
    bl_label = 'Leaves'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager
        if wm.SpeedTreeSubPanel == 'vertex':
            
            layout = self.layout
            me = context.active_object
            if me:
                mesh = me.data
                if "SpeedTreeTag" in mesh:
                    if mesh["SpeedTreeTag"] == 1:
                        if mesh.is_editmode:
                            bm = bmesh.from_edit_mesh(mesh)
                            bm.verts.ensure_lookup_table()
                            if bm.select_history.active is not None:
                                v_index = bm.select_history.active.index
                                f_index = bm.select_history.active.link_faces[0].index
                                mat = mesh.materials[mesh.polygons[f_index].material_index]
                                if mat['BLeavesPresent']:
                                    layout.separator()
                                    layout.label(text = "Leaves")
                                    row = layout.row()
                                    col = row.column()
                                    col.prop(wm, "leafAnchorPoint", text = "Leaf Anchor Point")
                                    if wm.leafAnchorPoint != bm.verts[v_index][bm.verts.layers.float_vector['leafAnchorPoint']]:
                                        wm.leafAnchorPoint = bm.verts[v_index][bm.verts.layers.float_vector['leafAnchorPoint']]
        
def updateVertexLodPosition(self, context):
    mesh = bpy.context.active_object.data
    if "SpeedTreeTag" in mesh:
        if mesh["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(mesh.vertices)
            sel = np.zeros(count, dtype=np.bool)
            mesh.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            mesh.attributes['vertexLodPosition'].data[v_index].vector = self.vertexLodPosition
            mesh.vertices[v_index].co = self.vertexLodPosition
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
    
def updateLeafCorner(self, context):
    mesh = bpy.context.active_object.data
    if "SpeedTreeTag" in mesh:
        if mesh["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(mesh.vertices)
            sel = np.zeros(count, dtype=np.bool)
            mesh.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            mesh.attributes['leafCardCorner'].data[v_index].vector = self.leafCardCornerTransform
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateLeafCardScalar(self, context):
    mesh = bpy.context.active_object.data
    if "SpeedTreeTag" in mesh:
        if mesh["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(mesh.vertices)
            sel = np.zeros(count, dtype=np.bool)
            mesh.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            mesh.attributes['leafCardLodScalar'].data[v_index].value = self.leafCardLodScalar
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateLeafAnchorPoint(self, context):
    mesh = bpy.context.active_object.data
    if "SpeedTreeTag" in mesh:
        if mesh["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(mesh.vertices)
            sel = np.zeros(count, dtype=np.bool)
            mesh.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            mesh.attributes['leafAnchorPoint'].data[v_index].vector = self.leafAnchorPoint
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
     
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
    ))
]

CLASSES_Vertex_Panel = [SpeedTreeVertexPropertiesPanel, SpeedTreeFacingLeavesPanel, SpeedTreeLeavesPanel]