# -*- coding: utf-8 -*-
# tools/generate_srt_billboards.py

import bpy
import numpy as np
import re
import os
import random, colorsys
import math
from bpy_extras.object_utils import object_data_add
from io_scene_srt_json import import_srt_json
from io_scene_srt_json.import_srt_json import JoinThem

def generate_srt_billboards(context, number_billboards, scale_billboards):
    parent_coll = bpy.context.view_layer.active_layer_collection
    if parent_coll.collection.children:
        for coll in parent_coll.collection.children:
            if re.search("LOD0", coll.name):
                objects = coll.objects
                objNames = []
                for obj in objects:
                    objNames.append(obj.name)
                JoinThem(objNames)
                extent = np.array(bpy.context.active_object.bound_box)
                break
    
        if "Vertical Billboards" in parent_coll.collection.children:
            bpy.context.view_layer.active_layer_collection = parent_coll.children["Vertical Billboards"]
        else:
            bb_coll = bpy.data.collections.new("Vertical Billboards")
            bb_coll_name = bb_coll.name
            parent_coll.collection.children.link(bb_coll)
            bpy.context.view_layer.active_layer_collection = parent_coll.children[bb_coll_name]
            
        if bpy.context.view_layer.active_layer_collection.collection.objects:
            for obj in bpy.context.view_layer.active_layer_collection.collection.objects:
                bpy.data.objects.remove(obj)
        width = abs(extent[0][0] - extent[6][0])
        bb_left = -width/2 * scale_billboards[0]
        bb_right = width/2 * scale_billboards[0]
        bb_top = extent[6][2] * scale_billboards[1]
        bb_bottom = extent[0][2] * scale_billboards[1]
        angle_diff = 360/number_billboards
        
        # Materials attribution
        if 'radish_placeholder_texture_d.png' not in bpy.data.images:
            bpy.ops.image.open(filepath = os.path.dirname(__file__) + "\\radish_placeholder_texture_d.png")
        if 'radish_placeholder_texture_n.png' not in bpy.data.images:
            bpy.ops.image.open(filepath = os.path.dirname(__file__) + "\\radish_placeholder_texture_n.png")
        if 'radish_placeholder_texture_s.png' not in bpy.data.images:
            bpy.ops.image.open(filepath = os.path.dirname(__file__) + "\\radish_placeholder_texture_s.png")
        temp_mat = bpy.data.materials.new("Material_Billboard")
        temp_mat.diffuse_color = (*colorsys.hsv_to_rgb(random.random(), .7, .9), 1) #random hue more pleasing than random rgb
        temp_mat.use_nodes = True
        temp_mat.blend_method = 'CLIP'
        temp_mat.shadow_method = 'CLIP'
        temp_mat.use_backface_culling = False
        node_main = temp_mat.node_tree.nodes[0]
        node_main.inputs["Specular"].default_value = 0
        
        # Apply textures
        # Diffuse
        node_uv_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
        node_uv_diff.uv_map = "DiffuseUV"
        node_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
        node_diff.name = "Billboard Diffuse Texture"
        node_diff.image = bpy.data.images['radish_placeholder_texture_d.png']
        temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_diff.inputs["Vector"])
        temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_main.inputs["Base Color"])
        temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_main.inputs["Alpha"])
        node_diff.location = (-600, 500)
        node_uv_diff.location = (-1500, 400)
            
        # Normal
        node_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
        node_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
        node_normal3 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeNormalMap')
        node_normal4 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBump')
        node_normal.name = "Billboard Normal Texture"
        node_normal.image = bpy.data.images['radish_placeholder_texture_n.png']
        node_normal.image.colorspace_settings.name='Non-Color'
        node_normal2.mapping.curves[1].points[0].location = (0,1)
        node_normal2.mapping.curves[1].points[1].location = (1,0)
        temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_normal.inputs["Vector"])
        temp_mat.node_tree.links.new(node_normal.outputs["Color"], node_normal2.inputs["Color"])
        temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_normal3.inputs["Color"])
        temp_mat.node_tree.links.new(node_normal3.outputs["Normal"], node_normal4.inputs["Normal"])
        temp_mat.node_tree.links.new(node_normal.outputs["Alpha"], node_normal4.inputs["Height"])
        temp_mat.node_tree.links.new(node_normal4.outputs["Normal"], node_main.inputs["Normal"])
        node_normal.location = (-1000, 0)
        node_normal2.location = (-700, 0)
        node_normal3.location = (-400, 0)
        node_normal4.location = (-200, 0)
        
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

            bb.uv_layers.new(name="DiffuseUV")
            for face in bb.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (0,0)
                    
            bb.materials.append(temp_mat)
                
    bpy.context.view_layer.active_layer_collection = parent_coll