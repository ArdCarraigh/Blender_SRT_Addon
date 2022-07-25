import bpy
import math as mt
import json
import random, colorsys
import os
import re
import numpy as np
import operator
import copy
from mathutils import Vector
from bpy_extras.object_utils import object_data_add
from io_scene_srt_json import import_srt_json
from io_scene_srt_json.import_srt_json import JoinThem

def GetLoopDataPerVertex(mesh, type, layername = None):
    vert_ids = []
    data = []
    for face in mesh.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            if vert_idx not in vert_ids:
                if type == "NORMAL":
                    data.append(list(mesh.data.loops[loop_idx].normal))
                elif type == "TANGENT":
                    data.append(list(mesh.data.loops[loop_idx].tangent))
                elif type == "UV":
                    data.append([mesh.data.uv_layers[layername].data[loop_idx].uv.x, 1-mesh.data.uv_layers[layername].data[loop_idx].uv.y])
                elif type == "VERTEXCOLOR":
                    data.append(mesh.data.vertex_colors[layername].data[loop_idx].color[0])
                vert_ids.append(vert_idx)
    vert_ids, data = (list(t) for t in zip(*sorted(zip(vert_ids, data))))
    return(data)

def getAttributesComponents(attributes):
    components = []
    for i in range(len(attributes)):
        if attributes[i] == "VERTEX_ATTRIB_UNASSIGNED":
            components+= ["VERTEX_COMPONENT_UNASSIGNED"]
        else:
            n = 0
            for j in range(len(attributes[:i])):
                if attributes[j] == attributes[i]:
                    n += 1
            if n == 0:
                components += ["VERTEX_COMPONENT_X"]
            if n == 1:
                components += ["VERTEX_COMPONENT_Y"]
            if n == 2:
                components += ["VERTEX_COMPONENT_Z"]
            if n == 3:
                components += ["VERTEX_COMPONENT_W"]
    return(components)
    

