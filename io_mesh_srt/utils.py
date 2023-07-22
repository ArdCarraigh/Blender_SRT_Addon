# -*- coding: utf-8 -*-
# utils.py

import bpy
import numpy as np
import re
import os
from copy import deepcopy

def JoinThem(objects):
    bpy.context.view_layer.objects.active = None
    bpy.ops.object.select_all(action='DESELECT')
    for obj in reversed(objects):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(state=True)
    bpy.ops.object.join()
    # Purge orphan data left by the joining
    override = bpy.context.copy()
    override["area.type"] = ['OUTLINER']
    override["display_mode"] = ['ORPHAN_DATA']
    bpy.ops.outliner.orphans_purge(override)

def GetLoopDataPerVertex(mesh, type, layername = None):
    corner_verts = mesh.attributes[".corner_vert"].data
    corner_verts_array = np.zeros(len(corner_verts), dtype = int)
    corner_verts.foreach_get("value", corner_verts_array)
    loops = mesh.loops
    data = [[] for i in range(len(mesh.vertices))]
    
    match type:
        case "NORMAL": 
            data_array = np.zeros(len(loops) * 3)
            loops.foreach_get("normal", data_array)
            data_array = data_array.reshape(-1,3)
            
        case "TANGENT":
            data_array = np.zeros(len(loops) * 3)
            loops.foreach_get("tangent", data_array)
            data_array = data_array.reshape(-1,3)
                
        case "UV":
            data_array = np.zeros(len(loops) * 2)
            mesh.attributes[layername].data.foreach_get("vector", data_array)
            data_array[1::2] = 1 - data_array[1::2]
            data_array = data_array.reshape(-1,2)
        
    for loop, vert in enumerate(corner_verts_array):
        data[vert].append(data_array[loop])
    for i in range(len(data)):
        data[i] = np.mean(data[i], axis=0).tolist()
    
    return(data)

def selectOnly(obj):
    bpy.context.view_layer.objects.active = None
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(state=True)
    
def SplitMesh(mesh):
    corner_verts = mesh.attributes[".corner_vert"].data
    corner_verts_array = np.zeros(len(corner_verts), dtype = int)
    corner_verts.foreach_get("value", corner_verts_array)
    loops = mesh.loops
    n_vertices = len(mesh.vertices)
    n_loops = len(loops)
    select_array = np.zeros(n_vertices, dtype=bool)
    
    # Normals
    data_array = np.zeros(n_loops * 3)
    loops.foreach_get("normal", data_array)
    data_array = data_array.reshape(-1,3).tolist()
    normals = [[] for i in range(n_vertices)]
    for loop, vert in enumerate(corner_verts_array):
        if select_array[vert]:
            continue
        normals[vert].append(data_array[loop])
        if normals[vert][-1] != normals[vert][0]:
            select_array[vert] = True
    
    # UVs
    for uv in mesh.uv_layers:
        data_array = np.zeros(n_loops * 2)
        mesh.attributes[uv.name].data.foreach_get("vector", data_array)
        data_array = data_array.reshape(-1,2).tolist()
        UVs = [[] for i in range(n_vertices)]
        for loop, vert in enumerate(corner_verts_array):
            if select_array[vert]:
                continue
            UVs[vert].append(data_array[loop])
            if UVs[vert][-1] != UVs[vert][0]:
                select_array[vert] = True
    
    # Select Vertices and Split
    if ".select_vert" not in mesh.attributes:
        mesh.attributes.new(".select_vert", "BOOLEAN", "POINT")
    mesh.attributes[".select_vert"].data.foreach_set("value", select_array)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.edge_split(type='EDGE')
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode='OBJECT')
    
def TriangulateActiveMesh():
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY')
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode='OBJECT')
    
def get_parent_collection(coll, parent_colls):
    for parent_collection in bpy.data.collections:
        if coll.name in parent_collection.children.keys():
            parent_colls.append(parent_collection)
    
def GetCollection(target = "Main", create_if_missing = False, make_active = True):
    active_coll = bpy.context.view_layer.active_layer_collection
    
    if re.search(target, active_coll.name) or ("SpeedTreeMainCollection" in active_coll.collection and target == "Main"):
        target_coll = active_coll.collection
        
    else:
        main_coll = None
        target_coll = None
        parent_colls = []
        get_parent_collection(active_coll, parent_colls)
        if "SpeedTreeMainCollection" in active_coll.collection:
            main_coll = active_coll.collection
        elif parent_colls:
            if "SpeedTreeMainCollection" in parent_colls[0]:
                main_coll = parent_colls[0]
                
        if main_coll:
            main_coll_layer = bpy.context.view_layer.layer_collection
            parent_colls = []
            get_parent_collection(main_coll, parent_colls)
            for col in reversed(parent_colls):
                main_coll_layer = main_coll_layer.children[col.name]
                    
            if target == "Main":
                target_coll = main_coll
                if make_active:
                    bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name]
            
            elif target in ["Collision Objects", "Vertical Billboards", "Horizontal Billboard"] or "LOD" in target:
                for col in main_coll.children:
                    if re.search(target, col.name):
                        target_coll = col
                        break
            
                if not target_coll and create_if_missing:
                    target_coll = bpy.data.collections.new(target)
                    main_coll.children.link(target_coll)
                    
                if target_coll and make_active:
                    bpy.context.view_layer.active_layer_collection = main_coll_layer.children[main_coll.name].children[target_coll.name]
    
    return target_coll

