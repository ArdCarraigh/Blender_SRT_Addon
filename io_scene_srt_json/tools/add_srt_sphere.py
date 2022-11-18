# -*- coding: utf-8 -*-
# tools/add_srt_sphere.py

import bpy
import re
from bpy_extras.object_utils import object_data_add
from io_scene_srt_json.tools import srt_mesh_setup
from io_scene_srt_json.tools.srt_mesh_setup import get_parent_collection

def add_srt_sphere(context, radius, location):
    
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    collision_coll = []
    main_coll_layer = bpy.context.view_layer.layer_collection
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
        parent_colls = []
        get_parent_collection(main_coll, parent_colls)
        for col in reversed(parent_colls):
            main_coll_layer = main_coll_layer.children[col.name]

    if collision_coll:
        bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[collision_coll.name]
    else:
        sphere_coll = bpy.data.collections.new("Collision Objects")
        sphere_coll_name = sphere_coll.name
        main_coll.children.link(sphere_coll)
        bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[sphere_coll_name]
        
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
    
    bpy.context.view_layer.active_layer_collection = active_coll
    
def remove_srt_sphere(context):
    wm = bpy.context.window_manager
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
        if collision_coll.objects:
            id = wm.SpeedTreeCollisionsIndex
            bpy.data.objects.remove(collision_coll.objects[id], do_unlink=True)
            
        if not collision_coll.objects:
            bpy.data.collections.remove(collision_coll, do_unlink=True)