def write_srt_json(context, filepath, randomType, terrainNormals, lodDist_Range3D,
        lodDist_HighDetail3D, lodDist_LowDetail3D, lodDist_RangeBillboard,
        lodDist_StartBillboard, lodDist_EndBillboard, grass):
    
    main_coll = bpy.context.view_layer.active_layer_collection
    if re.search("SRT Asset", main_coll.name):
        # Open main template
        os.chdir(os.path.dirname(__file__))
        with open("mainTemplate.json", 'r', encoding='utf-8') as mainfile:
            srtMain = json.load(mainfile)
            
        # Get and Write Collisions
        if "Collision Objects" in main_coll.collection.children:
            collisionObjects = main_coll.collection.children["Collision Objects"].objects
            if len(collisionObjects) > 0:
                for collisionObject in collisionObjects:
                    bpy.context.view_layer.objects.active = None
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = collisionObject
                    bpy.context.active_object.select_set(state=True)
                    with open("collisionTemplate.json", 'r', encoding='utf-8') as collisionfile:
                        srtCollision = json.load(collisionfile)
                    if len(collisionObject.data.materials) <= 1:
                        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
                        collisionObject_vert_coord = collisionObject.data.vertices[0].co
                        collisionObject_radius = (mt.sqrt((collisionObject_vert_coord[0])**2 + (collisionObject_vert_coord[1])**2 + (collisionObject_vert_coord[2])**2))
                        collisionObject_position = collisionObject.matrix_world.translation
                        srtCollision["m_vCenter1"]["x"] = collisionObject_position[0]
                        srtCollision["m_vCenter1"]["y"] = collisionObject_position[1]
                        srtCollision["m_vCenter1"]["z"] = collisionObject_position[2]
                        srtCollision["m_vCenter2"]["x"] = collisionObject_position[0]
                        srtCollision["m_vCenter2"]["y"] = collisionObject_position[1]
                        srtCollision["m_vCenter2"]["z"] = collisionObject_position[2]
                        srtCollision["m_fRadius"] = collisionObject_radius
                        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                    else:
                        coll_mesh_name = collisionObject.name
                        bpy.ops.mesh.separate(type='MATERIAL')
                        collisionObjects2 = main_coll.collection.children["Collision Objects"].objects
                        coll_mesh_names = []
                        for collisionObject2 in collisionObjects2:
                            if re.search(coll_mesh_name, collisionObject2.name):
                                bpy.context.view_layer.objects.active = None
                                bpy.ops.object.select_all(action='DESELECT')
                                bpy.context.view_layer.objects.active = collisionObject2
                                bpy.context.active_object.select_set(state=True)
                                coll_mesh_names.append(collisionObject2.name)
                                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
                                if "Material_Sphere1" in collisionObject2.data.materials:
                                    collisionObject_vert_coord = collisionObject2.data.vertices[0].co
                                    collisionObject_radius = (mt.sqrt((collisionObject_vert_coord[0])**2 + (collisionObject_vert_coord[1])**2 + (collisionObject_vert_coord[2])**2))
                                    collisionObject_position = collisionObject2.matrix_world.translation
                                    srtCollision["m_vCenter1"]["x"] = collisionObject_position[0]
                                    srtCollision["m_vCenter1"]["y"] = collisionObject_position[1]
                                    srtCollision["m_vCenter1"]["z"] = collisionObject_position[2]
                                    srtCollision["m_fRadius"] = collisionObject_radius
                                if "Material_Sphere2" in collisionObject2.data.materials:
                                    collisionObject_position = collisionObject2.matrix_world.translation
                                    srtCollision["m_vCenter2"]["x"] = collisionObject_position[0]
                                    srtCollision["m_vCenter2"]["y"] = collisionObject_position[1]
                                    srtCollision["m_vCenter2"]["z"] = collisionObject_position[2]
                            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                        JoinThem(coll_mesh_names)
                    srtMain["CollisionObjects"].append(srtCollision)
            else:
                srtMain.pop("CollisionObjects")
        else:
            srtMain.pop("CollisionObjects")
            
        # Get and Write Vertical Billboards
        bb_textures_names = []
        if "Vertical Billboards" in main_coll.collection.children:
            billboardObjects = main_coll.collection.children["Vertical Billboards"].objects
            if len(billboardObjects) > 0:
                billboard0 = billboardObjects[0].data
                billboard_bottom = billboard0.vertices[0].co.z
                billboard_top = billboard0.vertices[2].co.z
                billboard_width = abs(billboard0.vertices[0].co.x - billboard0.vertices[2].co.x)
                billboard_num = 0
                billboard_uvs = []
                billboard_rotated = []
                billboard0_cutout_verts = []
                billboard0_cutout_indices = []
                if len(billboard0.materials) > 0:
                    billboard_mat = billboard0.materials[0].node_tree.nodes
                    if "Billboard Diffuse Texture" in billboard_mat:
                        if billboard_mat["Billboard Diffuse Texture"].image:
                            billboard_diffuse = billboard_mat["Billboard Diffuse Texture"].image.name
                            srtMain["Geometry"]["ABillboardRenderStateMain"]["ApTextures"][0]["Val"] = billboard_diffuse
                            srtMain["Geometry"]["ABillboardRenderStateShadow"]["ApTextures"][0]["Val"] = billboard_diffuse
                            bb_textures_names.append(billboard_diffuse)
                    if "Billboard Normal Texture" in billboard_mat:
                        if billboard_mat["Billboard Normal Texture"].image:
                            billboard_normal = billboard_mat["Billboard Normal Texture"].image.name
                            srtMain["Geometry"]["ABillboardRenderStateMain"]["ApTextures"][1]["Val"] = billboard_normal
                            bb_textures_names.append(billboard_normal)
                for billboardObject in billboardObjects:
                    if re.search(billboard0.name+"_cutout", billboardObject.name):
                        billboard0_cutout = billboardObject.data
                        billboard0_cutout_nverts = len(billboardObject.data.vertices)
                        for vert in billboardObject.data.vertices:
                            billboard0_cutout_verts.append((vert.co.x - -billboard_width/2)/billboard_width)
                            billboard0_cutout_verts.append((vert.co.z - billboard_bottom)/(billboard_top - billboard_bottom))
                        for face in billboardObject.data.polygons:
                            for vertex in face.vertices:
                                billboard0_cutout_indices.append(vertex)
                    if "_cutout" not in billboardObject.name:
                        billboard_num += 1
                        billboard_uv_x = []
                        billboard_uv_y = []
                        for face in billboardObject.data.polygons:
                            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                                billboard_uv_x.append(billboardObject.data.uv_layers[0].data[loop_idx].uv.x)
                                billboard_uv_y.append(billboardObject.data.uv_layers[0].data[loop_idx].uv.y)
                        billboard_uv_sum = list(map(operator.add, billboard_uv_x, billboard_uv_y))
                        if billboard_uv_sum.index(min(billboard_uv_sum)) == 0:
                            billboard_rotated.append(0)
                            billboard_uvs.append(billboard_uv_x[0])
                            billboard_uvs.append(1-billboard_uv_y[0])
                            billboard_uvs.append(billboard_uv_x[2] - billboard_uv_x[0])
                            billboard_uvs.append((1-billboard_uv_y[2]) - (1-billboard_uv_y[0]))
                        elif billboard_uv_sum.index(min(billboard_uv_sum)) == 2:
                            billboard_rotated.append(1)
                            billboard_uvs.append(billboard_uv_x[0])
                            billboard_uvs.append(1-billboard_uv_y[2])
                            billboard_uvs.append(billboard_uv_x[2] - billboard_uv_x[0])
                            billboard_uvs.append((1-billboard_uv_y[0]) - (1-billboard_uv_y[2]))
                srtMain["VerticalBillboards"]["FWidth"] = billboard_width
                srtMain["VerticalBillboards"]["FTopPos"] = billboard_top
                srtMain["VerticalBillboards"]["FBottomPos"] = billboard_bottom
                srtMain["VerticalBillboards"]["NNumBillboards"] = billboard_num
                srtMain["VerticalBillboards"]["PTexCoords"] = billboard_uvs
                srtMain["VerticalBillboards"]["PRotated"] = billboard_rotated
                srtMain["VerticalBillboards"]["NNumCutoutVertices"] = billboard0_cutout_nverts
                srtMain["VerticalBillboards"]["PCutoutVertices"] = billboard0_cutout_verts
                srtMain["VerticalBillboards"]["NNumCutoutIndices"] = len(billboard0_cutout_indices)
                srtMain["VerticalBillboards"]["PCutoutIndices"] = billboard0_cutout_indices
        
        #Get and Write Meshes#
        lodsNum = 0
        mesh_index = 0
        meshesNum = 0
        textures_names = []
        for child_coll in main_coll.collection.children:
            if re.search("LOD", child_coll.name):
                mesh_objects = main_coll.collection.children[child_coll.name].objects
                if len(mesh_objects):
                    with open("lodTemplate.json", 'r', encoding='utf-8') as lodfile:
                        srtLod = json.load(lodfile)
                    # Get lodsNum
                    lodsNum += 1
                    # Get Extent
                    if re.search("LOD0", child_coll.name):
                        Extent = np.array(child_coll.objects[0].bound_box)
                    mainMesh = mesh_objects[0]
                    bpy.context.view_layer.objects.active = None
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = mainMesh
                    bpy.context.active_object.select_set(state=True)
                    # Triangulate faces
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    bpy.ops.mesh.select_all(action="SELECT")
                    bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY')
                    bpy.ops.mesh.select_all(action="DESELECT")
                    bpy.ops.object.mode_set(mode='OBJECT')
                    # Split by materials
                    bpy.ops.mesh.separate(type='MATERIAL')
                    # LOD Mesh
                    if mainMesh.name + "_LOD" in mesh_objects:
                        mainMesh_LOD = mesh_objects[mainMesh.name + "_LOD"]
                        bpy.context.view_layer.objects.active = None
                        bpy.ops.object.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active = mainMesh_LOD
                        bpy.context.active_object.select_set(state=True)
                        # Triangulate faces
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY')
                        bpy.ops.mesh.select_all(action="DESELECT")
                        bpy.ops.object.mode_set(mode='OBJECT')
                        # Split by materials
                        bpy.ops.mesh.separate(type='MATERIAL')
                    meshes = main_coll.collection.children[child_coll.name].objects
                    mesh_names = []
                    mesh_lod_names = []
                    for mesh in meshes:
                        if "_LOD" in mesh.name:
                            mesh.name = mesh.name[:mesh.name.find("_LOD")]+ mesh.name[mesh.name.find("_LOD")+4:] + "_LOD"
                            mesh_lod_names.append(mesh.name)
                    for mesh in meshes:
                        if mainMesh.name in mesh.name and not mesh.name.endswith("_LOD"):
                            with open("drawTemplate.json", 'r', encoding='utf-8') as drawfile:
                                srtDraw = json.load(drawfile)
                            if "DiffuseUV" in mesh.data.uv_layers:
                                mesh.data.uv_layers.active = mesh.data.uv_layers["DiffuseUV"]
                            mesh.data.calc_normals_split()
                            if len(mesh.data.uv_layers) > 0:
                                mesh.data.calc_tangents()
                            # Get data per vertex
                            verts = []
                            verts_lod = []
                            normals = []
                            uvs_diff = []
                            uvs_det = []
                            geom_types = []
                            wind_weight1 = []
                            wind_weight2 = []
                            wind_normal1 = []
                            wind_normal2 = []
                            wind_extra1 = []
                            wind_extra2 = []
                            wind_extra3 = []
                            branches_seam_diff = []
                            branches_seam_det = []
                            seam_blending = []
                            tangents = []
                            ambients = []
                            faces = []
                            mesh_names.append(mesh.name)
                            for vert in mesh.data.vertices:
                                # Verts' position
                                verts.append(list(vert.co))
                                # Wind data and Geom Type
                                # Add values if missing just to make the exporter more robust
                                if not vert.groups:
                                    if geom_types:
                                        mesh.vertex_groups["GeomType"].add([vert.index], ((1 + random.choice(geom_types))/5), 'REPLACE')
                                    if wind_weight1:
                                        mesh.vertex_groups["WindWeight1"].add([vert.index], 0, 'REPLACE')
                                    if wind_weight2:
                                        mesh.vertex_groups["WindWeight2"].add([vert.index], 0, 'REPLACE')
                                    if wind_normal1:
                                        mesh.vertex_groups["WindNormal1"].add([vert.index], 0, 'REPLACE')
                                    if wind_normal2:
                                        mesh.vertex_groups["WindNormal2"].add([vert.index], 0, 'REPLACE')
                                    if wind_extra1:
                                        mesh.vertex_groups["WindExtra1"].add([vert.index], 0, 'REPLACE')
                                    if wind_extra2:
                                        mesh.vertex_groups["WindExtra2"].add([vert.index], 0, 'REPLACE')
                                    if wind_extra3:
                                        mesh.vertex_groups["WindExtra3"].add([vert.index], 0, 'REPLACE')
                                for g in vert.groups:
                                    if mesh.vertex_groups[g.group].name == "GeomType":  
                                        geom_types.append(int(g.weight*5-1))
                                    if mesh.vertex_groups[g.group].name == "WindWeight1":
                                        wind_weight1.append(g.weight)
                                    if mesh.vertex_groups[g.group].name == "WindWeight2":
                                        wind_weight2.append(g.weight)
                                    if mesh.vertex_groups[g.group].name == "WindNormal1":
                                        wind_normal1.append(g.weight*16)
                                    if mesh.vertex_groups[g.group].name == "WindNormal2":
                                        wind_normal2.append(g.weight*16)
                                    if mesh.vertex_groups[g.group].name == "WindExtra1":
                                        wind_extra1.append(g.weight*16)
                                    if mesh.vertex_groups[g.group].name == "WindExtra2":
                                        wind_extra2.append(g.weight)
                                    if mesh.vertex_groups[g.group].name == "WindExtra3":
                                        wind_extra3.append(g.weight*2)
                                       
                            # Faces
                            for face in mesh.data.polygons:
                                for vert in face.vertices:
                                    faces.append(vert)
                                    
                            # Verts' normal and tangent
                            normals = GetLoopDataPerVertex(mesh, "NORMAL")
                            tangents = GetLoopDataPerVertex(mesh, "TANGENT")
                            
                            # UVs
                            if "DiffuseUV" in mesh.data.uv_layers:
                                uvs_diff = GetLoopDataPerVertex(mesh, "UV", "DiffuseUV")
                            if "DetailUV" in mesh.data.uv_layers:
                                uvs_det = GetLoopDataPerVertex(mesh, "UV", "DetailUV")
                            if "SeamDiffuseUV" in mesh.data.uv_layers:
                                branches_seam_diff = GetLoopDataPerVertex(mesh, "UV", "SeamDiffuseUV")
                            if "SeamDetailUV" in mesh.data.uv_layers:
                                branches_seam_det = GetLoopDataPerVertex(mesh, "UV", "SeamDetailUV")
                                
                            # Vertex Colors (Ambient Occlusion and Seam Blending)
                            if "AmbientOcclusion" in mesh.data.vertex_colors:
                                ambients = GetLoopDataPerVertex(mesh, "VERTEXCOLOR", "AmbientOcclusion")
                            if "SeamBlending" in mesh.data.vertex_colors:
                                seam_blending = GetLoopDataPerVertex(mesh, "VERTEXCOLOR", "SeamBlending")
                                        
                            # LOD Mesh
                            for mesh2 in meshes:
                                if mesh2.data.materials[0].name ==  mesh.data.materials[0].name and "_LOD" in mesh2.name:
                                    for vert in meshes[mesh2.name].data.vertices:
                                        # Verts' position
                                        verts_lod.append(list(vert.co))
                            if verts_lod and len(verts) != len(verts_lod):
                                verts_lod = verts
                                
                            # Write data per vertex
                            properties = ["START"]
                            components = []
                            offsets = []
                            formats = []
                            attributes = []
                            attributes_components = []
                            num_attrib = 0
                            attrib_name0 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name1 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name2 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name3 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name4 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name5 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name6 = "VERTEX_ATTRIB_UNASSIGNED"
                            for i in range(len(verts)):
                                with open("vertTemplate.json", 'r', encoding='utf-8') as vertfile:
                                    srtVert = json.load(vertfile)
                                offset = 0
                                # Vert position
                                if verts:
                                    srtVert["VertexProperties"][0]["ValueCount"] =  3
                                    srtVert["VertexProperties"][0]["FloatValues"] =  verts[i]
                                    srtVert["VertexProperties"][0]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][0]["ValueOffsets"] = [offset, offset +2, offset + 4]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_POSITION"] * 3
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"]
                                        offsets += [offset, offset +2, offset + 4]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 3
                                        attrib_name0 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes += [attrib_name0]*3
                                        num_attrib += 1
                                    offset += 6
                                # Lod position X
                                if verts_lod:
                                    srtVert["VertexProperties"][3]["ValueCount"] =  3
                                    srtVert["VertexProperties"][3]["FloatValues"] =  verts_lod[i]
                                    srtVert["VertexProperties"][3]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][3]["ValueOffsets"] = [offset, offset + 6, offset + 8]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_LOD_POSITION"] * 3
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"]
                                        offsets += [offset, offset + 6, offset + 8]
                                        if attrib_name0 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name0 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attrib_name1 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        num_attrib += 1
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 3
                                        attributes += [attrib_name0, attrib_name1, attrib_name1]
                                    offset += 6
                                # Diffuse UV
                                if uvs_diff:
                                    srtVert["VertexProperties"][1]["ValueCount"] =  2
                                    srtVert["VertexProperties"][1]["FloatValues"] =  uvs_diff[i]
                                    srtVert["VertexProperties"][1]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][1]["ValueOffsets"] = [offset-4, offset -2]
                                    if properties[-1] != "END":
                                        properties [-2:-2] = ["VERTEX_PROPERTY_DIFFUSE_TEXCOORDS"] * 2
                                        components [-2:-2] = ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y"]
                                        offsets [-2:-2] = [offset-4, offset -2]
                                        formats [-2:-2] = ["VERTEX_FORMAT_HALF_FLOAT"] * 2
                                        if attrib_name1 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name1 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes [-2:-2] = [attrib_name1]*2
                                    offset += 4
                                # Geometry Type
                                if geom_types:
                                    srtVert["VertexProperties"][4]["ValueCount"] =  1
                                    srtVert["VertexProperties"][4]["FloatValues"] =  [geom_types[i]]
                                    srtVert["VertexProperties"][4]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][4]["ValueOffsets"] = [offset]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_GEOMETRY_TYPE_HINT"]
                                        components += ["VERTEX_COMPONENT_X"]
                                        offsets += [offset]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"]
                                        attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes += [attrib_name2]
                                        num_attrib += 1
                                    offset += 2
                                # Wind Extra Data
                                if wind_extra1 and wind_extra2 and wind_extra3 and geom_types[0] != 0:
                                    srtVert["VertexProperties"][9]["ValueCount"] =  3
                                    srtVert["VertexProperties"][9]["FloatValues"] =  [wind_extra1[i], wind_extra2[i], wind_extra3[i]]
                                    srtVert["VertexProperties"][9]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][9]["ValueOffsets"] = [offset, offset +2, offset + 4]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_WIND_EXTRA_DATA"] * 3
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"]
                                        offsets += [offset, offset +2, offset + 4]
                                        if attrib_name2 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 3
                                        attributes += [attrib_name2]*3
                                    offset += 6
                                # Branch Seam Diffuse
                                if branches_seam_diff and seam_blending and geom_types[0] == 0:
                                    srtVert["VertexProperties"][13]["ValueCount"] =  3
                                    srtVert["VertexProperties"][13]["FloatValues"] =  [branches_seam_diff[i][0], branches_seam_diff[i][1], seam_blending[i]]
                                    srtVert["VertexProperties"][13]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][13]["ValueOffsets"] = [offset, offset +2, offset + 4]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE"] * 3
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"]
                                        offsets += [offset, offset +2, offset + 4]
                                        if attrib_name2 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 3
                                        attributes += [attrib_name2]*3
                                    offset += 6
                                # Wind Branch Data
                                if wind_weight1 and wind_weight2 and wind_normal1 and wind_normal2:
                                    srtVert["VertexProperties"][8]["ValueCount"] =  4
                                    srtVert["VertexProperties"][8]["FloatValues"] =  [wind_weight1[i], wind_normal1[i], wind_weight2[i], wind_normal2[i]]
                                    srtVert["VertexProperties"][8]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][8]["ValueOffsets"] = [offset, offset +2, offset + 4, offset + 6]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_WIND_BRANCH_DATA"] * 4
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z", "VERTEX_COMPONENT_W"]
                                        offsets += [offset, offset +2, offset + 4, offset + 6]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 4
                                        attrib_name3 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes += [attrib_name3]*4
                                        num_attrib += 1
                                    offset += 8
                                # Branch Seam Detail
                                if branches_seam_det and seam_blending and geom_types[0] == 0:
                                    srtVert["VertexProperties"][14]["ValueCount"] =  2
                                    srtVert["VertexProperties"][14]["FloatValues"] =  branches_seam_det[i]
                                    srtVert["VertexProperties"][14]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][14]["ValueOffsets"] = [offset, offset +2]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_BRANCH_SEAM_DETAIL"] * 2
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y"]
                                        offsets += [offset, offset +2]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 2
                                        attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes += [attrib_name4]*2
                                        num_attrib += 1
                                    offset += 4
                                # Detail UV
                                if uvs_det and geom_types[0] == 0:
                                    srtVert["VertexProperties"][15]["ValueCount"] =  2
                                    srtVert["VertexProperties"][15]["FloatValues"] =  uvs_det[i]
                                    srtVert["VertexProperties"][15]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                    srtVert["VertexProperties"][15]["ValueOffsets"] = [offset, offset +2]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_DETAIL_TEXCOORDS"] * 2
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y"]
                                        offsets += [offset, offset +2]
                                        if attrib_name4 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 2
                                        attributes += [attrib_name4]*2
                                    offset += 4
                                # half float padding
                                if len(properties[1:])/4 != int(len(properties[1:])/4) and properties[-1] != "END":
                                    if (len(properties)/4) % 1 == 0.25:
                                        properties += ["VERTEX_PROPERTY_PAD", "VERTEX_PROPERTY_UNASSIGNED","VERTEX_PROPERTY_UNASSIGNED"]
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_UNASSIGNED", "VERTEX_COMPONENT_UNASSIGNED"]
                                        offsets += [offset, 0, 0]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"] * 3
                                        attributes += ["VERTEX_ATTRIB_UNASSIGNED"]*3
                                        offset += 2
                                    elif (len(properties[1:])/4) % 1 == 0.5:
                                        properties += ["VERTEX_PROPERTY_UNASSIGNED"]*2
                                        components += ["VERTEX_COMPONENT_UNASSIGNED"]*2
                                        offsets += [0,0]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"]*2
                                        attributes += ["VERTEX_ATTRIB_UNASSIGNED"]*2
                                    elif (len(properties[1:])/4) % 1 == 0.75:
                                        properties += ["VERTEX_PROPERTY_PAD"]
                                        components += ["VERTEX_COMPONENT_X"]
                                        offsets += [offset]
                                        formats += ["VERTEX_FORMAT_HALF_FLOAT"]
                                        attributes += ["VERTEX_ATTRIB_UNASSIGNED"]
                                        offset += 2
                                # Normals
                                if normals:
                                    srtVert["VertexProperties"][2]["ValueCount"] =  3
                                    srtVert["VertexProperties"][2]["FloatValues"] =  normals[i]
                                    srtVert["VertexProperties"][2]["PropertyFormat"] = "VERTEX_FORMAT_BYTE"
                                    srtVert["VertexProperties"][2]["ValueOffsets"] = [offset, offset +1, offset + 2]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_NORMAL"] * 3
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"]
                                        offsets += [offset, offset +1, offset +2]
                                        formats += ["VERTEX_FORMAT_BYTE"] * 3
                                        attrib_name5 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes += [attrib_name5]*3
                                        num_attrib += 1
                                    offset += 3
                                # Ambient Occlusion
                                if ambients:
                                    srtVert["VertexProperties"][18]["ValueCount"] =  1
                                    srtVert["VertexProperties"][18]["FloatValues"] =  [ambients[i]]
                                    srtVert["VertexProperties"][18]["PropertyFormat"] = "VERTEX_FORMAT_BYTE"
                                    srtVert["VertexProperties"][18]["ValueOffsets"] = [offset]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_AMBIENT_OCCLUSION"]
                                        components += ["VERTEX_COMPONENT_X"]
                                        offsets += [offset]
                                        if attrib_name5 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name5 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        formats += ["VERTEX_FORMAT_BYTE"]
                                        attributes += [attrib_name5]
                                    offset += 1
                                # Tangents
                                if tangents:
                                    srtVert["VertexProperties"][16]["ValueCount"] =  3
                                    srtVert["VertexProperties"][16]["FloatValues"] =  tangents[i]
                                    srtVert["VertexProperties"][16]["PropertyFormat"] = "VERTEX_FORMAT_BYTE"
                                    srtVert["VertexProperties"][16]["ValueOffsets"] = [offset, offset +1, offset + 2]
                                    if properties[-1] != "END":
                                        properties += ["VERTEX_PROPERTY_TANGENT"] * 3
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y", "VERTEX_COMPONENT_Z"]
                                        offsets += [offset, offset +1, offset +2]
                                        formats += ["VERTEX_FORMAT_BYTE"] * 3
                                        attrib_name6 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes += [attrib_name6]*3
                                        num_attrib += 1
                                    offset += 3
                                # byte padding
                                if len(properties[1:])/4 != int(len(properties[1:])/4) and properties[-1] != "END":
                                    if (len(properties)/4) % 1 == 0.25:
                                        properties += ["VERTEX_PROPERTY_PAD", "VERTEX_PROPERTY_UNASSIGNED","VERTEX_PROPERTY_UNASSIGNED"]
                                        components += ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_UNASSIGNED", "VERTEX_COMPONENT_UNASSIGNED"]
                                        offsets += [offset, 0, 0]
                                        formats += ["VERTEX_FORMAT_BYTE"] * 3
                                        attributes += ["VERTEX_ATTRIB_UNASSIGNED"]*3
                                        offset += 1
                                    elif (len(properties[1:])/4) % 1 == 0.5:
                                        properties += ["VERTEX_PROPERTY_UNASSIGNED"]*2
                                        components += ["VERTEX_COMPONENT_UNASSIGNED"]*2
                                        offsets += [0,0]
                                        formats += ["VERTEX_FORMAT_BYTE"]*2
                                        attributes += ["VERTEX_ATTRIB_UNASSIGNED"]*2
                                    elif (len(properties[1:])/4) % 1 == 0.75:
                                        properties += ["VERTEX_PROPERTY_PAD"]
                                        components += ["VERTEX_COMPONENT_X"]
                                        offsets += [offset]
                                        formats += ["VERTEX_FORMAT_BYTE"]
                                        attributes += ["VERTEX_ATTRIB_UNASSIGNED"]
                                        offset += 1
                                
                                if properties[-1] != "END": 
                                    offset_final = offset
                                
                                while len(properties) < 65 and properties[-1] != "END":
                                    properties += ["VERTEX_PROPERTY_UNASSIGNED"]
                                    components += ["VERTEX_COMPONENT_UNASSIGNED"]
                                    offsets += [0]
                                    formats += ["VERTEX_FORMAT_UNASSIGNED"]
                                    attributes += ["VERTEX_ATTRIB_UNASSIGNED"]
                                
                                properties.append("END")
                                
                                srtDraw["PVertexData"].append(srtVert)
                            
                            # Write data per mesh
                            srtDraw["NNumVertices"] = len(verts)
                            srtDraw["NRenderStateIndex"] = mesh_index
                            mesh_index += 1
                            srtDraw["NNumIndices"] = len(faces)
                            srtDraw["PIndexData"] = faces
                            srtDraw["PRenderState"]["SVertexDecl"]["UiVertexSize"] = offset_final
                            if 0 in geom_types:
                                srtDraw["PRenderState"]["BBranchesPresent"] = True
                            if 1 in geom_types:
                                srtDraw["PRenderState"]["BFrondsPresent"] = True
                            if 2 in geom_types:
                                srtDraw["PRenderState"]["BLeavesPresent"] = True
                            if 3 in geom_types:
                                srtDraw["PRenderState"]["BFacingLeavesPresent"] = True
                            if 4 in geom_types:
                                srtDraw["PRenderState"]["BRigidMeshesPresent"] = True
                            if len(mesh.data.materials) > 0:
                                mesh_mat = mesh.data.materials[0]
                                mesh_mat_nodes = mesh_mat.node_tree.nodes
                                if "Diffuse Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes["Diffuse Texture"].image:
                                        mesh_diffuse = mesh_mat_nodes["Diffuse Texture"].image.name
                                        srtDraw["PRenderState"]["ApTextures"][0]["Val"] = mesh_diffuse
                                        textures_names.append(mesh_diffuse)
                                if "Normal Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes["Normal Texture"].image:
                                        mesh_normal = mesh_mat_nodes["Normal Texture"].image.name
                                        srtDraw["PRenderState"]["ApTextures"][1]["Val"] = mesh_normal
                                        textures_names.append(mesh_normal)
                                if "Detail Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes["Detail Texture"].image:
                                        mesh_detail = mesh_mat_nodes["Detail Texture"].image.name
                                        srtDraw["PRenderState"]["ApTextures"][2]["Val"] = mesh_detail
                                        textures_names.append(mesh_detail)
                                if "Detail Normal Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes["Detail Normal Texture"].image:
                                        mesh_detail_normal = mesh_mat_nodes["Detail Normal Texture"].image.name
                                        srtDraw["PRenderState"]["ApTextures"][3]["Val"] = mesh_detail_normal
                                        textures_names.append(mesh_detail_normal)
                                if "Specular Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes["Specular Texture"].image:
                                        mesh_specular = mesh_mat_nodes["Specular Texture"].image.name
                                        srtDraw["PRenderState"]["ApTextures"][4]["Val"] = mesh_specular
                                        textures_names.append(mesh_specular)
                                        mesh_transmission = mesh_mat_nodes["Specular Texture"].image.name 
                                        srtDraw["PRenderState"]["ApTextures"][5]["Val"] = mesh_transmission
                                        textures_names.append(mesh_transmission)
                                        
                                srtDraw["PRenderState"]["VAmbientColor"]["x"] = mesh_mat_nodes["Ambient Color"].outputs['Color'].default_value[0]
                                srtDraw["PRenderState"]["VAmbientColor"]["y"] = mesh_mat_nodes["Ambient Color"].outputs['Color'].default_value[1]
                                srtDraw["PRenderState"]["VAmbientColor"]["z"] = mesh_mat_nodes["Ambient Color"].outputs['Color'].default_value[2]
                                srtDraw["PRenderState"]["FAmbientContrastFactor"] = mesh_mat_nodes['Ambient Contrast Factor'].outputs['Value'].default_value
                                srtDraw["PRenderState"]["VDiffuseColor"]["x"] = mesh_mat_nodes['Diffuse Color'].outputs['Color'].default_value[0]
                                srtDraw["PRenderState"]["VDiffuseColor"]["y"] = mesh_mat_nodes['Diffuse Color'].outputs['Color'].default_value[1]
                                srtDraw["PRenderState"]["VDiffuseColor"]["z"] = mesh_mat_nodes['Diffuse Color'].outputs['Color'].default_value[2]
                                srtDraw["PRenderState"]["FDiffuseScalar"] = mesh_mat_nodes['Diffuse Scalar'].outputs['Value'].default_value
                                srtDraw["PRenderState"]["FShininess"] = mesh_mat_nodes['Shininess'].outputs['Value'].default_value
                                srtDraw["PRenderState"]["VSpecularColor"]["x"] = mesh_mat_nodes['Specular Color'].outputs['Color'].default_value[0]
                                srtDraw["PRenderState"]["VSpecularColor"]["y"] = mesh_mat_nodes['Specular Color'].outputs['Color'].default_value[1]
                                srtDraw["PRenderState"]["VSpecularColor"]["z"] = mesh_mat_nodes['Specular Color'].outputs['Color'].default_value[2]
                                srtDraw["PRenderState"]["VTransmissionColor"]["x"] = mesh_mat_nodes['Transmission Color'].outputs['Color'].default_value[0]
                                srtDraw["PRenderState"]["VTransmissionColor"]["y"] = mesh_mat_nodes['Transmission Color'].outputs['Color'].default_value[1]
                                srtDraw["PRenderState"]["VTransmissionColor"]["z"] = mesh_mat_nodes['Transmission Color'].outputs['Color'].default_value[2]
                                srtDraw["PRenderState"]["FTransmissionShadowBrightness"] = mesh_mat_nodes['Transmission Shadow Brightness'].outputs['Value'].default_value
                                srtDraw["PRenderState"]["FTransmissionViewDependency"] = mesh_mat_nodes['Transmission View Dependency'].outputs['Value'].default_value
                                if "Branch Seam Diffuse Texture" in mesh_mat_nodes:
                                    srtDraw["PRenderState"]["FBranchSeamWeight"] = mesh_mat_nodes['Branch Seam Weight'].outputs['Value'].default_value
                                srtDraw["PRenderState"]["FAlphaScalar"] = mesh_mat_nodes['Alpha Scalar'].outputs['Value'].default_value
                                
                                if mesh_mat.use_backface_culling == True:
                                    srtDraw["PRenderState"]["EFaceCulling"] = "CULLTYPE_BACK"
                                if mesh_mat.blend_method == 'OPAQUE':
                                    srtDraw["PRenderState"]["BDiffuseAlphaMaskIsOpaque"] = True
                                if mesh_mat.shadow_method == 'NONE':
                                    srtDraw["PRenderState"]["BCastsShadows"] = False
                                if mesh_mat_nodes['Specular'].inputs["Ambient Occlusion"].links:
                                    if mesh_mat_nodes['Specular'].inputs["Ambient Occlusion"].links[0].from_node == mesh_mat_nodes["Ambient Occlusion"]:
                                        srtDraw["PRenderState"]["BAmbientOcclusion"] = True
                                if mesh_mat_nodes['Ambient Contrast'].inputs['Fac'].links:
                                    if mesh_mat_nodes['Ambient Contrast'].inputs['Fac'].links[0].from_node == mesh_mat_nodes['Ambient Contrast Factor']:
                                        srtDraw["PRenderState"]["EAmbientContrast"] = "EFFECT_ON"
                                if "Detail Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes['Mix Detail Diffuse'].inputs['Fac'].links and mesh_mat_nodes['Mix Detail Normal'].inputs['Fac'].links:
                                        if mesh_mat_nodes['Mix Detail Diffuse'].inputs['Fac'].links[0].from_node == mesh_mat_nodes["Detail Texture"] and mesh_mat_nodes['Mix Detail Normal'].inputs['Fac'].links[0].from_node == mesh_mat_nodes["Detail Normal Texture"]:
                                            srtDraw["PRenderState"]["EDetailLayer"] = "EFFECT_ON"
                                        elif mesh_mat_nodes['Mix Detail Diffuse'].inputs['Fac'].links[0].from_node == mesh_mat_nodes['Mix Detail Seam'] and mesh_mat_nodes['Mix Detail Normal'].inputs['Fac'].links[0].from_node == mesh_mat_nodes['Mix Detail Normal Seam']:
                                            srtDraw["PRenderState"]["EDetailLayer"] = "EFFECT_ON"
                                if mesh_mat_nodes["Mix Specular Color"].inputs['Color2'].links and mesh_mat_nodes['Specular'].inputs['Roughness'].links:
                                    if mesh_mat_nodes["Mix Specular Color"].inputs['Color2'].links[0].from_node == mesh_mat_nodes["Specular Color"] and mesh_mat_nodes['Specular'].inputs['Roughness'].links[0].from_node == mesh_mat_nodes['Invert Shininess']:
                                        srtDraw["PRenderState"]["ESpecular"] = "EFFECT_ON"
                                if mesh_mat_nodes["Mix Transmission Alpha"].inputs["Color2"].links and mesh_mat_nodes["Mix Shader Fresnel"].inputs["Fac"].links and mesh_mat_nodes["Mix Shadow Brightness"].inputs["Fac"].links:
                                    if mesh_mat_nodes["Mix Transmission Alpha"].inputs["Color2"].links[0].from_node == mesh_mat_nodes["Mix Transmission Color"] and mesh_mat_nodes["Mix Shader Fresnel"].inputs["Fac"].links[0].from_node == mesh_mat_nodes['Transmission Fresnel'] and mesh_mat_nodes["Mix Shadow Brightness"].inputs["Fac"].links[0].from_node == mesh_mat_nodes['Transmission Shadow Brightness']:
                                        srtDraw["PRenderState"]["ETransmission"] = "EFFECT_ON"
                                if "Branch Seam Diffuse Texture" in mesh_mat_nodes:
                                    if mesh_mat_nodes['Branch Seam Weight Mult'].outputs['Value'].links:
                                        srtDraw["PRenderState"]["EBranchSeamSmoothing"] = "EFFECT_ON"
                                
                            if child_coll == main_coll.collection.children[-1]:
                                srtDraw["PRenderState"]["BFadeToBillboard"] = True
                            if grass == True:
                                srtDraw["PRenderState"]["BUsedAsGrass"] = True
                                
                            # Properties
                            prop_index = 0
                            properties = properties[1:-1]
                            for property in srtDraw["PRenderState"]["SVertexDecl"]["AsProperties"]:
                                property["AeProperties"] = [properties[prop_index], properties[prop_index+1],
                                properties[prop_index+2], properties[prop_index+3]]
                                property["AePropertyComponents"] = [components[prop_index], components[prop_index+1],
                                components[prop_index+2], components[prop_index+3]]
                                property["AuiVertexOffsets"] = [offsets[prop_index], offsets[prop_index+1],
                                offsets[prop_index+2], offsets[prop_index+3]]
                                property["EFormat"] = formats[prop_index+3]
                                prop_index += 4
                            
                            # Attributes
                            attributes_components = getAttributesComponents(attributes)
                            srtAttributes = srtDraw["PRenderState"]["SVertexDecl"]["AsAttributes"]
                            # Attrib 0
                            if "VERTEX_PROPERTY_POSITION" in properties:
                                attrib0 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_POSITION" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib0[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_POSITION" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib0[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_POSITION" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib0[2] = i
                                srtAttributes[0]["AeAttribs"] = [attributes[x] for x in attrib0]
                                srtAttributes[0]["AeAttribComponents"] = [attributes_components[x] for x in attrib0]
                                srtAttributes[0]["AuiOffsets"] = [offsets[x] for x in attrib0]
                                srtAttributes[0]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 1
                            if "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS" in properties:
                                attrib1 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib1[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib1[1] = i
                                srtAttributes[1]["AeAttribs"] = [attributes[x] for x in attrib1]
                                srtAttributes[1]["AeAttribComponents"] = [attributes_components[x] for x in attrib1]
                                srtAttributes[1]["AuiOffsets"] = [offsets[x] for x in attrib1]
                                srtAttributes[1]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 2
                            if "VERTEX_PROPERTY_NORMAL" in properties:
                                attrib2 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_NORMAL" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib2[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_NORMAL" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib2[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_NORMAL" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib2[2] = i
                                srtAttributes[2]["AeAttribs"] = [attributes[x] for x in attrib2]
                                srtAttributes[2]["AeAttribComponents"] = [attributes_components[x] for x in attrib2]
                                srtAttributes[2]["AuiOffsets"] = [offsets[x] for x in attrib2]
                                srtAttributes[2]["EFormat"] = "VERTEX_FORMAT_BYTE"
                            # Attrib 3
                            if "VERTEX_PROPERTY_LOD_POSITION" in properties:
                                attrib3 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_LOD_POSITION" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib3[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_LOD_POSITION" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib3[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_LOD_POSITION" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib3[2] = i
                                srtAttributes[3]["AeAttribs"] = [attributes[x] for x in attrib3]
                                srtAttributes[3]["AeAttribComponents"] = [attributes_components[x] for x in attrib3]
                                srtAttributes[3]["AuiOffsets"] = [offsets[x] for x in attrib3]
                                srtAttributes[3]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 4
                            if "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT" in properties:
                                attrib4 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib4[0] = i
                                srtAttributes[4]["AeAttribs"] = [attributes[x] for x in attrib4]
                                srtAttributes[4]["AeAttribComponents"] = [attributes_components[x] for x in attrib4]
                                srtAttributes[4]["AuiOffsets"] = [offsets[x] for x in attrib4]
                                srtAttributes[4]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 8
                            if "VERTEX_PROPERTY_WIND_BRANCH_DATA" in properties:
                                attrib8 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_WIND_BRANCH_DATA" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib8[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_WIND_BRANCH_DATA" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib8[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_WIND_BRANCH_DATA" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib8[2] = i
                                    if properties[i] == "VERTEX_PROPERTY_WIND_BRANCH_DATA" and components[i] == "VERTEX_COMPONENT_W":
                                        attrib8[3] = i
                                srtAttributes[8]["AeAttribs"] = [attributes[x] for x in attrib8]
                                srtAttributes[8]["AeAttribComponents"] = [attributes_components[x] for x in attrib8]
                                srtAttributes[8]["AuiOffsets"] = [offsets[x] for x in attrib8]
                                srtAttributes[8]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 9
                            if "VERTEX_PROPERTY_WIND_EXTRA_DATA" in properties:
                                attrib9 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_WIND_EXTRA_DATA" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib9[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_WIND_EXTRA_DATA" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib9[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_WIND_EXTRA_DATA" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib9[2] = i
                                srtAttributes[9]["AeAttribs"] = [attributes[x] for x in attrib9]
                                srtAttributes[9]["AeAttribComponents"] = [attributes_components[x] for x in attrib9]
                                srtAttributes[9]["AuiOffsets"] = [offsets[x] for x in attrib9]
                                srtAttributes[9]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 13
                            if "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE" in properties:
                                attrib13 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib13[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib13[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib13[2] = i
                                srtAttributes[13]["AeAttribs"] = [attributes[x] for x in attrib13]
                                srtAttributes[13]["AeAttribComponents"] = [attributes_components[x] for x in attrib13]
                                srtAttributes[13]["AuiOffsets"] = [offsets[x] for x in attrib13]
                                srtAttributes[13]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 14
                            if "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL" in properties:
                                attrib14 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib14[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib14[1] = i
                                srtAttributes[14]["AeAttribs"] = [attributes[x] for x in attrib14]
                                srtAttributes[14]["AeAttribComponents"] = [attributes_components[x] for x in attrib14]
                                srtAttributes[14]["AuiOffsets"] = [offsets[x] for x in attrib14]
                                srtAttributes[14]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 15
                            if "VERTEX_PROPERTY_DETAIL_TEXCOORDS" in properties:
                                attrib15 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_DETAIL_TEXCOORDS" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib15[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_DETAIL_TEXCOORDS" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib15[1] = i
                                srtAttributes[15]["AeAttribs"] = [attributes[x] for x in attrib15]
                                srtAttributes[15]["AeAttribComponents"] = [attributes_components[x] for x in attrib15]
                                srtAttributes[15]["AuiOffsets"] = [offsets[x] for x in attrib15]
                                srtAttributes[15]["EFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                            # Attrib 16
                            if "VERTEX_PROPERTY_TANGENT" in properties:
                                attrib16 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_TANGENT" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib16[0] = i
                                    if properties[i] == "VERTEX_PROPERTY_TANGENT" and components[i] == "VERTEX_COMPONENT_Y":
                                        attrib16[1] = i
                                    if properties[i] == "VERTEX_PROPERTY_TANGENT" and components[i] == "VERTEX_COMPONENT_Z":
                                        attrib16[2] = i
                                srtAttributes[16]["AeAttribs"] = [attributes[x] for x in attrib16]
                                srtAttributes[16]["AeAttribComponents"] = [attributes_components[x] for x in attrib16]
                                srtAttributes[16]["AuiOffsets"] = [offsets[x] for x in attrib16]
                                srtAttributes[16]["EFormat"] = "VERTEX_FORMAT_BYTE"
                            # Attrib 18
                            if "VERTEX_PROPERTY_AMBIENT_OCCLUSION" in properties:
                                attrib18 = [-1,-1,-1,-1]
                                for i in range(len(properties)):
                                    if properties[i] == "VERTEX_PROPERTY_AMBIENT_OCCLUSION" and components[i] == "VERTEX_COMPONENT_X":
                                        attrib18[0] = i
                                srtAttributes[18]["AeAttribs"] = [attributes[x] for x in attrib18]
                                srtAttributes[18]["AeAttribComponents"] = [attributes_components[x] for x in attrib18]
                                srtAttributes[18]["AuiOffsets"] = [offsets[x] for x in attrib18]
                                srtAttributes[18]["EFormat"] = "VERTEX_FORMAT_BYTE"
                                
                            srtLod["PDrawCalls"].append(srtDraw)
                            
                            # Write P3dRenderStateMain 
                            srtMain["Geometry"]["P3dRenderStateMain"].append(srtDraw["PRenderState"])
                            
                            # Write P3dRenderStateDepth
                            with open("depthTemplate.json", 'r', encoding='utf-8') as depthfile:
                                srtDepth = json.load(depthfile)
                            srtMain["Geometry"]["P3dRenderStateDepth"].append(srtDepth)
                            
                            # Write P3dRenderStateShadow
                            srtShadow = copy.deepcopy(srtDraw["PRenderState"])
                            srtMain["Geometry"]["P3dRenderStateShadow"].append(srtShadow)
                            for i in range(1, len(srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ApTextures"])):
                                srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ApTextures"][i]["Val"] = ""
                            srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ERenderPass"] = "RENDER_PASS_SHADOW_CAST"
                            
                    #Join meshes back again  
                    JoinThem(mesh_names)
                    JoinThem(mesh_lod_names)
                    
                    srtLod["NNumDrawCalls"] = len(mesh_names)
                    meshesNum += len(mesh_names)
                    srtMain["Geometry"]["PLods"].append(srtLod)                  
                        
        # Write Extent
        srtMain["Extents"]["m_cMin"] = list(Extent[0])
        srtMain["Extents"]["m_cMax"] = list(Extent[6])   
                
        # Write lodsNum et meshesNum
        srtMain["Geometry"]["NNum3dRenderStates"] = meshesNum
        srtMain["Geometry"]["NNumLods"] = lodsNum
        
        # Write LodProfile
        srtMain["LodProfile"]["m_f3dRange"] = lodDist_Range3D
        srtMain["LodProfile"]["m_fHighDetail3dDistance"] = lodDist_HighDetail3D
        srtMain["LodProfile"]["m_fLowDetail3dDistance"] = lodDist_LowDetail3D
        srtMain["LodProfile"]["m_fBillboardRange"] = lodDist_RangeBillboard
        srtMain["LodProfile"]["m_fBillboardStartDistance"] = lodDist_StartBillboard
        srtMain["LodProfile"]["m_fBillboardFinalDistance"] = lodDist_EndBillboard
        if lodsNum > 1:
            srtMain["LodProfile"]["m_bLodIsPresent"] = True
            
        # User Strings
        if randomType != "OFF":
            srtMain["PUserStrings"].append(randomType)
        if terrainNormals == True:
            srtMain["PUserStrings"].append("TerrainNormalsOn")
        while len(srtMain["PUserStrings"]) < 5:
            srtMain["PUserStrings"].append("")
            
        # StringTable
        srtMain["StringTable"] = [""]
        if randomType != "OFF":
            srtMain["StringTable"].append(randomType)
        if terrainNormals == True:
            srtMain["StringTable"].append("TerrainNormalsOn")
        srtMain["StringTable"].append("../../../../../bin/shaders/speedtree")
        textures_names = np.array(textures_names)
        unique_textures_names = list(np.unique(textures_names))
        bb_textures_names = np.array(bb_textures_names)
        unique_bb_textures_names = list(np.unique(bb_textures_names))
        srtMain["StringTable"]+= unique_textures_names
        srtMain["StringTable"]+= unique_bb_textures_names    
        
        # Get fileName
        fileName = os.path.basename(filepath)[:-4] + "srt"
        
        # Write fileName
        srtMain["FileName"] = fileName
    
        #%% write the template with generated values
        with open(filepath, 'w', encoding = 'utf-8') as f:
            json.dump(srtMain, f, indent=2)
