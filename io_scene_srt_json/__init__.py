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
import numpy as np
import bmesh
import re
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty, CollectionProperty
from bpy.types import Operator
from io_scene_srt_json import import_srt_json
from io_scene_srt_json.import_srt_json import read_srt_json
from io_scene_srt_json import export_srt_json
from io_scene_srt_json.export_srt_json import write_srt_json
from io_scene_srt_json.tools import add_srt_sphere 
from io_scene_srt_json.tools.add_srt_sphere import add_srt_sphere, remove_srt_sphere
from io_scene_srt_json.tools import add_srt_connection
from io_scene_srt_json.tools.add_srt_connection import add_srt_connection
from io_scene_srt_json.tools import srt_mesh_setup
from io_scene_srt_json.tools.srt_mesh_setup import srt_mesh_setup, get_parent_collection
from io_scene_srt_json.tools import generate_srt_billboards
from io_scene_srt_json.tools.generate_srt_billboards import generate_srt_billboards, generate_srt_horizontal_billboard

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

    def execute(self, context):
        
        # Should work from all modes
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        
        write_srt_json(context, self.filepath)
        
        return {'FINISHED'}
    
class AddSRTCollisionSphere(Operator):
    """Create a new Collision Sphere"""
    bl_idname = "speed_tree.add_srt_collision_sphere"
    bl_label = "Add Collision Sphere"
    bl_options = {'REGISTER', 'UNDO'}

    radius: FloatProperty(
        name="Radius",
        default = 0.15,
        description="Set the radius of the sphere"
    )
    location: FloatVectorProperty(
        name="Location",
        default=(0.0, 0.0, 0.0),
        description="Set the location of the sphere",
        subtype = 'COORDINATES'
    )

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        add_srt_sphere(context, self.radius, self.location)
        return {'FINISHED'}
    
class RemoveSRTCollisionObject(Operator):
    """Remove a Collision Object"""
    bl_idname = "speed_tree.remove_srt_collision_object"
    bl_label = "Remove Collision Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        remove_srt_sphere(context)
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
    
class SRTMeshSetup(Operator):
    """Set Up a SRT Asset"""
    bl_idname = "speed_tree.srt_mesh_setup"
    bl_label = "Set Up a SRT Asset"
    bl_options = {'REGISTER', 'UNDO'}
    
    apply_geom_type: BoolProperty(
        name="Apply Geometry Type to Vertices",
        description="Enable per vertex definition of geometry type",
        default = False
    )
    
    geom_type: EnumProperty(
        name="Geometry Type",
        description="Set the geometry type of the mesh",
        items=(
            ('0.2', "Branches", "Set the mesh as branches"),
            ('0.4', "Fronds", "Set the mesh as fronds"),
            ('0.6', "Leaves", "Set the mesh as leaves"),
            ('0.8', "Facing Leaves", "Set the mesh as facing leaves"),
            ('1.0', "Rigid Meshes", "Set the mesh as rigid meshes")
        ),
        default='0.2'
    )

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        srt_mesh_setup(context, self.apply_geom_type, self.geom_type)
        return {'FINISHED'}

class SpeedTreeMainPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_idname = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        layout.operator(SRTMeshSetup.bl_idname, text = "Set Up a SRT Asset", icon = "WORLD")
        return
    
