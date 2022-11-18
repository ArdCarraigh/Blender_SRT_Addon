# -*- coding: utf-8 -*-
# tools/add_srt_connection.py

import bpy
import math
import copy
import numpy as np
import re
from math import sqrt
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
from io_scene_srt_json import export_srt_json
from io_scene_srt_json.export_srt_json import JoinThem
from io_scene_srt_json.tools import srt_mesh_setup
from io_scene_srt_json.tools.srt_mesh_setup import get_parent_collection
from io_scene_srt_json.tools import add_srt_sphere
from io_scene_srt_json.tools.add_srt_sphere import add_srt_sphere

def add_srt_connection(context):
    wm = bpy.context.window_manager
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
            
    bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[collision_coll.name]            
                
    objects = [wm.collisionObject1, wm.collisionObject2]
    objCenter = []
    objName = []
    correctNames = 0
    for obj in objects:
        objName.append(obj.name)
        if re.search("Mesh_col", obj.name):
            correctNames += 1
        else:
            print("You need to connect two collision spheres.")
            break
        
    if "Material_Sphere1" in bpy.data.materials:
        if correctNames == 2 and objects[0].data.materials[0] == bpy.data.materials["Material_Sphere1"] and objects[1].data.materials[0] == bpy.data.materials["Material_Sphere1"]:
            if "Material_Sphere2" not in bpy.data.materials:
                sphere2_mat = bpy.data.materials.new("Material_Sphere2")
            else:
                sphere2_mat = bpy.data.materials["Material_Sphere2"]
            if "Material_Cylinder" not in bpy.data.materials:
                cylinder_mat = bpy.data.materials.new("Material_Cylinder")
            else:
                cylinder_mat = bpy.data.materials["Material_Cylinder"]
            
            for obj in objects:
                bpy.context.view_layer.objects.active = None
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                bpy.context.active_object.select_set(state=True)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
                objCenter.append(copy.deepcopy(obj.matrix_world.translation))
                vert = obj.data.vertices[0].co
                if not 'radius' in locals():
                    radius = sqrt((vert[0])**2 + (vert[1])**2 + (vert[2])**2)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            
            bpy.data.objects.remove(objects[1])
            add_srt_sphere(bpy.context, radius, objCenter[1])
            bpy.context.active_object.data.materials.pop()
            bpy.context.active_object.data.materials.append(sphere2_mat)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            objName[1] = bpy.context.active_object.name
                
            pos_2 = objCenter[1]
            pos_1 = objCenter[0]
            R2 = radius
            R1 = R2
            
            AB = np.linalg.norm(pos_2-pos_1)
            BE = abs(R2-R1)
            AE = (AB**2 - (R2-R1)**2)**.5
            cone_radius_1 = R1 * AE / AB
            cone_radius_2 = R2 * AE / AB
            AG = R1 * BE / AB
            BF = R2 * BE / AB
            
            AB_dir = (pos_2-pos_1)/AB
            if R1 > R2:
                cone_pos = pos_1 + AB_dir * AG
            else:
                cone_pos = pos_1 - AB_dir * AG
            
            cone_depth = AB - abs(AG-BF)
            cone_pos = cone_pos + AB_dir * cone_depth * .5 #cone pos is midpoint of centerline
            rotation = Vector([0,0,1]).rotation_difference(Vector(AB_dir)).to_euler("XYZ") ### may need to change
            
            bpy.ops.mesh.primitive_cone_add(
                vertices=24, 
                radius1=cone_radius_1, 
                radius2=cone_radius_2, 
                depth=cone_depth, 
                location=cone_pos, 
                rotation=rotation, 
                )
            
            bpy.context.active_object.display_type = 'WIRE'
            bpy.context.active_object.data.materials.append(cylinder_mat)
            objName.append(bpy.context.active_object.name)
            JoinThem(objName)
                
        else:
            print("You need to connect two collision spheres.")
            bpy.context.view_layer.objects.active = None
            bpy.ops.object.select_all(action='DESELECT')
            
    bpy.context.view_layer.active_layer_collection = active_coll
    wm.collisionObject1 = None
    wm.collisionObject2 = None