def ImportTemplates():
    #if 'srt_shading_and_geometry_nodes_templates.blend' not in bpy.data.libraries:
    with bpy.data.libraries.load(os.path.dirname(__file__) + "/templates/srt_shading_and_geometry_nodes_templates.blend", link = False) as (data_from, data_to):
        data_to.materials = data_from.materials
        data_to.node_groups = data_from.node_groups
        
def getAttributesComponents(attributes):
    components = []
    for i in range(len(attributes)):
        if attributes[i] == "VERTEX_ATTRIB_UNASSIGNED":
            components.append("VERTEX_COMPONENT_UNASSIGNED")
        else:
            n = 0
            for j in range(len(attributes[:i])):
                if attributes[j] == attributes[i]:
                    n += 1
            match n:
                case 0:
                    components.append("VERTEX_COMPONENT_X")
                case 1:
                    components.append("VERTEX_COMPONENT_Y")
                case 2:
                    components.append("VERTEX_COMPONENT_Z")
                case 3:
                    components.append("VERTEX_COMPONENT_W")
    return(components)

def getVertexProperty(srtVert, prop_id, data, count, format, property_name, start_offset, add_offsets, prop_count):
    new_offsets = (np.array(start_offset).repeat(count) + add_offsets).tolist()
    srtVert["VertexProperties"][prop_id]["ValueCount"] =  count
    srtVert["VertexProperties"][prop_id]["FloatValues"] =  data
    srtVert["VertexProperties"][prop_id]["PropertyFormat"] = format
    srtVert["VertexProperties"][prop_id]["ValueOffsets"] = new_offsets
    offset_shift = count
    if format == "VERTEX_FORMAT_HALF_FLOAT":
        offset_shift = offset_shift * 2
    elif format == "VERTEX_FORMAT_BYTE":
        offset_shift = offset_shift
    start_offset += offset_shift
    prop_count += count
    return start_offset, new_offsets, prop_count

def updateVertexProperties(property_name, format, count, new_offsets, properties, components, offsets, formats):
    properties.extend(np.array(property_name).repeat(count).tolist())
    match count:
        case 1:
            components.extend(["VERTEX_COMPONENT_X"])
        case 2:  
            components.extend(["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y"])
        case 3:    
            components.extend(["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"])
        case 4:    
            components.extend(["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z", "VERTEX_COMPONENT_W"])
    offsets.extend(new_offsets)
    formats.extend(np.array(format).repeat(count).tolist())

def setAttribute(srtAttributes, attrib_id, attrib_name, format, properties, components, offsets, attributes_components, attributes):
    if attrib_name in properties:
        properties_array = np.array(properties)
        components_array = np.array(components)
        attrib = [-1,-1,-1,-1]
        for i, comp in enumerate(["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z", "VERTEX_COMPONENT_W"]): 
            id = np.where((properties_array == attrib_name) & (components_array == comp))[0]
            if id.size:
                attrib[i] = id[0]
        srtAttributes[attrib_id]["AeAttribs"] = [attributes[x] for x in attrib]
        srtAttributes[attrib_id]["AeAttribComponents"] = [attributes_components[x] for x in attrib]
        srtAttributes[attrib_id]["AuiOffsets"] = [offsets[x] for x in attrib]
        srtAttributes[attrib_id]["EFormat"] = format
        
