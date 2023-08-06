# -*- coding: utf-8 -*-
# tools/setup_tools.py

import bpy
import numpy as np
import re
import random, colorsys
import os
import json
from io_mesh_srt.utils import get_parent_collection, ImportTemplates, checkWeightPaint

def srt_mesh_setup(context, obj, geom_type = '0', vertex_data = None):
    geom_type = float(geom_type)
    mesh = obj.data
    verts = mesh.vertices
    nverts = len(verts)
    # Import Material and Geometry Nodes Templates
    ImportTemplates()
    # Deal with Collections
    parent_coll = bpy.context.view_layer.active_layer_collection
    sub_colls = []
    main_colls = []
    if obj.users_collection:
        sub_colls.append(obj.users_collection)
    if sub_colls:
        get_parent_collection(sub_colls[0][0], main_colls)
        
    if (sub_colls and main_colls) and (re.search("LOD", sub_colls[0][0].name) or "SpeedTreeMainCollection" in main_colls[0]):
        srt_coll = None
    else:
        srt_coll = bpy.data.collections.new("SRT Asset")
        srt_coll["SpeedTreeMainCollection"] = "SpeedTreeMainCollection"
        lod_coll = bpy.data.collections.new("LOD0")
        parent_coll.collection.children.link(srt_coll)
        srt_coll.children.link(lod_coll)
        bpy.context.view_layer.active_layer_collection = parent_coll.children[srt_coll.name].children[lod_coll.name]
        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)
        if sub_colls:
            sub_colls[0][0].objects.unlink(obj)
            
    #Custom Properties for General User Settings
    if srt_coll:
        # User Strings
        srt_coll['PUserStrings'] = []
        # Shader Settings
        srt_coll['ELightingModel'] = 'LIGHTING_MODEL_DEFERRED'
        srt_coll['ELodMethod'] = 'LOD_METHOD_SMOOTH'
        srt_coll['EShaderGenerationMode'] = 'SHADER_GEN_MODE_UNIFIED_SHADERS'
        srt_coll['BUsedAsGrass'] = 0
        
        # LOD Profile
        srt_coll['m_f3dRange'] = 0
        srt_coll['m_fHighDetail3dDistance'] = 10
        srt_coll['m_fLowDetail3dDistance'] = 30
        srt_coll['m_fBillboardRange'] = 0
        srt_coll['m_fBillboardStartDistance'] = 80
        srt_coll['m_fBillboardFinalDistance'] = 90
        
        # Wind
        with open(os.path.dirname(__file__) +"/../templates/mainTemplate.json", 'r', encoding='utf-8') as mainfile:
            srtMain = json.load(mainfile)
        for k in srtMain['Wind']:
            srt_coll[k] = srtMain['Wind'][k]
            
    # Deal with Vertex Groups
    #Geometry Type
    if 'GeomType' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name="GeomType")
    if vertex_data and vertex_data["VERTEX_PROPERTY_GEOMETRY_TYPE_HINT"]:
        geom_types = vertex_data["VERTEX_PROPERTY_GEOMETRY_TYPE_HINT"]
        for k in range(nverts):
            v_group.add([k], ((1 + geom_types[k][0])*0.2), 'REPLACE')
    else:
        for k in range(nverts):
            v_group.add([k], geom_type, 'REPLACE')
            
    #Wind        
    if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_BRANCH_DATA"]:
        branches_wind = vertex_data["VERTEX_PROPERTY_WIND_BRANCH_DATA"]

    if 'WindWeight1' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindWeight1')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_BRANCH_DATA"]:
            for k in range(nverts):
                v_group.add([k], branches_wind[k][0], 'REPLACE')
            
    if 'WindNormal1' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindNormal1')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_BRANCH_DATA"]:
            for k in range(nverts):
                v_group.add([k], branches_wind[k][1]*0.0625, 'REPLACE')
            
    if 'WindWeight2' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindWeight2')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_BRANCH_DATA"]:
            for k in range(nverts):
                v_group.add([k], branches_wind[k][2], 'REPLACE')
            
    if 'WindNormal2' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindNormal2')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_BRANCH_DATA"]:
            for k in range(nverts):
                v_group.add([k], branches_wind[k][3]*0.0625, 'REPLACE')
    
    #Wind Extra            
    if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_EXTRA_DATA"]:
        wind_extras = vertex_data["VERTEX_PROPERTY_WIND_EXTRA_DATA"]
            
    if 'WindExtra1' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindExtra1')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_EXTRA_DATA"]:
            for k in range(nverts):
                v_group.add([k], wind_extras[k][0]*0.0625, 'REPLACE')
            
    if 'WindExtra2' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindExtra2')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_EXTRA_DATA"]:
            for k in range(nverts):
                v_group.add([k], wind_extras[k][1], 'REPLACE')
            
    if 'WindExtra3' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindExtra3')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_EXTRA_DATA"]:
            for k in range(nverts):
                v_group.add([k], wind_extras[k][2]*0.5, 'REPLACE')
    
    #Wind Flag
    if 'WindFlag' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='WindFlag')
        if vertex_data and vertex_data["VERTEX_PROPERTY_WIND_FLAGS"]:
            wind_flags = vertex_data["VERTEX_PROPERTY_WIND_FLAGS"]
            for k in range(nverts):
                v_group.add([k], wind_flags[k][0], 'REPLACE')
            
    #Ambient Occlusion
    if 'AmbientOcclusion' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='AmbientOcclusion')
        if vertex_data and vertex_data["VERTEX_PROPERTY_AMBIENT_OCCLUSION"]:
            ambients = 1 - (np.array(vertex_data["VERTEX_PROPERTY_AMBIENT_OCCLUSION"]) / 255)
            for k in range(nverts):
                v_group.add([k], ambients[k][0], 'REPLACE')
                
    #Seam Blending
    if 'SeamBlending' not in obj.vertex_groups:
        v_group = obj.vertex_groups.new(name='SeamBlending')
        if vertex_data and vertex_data["VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE"]:
            branches_seam_diff = 1 - np.array(vertex_data["VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE"])[:,2]
            for k in range(nverts):
                v_group.add([k], branches_seam_diff[k], 'REPLACE')
            
    #Add values if missing for new unpainted vertices
    checkWeightPaint(obj)
            
    # Deal with UV maps
    corner_verts = mesh.attributes[".corner_vert"].data
    corner_verts_array = np.zeros(len(corner_verts), dtype = int)
    corner_verts.foreach_get("value", corner_verts_array)
    if 'DiffuseUV' not in mesh.attributes:
        uv_map = mesh.attributes.new("DiffuseUV", 'FLOAT2', 'CORNER')
        if vertex_data and vertex_data["VERTEX_PROPERTY_DIFFUSE_TEXCOORDS"]:
            uvs_diff = np.array(vertex_data["VERTEX_PROPERTY_DIFFUSE_TEXCOORDS"])[corner_verts_array].flatten()
            uvs_diff[1::2] = 1-uvs_diff[1::2]
            uv_map.data.foreach_set("vector", uvs_diff)
                
    if 'DetailUV' not in mesh.attributes:
        uv_map = mesh.attributes.new("DetailUV", 'FLOAT2', 'CORNER')
        if vertex_data and vertex_data["VERTEX_PROPERTY_DETAIL_TEXCOORDS"]:
            uvs_det = np.array(vertex_data["VERTEX_PROPERTY_DETAIL_TEXCOORDS"])[corner_verts_array].flatten()
            uvs_det[1::2] = 1-uvs_det[1::2]
            uv_map.data.foreach_set("vector", uvs_det)
                    
    if 'SeamDiffuseUV' not in mesh.attributes:
        uv_map = mesh.attributes.new("SeamDiffuseUV", 'FLOAT2', 'CORNER')
        if vertex_data and vertex_data["VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE"]:
            branches_seam_diff = np.array(vertex_data["VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE"])[corner_verts_array,:2].flatten()
            branches_seam_diff[1::2] = 1-branches_seam_diff[1::2]
            uv_map.data.foreach_set("vector", branches_seam_diff)
                    
    if 'SeamDetailUV' not in mesh.attributes:
        uv_map = mesh.attributes.new("SeamDetailUV", 'FLOAT2', 'CORNER')
        if vertex_data and vertex_data["VERTEX_PROPERTY_BRANCH_SEAM_DETAIL"]:
            branches_seam_det = np.array(vertex_data["VERTEX_PROPERTY_BRANCH_SEAM_DETAIL"])[corner_verts_array].flatten()
            branches_seam_det[1::2] = 1-branches_seam_det[1::2]
            uv_map.data.foreach_set("vector", branches_seam_det)
                
    # Deal with Attributes
    if vertex_data and vertex_data["VERTEX_PROPERTY_POSITION"]:
        vert_array = np.array(vertex_data["VERTEX_PROPERTY_POSITION"]).flatten()
    else:
        vert_array = np.zeros(nverts * 3)
        mesh.attributes['position'].data.foreach_get('vector', vert_array)
        
    if 'vertexPosition' not in mesh.attributes:
        attrib = mesh.attributes.new(name='vertexPosition', type='FLOAT_VECTOR', domain='POINT')
        attrib.data.foreach_set('vector', vert_array)
        
    if 'vertexLodPosition' not in mesh.attributes:
        attrib = mesh.attributes.new(name='vertexLodPosition', type='FLOAT_VECTOR', domain='POINT')
        if vertex_data and vertex_data["VERTEX_PROPERTY_LOD_POSITION"]:
            verts_lod = np.array(vertex_data["VERTEX_PROPERTY_LOD_POSITION"]).flatten()
            attrib.data.foreach_set('vector', verts_lod)
        else:
            attrib.data.foreach_set('vector', vert_array)
        
    if 'leafCardCorner' not in mesh.attributes:
        attrib = mesh.attributes.new(name='leafCardCorner', type='FLOAT_VECTOR', domain='POINT')
        if vertex_data and vertex_data["VERTEX_PROPERTY_LEAF_CARD_CORNER"]:
            leaf_card_corners = np.array(vertex_data["VERTEX_PROPERTY_LEAF_CARD_CORNER"])[:,[2,0,1]].flatten()
            attrib.data.foreach_set('vector', leaf_card_corners)
        
    if 'leafCardLodScalar' not in mesh.attributes:
        attrib = mesh.attributes.new(name='leafCardLodScalar', type='FLOAT', domain='POINT')
        if vertex_data and vertex_data["VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR"]:
            leaf_card_lod_scalars = np.array(vertex_data["VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR"]).flatten()
            attrib.data.foreach_set('value', leaf_card_lod_scalars)
        
    if 'leafAnchorPoint' not in mesh.attributes:
        attrib = mesh.attributes.new(name='leafAnchorPoint', type='FLOAT_VECTOR', domain='POINT')
        if vertex_data and vertex_data["VERTEX_PROPERTY_LEAF_ANCHOR_POINT"]:
            leaf_anchor_points = np.array(vertex_data["VERTEX_PROPERTY_LEAF_ANCHOR_POINT"]).flatten()
            attrib.data.foreach_set('vector', leaf_anchor_points)
        
    #SpeedTree Tag
    mesh["SpeedTreeTag"] = 1
        
    # Deal with Geometry Nodes
    if obj.modifiers and "Leaf_Card" not in obj.modifiers[0].node_group.name:
        while obj.modifiers:
            obj.modifiers.remove(obj.modifiers[0])
    node_group = bpy.data.node_groups["Leaf_Card_Template"].copy()
    node_group.name = "Leaf_Card"
    obj.modifiers.new(type='NODES', name = "Leaf_Card")
    obj.modifiers[-1].node_group = node_group
    
    # Deal with the Material
    if mesh.materials and "SRT_Material" not in mesh.materials[0].name:
        while mesh.materials:
            mesh.materials.pop(index = 0)
    mat = bpy.data.materials["SRT_Material_Template"].copy()
    mat.name = "SRT_Material"
    if geom_type == 0.2:
        mat["BBranchesPresent"] = 1
    elif geom_type == 0.4:
        mat["BFrondsPresent"] = 1
    elif geom_type == 0.6:
        mat["BLeavesPresent"] = 1
    elif geom_type == 0.8:
        mat["BFacingLeavesPresent"] = 1
    elif geom_type == 1.0:
        mat["BRigidMeshesPresent"] = 1
    mesh.materials.append(mat) 