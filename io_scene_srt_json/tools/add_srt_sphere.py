# -*- coding: utf-8 -*-
# tools/add_srt_sphere.py

import bpy
from bpy_extras.object_utils import object_data_add

def add_srt_sphere(context, radius, location):
    parent_coll = bpy.context.view_layer.active_layer_collection
    if "Collision Objects" in parent_coll.collection.children:
        bpy.context.view_layer.active_layer_collection = parent_coll.children["Collision Objects"]
    else:
        sphere_coll = bpy.data.collections.new("Collision Objects")
        sphere_coll_name = sphere_coll.name
        parent_coll.collection.children.link(sphere_coll)
        bpy.context.view_layer.active_layer_collection = parent_coll.children[sphere_coll_name]
        
    if "Material_Sphere1" not in bpy.data.materials:
        sphere1_mat = bpy.data.materials.new("Material_Sphere1")
    else:
        sphere1_mat = bpy.data.materials["Material_Sphere1"]
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=24, ring_count=16)
    
    num = 0
    while "Mesh_col" + str(num) in bpy.context.view_layer.active_layer_collection.collection.objects:
        num += 1
    else:
        bpy.context.active_object.name = "Mesh_col" + str(num)
        
    bpy.context.active_object.display_type = 'WIRE'
    
    bpy.context.active_object.data.materials.append(sphere1_mat)
    
    bpy.context.view_layer.active_layer_collection = parent_coll