def getSphere(obj, compute_radius = True):
    selectOnly(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
    Pos = deepcopy(obj.matrix_world.translation)
    Radius = None
    if compute_radius:
        Radius = np.linalg.norm(obj.data.vertices[0].co)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    return Pos, Radius

def isBillboardRotated(uv_array):
    billboard_uv_x = uv_array[::2]
    billboard_uv_y = uv_array[1::2]
    check = False
    index = np.argmin(billboard_uv_x + billboard_uv_y)
    if index == 0 or index == 5:
        check = False
    elif index == 2 or index == 3:
        check = True
    return check, billboard_uv_x, billboard_uv_y

def checkWeightPaint(obj, geom_type = 0, wind_flag = 0):
    weight_layers = ["GeomType", "WindWeight1", "WindWeight2", "WindNormal1", "WindNormal2", "WindExtra1", "WindExtra2", "WindExtra3", "WindFlag", "AmbientOcclusion", "SeamBlending"]
    existing_layers = []
    for k, vert in enumerate(obj.data.vertices):
        if vert.groups:
            existing_layers = [obj.vertex_groups[g.group].name for g in vert.groups]
        for layer in weight_layers:
            if layer not in existing_layers:
                match layer:
                    case "GeomType":
                        obj.vertex_groups[layer].add([k], ((1 + geom_type)*0.2), 'REPLACE')
                    case "WindFlag":
                        obj.vertex_groups[layer].add([k], wind_flag, 'REPLACE')
                    case "WindWeight1"|"WindWeight2"|"WindNormal1"|"WindNormal2"|"WindExtra1"|"WindExtra2"|"WindExtra3"|"AmbientOcclusion"|"SeamBlending":
                        obj.vertex_groups[layer].add([k], 0, 'REPLACE')
                        
def getMaterial(main_coll, mat, srtMat):
    # Collection Settings
    for prop in srtMat:
        if prop in main_coll:
            if prop == 'BUsedAsGrass':
                srtMat[prop] = bool(main_coll[prop])
            else:    
                srtMat[prop] = main_coll[prop]
    
    # Material Custom Attributes
    for prop, value in list(mat.items()):
        if prop in ["BBlending", "BReceivesShadows", "BShadowSmoothing", "BBranchesPresent", "BFrondsPresent", "BLeavesPresent", "BFacingLeavesPresent", "BRigidMeshesPresent"]:
            srtMat[prop] = bool(value)
        else:
            srtMat[prop] = value
        
    # Material Nodes
    n_tree = mat.node_tree
    nodes = n_tree.nodes
    links = n_tree.links
    
    # Color Sets
    srtMat["VAmbientColor"] = dict(zip(["x", "y", "z"], list(nodes["Ambient Color"].outputs['Color'].default_value)[:-1]))
    srtMat["VDiffuseColor"] = dict(zip(["x", "y", "z"], list(nodes["Diffuse Color"].outputs['Color'].default_value)[:-1]))
    srtMat["VSpecularColor"] = dict(zip(["x", "y", "z"], list(nodes["Specular Color"].outputs['Color'].default_value)[:-1]))
    srtMat["VTransmissionColor"] = dict(zip(["x", "y", "z"], list(nodes["Transmission Color"].outputs['Color'].default_value)[:-1]))
    
    srtMat["FAmbientContrastFactor"] = nodes['Ambient Contrast Factor'].outputs['Value'].default_value
    srtMat["FDiffuseScalar"] = nodes['Diffuse Scalar'].outputs['Value'].default_value
    srtMat["FShininess"] = nodes['Shininess'].outputs['Value'].default_value
    srtMat["FTransmissionShadowBrightness"] = nodes['Transmission Shadow Brightness'].outputs['Value'].default_value
    srtMat["FTransmissionViewDependency"] = nodes['Transmission View Dependency'].outputs['Value'].default_value
    srtMat["FBranchSeamWeight"] = nodes['Branch Seam Weight'].outputs['Value'].default_value
    srtMat["FAlphaScalar"] = nodes['Alpha Scalar'].outputs['Value'].default_value
    
    if not nodes['Ambient Occlusion'].inputs["Color"].links:
        srtMat["BAmbientOcclusion"] = False
    else:
        srtMat["BAmbientOcclusion"] = True
        
    if mat.blend_method == 'OPAQUE':
        srtMat["BDiffuseAlphaMaskIsOpaque"] = True
    else:
        srtMat["BDiffuseAlphaMaskIsOpaque"] = False
    
    if mat.shadow_method != 'NONE':
        srtMat["BCastsShadows"] = True
    else:
        srtMat["BCastsShadows"] = False
    
    #Textures
    texture_names = []
    diff_tex = nodes["Diffuse Texture"].image
    norm_tex = nodes["Normal Texture"].image
    det_tex = nodes["Detail Texture"].image
    det_norm_tex = nodes["Detail Normal Texture"].image
    spec_tex = nodes["Specular Texture"].image
    if diff_tex:
        diff_tex_name = diff_tex.name
        srtMat["ApTextures"][0]["Val"] = diff_tex_name
        texture_names.append(diff_tex_name)
        
    if norm_tex:
        norm_tex_name = norm_tex.name
        srtMat["ApTextures"][1]["Val"] = norm_tex_name
        texture_names.append(norm_tex_name)
            
    if det_tex:
        det_tex_name = det_tex.name
        srtMat["ApTextures"][2]["Val"] = det_tex_name
        texture_names.append(det_tex_name)
        
    if det_norm_tex:
        det_norm_tex_name = det_norm_tex.name
        srtMat["ApTextures"][3]["Val"] = det_norm_tex_name
        texture_names.append(det_norm_tex_name)
        
    if spec_tex:
        spec_tex_name = spec_tex.name
        srtMat["ApTextures"][4]["Val"] = spec_tex_name
        srtMat["ApTextures"][5]["Val"] = spec_tex_name
        texture_names.append(spec_tex_name)
        
    return texture_names