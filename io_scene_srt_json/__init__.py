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
from io_scene_srt_json.tools import make_it_branch
from io_scene_srt_json.tools.make_it_branch import make_it_branch
from io_scene_srt_json.tools import make_it_frond
from io_scene_srt_json.tools.make_it_frond import make_it_frond
from io_scene_srt_json.tools import make_it_facing_leave
from io_scene_srt_json.tools.make_it_facing_leave import make_it_facing_leave
from io_scene_srt_json.tools import generate_srt_billboards
from io_scene_srt_json.tools.generate_srt_billboards import generate_srt_billboards

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
        default = 80,
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
        default = 100,
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
    
class MakeItBranch(Operator):
    """Make your Mesh a Branch Geometry"""
    bl_idname = "speed_tree.make_it_branch"
    bl_label = "Make it Branch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        make_it_branch(context)
        return {'FINISHED'}
    
class MakeItFrond(Operator):
    """Make your Mesh a Frond Geometry"""
    bl_idname = "speed_tree.make_it_frond"
    bl_label = "Make it Frond"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        make_it_frond(context)
        return {'FINISHED'}
    
class MakeItFacingLeave(Operator):
    """Make your Mesh a Facing Leave Geometry"""
    bl_idname = "speed_tree.make_it_facing_leave"
    bl_label = "Make it Facing Leave"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        make_it_facing_leave(context)
        return {'FINISHED'}
    
class GenerateSRTBillboards(Operator):
    """Generate Billboards"""
    bl_idname = "speed_tree.generate_srt_billboards"
    bl_label = "Generate Billboards"
    bl_options = {'REGISTER', 'UNDO'}

    number_billboards: IntProperty(
        name="Number",
        default = 1,
        description="Set the number of billboards"
    )
    scale_billboards: FloatVectorProperty(
        name="Scale",
        default=(1, 1),
        description="Set the scale of the billboards regarding the bounding box of the mesh",
        size = 2
    )

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        generate_srt_billboards(context, self.number_billboards, self.scale_billboards)
        return {'FINISHED'}
    
class SpeedTreeMenu(bpy.types.Menu):
    bl_label = "SpeedTree"
    bl_idname = "VIEW3D_MT_object_SpeedTree_menu"

    def draw(self, context):
        layout = self.layout
        
        layout.operator(MakeItBranch.bl_idname, text = "Make it Branch", icon = 'MESH_CYLINDER')
        layout.operator(MakeItFrond.bl_idname, text = "Make it Frond", icon = 'MESH_PLANE')
        layout.operator(MakeItFacingLeave.bl_idname, text = "Make it Facing Leave", icon = 'MESH_PLANE')
        layout.operator(GenerateSRTBillboards.bl_idname, text = "Generate Billboards", icon = 'MESH_PLANE')
        layout.operator(AddSRTCollisionSphere.bl_idname, text = "Add Collision Sphere", icon='MESH_UVSPHERE')
        layout.operator(AddSRTSphereConnection.bl_idname, text = "Add Sphere Connection", icon='MESH_CAPSULE')
        

class SpeedTreeMainPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_idname = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree'
    
    def draw(self, context):
        return
    
class SpeedTreeFacingLeavesPanel(bpy.types.Panel):
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'Facing Leaves'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        me = context.object
        if me.data.is_editmode:
            bm = bmesh.from_edit_mesh(me.data)
            if bm.select_history.active is not None:
                v_index = bm.select_history.active.index
                for g in me.data.vertices[v_index].groups:
                    if me.vertex_groups[g.group].name == "GeomType":
                        geom_type = int(g.weight*5-1)
                        break
                if geom_type == 3 and 'leafCardCorner' in me.data.attributes:
                    row = layout.row()
                    col = row.column()
                    col.prop(wm, "leafCardCornerTransform", text = "Leaf Card Corner Transform")
                    if wm.leafCardCornerTransform != me.data.attributes['leafCardCorner'].data[v_index].vector:
                        wm.leafCardCornerTransform = me.data.attributes['leafCardCorner'].data[v_index].vector
                        
class SpeedTreeLODPanel(bpy.types.Panel):
    bl_parent_id = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree LOD System'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        row = layout.row()
        row.prop(wm, "previewLod", text = "Preview LOD")
        
        if wm.previewLod:
            me = context.object
            if me.data.is_editmode:
                bm = bmesh.from_edit_mesh(me.data)
                if bm.select_history.active is not None:
                    v_index = bm.select_history.active.index
                    row = layout.row()
                    col = row.column()
                    col.prop(wm, "vertexLodPosition", text = "Vertex LOD Position")
                    if wm.vertexLodPosition != me.data.vertices[v_index].co:
                        wm.vertexLodPosition = me.data.vertices[v_index].co
                        me.data.attributes['vertexLodPosition'].data[v_index].vector = me.data.vertices[v_index].co
                        
                    for g in me.data.vertices[v_index].groups:
                        if me.vertex_groups[g.group].name == "GeomType":
                            geom_type = int(g.weight*5-1)
                            break
                    if geom_type == 3 and 'leafCardLodScalar' in me.data.attributes:
                        row = layout.row()
                        row.label(text="Leaf Card LOD Scalar")
                        row = layout.row()
                        row.prop(wm, "leafCardLodScalar", text="")
                        if wm.leafCardLodScalar != me.data.attributes['leafCardLodScalar'].data[v_index].value:
                            wm.leafCardLodScalar = me.data.attributes['leafCardLodScalar'].data[v_index].value
        
