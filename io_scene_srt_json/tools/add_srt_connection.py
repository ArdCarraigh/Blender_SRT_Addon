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
from io_scene_srt_json import import_srt_json
from io_scene_srt_json.import_srt_json import JoinThem

def add_srt_connection(context):
    parent_coll = bpy.context.view_layer.active_layer_collection
    if "Collision Objects" in parent_coll.collection.children:
        bpy.context.view_layer.active_layer_collection = parent_coll.children["Collision Objects"]
        
        if bpy.context.selected_objects[0] in list(bpy.context.view_layer.active_layer_collection.collection.objects) and bpy.context.selected_objects[1] in list(bpy.context.view_layer.active_layer_collection.collection.objects):
            objects = bpy.context.selected_objects
            objCenter = []
            objRadius = []
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
                    objects[1].data.materials.pop()
                    objects[1].data.materials.append(sphere2_mat)
                    for obj in objects:
                        bpy.context.view_layer.objects.active = None
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = obj
                        bpy.context.active_object.select_set(state=True)
                        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
                        objCenter.append(copy.deepcopy(obj.matrix_world.translation))
                        center = obj.matrix_world.translation
                        vert = obj.data.vertices[0].co
                        radius = sqrt((vert[0])**2 + (vert[1])**2 + (vert[2])**2)
                        objRadius.append(copy.deepcopy(radius))
                        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                        
                    pos_2 = objCenter[1]
                    pos_1 = objCenter[0]
                    R2 = objRadius[1]
                    R1 = objRadius[0]
                    
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
                
    bpy.context.view_layer.active_layer_collection = parent_coll