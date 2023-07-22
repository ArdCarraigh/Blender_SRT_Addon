# -*- coding: utf-8 -*-
# ui/main_panel.py

import bpy
from bpy.props import EnumProperty
from bpy.types import Operator
from io_mesh_srt.tools.setup_tools import srt_mesh_setup
    
class SRTMeshSetup(Operator):
    """Set Up a SRT Asset"""
    bl_idname = "speed_tree.srt_mesh_setup"
    bl_label = "Set Up a SRT Asset"
    bl_options = {'REGISTER', 'UNDO'}
    
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
        srt_mesh_setup(context, bpy.context.active_object, self.geom_type)
        return {'FINISHED'}

class SpeedTreeMainPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SpeedTree'
    bl_idname = 'VIEW3D_PT_SpeedTree_panel'
    bl_label = 'SpeedTree'
    
    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        layout.operator(SRTMeshSetup.bl_idname, text = "Set Up a SRT Asset", icon = "WORLD")
        layout.separator()
        row = layout.row(align = True)
        row.alignment = "CENTER"
        row.scale_x = 1.44
        row.scale_y = 1.4
        row.prop_enum(wm, "SpeedTreeSubPanel", 'general', text = "")
        row.prop_enum(wm, "SpeedTreeSubPanel", 'lod', text = "")
        row.prop_enum(wm, "SpeedTreeSubPanel", 'vertex', text = "")
        row.prop_enum(wm, "SpeedTreeSubPanel", 'collision', text = "")
        row.prop_enum(wm, "SpeedTreeSubPanel", 'billboard', text = "")
        row.prop_enum(wm, "SpeedTreeSubPanel", 'material', text = "")
        
        return 
            
PROPS_Main_Panel = [
('SpeedTreeSubPanel', EnumProperty(
        name="SpeedTree SubPanel",
        description="Set the active SpeedTree subpanel",
        items=(
            ('general', "general", "Show the general SpeedTree subpanel", 'SETTINGS', 0),
            ('lod', "lod", "Show the general SpeedTree subpanel", 'MOD_DECIM', 1),
            ('vertex', "vertex", "Show the vertex SpeedTree subpanel",'VERTEXSEL', 2),
            ('collision', "collision", "Show the collision SpeedTree subpanel", 'META_CAPSULE', 3),
            ('billboard', "billboard", "Show the billboard SpeedTree subpanel", 'IMAGE_PLANE', 4),
            ('material', "material", "Show the material SpeedTree subpanel", 'NODE_MATERIAL', 5)
        ),
        default='general'
    ))
]

CLASSES_Main_Panel = [SRTMeshSetup, SpeedTreeMainPanel]