class SpeedTreeGeneralSettings(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_settings_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree General Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        active_coll = bpy.context.view_layer.active_layer_collection
        parent_colls = []
        main_coll = []
        bb_coll = []
        horiz_coll = []
        get_parent_collection(active_coll, parent_colls)
        if re.search("SRT Asset", active_coll.name):
            main_coll = active_coll.collection
        elif parent_colls:
            if re.search("SRT Asset", parent_colls[0].name):
                main_coll = parent_colls[0]
                
        if main_coll:
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
    
class SpeedTreeLODPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_lod_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree LOD System'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        active_coll = bpy.context.view_layer.active_layer_collection
        parent_colls = []
        main_coll = []
        get_parent_collection(active_coll, parent_colls)
        if re.search("SRT Asset", active_coll.name):
            main_coll = active_coll.collection
        elif parent_colls:
            if re.search("SRT Asset", parent_colls[0].name):
                main_coll = parent_colls[0]
                
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
        
    
class SpeedTreeVertexPropertiesPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_vertex_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Vertex Properties'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        if wm.previewLod:
            me = context.active_object
            if me:
                if "SpeedTreeTag" in me.data:
                    if me.data["SpeedTreeTag"] == 1:
                        if me.data.is_editmode:
                            bm = bmesh.from_edit_mesh(me.data)
                            bm.verts.ensure_lookup_table()
                            if bm.select_history.active is not None:
                                v_index = bm.select_history.active.index
                                row = layout.row()
                                col = row.column()
                                col.prop(wm, "vertexLodPosition", text = "Vertex LOD Position")
                                if wm.vertexLodPosition != me.data.vertices[v_index].co:
                                    wm.vertexLodPosition = me.data.vertices[v_index].co
                                    me.data.attributes['vertexLodPosition'].data[v_index].vector = me.data.vertices[v_index].co
                                    
        return
    
class SpeedTreeFacingLeavesPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_facing_leaves_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_vertex_panel'
    bl_label = 'Facing Leaves'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.active_object
        if me:
            if "SpeedTreeTag" in me.data:
                if me.data["SpeedTreeTag"] == 1:
                    if me.data.is_editmode:
                        bm = bmesh.from_edit_mesh(me.data)
                        bm.verts.ensure_lookup_table()
                        if bm.select_history.active is not None:
                            v_index = bm.select_history.active.index
                            f_index = bm.select_history.active.link_faces[0].index
                            mat = me.data.materials[me.data.polygons[f_index].material_index]
                            if mat['BFacingLeavesPresent']:
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
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.active_object
        if me:
            if "SpeedTreeTag" in me.data:
                if me.data["SpeedTreeTag"] == 1:
                    if me.data.is_editmode:
                        bm = bmesh.from_edit_mesh(me.data)
                        bm.verts.ensure_lookup_table()
                        if bm.select_history.active is not None:
                            v_index = bm.select_history.active.index
                            f_index = bm.select_history.active.link_faces[0].index
                            mat = me.data.materials[me.data.polygons[f_index].material_index]
                            if mat['BLeavesPresent']:
                                row = layout.row()
                                col = row.column()
                                col.prop(wm, "leafAnchorPoint", text = "Leaf Anchor Point")
                                if wm.leafAnchorPoint != bm.verts[v_index][bm.verts.layers.float_vector['leafAnchorPoint']]:
                                    wm.leafAnchorPoint = bm.verts[v_index][bm.verts.layers.float_vector['leafAnchorPoint']]
                                    
class SPEEDTREE_UL_collisions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        coll = data
        ob = item
        icon = "NONE"
        
        if "Material_Cylinder" in ob.data.materials:
            icon = 'MESH_CAPSULE'
        else:
            icon = 'MESH_UVSPHERE'
            
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ob:
                layout.prop(ob, "name", text="", emboss=False, icon=icon)
            else:
                layout.label(text="", translate=False, icon=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon=icon)
                                        
class SpeedTreeCollisionPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_collision_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Collisions'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        active_coll = bpy.context.view_layer.active_layer_collection
        parent_colls = []
        main_coll = []
        collision_coll = []
        get_parent_collection(active_coll, parent_colls)
        if re.search("SRT Asset", active_coll.name):
            main_coll = active_coll.collection
        elif parent_colls:
            if re.search("SRT Asset", parent_colls[0].name):
                main_coll = parent_colls[0]
        
        if main_coll:
            for col in main_coll.children:
                if re.search("Collision Objects", col.name):
                    collision_coll = col
                
        if collision_coll:
            row = layout.row()
            row.template_list("SPEEDTREE_UL_collisions", "", collision_coll, "objects", wm, "SpeedTreeCollisionsIndex", rows=3)
            if bpy.context.active_object not in list(collision_coll.objects):
                wm.SpeedTreeCollisionsIndex = -1
            else:
                wm.SpeedTreeCollisionsIndex = list(collision_coll.objects).index(bpy.context.active_object)
            
        if main_coll:
            row = layout.row(align=True)
            row.operator(AddSRTCollisionSphere.bl_idname, text = "Add")
            row.operator(RemoveSRTCollisionObject.bl_idname, text = "Remove")
            
        if collision_coll:
            n = 0
            for obj in collision_coll.objects:
                if "Material_Cylinder" not in obj.data.materials:
                    n += 1
            if n>=2:
                row = layout.row()
                box = row.box()
                box.label(text="Collision Sphere Connection:")
                box_row = box.row(align=True)
                box_row.prop(wm, "collisionObject1", text = "From")
                box_row.prop(wm, "collisionObject2", text = "To")
                box_row = box.row()
                box_row.enabled = wm.collisionObject1 is not None and wm.collisionObject2 is not None
                box_row.operator(AddSRTSphereConnection.bl_idname, text = "Add Sphere Connection")
            
        return
    
class SpeedTreeBillboardsPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_billboards_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree Billboards'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        active_coll = bpy.context.view_layer.active_layer_collection
        parent_colls = []
        main_coll = []
        bb_coll = []
        horiz_coll = []
        get_parent_collection(active_coll, parent_colls)
        if re.search("SRT Asset", active_coll.name):
            main_coll = active_coll.collection
        elif parent_colls:
            if re.search("SRT Asset", parent_colls[0].name):
                main_coll = parent_colls[0]
        
        if main_coll:
            for col in main_coll.children:
                if re.search("Vertical Billboards", col.name):
                    bb_coll = col
                if re.search("Horizontal Billboard", col.name):
                    horiz_coll = col
                        
            row = layout.row()
            box = row.box()
            box_row = box.row()
            box_row.label(text="Vertical Billboards")
            box_row = box.row()
            box_row.prop(wm, "NNumBillboards", text = 'Number')
            if not bb_coll:
                wm.NNumBillboards = 0
            elif not re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects])):
                wm.NNumBillboards = 0
            else:
                bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
                bb_width = bb_coll.objects[bb_objects[0]].data.vertices[2].co[0] - bb_coll.objects[bb_objects[0]].data.vertices[0].co[0]
                bb_top = bb_coll.objects[bb_objects[0]].data.vertices[2].co[2]
                bb_bottom = bb_coll.objects[bb_objects[0]].data.vertices[0].co[2]
                number_billboards = len(bb_objects)
                ngroup = bb_coll.objects[bb_objects[0]].modifiers[0].node_group
                if wm.NNumBillboards != number_billboards:
                    wm.NNumBillboards = number_billboards
                        
                box_row = box.row()
                box_row.enabled = wm.NNumBillboards>0
                box_row.prop(wm, "FWidth", text = 'Width')
                if wm.FWidth != bb_width:
                    wm.FWidth = bb_width
                
                box_row = box.row()
                box_row.enabled = wm.NNumBillboards>0
                box_row.prop(wm, "FTopPos", text = 'Top')
                if wm.FTopPos != bb_top:
                    wm.FTopPos = bb_top
                
                box_row = box.row()
                box_row.enabled = wm.NNumBillboards>0
                box_row.prop(wm, "FBottomPos", text = 'Bottom')
                if wm.FBottomPos != bb_bottom:
                    wm.FBottomPos = bb_bottom
                    
                box_row = box.row()
                box_row.enabled = wm.NNumBillboards>0
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
            box_row.prop(wm, "BHorizontalBillboard", text = "Is Present")
            if not horiz_coll:
                wm.BHorizontalBillboard = False
            elif not horiz_coll.objects:
                wm.BHorizontalBillboard = False
            else:
                wm.BHorizontalBillboard = True
            
        return
    
