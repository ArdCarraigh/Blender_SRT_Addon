# -*- coding: utf-8 -*-
# tools/generate_srt_billboards.py

import bpy
import numpy as np
import re
import os
import random, colorsys
import math
from bpy_extras.object_utils import object_data_add
from io_scene_srt_json.tools import srt_mesh_setup
from io_scene_srt_json.tools.srt_mesh_setup import srt_mesh_material, get_parent_collection
from io_scene_srt_json import export_srt_json
from io_scene_srt_json.export_srt_json import GetLoopDataPerVertex

def generate_srt_billboards(context, number_billboards, bb_width, bb_bottom, bb_top, uvs = None):
    
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    bb_coll = []
    horiz_coll = []
    main_coll_layer = bpy.context.view_layer.layer_collection
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        parent_colls = []
        get_parent_collection(main_coll, parent_colls)
        for col in reversed(parent_colls):
            main_coll_layer = main_coll_layer.children[col.name]
        for col in main_coll.children:
            if re.search("Vertical Billboards", col.name):
                bb_coll = col
            if re.search("Horizontal Billboard", col.name):
                horiz_coll = col

    if bb_coll:
        bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[bb_coll.name]
    else:
        bb_coll = bpy.data.collections.new("Vertical Billboards")
        bb_coll_name = bb_coll.name
        main_coll.children.link(bb_coll)
        bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[bb_coll_name]
    
    # Save UV Maps and Material from old billboards
    uvs_all = [] 
    for obj in bpy.context.view_layer.active_layer_collection.collection.objects:
        if "_billboard" in obj.name:
            uvs_obj = GetLoopDataPerVertex(obj, "UV", "DiffuseUV")
            uvs_all.append(uvs_obj)
            old_mat = obj.data.materials[0]
            old_ngroup = obj.modifiers[0].node_group
            bpy.data.objects.remove(obj, do_unlink=True)
            
    # Get Horizontal Billboard Material if it exists           
    if horiz_coll:
        if horiz_coll.objects:
            horiz_mat = horiz_coll.objects[0].data.materials[0]
            
    if number_billboards > 0:       
        bb_left = -bb_width/2
        bb_right = bb_width/2
        angle_diff = 360/number_billboards
        
        # Material Creation
        if 'old_mat' not in locals() and 'horiz_mat' not in locals():
            srt_mesh_material(is_bb = True)
        
        for i in range(number_billboards):
            verts = [[bb_left, 0, bb_bottom], [bb_right, 0, bb_bottom], [bb_right, 0, bb_top], [bb_left, 0, bb_top]]
            faces = [[0,1,2], [2,3,0]]
            # Add the mesh to the scene
            bb = bpy.data.meshes.new(name="Mesh_billboard"+str(i))
            bb.from_pydata(verts, [],faces)
            for k in bb.polygons:
                k.use_smooth = True
            object_data_add(context, bb)
            bpy.context.active_object.rotation_euler[2] = math.radians(angle_diff * i)
            
            #SpeedTree Tag
            bb["SpeedTreeTag"] = 2
        
            # UV Map
            bb.uv_layers.new(name="DiffuseUV")
            if i < len(uvs_all):
                for face in bb.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (uvs_all[i][vert_idx][0], 1-uvs_all[i][vert_idx][1])
            else:
                for face in bb.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        if uvs:
                            bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (uvs[i][vert_idx][0], 1-uvs[i][vert_idx][1])
                        else:
                            bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (0,0)
            
            # Material Attribution
            if 'old_mat' not in locals() and 'horiz_mat' not in locals():    
                bb.materials.append(bpy.data.materials[-1])
            elif 'old_mat' in locals():
                bb.materials.append(old_mat)
            elif 'horiz_mat' in locals():
                bb.materials.append(horiz_mat)
            
            # Geometry Node Creation
            bpy.context.active_object.modifiers.new(type='NODES', name = "Billboard Cutout")
            geom_nodes = bpy.context.active_object.modifiers[0]
            if 'old_ngroup' not in locals():
                if i == 0:
                    bpy.ops.node.new_geometry_node_group_assign()
                    ngroup = geom_nodes.node_group
                    start_geom = ngroup.nodes['Group Input']
                    end_geom = ngroup.nodes['Group Output']
                    uv_source = ngroup.nodes.new(type = 'GeometryNodeInputNamedAttribute')
                    uv_source.data_type = 'FLOAT_VECTOR'
                    uv_source.inputs['Name'].default_value = "DiffuseUV"
                    uv_source.location = (-330, -100)
                    uv_transfer = ngroup.nodes.new(type = 'GeometryNodeAttributeTransfer')
                    uv_transfer.data_type = 'FLOAT_VECTOR'
                    uv_transfer.location = (-160, -100)
                    mesh_cutout = ngroup.nodes.new(type = 'GeometryNodeObjectInfo')
                    mesh_cutout.name = 'Billboard Cutout'
                    mesh_cutout.location = (-160, -300)
                    uv_target = ngroup.nodes.new(type = 'GeometryNodeStoreNamedAttribute')
                    uv_target.name = 'Cutout Diffuse UV'
                    uv_target.data_type = 'FLOAT_VECTOR'
                    uv_target.domain = 'CORNER'
                    uv_target.inputs['Name'].default_value = "DiffuseUV"
                    uv_target.location = (10, -100)
                    ngroup.links.new(start_geom.outputs['Geometry'], uv_transfer.inputs["Source"])
                    ngroup.links.new(uv_source.outputs['Attribute'], uv_transfer.inputs["Attribute"])
                    ngroup.links.new(uv_transfer.outputs['Attribute'], uv_target.inputs["Value"])
                    ngroup.links.new(mesh_cutout.outputs['Geometry'], uv_target.inputs["Geometry"])
                else:
                    geom_nodes.node_group = ngroup
            else:
                geom_nodes.node_group = old_ngroup
            
    elif number_billboards == 0:
        if bb_coll.objects:
            for obj in bb_coll.objects:
                bpy.data.objects.remove(obj, do_unlink = True)
        bpy.data.collections.remove(bpy.context.view_layer.active_layer_collection.collection, do_unlink=True)
                
    bpy.context.view_layer.active_layer_collection = active_coll
    
