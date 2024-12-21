# -*- coding: utf-8 -*-
# tools/collision_tools.py

import bpy
import re
import numpy as np
from copy import deepcopy
from mathutils import Vector
from io_mesh_srt.utils import GetCollection, selectOnly, JoinThem

def add_srt_sphere(context, radius, location):
    collision_coll = GetCollection("Collision Objects", True)
        
    if "Material_Sphere1" not in bpy.data.materials:
        sphere1_mat = bpy.data.materials.new("Material_Sphere1")
    else:
        sphere1_mat = bpy.data.materials["Material_Sphere1"]
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=24, ring_count=16)
    sphere = bpy.context.active_object
    
    num = 0
    while "Mesh_col" + str(num) in collision_coll.objects:
        num += 1
    else:
        sphere.name = "Mesh_col" + str(num)
        
    sphere.display_type = 'WIRE'
    sphere.data.materials.append(sphere1_mat)
    
    return sphere
    
def remove_srt_sphere(context, index):
    collision_coll = GetCollection("Collision Objects", make_active=False)
    
    if collision_coll:
        if collision_coll.objects:
            bpy.data.objects.remove(collision_coll.objects[index], do_unlink=True)
            
        if not collision_coll.objects:
            bpy.data.collections.remove(collision_coll, do_unlink=True)
            
            
def add_srt_connection(context, objects):
    collision_coll = GetCollection("Collision Objects")       
                
    objCenter = []
    meshes = []
    assert(len(objects) == 2)
    
    correctNames = 0
    for obj in objects:
        if re.search("Mesh_col", obj.name):
            correctNames += 1
    assert(correctNames == 2)
    
    assert("Material_Sphere1" in objects[0].data.materials and "Material_Sphere1" in objects[1].data.materials)
    if "Material_Sphere2" not in bpy.data.materials:
        sphere2_mat = bpy.data.materials.new("Material_Sphere2")
    if "Material_Cylinder" not in bpy.data.materials:
        cylinder_mat = bpy.data.materials.new("Material_Cylinder")
    
    for obj in objects:
        selectOnly(obj)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
        objCenter.append(deepcopy(obj.matrix_world.translation))
        if 'radius' not in locals():
            radius = np.linalg.norm(obj.data.vertices[0].co)
            meshes.append(obj)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    
    bpy.data.objects.remove(objects[1])
    sphere = add_srt_sphere(bpy.context, radius, objCenter[1])
    sphere.data.materials.pop()
    sphere.data.materials.append(bpy.data.materials["Material_Sphere2"])
    meshes.append(sphere)
    
    vec_cylinder = objCenter[1] - objCenter[0]
    cone_depth = np.linalg.norm(vec_cylinder)
    cone_pos = np.mean(objCenter, axis = 0)
    rotation = Vector([0,0,1]).rotation_difference(Vector(vec_cylinder)).to_euler("XYZ") ### may need to change
    
    bpy.ops.mesh.primitive_cone_add(
        vertices=24, 
        radius1=radius, 
        radius2=radius, 
        depth=cone_depth, 
        location=cone_pos, 
        rotation=rotation, 
        )
    
    connection = bpy.context.active_object
    connection.display_type = 'WIRE'
    connection.data.materials.append(bpy.data.materials["Material_Cylinder"])
    meshes.append(connection)
    JoinThem(meshes)
    
    return bpy.context.active_object