def updateLeafCorner(self, context):
    if 'leafCardCorner' in bpy.context.active_object.data.attributes:
        bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
        ob = bpy.context.active_object
        count = len(ob.data.vertices)
        sel = np.zeros(count, dtype=np.bool)
        ob.data.vertices.foreach_get('select', sel)
        v_index = list(sel).index(True)
        ob.data.attributes['leafCardCorner'].data[v_index].vector = self.leafCardCornerTransform
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
        
def updateLodPreview(self, context):
    prev_mode = bpy.context.mode
    bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    if self.previewLod:
        for obj in bpy.data.objects:
            if 'vertexPosition' in obj.data.attributes and 'vertexLodPosition' in obj.data.attributes:
                for i in range(len(obj.data.vertices)):
                    obj.data.attributes['vertexPosition'].data[i].vector = obj.data.vertices[i].co
                    obj.data.vertices[i].co = obj.data.attributes['vertexLodPosition'].data[i].vector
            if obj.modifiers:
                geom_nodes = obj.modifiers[0]
                if 'Leaf Card LOD Scalar' in geom_nodes.node_group.nodes and 'Leaf Card Corner' in geom_nodes.node_group.nodes:
                    leaf_card_lod_scalar = geom_nodes.node_group.nodes['Leaf Card LOD Scalar']
                    leaf_card_lod_scalar.input_type_b = 'ATTRIBUTE'
                    leaf_card_lod_scalar.inputs['B'].default_value = 'leafCardLodScalar'
    else:
        for obj in bpy.data.objects:
            if 'vertexPosition' in obj.data.attributes and 'vertexLodPosition' in obj.data.attributes:
                for i in range(len(obj.data.vertices)):
                    obj.data.attributes['vertexLodPosition'].data[i].vector = obj.data.vertices[i].co
                    obj.data.vertices[i].co = obj.data.attributes['vertexPosition'].data[i].vector
            if obj.modifiers:
                geom_nodes = obj.modifiers[0]
                if 'Leaf Card LOD Scalar' in geom_nodes.node_group.nodes and 'Leaf Card Corner' in geom_nodes.node_group.nodes:
                    leaf_card_lod_scalar = geom_nodes.node_group.nodes['Leaf Card LOD Scalar']
                    leaf_card_lod_scalar.input_type_b = 'VECTOR'
                    leaf_card_lod_scalar.inputs[4].default_value = (1,1,1)
    if prev_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
        
def updateVertexLodPosition(self, context):
    if 'vertexLodPosition' in bpy.context.active_object.data.attributes:
        bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
        ob = bpy.context.active_object
        count = len(ob.data.vertices)
        sel = np.zeros(count, dtype=np.bool)
        ob.data.vertices.foreach_get('select', sel)
        v_index = list(sel).index(True)
        ob.data.attributes['vertexLodPosition'].data[v_index].vector = self.vertexLodPosition
        ob.data.vertices[v_index].co = self.vertexLodPosition
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
        
def updateLeafCardScalar(self, context):
    if 'leafCardLodScalar' in bpy.context.active_object.data.attributes:
        bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
        ob = bpy.context.active_object
        count = len(ob.data.vertices)
        sel = np.zeros(count, dtype=np.bool)
        ob.data.vertices.foreach_get('select', sel)
        v_index = list(sel).index(True)
        ob.data.attributes['leafCardLodScalar'].data[v_index].value = self.leafCardLodScalar
        bpy.ops.object.mode_set(mode='EDIT', toggle = False)
                
PROPS = [
("leafCardCornerTransform", FloatVectorProperty(
        name="Leaf Card Corner Transform",
        update = updateLeafCorner,
        description="Set the transform of the leaf card corner of the selected vertex",
        subtype = 'COORDINATES',
        precision = 6
    )),
("previewLod", BoolProperty(
        name="Preview LOD",
        update = updateLodPreview,
        description="Enable/Diable LOD Previewing",
        default = False
    )),
("leafCardLodScalar", FloatProperty(
        name="Leaf Card Lod Scalar",
        update = updateLeafCardScalar,
        description="Set the leaf card lod system scalar of the selected vertex",
        precision = 6
    )),
("vertexLodPosition", FloatVectorProperty(
        name="Vertex LOD Position",
        update = updateVertexLodPosition,
        description="Set the LOD position of the selected vertex",
        subtype = 'COORDINATES',
        precision = 6
    ))
]

CLASSES = [ImportSrtJson, ExportSrtJson, AddSRTCollisionSphere, AddSRTSphereConnection, MakeItBranch, MakeItFrond, MakeItFacingLeave, GenerateSRTBillboards, SpeedTreeMenu, SpeedTreeMainPanel, SpeedTreeFacingLeavesPanel, SpeedTreeLODPanel]

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
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(draw_item)
    
    for klass in CLASSES:
        bpy.utils.register_class(klass)
    
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.WindowManager, prop_name, prop_value)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(draw_item)
    
    for klass in CLASSES:
        bpy.utils.unregister_class(klass)
    
    for (prop_name, _) in PROPS:
        delattr(bpy.types.WindowManager, prop_name)

if __name__ == "__main__":
    register()
    
    # test call
    bpy.ops.export.srt_json('INVOKE_DEFAULT')
