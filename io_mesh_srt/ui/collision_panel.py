# -*- coding: utf-8 -*-
# ui/collision_panel.py

import bpy
import numpy as np
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, PointerProperty
from bpy.types import Operator
from io_mesh_srt.tools.collision_tools import add_srt_sphere, remove_srt_sphere, add_srt_connection
from io_mesh_srt.utils import GetCollection, selectOnly
    
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
        wm = bpy.context.window_manager.speedtree
        index = wm.SpeedTreeCollisionsIndex
        remove_srt_sphere(context, index)
        if not index:
            wm.SpeedTreeCollisionsIndex = 0
        elif index > 0:
            wm.SpeedTreeCollisionsIndex = index - 1  
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
        wm = bpy.context.window_manager.speedtree
        add_srt_connection(context, [wm.collisionObject1, wm.collisionObject2])
        wm.collisionObject1 = None
        wm.collisionObject2 = None
        return {'FINISHED'}
                                    
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
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        wm = context.window_manager.speedtree
        if wm.SpeedTreeSubPanel == 'collision':
            
            layout = self.layout
            main_coll = GetCollection(make_active=False)
            collision_coll = GetCollection("Collision Objects", make_active=False)
            if collision_coll:
                row = layout.row()
                row.template_list("SPEEDTREE_UL_collisions", "", collision_coll, "objects", wm, "SpeedTreeCollisionsIndex", rows=3)
                index = np.where(np.array(collision_coll.objects) == bpy.context.active_object)[0]
                if index.size:
                    if wm.SpeedTreeCollisionsIndex != index[0]:
                        wm.SpeedTreeCollisionsIndex = index[0]
                else:
                    wm.SpeedTreeCollisionsIndex = -1
                
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
            
def updateSpeedTreeCollisionsIndex(self, context):
    collision_coll = GetCollection("Collision Objects", make_active=False)      
    if collision_coll:
        if collision_coll.objects and self.SpeedTreeCollisionsIndex != -1:
            selectOnly(collision_coll.objects[self.SpeedTreeCollisionsIndex])
            
def pollCollisionObject1(self, object):
    collision_coll = GetCollection("Collision Objects", make_active=False)
    return collision_coll == object.users_collection[0] and "Material_Cylinder" not in object.data.materials and object != self.collisionObject2
        
def pollCollisionObject2(self, object):
    collision_coll = GetCollection("Collision Objects", make_active=False)    
    return collision_coll == object.users_collection[0] and "Material_Cylinder" not in object.data.materials and object != self.collisionObject1
     
PROPS_Collision_Panel = [
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
    ))
]

CLASSES_Collision_Panel = [AddSRTCollisionSphere, RemoveSRTCollisionObject, AddSRTSphereConnection, SPEEDTREE_UL_collisions, SpeedTreeCollisionPanel]