def generate_srt_horizontal_billboard(context, verts = None, uvs = None):
    
    active_coll = bpy.context.view_layer.active_layer_collection
    parent_colls = []
    main_coll = []
    bb_coll = []
    vert_coll = []
    main_coll_layer = bpy.context.view_layer.layer_collection
    get_parent_collection(active_coll, parent_colls)
    if re.search("SRT Asset", active_coll.name):
        main_coll = active_coll.collection
    elif parent_colls:
        if re.search("SRT Asset", parent_colls[0].name):
            main_coll = parent_colls[0]
    
    if main_coll:
        parent_colls = []
        get_parent_collection(main_coll, parent_colls)
        for col in reversed(parent_colls):
            main_coll_layer = main_coll_layer.children[col.name]
        for col in main_coll.children:
            if re.search("Horizontal Billboard", col.name):
                bb_coll = col
            if re.search("Vertical Billboards", col.name):
                vert_coll = col
        
    if bb_coll:
        bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[bb_coll.name]
    else:
        bb_coll = bpy.data.collections.new("Horizontal Billboard")
        bb_coll_name = bb_coll.name
        main_coll.children.link(bb_coll)
        bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[bb_coll_name]
        
    # Get Vertical Billboard Material if it exists        
    if vert_coll:
        vert_mat = vert_coll.objects[0].data.materials[0]
        
    # Material Creation
    if 'vert_mat' not in locals():
        srt_mesh_material(is_bb = True)
        
    if not verts:
        verts = [[1, -1, 0.5], [-1, -1, 0.5], [-1, 1, 0.5], [1, 1, 0.5]]
    faces = [[0,1,2], [2,3,0]]
    # Add the mesh to the scene
    bb = bpy.data.meshes.new(name="Mesh_horizontal_billboard")
    bb.from_pydata(verts, [],faces)
    for k in bb.polygons:
        k.use_smooth = True
    object_data_add(context, bb)
    
    #SpeedTree Tag
    bb["SpeedTreeTag"] = 2

    # UV Map
    bb.uv_layers.new(name="DiffuseUV")
    for face in bb.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            if uvs:
                bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (uvs[vert_idx][0], 1-uvs[vert_idx][1])
            else:
                bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (0,0)
        
    # Material Attribution
    if 'vert_mat' not in locals():    
        bb.materials.append(bpy.data.materials[-1])
    else:
        bb.materials.append(vert_mat)
                
    bpy.context.view_layer.active_layer_collection = active_coll