class SPEEDTREE_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        coll = data
        slot = item
        ma = slot.material
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
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.active_object
        if me:
            if "SpeedTreeTag" in me.data:
                if me.data["SpeedTreeTag"] in [1,2]:
                    if me.data.materials:
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
        return
    
class SpeedTreeTexturePanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_texture_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_material_panel'
    bl_label = 'Textures'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.active_object
        if me:
            if "SpeedTreeTag" in me.data:
                if me.data["SpeedTreeTag"] in [1,2]:
                    if me.data.materials:
                        mat = me.active_material
                        ntree = mat.node_tree
                        
                        #Diffuse
                        row = layout.row()
                        box = row.box()
                        box.label(text="Diffuse Texture")
                        box.template_ID(wm, "diffuseTexture", new="image.new", open="image.open")
                        if wm.diffuseTexture != ntree.nodes["Diffuse Texture"].image:
                            wm.diffuseTexture = ntree.nodes["Diffuse Texture"].image
                            
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
                        if wm.normalTexture != ntree.nodes["Normal Texture"].image:
                            wm.normalTexture = ntree.nodes["Normal Texture"].image
                                
                        #Specular
                        row = layout.row()
                        box = row.box()
                        box.label(text="Specular Texture")
                        box.template_ID(wm, "specularTexture", new="image.new", open="image.open")
                        if wm.specularTexture != ntree.nodes["Specular Texture"].image:
                            wm.specularTexture = ntree.nodes["Specular Texture"].image
                        
                        #Branch Seam
                        row = layout.row()
                        box = row.box()
                        box.label(text = "Branch Seam Smoothing")
                        box.enabled = wm.BBranchesPresent
                        box.prop(wm, "EBranchSeamSmoothing", text = "")
                        if wm.EBranchSeamSmoothing != mat["EBranchSeamSmoothing"]:
                            wm.EBranchSeamSmoothing = mat["EBranchSeamSmoothing"]
                        if len(ntree.nodes['Branch Seam Weight Mult'].outputs['Value'].links) != 10:
                            wm.EBranchSeamSmoothing = 'EFFECT_OFF'
                             
                        box_row = box.row()
                        box_row.enabled = wm.EBranchSeamSmoothing in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FBranchSeamWeight", text = "Branch Seam Weight")
                        if wm.FBranchSeamWeight != ntree.nodes["Branch Seam Weight"].outputs["Value"].default_value:
                            wm.FBranchSeamWeight = ntree.nodes["Branch Seam Weight"].outputs["Value"].default_value
                            
                        #Detail Layer
                        row = layout.row()
                        box = row.box()
                        box.label(text = "Detail Layer")
                        box.enabled = wm.BBranchesPresent
                        box.prop(wm, "EDetailLayer", text = "")
                        if wm.EDetailLayer != mat["EDetailLayer"]:
                            wm.EDetailLayer = mat["EDetailLayer"]
                        if not ntree.nodes['Mix Detail Diffuse'].inputs["Fac"].links or not ntree.nodes['Mix Detail Normal'].inputs["Fac"].links:
                            wm.EDetailLayer = 'EFFECT_OFF'
                        
                        box_row = box.row()
                        box_row.label(text = "Detail Texture")
                        box_row.enabled = wm.EDetailLayer in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.template_ID(wm, "detailTexture", new="image.new", open="image.open")
                        if wm.detailTexture != ntree.nodes["Detail Texture"].image:
                            wm.detailTexture = ntree.nodes["Detail Texture"].image
                            
                        box_row = box.row()
                        box_row.label(text = "Detail Normal Texture")
                        box_row.enabled = wm.EDetailLayer in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.template_ID(wm, "detailNormalTexture", new="image.new", open="image.open")
                        if wm.detailNormalTexture != ntree.nodes["Detail Normal Texture"].image:
                            wm.detailNormalTexture = ntree.nodes["Detail Normal Texture"].image
                               
        return
    
class SpeedTreeColorSetPanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_SpeedTree_color_set_panel'
    bl_parent_id = 'VIEW3D_PT_SpeedTree_material_panel'
    bl_label = 'Color Set'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.active_object
        if me:
            if "SpeedTreeTag" in me.data:
                if me.data["SpeedTreeTag"] in [1,2]:
                    if me.data.materials:
                        mat = me.active_material
                        ntree = mat.node_tree
                        
                        # Diffuse Color
                        row = layout.row()
                        box = row.box()
                        box_row = box.row()
                        box_row.label(text="Diffuse Color")
                        box_row.prop(wm, "VDiffuseColor", text = "")
                        if wm.VDiffuseColor != ntree.nodes["Diffuse Color"].outputs["Color"].default_value:
                            wm.VDiffuseColor = ntree.nodes["Diffuse Color"].outputs["Color"].default_value
                            
                        box.prop(wm, "FDiffuseScalar", text = "Diffuse Scalar")
                        if wm.FDiffuseScalar != ntree.nodes["Diffuse Scalar"].outputs["Value"].default_value:
                            wm.FDiffuseScalar = ntree.nodes["Diffuse Scalar"].outputs["Value"].default_value
                            
                        #Ambient Color
                        row = layout.row()
                        box = row.box()
                        box.label(text='Ambient Contrast')
                        box.prop(wm, "EAmbientContrast", text = "")
                        if wm.EAmbientContrast != mat["EAmbientContrast"]:
                            wm.EAmbientContrast = mat["EAmbientContrast"]
                        if not ntree.nodes['Ambient Contrast'].inputs["Fac"].links:
                            wm.EAmbientContrast = 'EFFECT_OFF'
                        
                        box_row = box.row()
                        box_row.label(text="Ambient Color")
                        box_row.enabled = wm.EAmbientContrast in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "VAmbientColor", text = '')
                        if wm.VAmbientColor != ntree.nodes["Ambient Color"].outputs["Color"].default_value:
                            wm.VAmbientColor = ntree.nodes["Ambient Color"].outputs["Color"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.EAmbientContrast in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FAmbientContrastFactor", text = 'Ambient Contrast Factor')
                        if wm.FAmbientContrastFactor != ntree.nodes["Ambient Contrast Factor"].outputs["Value"].default_value:
                            wm.FAmbientContrastFactor = ntree.nodes["Ambient Contrast Factor"].outputs["Value"].default_value
                            
                        #Specular Color
                        row = layout.row()
                        box = row.box()
                        box.label(text='Specular')
                        box.prop(wm, "ESpecular", text = "")
                        if wm.ESpecular != mat["ESpecular"]:
                            wm.ESpecular = mat["ESpecular"]
                        if not ntree.nodes['Specular BSDF'].inputs['Roughness'].links or not ntree.nodes["Mix Specular Color"].inputs['Color2'].links:
                            wm.ESpecular = 'EFFECT_OFF'
                            
                        box_row = box.row()
                        box_row.label(text="Specular Color")
                        box_row.enabled = wm.ESpecular in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "VSpecularColor", text = '')
                        if wm.VSpecularColor!= ntree.nodes["Specular Color"].outputs["Color"].default_value:
                            wm.VSpecularColor = ntree.nodes["Specular Color"].outputs["Color"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.ESpecular in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FShininess", text = 'Shininess')
                        if wm.FShininess != ntree.nodes["Shininess"].outputs["Value"].default_value:
                            wm.FShininess = ntree.nodes["Shininess"].outputs["Value"].default_value
                            
                        #Transmission Color
                        row = layout.row()
                        box = row.box()
                        box.label(text='Transmission')
                        box.prop(wm, "ETransmission", text = "")
                        if wm.ETransmission != mat["ETransmission"]:
                            wm.ETransmission = mat["ETransmission"]
                        if not ntree.nodes["Mix Transmission Color"].inputs["Color2"].links or not ntree.nodes["Mix Shader Fresnel"].inputs["Fac"].links or not ntree.nodes["Mix Shadow Brightness"].inputs["Fac"].links:
                            wm.ETransmission = 'EFFECT_OFF'
                            
                        box_row = box.row()
                        box_row.label(text="Transmission Color")
                        box_row.enabled = wm.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "VTransmissionColor", text = '')
                        if wm.VTransmissionColor!= ntree.nodes["Transmission Color"].outputs["Color"].default_value:
                            wm.VTransmissionColor = ntree.nodes["Transmission Color"].outputs["Color"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FTransmissionViewDependency", text = 'View Influence')
                        if wm.FTransmissionViewDependency != ntree.nodes["Transmission View Dependency"].outputs["Value"].default_value:
                            wm.FTransmissionViewDependency = ntree.nodes["Transmission View Dependency"].outputs["Value"].default_value
                            
                        box_row = box.row()
                        box_row.enabled = wm.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]
                        box_row.prop(wm, "FTransmissionShadowBrightness", text = 'Shadow Brightness')
                        if wm.FTransmissionShadowBrightness != ntree.nodes["Transmission Shadow Brightness"].outputs["Value"].default_value:
                            wm.FTransmissionShadowBrightness = ntree.nodes["Transmission Shadow Brightness"].outputs["Value"].default_value
                            
                        #Visibility
                        row = layout.row()
                        box = row.box()
                        box.label(text='Visibility')
                        box.prop(wm, "FAlphaScalar", text = "Alpha Scalar")
                        if wm.FAlphaScalar != ntree.nodes["Alpha Scalar"].outputs["Value"].default_value:
                            wm.FAlphaScalar = ntree.nodes["Alpha Scalar"].outputs["Value"].default_value
                        
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
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.active_object
        if me:
            if "SpeedTreeTag" in me.data:
                if me.data["SpeedTreeTag"] in [1,2]:
                    if me.data.materials:
                        mat = me.active_material
                        ntree = mat.node_tree
                        
                        #Supported
                        row = layout.row()
                        box = row.box()
                        box.label(text="Supported")
                        box.prop(wm, "BAmbientOcclusion", text = "Ambient Occlusion")
                        if not ntree.nodes['Specular BSDF'].inputs["Ambient Occlusion"].links:
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

def updateEBillboardRandomType(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["EBillboardRandomType"] = self.EBillboardRandomType
        
def updateETerrainNormals(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["ETerrainNormals"] = self.ETerrainNormals
        
def updateELightingModel(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["ELightingModel"] = self.ELightingModel
        
def updateELodMethod(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["ELodMethod"] = self.ELodMethod
            
def updateEShaderGenerationMode(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["EShaderGenerationMode"] = self.EShaderGenerationMode
            
def updateBUsedAsGrass(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["BUsedAsGrass"] = self.BUsedAsGrass
    
def updatem_f3dRange(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["m_f3dRange"] = self.m_f3dRange
        
def updatem_fHighDetail3dDistance(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["m_fHighDetail3dDistance"] = self.m_fHighDetail3dDistance
        
def updatem_fLowDetail3dDistance(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["m_fLowDetail3dDistance"] = self.m_fLowDetail3dDistance
        
def updatem_fBillboardRange(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["m_fBillboardRange"] = self.m_fBillboardRange
        
def updatem_fBillboardStartDistance(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["m_fBillboardStartDistance"] = self.m_fBillboardStartDistance
        
def updatem_fBillboardFinalDistance(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
            
    if main_coll:
        main_coll["m_fBillboardFinalDistance"] = self.m_fBillboardFinalDistance
            
def updateLodPreview(self, context):
    prev_mode = bpy.context.mode
    if bpy.data.objects:
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False) 
        if self.previewLod:
            for obj in bpy.data.objects:
                if "SpeedTreeTag" in obj.data:
                    if obj.data["SpeedTreeTag"] == 1:
                        for i in range(len(obj.data.vertices)):
                            obj.data.attributes['vertexPosition'].data[i].vector = obj.data.vertices[i].co
                            obj.data.vertices[i].co = obj.data.attributes['vertexLodPosition'].data[i].vector
                        geom_nodes = obj.modifiers[0]
                        vector_math = geom_nodes.node_group.nodes["Vector Math"]
                        leaf_card_lod_scalar = geom_nodes.node_group.nodes['Leaf Card LOD Scalar']
                        geom_nodes.node_group.links.new(leaf_card_lod_scalar.outputs['Attribute'], vector_math.inputs[1])
        else:
            for obj in bpy.data.objects:
                if "SpeedTreeTag" in obj.data:
                    if obj.data["SpeedTreeTag"] == 1:
                        for i in range(len(obj.data.vertices)):
                            obj.data.attributes['vertexLodPosition'].data[i].vector = obj.data.vertices[i].co
                            obj.data.vertices[i].co = obj.data.attributes['vertexPosition'].data[i].vector
                        geom_nodes = obj.modifiers[0]
                        vector_math = geom_nodes.node_group.nodes["Vector Math"]
                        if vector_math.inputs[1].links:
                            geom_nodes.node_group.links.remove(vector_math.inputs[1].links[0])
                            
    if prev_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
        
def updateVertexLodPosition(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(ob.data.vertices)
            sel = np.zeros(count, dtype=np.bool)
            ob.data.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            ob.data.attributes['vertexLodPosition'].data[v_index].vector = self.vertexLodPosition
            ob.data.vertices[v_index].co = self.vertexLodPosition
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
    
def updateLeafCorner(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(ob.data.vertices)
            sel = np.zeros(count, dtype=np.bool)
            ob.data.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            ob.data.attributes['leafCardCorner'].data[v_index].vector = self.leafCardCornerTransform
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateLeafCardScalar(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(ob.data.vertices)
            sel = np.zeros(count, dtype=np.bool)
            ob.data.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            ob.data.attributes['leafCardLodScalar'].data[v_index].value = self.leafCardLodScalar
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateLeafAnchorPoint(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] == 1:
            bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
            count = len(ob.data.vertices)
            sel = np.zeros(count, dtype=np.bool)
            ob.data.vertices.foreach_get('select', sel)
            v_index = list(sel).index(True)
            ob.data.attributes['leafAnchorPoint'].data[v_index].vector = self.leafAnchorPoint
            bpy.ops.object.mode_set(mode='EDIT', toggle = False)
            
def updateSpeedTreeCollisionsIndex(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        for col in main_coll.children:
            if re.search("Collision Objects", col.name):
                collision_coll = col
                
    if collision_coll:
        if collision_coll.objects and self.SpeedTreeCollisionsIndex != -1:
            if bpy.context.active_object:
                bpy.context.active_object.select_set(state=False)
            bpy.context.view_layer.objects.active = None
            bpy.context.view_layer.objects.active = collision_coll.objects[self.SpeedTreeCollisionsIndex]
            bpy.context.active_object.select_set(state=True)
            
def pollCollisionObject1(self, object):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        for col in main_coll.children:
            if re.search("Collision Objects", col.name):
                collision_coll = col

    if collision_coll == object.users_collection[0] and "Material_Cylinder" not in object.data.materials and object != self.collisionObject2:
        return True
    else:
        return False
        
def pollCollisionObject2(self, object):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        for col in main_coll.children:
            if re.search("Collision Objects", col.name):
                collision_coll = col
            
    if collision_coll == object.users_collection[0] and "Material_Cylinder" not in object.data.materials and object != self.collisionObject1:
        return True
    else:
        return False

def updateVerticalBillboards(self, context):
    generate_srt_billboards(context, self.NNumBillboards, self.FWidth, self.FBottomPos, self.FTopPos)
    
def updateBCutout(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    bb_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        for col in main_coll.children:
            if re.search("Vertical Billboards", col.name):
                bb_coll = col 
                
    if bb_coll:
        bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
        ngroup = bb_coll.objects[bb_objects[0]].modifiers[0].node_group
        if self.BCutout:
            if not re.findall('_cutout', str([x.name for x in bb_coll.objects])):
                if bpy.context.active_object:
                    bpy.context.active_object.select_set(state=False)
                bpy.context.view_layer.objects.active = None
                bpy.context.view_layer.objects.active = bb_coll.objects[bb_objects[0]]
                bpy.context.active_object.select_set(state=True)
                bpy.ops.object.duplicate()
                bpy.context.active_object.name = 'Mesh_cutout'
                bpy.context.active_object.modifiers.remove(bpy.context.active_object.modifiers[0])
                
            ngroup.nodes["Billboard Cutout"].inputs[0].default_value = bb_coll.objects[re.findall(r"Mesh_cutout\.?\d*", str([x.name for x in bb_coll.objects]))[0]]
            ngroup.links.new(ngroup.nodes["Cutout Diffuse UV"].outputs['Geometry'], ngroup.nodes["Group Output"].inputs['Geometry'])
            
        else:
            ngroup.nodes["Billboard Cutout"].inputs[0].default_value = None
            ngroup.links.new(ngroup.nodes["Group Input"].outputs['Geometry'], ngroup.nodes["Group Output"].inputs['Geometry'])
            
def updateBHorizontalBillboard(self, context):
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    bb_coll = []
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        for col in main_coll.children:
            if re.search("Horizontal Billboard", col.name):
                bb_coll = col
                
    if self.BHorizontalBillboard:
        if not bb_coll:
            generate_srt_horizontal_billboard(context)
        else:
            if not bb_coll.objects:
                generate_srt_horizontal_billboard(context)
    else:
        if bb_coll:
            if bb_coll.objects:
                for obj in bb_coll.objects:
                    bpy.data.objects.remove(obj, do_unlink = True)
                bpy.data.collections.remove(bb_coll, do_unlink=True)

def updateDiffuseTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Diffuse Texture"].image = self.diffuseTexture
            ntree.nodes["Branch Seam Diffuse Texture"].image = self.diffuseTexture
                
def updateNormalTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Normal Texture"].image = self.normalTexture
            ntree.nodes["Branch Seam Normal Texture"].image = self.normalTexture
            if self.normalTexture:
                ntree.nodes["Normal Texture"].image.colorspace_settings.name='Non-Color'
                ntree.nodes["Branch Seam Normal Texture"].image.colorspace_settings.name='Non-Color'
                
def updateDetailTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Detail Texture"].image = self.detailTexture
            ntree.nodes["Branch Seam Detail Texture"].image = self.detailTexture
                
def updateDetailNormalTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Detail Normal Texture"].image = self.detailNormalTexture
            ntree.nodes["Branch Seam Detail Normal Texture"].image = self.detailNormalTexture
            if self.detailNormalTexture:
                ntree.nodes["Detail Normal Texture"].image.colorspace_settings.name='Non-Color'
                ntree.nodes["Branch Seam Detail Normal Texture"].image.colorspace_settings.name='Non-Color'
                
def updateSpecularTexture(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Specular Texture"].image = self.specularTexture
            ntree.nodes["Branch Seam Specular Texture"].image = self.specularTexture
            if self.specularTexture:
                ntree.nodes["Specular Texture"].image.colorspace_settings.name='Non-Color'
                ntree.nodes["Branch Seam Specular Texture"].image.colorspace_settings.name='Non-Color'
            
def updateVAmbientColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Ambient Color"].outputs["Color"].default_value = self.VAmbientColor
            
def updateEAmbientContrast(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EAmbientContrast"] = self.EAmbientContrast
            while mat.node_tree.nodes['Ambient Contrast'].inputs["Fac"].links:
                mat.node_tree.links.remove(mat.node_tree.nodes['Ambient Contrast'].inputs["Fac"].links[0])
            if self.EAmbientContrast in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
                mat.node_tree.links.new(mat.node_tree.nodes['Ambient Contrast Factor'].outputs["Value"], mat.node_tree.nodes['Ambient Contrast'].inputs["Fac"])
                
def updateFAmbientContrastFactor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Ambient Contrast Factor"].outputs["Value"].default_value = self.FAmbientContrastFactor
            
def updateBAmbientOcclusion(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            while mat.node_tree.nodes['Specular BSDF'].inputs["Ambient Occlusion"].links:
                mat.node_tree.links.remove(mat.node_tree.nodes['Specular BSDF'].inputs["Ambient Occlusion"].links[0])
            if self.BAmbientOcclusion:
                mat.node_tree.links.new(mat.node_tree.nodes["Ambient Occlusion"].outputs["Color"], mat.node_tree.nodes['Specular BSDF'].inputs["Ambient Occlusion"])
                
def updateVDiffuseColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Diffuse Color"].outputs["Color"].default_value = self.VDiffuseColor
            
def updateFDiffuseScalar(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Diffuse Scalar"].outputs["Value"].default_value = self.FDiffuseScalar
            
def updateBDiffuseAlphaMaskIsOpaque(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            if self.BDiffuseAlphaMaskIsOpaque:
                mat.blend_method = 'OPAQUE'
            else:
                mat.blend_method = 'CLIP'
                
def updateEDetailLayer(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EDetailLayer"] = self.EDetailLayer
            while mat.node_tree.nodes['Mix Detail Diffuse'].inputs["Fac"].links or mat.node_tree.nodes['Mix Detail Normal'].inputs["Fac"].links:
                mat.node_tree.links.remove(mat.node_tree.nodes['Mix Detail Diffuse'].inputs["Fac"].links[0])
                mat.node_tree.links.remove(mat.node_tree.nodes['Mix Detail Normal'].inputs["Fac"].links[0])
            if self.EDetailLayer in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
                mat.node_tree.links.new(mat.node_tree.nodes["Mix Detail Alpha Seam Blending"].outputs["Color"], mat.node_tree.nodes['Mix Detail Diffuse'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Mix Detail Normal Alpha Seam Blending'].outputs["Color"], mat.node_tree.nodes['Mix Detail Normal'].inputs["Fac"])
                
def updateESpecular(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["ESpecular"] = self.ESpecular
            while mat.node_tree.nodes['Specular BSDF'].inputs['Roughness'].links or mat.node_tree.nodes["Mix Specular Color"].inputs['Color2'].links:
                mat.node_tree.links.remove(mat.node_tree.nodes['Specular BSDF'].inputs['Roughness'].links[0])
                mat.node_tree.links.remove(mat.node_tree.nodes["Mix Specular Color"].inputs['Color2'].links[0])
            if self.ESpecular in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
                mat.node_tree.links.new(mat.node_tree.nodes["Invert Shininess"].outputs["Color"], mat.node_tree.nodes['Specular BSDF'].inputs['Roughness'])
                mat.node_tree.links.new(mat.node_tree.nodes['Specular Color'].outputs["Color"], mat.node_tree.nodes["Mix Specular Color"].inputs['Color2'])
                
def updateFShininess(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Shininess"].outputs["Value"].default_value = self.FShininess
            
def updateVSpecularColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Specular Color"].outputs["Color"].default_value = self.VSpecularColor
            
def updateETransmission(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["ETransmission"] = self.ETransmission
            while mat.node_tree.nodes["Mix Transmission Color"].inputs["Color2"].links or mat.node_tree.nodes["Mix Shader Fresnel"].inputs["Fac"].links or mat.node_tree.nodes["Mix Shadow Brightness"].inputs["Fac"].links:
                mat.node_tree.links.remove(mat.node_tree.nodes["Mix Transmission Color"].inputs["Color2"].links[0])
                mat.node_tree.links.remove(mat.node_tree.nodes["Mix Shader Fresnel"].inputs["Fac"].links[0])
                mat.node_tree.links.remove(mat.node_tree.nodes["Mix Shadow Brightness"].inputs["Fac"].links[0])
            if self.ETransmission in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
                mat.node_tree.links.new(mat.node_tree.nodes["Transmission Color Brightness"].outputs["Color"], mat.node_tree.nodes["Mix Transmission Color"].inputs["Color2"])
                mat.node_tree.links.new(mat.node_tree.nodes['Transmission Fresnel'].outputs["Fac"], mat.node_tree.nodes["Mix Shader Fresnel"].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Transmission Shadow Brightness'].outputs["Value"], mat.node_tree.nodes["Mix Shadow Brightness"].inputs["Fac"])
                
def updateVTransmissionColor(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Transmission Color"].outputs["Color"].default_value = self.VTransmissionColor
            
def updateFTransmissionShadowBrightness(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes['Transmission Shadow Brightness'].outputs["Value"].default_value = self.FTransmissionShadowBrightness
            
def updateFTransmissionViewDependency(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Transmission View Dependency"].outputs["Value"].default_value = self.FTransmissionViewDependency
            
def updateEBranchSeamSmoothing(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EBranchSeamSmoothing"] = self.EBranchSeamSmoothing
            while mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'].links:
                mat.node_tree.links.remove(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'].links[0])
            if self.EBranchSeamSmoothing in ["EFFECT_OFF_X_ON", "EFFECT_ON"]:
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Diffuse Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Diffuse Alpha Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Normal Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Normal Alpha Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Detail Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Detail Alpha Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Detail Normal Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Detail Normal Alpha Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Specular Seam Blending'].inputs["Fac"])
                mat.node_tree.links.new(mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'], mat.node_tree.nodes['Mix Specular Alpha Seam Blending'].inputs["Fac"])
                
def updateFBranchSeamWeight(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Branch Seam Weight"].outputs["Value"].default_value = self.FBranchSeamWeight
            
def updateEFaceCulling(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EFaceCulling"] = self.EFaceCulling
            if self.EFaceCulling == "CULLTYPE_BACK":
                mat.use_backface_culling = True
            else:
                mat.use_backface_culling = False
                
def updateBBlending(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BBlending"] = self.BBlending
            
def updateEAmbientImageLighting(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EAmbientImageLighting"] = self.EAmbientImageLighting
            
def updateEHueVariation(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EHueVariation"] = self.EHueVariation
            
def updateEFogCurve(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EFogCurve"] = self.EFogCurve
            
def updateEFogColorStyle(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EFogColorStyle"] = self.EFogColorStyle
            
def updateBCastsShadows(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            if self.BCastsShadows:
                mat.shadow_method = 'CLIP'
            else:
                mat.shadow_method = 'NONE'
                
def updateBReceivesShadows(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BReceivesShadows"] = self.BReceivesShadows
            
def updateBShadowSmoothing(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BShadowSmoothing"] = self.BShadowSmoothing
    
def updateFAlphaScalar(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            ntree = ob.active_material.node_tree
            ntree.nodes["Alpha Scalar"].outputs["Value"].default_value = self.FAlphaScalar
            
def updateEWindLod(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["EWindLod"] = self.EWindLod
            
def updateBBranchesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BBranchesPresent"] = self.BBranchesPresent
        
def updateBFrondsPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BFrondsPresent"] = self.BFrondsPresent
            
def updateBLeavesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BLeavesPresent"] = self.BLeavesPresent
            
def updateBFacingLeavesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BFacingLeavesPresent"] = self.BFacingLeavesPresent
            
def updateBRigidMeshesPresent(self, context):
    ob = bpy.context.active_object
    if "SpeedTreeTag" in ob.data:
        if ob.data["SpeedTreeTag"] in [1,2]:
            mat = ob.active_material
            mat["BRigidMeshesPresent"] = self.BRigidMeshesPresent
     
PROPS = [
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
    )),
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
    )),
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
("SpeedTreeCollisionsIndex", IntProperty(
        name = "Index of the SpeedTree Collision",
        update = updateSpeedTreeCollisionsIndex,
        default = 0
    )),
("collisionObject1", PointerProperty(
        type=bpy.types.Object,
        poll = pollCollisionObject1,
        name="Collision Object 1",
        description="Set the first collision object to connect"
    )),
("collisionObject2", PointerProperty(
        type=bpy.types.Object,
        poll = pollCollisionObject2,
        name="Collision Object 2",
        description="Set the second collision object to connect"
    )),
("NNumBillboards", IntProperty(
        name = "Number of Vertical Billboards",
        update = updateVerticalBillboards,
        default = 0,
        min = 0
    )),
("FWidth", FloatProperty(
        name = "Width of Vertical Billboards",
        update = updateVerticalBillboards,
        default = 0,
        precision = 4,
        min = 0
    )),
("FTopPos", FloatProperty(
        name = "Top Position of Vertical Billboards",
        update = updateVerticalBillboards,
        default = 0,
        precision = 4
    )),
("FBottomPos", FloatProperty(
        name = "Bottom Position of Vertical Billboards",
        update = updateVerticalBillboards,
        default = 0,
        precision = 4
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
    ))
]

CLASSES = [ImportSrtJson, ExportSrtJson, AddSRTCollisionSphere, RemoveSRTCollisionObject, AddSRTSphereConnection, SRTMeshSetup, SpeedTreeMainPanel, SpeedTreeGeneralSettings, SpeedTreeLODPanel, SpeedTreeVertexPropertiesPanel, SpeedTreeFacingLeavesPanel, SpeedTreeLeavesPanel, SPEEDTREE_UL_collisions, SpeedTreeCollisionPanel, SpeedTreeBillboardsPanel, SPEEDTREE_UL_materials, SpeedTreeMaterialPanel, SpeedTreeTexturePanel, SpeedTreeColorSetPanel, SpeedTreeOthersPanel]

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSrtJson.bl_idname, text="SRT JSON (.json)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportSrtJson.bl_idname, text="SRT JSON (.json)")

def register():
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    for klass in CLASSES:
        bpy.utils.register_class(klass)
    
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.WindowManager, prop_name, prop_value)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    for klass in CLASSES:
        bpy.utils.unregister_class(klass)
    
    for (prop_name, _) in PROPS:
        delattr(bpy.types.WindowManager, prop_name)

if __name__ == "__main__":
    register()
    
    # test call
    bpy.ops.export.srt_json('INVOKE_DEFAULT')
