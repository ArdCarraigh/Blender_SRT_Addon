# -*- coding: utf-8 -*-
# export_srt_json.py

import bpy
import json
import os
import re
import numpy as np
from copy import deepcopy
from io_mesh_srt.utils import GetLoopDataPerVertex, GetCollection, JoinThem, getAttributesComponents, getVertexProperty, selectOnly, setAttribute, getSphere, isBillboardRotated, TriangulateActiveMesh, SplitMesh, getMaterial, checkWeightPaint, updateVertexProperties

def write_srt_json(context, filepath):
    wm = bpy.context.window_manager
    collision_coll = None
    bb_coll = None
    #horiz_coll = []
    lod_colls = []
    main_coll = GetCollection()
            
    if main_coll:
        main_coll["EShaderGenerationMode"] = 'SHADER_GEN_MODE_UNIFIED_SHADERS'
        if wm.previewLod:
            wm.previewLod = False
        for col in main_coll.children:
            if re.search("Collision Objects", col.name):
                collision_coll = col
            if re.search("Vertical Billboards", col.name):
                bb_coll = col
            #if re.search("Horizontal Billboard", col.name):
            #    horiz_coll = col
            if re.search("LOD", col.name):
                lod_colls.append(col)
        
        # Open Templates
        os.chdir(os.path.dirname(__file__))
        with open("templates/mainTemplate.json", 'r', encoding='utf-8') as mainfile:
            srtMain = json.load(mainfile)
        with open("templates/collisionTemplate.json", 'r', encoding='utf-8') as collisionfile:
            srtCollisionTemplate = json.load(collisionfile)
        with open("templates/lodTemplate.json", 'r', encoding='utf-8') as lodfile:
            srtLodTemplate = json.load(lodfile)
        with open("templates/drawTemplate.json", 'r', encoding='utf-8') as drawfile:
            srtDrawTemplate = json.load(drawfile)
        with open("templates/vertTemplate.json", 'r', encoding='utf-8') as vertfile:
            srtVertTemplate = json.load(vertfile)
        with open("templates/depthTemplate.json", 'r', encoding='utf-8') as depthfile:
            srtDepthTemplate = json.load(depthfile)
            
        # Get and Write Collisions #CollisionObjects
        if collision_coll and collision_coll.objects:
            collisionObjects = collision_coll.objects
            for collisionObject in collisionObjects:
                srtCollision = deepcopy(srtCollisionTemplate)
                    
                if len(collisionObject.data.materials) <= 1:
                    pos, radius = getSphere(collisionObject)
                    srtCollision["m_vCenter1"] = dict(zip(['x','y','z'], pos))
                    srtCollision["m_fRadius"] = radius
                    
                else:
                    selectOnly(collisionObject)
                    bpy.ops.mesh.separate(type='MATERIAL')
                    coll_meshes = []
                    for subcollisionObject in collisionObjects:
                        if collisionObject.name in subcollisionObject.name:
                            coll_meshes.append(subcollisionObject)
                            if "Material_Sphere1" in subcollisionObject.data.materials:
                                pos, radius = getSphere(subcollisionObject)
                                srtCollision["m_vCenter1"] = dict(zip(['x','y','z'], pos))
                                srtCollision["m_fRadius"] = radius
                            if "Material_Sphere2" in subcollisionObject.data.materials:
                                pos, radius = getSphere(subcollisionObject, False)
                                srtCollision["m_vCenter2"] = dict(zip(['x','y','z'], pos))
 
                    JoinThem(coll_meshes)
                    
                srtMain["CollisionObjects"].append(srtCollision)
        else:
            srtMain.pop("CollisionObjects")
            
        # Get and Write Vertical Billboards #VerticalBillboards
        if bb_coll:
            billboard_uvs = []
            billboard_rotated = []
            billboard_cutout_verts = []
            billboard_cutout_indices = []
            billboards = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            cutout = re.findall(r"Mesh_cutout\.?\d*", str([x.name for x in bb_coll.objects]))
            uv_array = np.zeros(12)
            if billboards:
                for i, billboard in enumerate(billboards):
                    bb = bb_coll.objects[billboard].data
                    if not i:
                        verts = bb.vertices
                        bb_width = verts[2].co[0] - verts[0].co[0]
                        bb_top = verts[2].co[2]
                        bb_bottom = verts[0].co[2]
                        number_billboards = len(billboards)
                        mat = bb.materials[0]
                        
                    billboard_uv_x = []
                    billboard_uv_y = []
                    bb.attributes["DiffuseUV"].data.foreach_get("vector", uv_array)
                    check, billboard_uv_x, billboard_uv_y = isBillboardRotated(uv_array)
                    billboard_uv_y = 1 - billboard_uv_y
                    if check:
                        billboard_rotated.append(1)
                        billboard_uvs.append(billboard_uv_x[0])
                        billboard_uvs.append(billboard_uv_y[2])
                        billboard_uvs.append(billboard_uv_x[2] - billboard_uv_x[0])
                        billboard_uvs.append((billboard_uv_y[0]) - (billboard_uv_y[2]))
                    else:
                        billboard_rotated.append(0)
                        billboard_uvs.append(billboard_uv_x[0])
                        billboard_uvs.append(billboard_uv_y[0])
                        billboard_uvs.append(billboard_uv_x[2] - billboard_uv_x[0])
                        billboard_uvs.append((billboard_uv_y[2]) - (billboard_uv_y[0]))
            
            if cutout:            
                cut_obj = bb_coll.objects[cutout[0]]
                selectOnly(cut_obj)
                #Triangulate mesh as user might make a custom cutout with quads
                TriangulateActiveMesh()
                cut = cut_obj.data
                billboard_cutout_nverts = len(cut.vertices)
                cutout_vert_array = np.zeros(billboard_cutout_nverts * 3)
                cut.attributes["position"].data.foreach_get("vector", cutout_vert_array)
                cutout_vert_array[::3] = (cutout_vert_array[::3] - -bb_width * 0.5) / bb_width
                cutout_vert_array[2::3] = (cutout_vert_array[2::3] - bb_bottom) / (bb_top - bb_bottom)
                billboard_cutout_verts = cutout_vert_array.reshape(-1,3)[:,[0,2]].flatten().tolist()
                n_indices = len(cut.polygons) * 3
                billboard_cutout_indices = np.zeros(n_indices, dtype = int)
                cut.attributes[".corner_vert"].data.foreach_get("value", billboard_cutout_indices)
                       
            srtMain["VerticalBillboards"]["FWidth"] = bb_width
            srtMain["VerticalBillboards"]["FTopPos"] = bb_top
            srtMain["VerticalBillboards"]["FBottomPos"] = bb_bottom
            srtMain["VerticalBillboards"]["NNumBillboards"] = number_billboards
            srtMain["VerticalBillboards"]["PTexCoords"] = billboard_uvs
            srtMain["VerticalBillboards"]["PRotated"] = billboard_rotated
            srtMain["VerticalBillboards"]["NNumCutoutVertices"] = billboard_cutout_nverts
            srtMain["VerticalBillboards"]["PCutoutVertices"] = billboard_cutout_verts
            srtMain["VerticalBillboards"]["NNumCutoutIndices"] = n_indices
            srtMain["VerticalBillboards"]["PCutoutIndices"] = billboard_cutout_indices.tolist()
            
        #Get and Write Horizontal Billboard #HorizontalBillboard    #Unsupported by RedEngine
                                                                    # But remains here in case
                                                                    # I decide to support other
                                                                    # shader generation modes
        #if horiz_coll:
        #    horiz_bb_verts = []
        #    horiz_bb_uvs = []
        #    horiz_bb = horiz_coll.objects[0]
        #    bpy.context.view_layer.objects.active = None
        #    bpy.ops.object.select_all(action='DESELECT')
        #    bpy.context.view_layer.objects.active = horiz_bb
        #    bpy.context.active_object.select_set(state=True)
        #    for vert in horiz_bb.data.vertices:
        #        horiz_bb_verts.append(vert.co)
        #    for face in horiz_bb.data.polygons:
        #        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
        #            horiz_bb_uvs.append(horiz_bb.data.uv_layers[0].data[loop_idx].uv.x)
        #            horiz_bb_uvs.append(1 - horiz_bb.data.uv_layers[0].data[loop_idx].uv.y)
        #    srtMain["HorizontalBillboard"]["BPresent"] = True
        #    srtMain["HorizontalBillboard"]["AfTexCoords"] = horiz_bb_uvs
        #    for i in range(4):
        #        srtMain["HorizontalBillboard"]["AvPositions"][i]["x"] = horiz_bb_verts[i][0]
        #        srtMain["HorizontalBillboard"]["AvPositions"][i]["y"] = horiz_bb_verts[i][1]
        #        srtMain["HorizontalBillboard"]["AvPositions"][i]["z"] = horiz_bb_verts[i][2]
                
        #Write Billboard Material #ABillboardRenderStateMain
        bb_textures_names = []
        if bb_coll: #or horiz_coll:
            srtBBMat = srtMain["Geometry"]["ABillboardRenderStateMain"]
            bb_textures_names = getMaterial(main_coll, mat, srtBBMat)
            
            # Deal with Billboard Specificities
            srtBBMat["BUsedAsGrass"] = False
            srtBBMat["ELodMethod"] = "LOD_METHOD_POP"
            srtBBMat["EShaderGenerationMode"] = "SHADER_GEN_MODE_STANDARD"
            srtBBMat["EDetailLayer"] = "EFFECT_OFF"
            srtBBMat["EBranchSeamSmoothing"] = "EFFECT_OFF"
            srtBBMat["EWindLod"] = "WIND_LOD_NONE"
            srtBBMat["BBranchesPresent"] = False
            srtBBMat["BFrondsPresent"] = False
            srtBBMat["BLeavesPresent"] = False
            srtBBMat["BFacingLeavesPresent"] = False
            srtBBMat["BRigidMeshesPresent"] = False
            #if horiz_coll:
            #    srtMain["Geometry"]["ABillboardRenderStateMain"]["BHorzBillboard"] = True
                        
            #Write ABillboardRenderStateShadow
            srtMain["Geometry"]["ABillboardRenderStateShadow"] = deepcopy(srtBBMat)
            for i, texture in enumerate(srtMain["Geometry"]["ABillboardRenderStateShadow"]["ApTextures"]):
                if i:
                    texture["Val"] = ""
            srtMain["Geometry"]["ABillboardRenderStateShadow"]["ERenderPass"] = "RENDER_PASS_SHADOW_CAST"
            srtMain["Geometry"]["ABillboardRenderStateShadow"]["BFadeToBillboard"] = False  
            
        #Get and Write Meshes#
        lodsNum = 0
        mesh_index = 0
        meshesNum = 0
        textures_names = []
        if lod_colls:
            for col in lod_colls:
                objects = col.objects
                if objects:
                    srtLod = deepcopy(srtLodTemplate)
                    # Get lodsNum
                    lodsNum += 1
                    for mesh in objects:
                        # Prepare Mesh
                        selectOnly(mesh)
                        #Edge Split where split normals or uv seam (necessary as these face corner data are stored per vertex in srt)
                        #SplitMesh(mesh.data)
                        TriangulateActiveMesh()
                        bpy.ops.mesh.separate(type='MATERIAL')
                        
                    meshes = []
                    for mesh in objects:
                        srtDraw = deepcopy(srtDrawTemplate)
                        mesh_data = mesh.data
                        mat = mesh_data.materials[0]
                        
                        # Deal with Grass
                        if main_coll["BUsedAsGrass"]:
                            mat["BBranchesPresent"] = False
                            mat["BFrondsPresent"] = True
                            mat["BLeavesPresent"] = True
                            mat["BFacingLeavesPresent"] = True
                            mat["BRigidMeshesPresent"] = True
                            
                        # Compute Normals and Tangents
                        mesh_data.uv_layers.active = mesh_data.uv_layers["DiffuseUV"]
                        mesh_data.calc_normals_split()
                        if mesh_data.uv_layers:
                            mesh_data.calc_tangents()
                            
                        if not mat["BRigidMeshesPresent"] or (mat["BFacingLeavesPresent"] and mat["BRigidMeshesPresent"]): #Dont export pure rigid meshes because not supported by RedEngine
                            meshes.append(mesh)
                            
                            # Faces
                            n_indices = len(mesh_data.polygons) * 3
                            faces = np.zeros(n_indices, dtype = int)
                            mesh_data.attributes[".corner_vert"].data.foreach_get("value", faces)
                            faces = faces.tolist()
                            
                            # Get data per vertex
                            # Verts' position
                            mesh_vertices = mesh_data.vertices
                            n_verts = len(mesh_vertices)
                            n_verts_3 = n_verts * 3
                            verts = np.zeros(n_verts_3)
                            mesh_data.attributes["position"].data.foreach_get("vector", verts)
                            verts = verts.reshape(-1,3).tolist()
                            
                            # Verts' lod position
                            verts_lod = np.zeros(n_verts_3)
                            mesh_data.attributes["vertexLodPosition"].data.foreach_get("vector", verts_lod)
                            verts_lod = verts_lod.reshape(-1,3).tolist()
                            
                            # Leaf Card Corner
                            leaf_card_corners = np.zeros(n_verts_3)
                            mesh_data.attributes["leafCardCorner"].data.foreach_get("vector", leaf_card_corners)
                            leaf_card_corners = leaf_card_corners.reshape(-1,3)[:,[0,2,1]].tolist()
                            
                            # Leaf Card LOD Scalar
                            leaf_card_lod_scalars = np.zeros(n_verts)
                            mesh_data.attributes["leafCardLodScalar"].data.foreach_get("value", leaf_card_lod_scalars)
                            leaf_card_lod_scalars = leaf_card_lod_scalars.tolist()
                            
                            # Leaf Anchor Point
                            leaf_anchor_points = np.zeros(n_verts_3)
                            mesh_data.attributes["leafAnchorPoint"].data.foreach_get("vector", leaf_anchor_points)
                            leaf_anchor_points = leaf_anchor_points.reshape(-1,3).tolist()
                            
                            # Normals
                            normals = GetLoopDataPerVertex(mesh_data, "NORMAL")
                            
                            # Tangents
                            tangents = GetLoopDataPerVertex(mesh_data, "TANGENT")
                            
                            # Diffuse UV
                            uvs_diff = GetLoopDataPerVertex(mesh_data, "UV", "DiffuseUV")
                            
                            # Detail UV
                            uvs_det = GetLoopDataPerVertex(mesh_data, "UV", "DetailUV")
                            
                            # Branch Seam Diffuse UV
                            branches_seam_diff = GetLoopDataPerVertex(mesh_data, "UV", "SeamDiffuseUV")
                            
                            # Branch Seam Detail UV
                            branches_seam_det = GetLoopDataPerVertex(mesh_data, "UV", "SeamDetailUV")
                            
                            #Add values if missing just to make the exporter more robust
                            checkWeightPaint(mesh, mesh_vertices[0].groups[mesh.vertex_groups["GeomType"].index].weight, mesh_vertices[0].groups[mesh.vertex_groups["WindFlag"].index].weight)
                            
                            # Get the vertex group data  # Wind data, Geom Type, AO and Seam Blending
                            geom_types = []
                            wind_weight1 = []
                            wind_weight2 = []
                            wind_normal1 = []
                            wind_normal2 = []
                            wind_extra1 = []
                            wind_extra2 = []
                            wind_extra3 = []
                            wind_flags = []
                            seam_blending = []
                            ambients = []
                            for k, vert in enumerate(mesh_vertices):
                                for g in vert.groups:
                                    match mesh.vertex_groups[g.group].name:
                                        case "GeomType":
                                            geom_types.append(int(g.weight*5-1))
                                        case "WindWeight1":
                                            wind_weight1.append(g.weight)
                                        case "WindWeight2":
                                            wind_weight2.append(g.weight)
                                        case "WindNormal1":
                                            wind_normal1.append(g.weight*16)
                                        case "WindNormal2":
                                            wind_normal2.append(g.weight*16)
                                        case "WindExtra1":
                                            wind_extra1.append(g.weight*16)
                                        case "WindExtra2":
                                            wind_extra2.append(g.weight)
                                        case "WindExtra3":
                                            wind_extra3.append(g.weight*2)
                                        case "WindFlag":
                                            wind_flags.append(g.weight)
                                        case "AmbientOcclusion":
                                            ambients.append(1 - g.weight)
                                        case "SeamBlending":
                                            seam_blending.append(1 - g.weight)
                                        
                            # Geom Types for GRASS
                            if main_coll["BUsedAsGrass"]:
                                geom_types = np.ones(n_verts).tolist()
                                
                            # Write data per vertex
                            properties = []
                            components = []
                            offsets = []
                            formats = []
                            attributes = []
                            num_attrib = 0
                            attrib_name0 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name1 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name2 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name3 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name4 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name5 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name6 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name7 = "VERTEX_ATTRIB_UNASSIGNED"
                            attrib_name8 = "VERTEX_ATTRIB_UNASSIGNED"
                            for i in range(n_verts):
                                srtVert = deepcopy(srtVertTemplate)
                                offset = 0
                                prop_count = 0
                                
                                # Vert position
                                offset, new_offsets, prop_count = getVertexProperty(srtVert, 0, verts[i], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_POSITION", offset, [0,2,4], prop_count)
                                if not i:
                                    updateVertexProperties("VERTEX_PROPERTY_POSITION", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                    attrib_name0 = "VERTEX_ATTRIB_"+str(num_attrib)
                                    num_attrib += 1
                                    attributes.extend([attrib_name0, attrib_name0, attrib_name0])
                                    
                                # Lod position
                                if not mat["BFacingLeavesPresent"] or (mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 3, verts_lod[i], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_LOD_POSITION", offset, [0,6,8], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_LOD_POSITION", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                        if attrib_name0 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name0 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attrib_name1 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        num_attrib += 1
                                        attributes.extend([attrib_name0, attrib_name1, attrib_name1])
                                    
                                # Leaf Card Corner
                                if mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 5, leaf_card_corners[i], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_LEAF_CARD_CORNER", offset, [0,6,8], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_LEAF_CARD_CORNER", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                        if attrib_name0 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name0 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        if attrib_name1 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name1 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes.extend([attrib_name0, attrib_name1, attrib_name1])
                                    
                                # Diffuse UV #Sneaky Special Case
                                srtVert["VertexProperties"][1]["ValueCount"] =  2
                                srtVert["VertexProperties"][1]["FloatValues"] =  uvs_diff[i]
                                srtVert["VertexProperties"][1]["PropertyFormat"] = "VERTEX_FORMAT_HALF_FLOAT"
                                srtVert["VertexProperties"][1]["ValueOffsets"] = [offset-4, offset -2]
                                if not i:
                                    properties [-2:-2] = ["VERTEX_PROPERTY_DIFFUSE_TEXCOORDS", "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS"]
                                    components [-2:-2] = ["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_Y"]
                                    offsets [-2:-2] = [offset-4, offset -2]
                                    formats [-2:-2] = ["VERTEX_FORMAT_HALF_FLOAT", "VERTEX_FORMAT_HALF_FLOAT"]
                                    if attrib_name1 == "VERTEX_ATTRIB_UNASSIGNED":
                                        attrib_name1 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        num_attrib += 1
                                    attributes [-2:-2] = [attrib_name1, attrib_name1]
                                offset += 4
                                prop_count += 2
                                    
                                # Geometry Type
                                if (not mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]) or (mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 4, [geom_types[i]], 1, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT", offset, [0], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_GEOMETRY_TYPE_HINT", "VERTEX_FORMAT_HALF_FLOAT", 1, new_offsets, properties, components, offsets, formats)
                                        attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        num_attrib += 1
                                        attributes.append(attrib_name2)
                                    
                                ### Leaf Card Corner FOR GRASS ###
                                if mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 5, leaf_card_corners[i], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_LEAF_CARD_CORNER", offset, [0,2,4], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_LEAF_CARD_CORNER", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                        if attrib_name2 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes.extend([attrib_name2, attrib_name2, attrib_name2])
                                    
                                # Leaf Card Lod Scalar
                                if mat["BFacingLeavesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 6, [leaf_card_lod_scalars[i]], 1, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR", offset, [0], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR", "VERTEX_FORMAT_HALF_FLOAT", 1, new_offsets, properties, components, offsets, formats)
                                        if mat["BLeavesPresent"]: #Exception for Grass
                                            if attrib_name3 == "VERTEX_ATTRIB_UNASSIGNED":
                                                attrib_name3 = "VERTEX_ATTRIB_"+str(num_attrib)
                                                num_attrib += 1
                                            attributes.append(attrib_name3)
                                        else:
                                            if attrib_name2 == "VERTEX_ATTRIB_UNASSIGNED":
                                                attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                                num_attrib += 1
                                            attributes.append(attrib_name2)
                                    
                                ### Wind Branch Data FOR LEAVES ###
                                if not mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 8, [wind_weight1[i], wind_normal1[i], wind_weight2[i], wind_normal2[i]], 4, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_WIND_BRANCH_DATA", offset, [0,2,4,6], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_WIND_BRANCH_DATA", "VERTEX_FORMAT_HALF_FLOAT", 4, new_offsets, properties, components, offsets, formats)
                                        attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes.extend([attrib_name2, attrib_name2, attrib_name2, attrib_name2])
                                        num_attrib += 1
                                    
                                # Wind Extra Data
                                if not mat["BBranchesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 9, [wind_extra1[i], wind_extra2[i], wind_extra3[i]], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_WIND_EXTRA_DATA", offset, [0,2,4], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_WIND_EXTRA_DATA", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                        if mat["BLeavesPresent"]: #Exception for Grass and Leaves
                                            if attrib_name3 == "VERTEX_ATTRIB_UNASSIGNED":
                                                attrib_name3 = "VERTEX_ATTRIB_"+str(num_attrib)
                                                num_attrib += 1
                                            attributes.extend([attrib_name3, attrib_name3, attrib_name3])
                                        else:
                                            if attrib_name2 == "VERTEX_ATTRIB_UNASSIGNED":
                                                attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                                num_attrib += 1
                                            attributes.extend([attrib_name2, attrib_name2, attrib_name2])
                                    
                                # Branch Seam Diffuse
                                if mat["BBranchesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 13, [branches_seam_diff[i][0], branches_seam_diff[i][1], seam_blending[i]], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE", offset, [0,2,4], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                        if attrib_name2 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name2 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes.extend([attrib_name2, attrib_name2, attrib_name2])
                                    
                                # Wind Branch Data
                                if not mat["BLeavesPresent"] or (mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 8, [wind_weight1[i], wind_normal1[i], wind_weight2[i], wind_normal2[i]], 4, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_WIND_BRANCH_DATA", offset, [0,2,4,6], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_WIND_BRANCH_DATA", "VERTEX_FORMAT_HALF_FLOAT", 4, new_offsets, properties, components, offsets, formats)
                                        if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                            attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            attributes.extend([attrib_name4, attrib_name4, attrib_name4, attrib_name4])
                                            num_attrib += 1
                                        else:
                                            attrib_name3 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            attributes.extend([attrib_name3, attrib_name3, attrib_name3, attrib_name3])
                                            num_attrib += 1
                                    
                                # Branch Seam Detail
                                if mat["BBranchesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 14, branches_seam_det[i], 2, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL", offset, [0,2], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_BRANCH_SEAM_DETAIL", "VERTEX_FORMAT_HALF_FLOAT", 2, new_offsets, properties, components, offsets, formats)
                                        attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes.extend([attrib_name4, attrib_name4])
                                        num_attrib += 1
                                    
                                # Detail UV
                                if mat["BBranchesPresent"]:
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 15, uvs_det[i], 2, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_DETAIL_TEXCOORDS", offset, [0,2], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_DETAIL_TEXCOORDS", "VERTEX_FORMAT_HALF_FLOAT", 2, new_offsets, properties, components, offsets, formats)
                                        if attrib_name4 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes.extend([attrib_name4, attrib_name4])
                                    
                                # Wind Flags
                                if (mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]) or (not mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 10, [wind_flags[i]], 1, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_WIND_FLAGS", offset, [0], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_WIND_FLAGS", "VERTEX_FORMAT_HALF_FLOAT", 1, new_offsets, properties, components, offsets, formats)
                                        if mat["BLeavesPresent"] and not mat["BFacingLeavesPresent"]: # Exception for Leaves
                                            if attrib_name3 == "VERTEX_ATTRIB_UNASSIGNED":
                                                attrib_name3 = "VERTEX_ATTRIB_"+str(num_attrib)
                                                num_attrib += 1
                                            attributes.append(attrib_name3)
                                        elif mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]: # Exception for Facing Leaves
                                            if attrib_name4 == "VERTEX_ATTRIB_UNASSIGNED":
                                                attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                                num_attrib += 1
                                            attributes.append(attrib_name4)
                                    
                                # Leaf Anchor Point
                                if (mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]) or (mat["BLeavesPresent"] and not mat["BFacingLeavesPresent"]):
                                    offset, new_offsets, prop_count = getVertexProperty(srtVert, 11, leaf_anchor_points[i], 3, "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_PROPERTY_LEAF_ANCHOR_POINT", offset, [0,2,4], prop_count)
                                    if not i:
                                        updateVertexProperties("VERTEX_PROPERTY_LEAF_ANCHOR_POINT", "VERTEX_FORMAT_HALF_FLOAT", 3, new_offsets, properties, components, offsets, formats)
                                        if mat["BLeavesPresent"] and not mat["BFacingLeavesPresent"]: #Exception for Leaves
                                            attrib_name4 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            attributes.extend([attrib_name4, attrib_name4, attrib_name4])
                                            num_attrib += 1
                                        elif mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                            attrib_name5 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            attributes.extend([attrib_name5, attrib_name5, attrib_name5])
                                            num_attrib += 1
                                    
                                # half float padding
                                if prop_count/4 != int(prop_count/4):
                                    if (prop_count/4) % 1 == 0.25:
                                        if not i:
                                            properties.extend(["VERTEX_PROPERTY_PAD", "VERTEX_PROPERTY_UNASSIGNED","VERTEX_PROPERTY_UNASSIGNED"])
                                            components.extend(["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_UNASSIGNED", "VERTEX_COMPONENT_UNASSIGNED"])
                                            offsets.extend([offset, 0, 0])
                                            formats.extend(["VERTEX_FORMAT_HALF_FLOAT", "VERTEX_FORMAT_HALF_FLOAT", "VERTEX_FORMAT_HALF_FLOAT"])
                                            attributes.extend(["VERTEX_ATTRIB_UNASSIGNED", "VERTEX_ATTRIB_UNASSIGNED", "VERTEX_ATTRIB_UNASSIGNED"])
                                        offset += 2
                                        prop_count += 1
                                    elif (prop_count/4) % 1 == 0.5:
                                        if not i:
                                            properties.extend(["VERTEX_PROPERTY_UNASSIGNED", "VERTEX_PROPERTY_UNASSIGNED"])
                                            components.extend(["VERTEX_COMPONENT_UNASSIGNED", "VERTEX_COMPONENT_UNASSIGNED"])
                                            offsets.extend([0,0])
                                            formats.extend(["VERTEX_FORMAT_HALF_FLOAT", "VERTEX_FORMAT_HALF_FLOAT"])
                                            attributes.extend(["VERTEX_ATTRIB_UNASSIGNED", "VERTEX_ATTRIB_UNASSIGNED"])
                                    elif (prop_count/4) % 1 == 0.75:
                                        if not i:
                                            properties.append("VERTEX_PROPERTY_PAD")
                                            components.append("VERTEX_COMPONENT_X")
                                            offsets.append(offset)
                                            formats.append("VERTEX_FORMAT_HALF_FLOAT")
                                            attributes.append("VERTEX_ATTRIB_UNASSIGNED")
                                        offset += 2
                                        prop_count += 1
                                        
                                # Normals
                                offset, new_offsets, prop_count = getVertexProperty(srtVert, 2, normals[i], 3, "VERTEX_FORMAT_BYTE", "VERTEX_PROPERTY_NORMAL", offset, [0,1,2], prop_count)
                                if not i:
                                    updateVertexProperties("VERTEX_PROPERTY_NORMAL", "VERTEX_FORMAT_BYTE", 3, new_offsets, properties, components, offsets, formats)
                                    if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                        attrib_name6 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes.extend([attrib_name6, attrib_name6, attrib_name6])
                                        num_attrib += 1
                                    else:
                                        attrib_name5 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes.extend([attrib_name5, attrib_name5, attrib_name5])
                                        num_attrib += 1
                                    
                                # Ambient Occlusion
                                offset, new_offsets, prop_count = getVertexProperty(srtVert, 18, [ambients[i]], 1, "VERTEX_FORMAT_BYTE", "VERTEX_PROPERTY_AMBIENT_OCCLUSION", offset, [0], prop_count)
                                srtVert["VertexProperties"][18]["ByteValues"] =  [int(ambients[i] * 255)]
                                srtVert["VertexProperties"][18]["FloatValues"] = [] #Faster to attribute a new value than to have an "if" in the function
                                if not i:
                                    updateVertexProperties("VERTEX_PROPERTY_AMBIENT_OCCLUSION", "VERTEX_FORMAT_BYTE", 1, new_offsets, properties, components, offsets, formats)
                                    if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                        if attrib_name6 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name6 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes.append(attrib_name6)
                                    else:
                                        if attrib_name5 == "VERTEX_ATTRIB_UNASSIGNED":
                                            attrib_name5 = "VERTEX_ATTRIB_"+str(num_attrib)
                                            num_attrib += 1
                                        attributes.append(attrib_name5)
                                    
                                # Tangents
                                offset, new_offsets, prop_count = getVertexProperty(srtVert, 16, tangents[i], 3, "VERTEX_FORMAT_BYTE", "VERTEX_PROPERTY_TANGENT", offset, [0,1,2], prop_count)
                                if not i:
                                    updateVertexProperties("VERTEX_PROPERTY_TANGENT", "VERTEX_FORMAT_BYTE", 3, new_offsets, properties, components, offsets, formats)
                                    if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                        attrib_name7 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes.extend([attrib_name7, attrib_name7, attrib_name7])
                                        num_attrib += 1
                                    else:
                                        attrib_name6 = "VERTEX_ATTRIB_"+str(num_attrib)
                                        attributes.extend([attrib_name6, attrib_name6, attrib_name6])
                                        num_attrib += 1
                                    
                                # byte padding
                                if prop_count/4 != int(prop_count/4):
                                    if (prop_count/4) % 1 == 0.25:
                                        if not i:
                                            properties.extend(["VERTEX_PROPERTY_PAD", "VERTEX_PROPERTY_UNASSIGNED","VERTEX_PROPERTY_UNASSIGNED"])
                                            components.extend(["VERTEX_COMPONENT_X", "VERTEX_COMPONENT_UNASSIGNED", "VERTEX_COMPONENT_UNASSIGNED"])
                                            offsets.extend([offset, 0, 0])
                                            formats.extend(["VERTEX_FORMAT_BYTE", "VERTEX_FORMAT_BYTE", "VERTEX_FORMAT_BYTE"])
                                            attributes.extend(["VERTEX_ATTRIB_UNASSIGNED", "VERTEX_ATTRIB_UNASSIGNED", "VERTEX_ATTRIB_UNASSIGNED"])
                                        offset += 1
                                        prop_count += 1
                                    elif (prop_count/4) % 1 == 0.5:
                                        if not i:
                                            properties.extend(["VERTEX_PROPERTY_UNASSIGNED", "VERTEX_PROPERTY_UNASSIGNED"])
                                            components.extend(["VERTEX_COMPONENT_UNASSIGNED","VERTEX_COMPONENT_UNASSIGNED"])
                                            offsets.extend([0,0])
                                            formats.extend(["VERTEX_FORMAT_BYTE", "VERTEX_FORMAT_BYTE"])
                                            attributes.extend(["VERTEX_ATTRIB_UNASSIGNED", "VERTEX_ATTRIB_UNASSIGNED"])
                                    elif (prop_count/4) % 1 == 0.75:
                                        if not i:
                                            properties.append("VERTEX_PROPERTY_PAD")
                                            components.append("VERTEX_COMPONENT_X")
                                            offsets.append(offset)
                                            formats.append("VERTEX_FORMAT_BYTE")
                                            attributes.append("VERTEX_ATTRIB_UNASSIGNED")
                                        offset += 1
                                        prop_count += 1
                                
                                if not i:
                                    offset_final = offset
                                    
                                while len(properties) < 64:
                                    properties.append("VERTEX_PROPERTY_UNASSIGNED")
                                    components.append("VERTEX_COMPONENT_UNASSIGNED")
                                    offsets.append(0)
                                    formats.append("VERTEX_FORMAT_UNASSIGNED")
                                    attributes.append("VERTEX_ATTRIB_UNASSIGNED")
                                
                                srtDraw["PVertexData"].append(srtVert)
                            
                            # Write data per mesh
                            srtDraw["NNumVertices"] = n_verts
                            srtDraw["NRenderStateIndex"] = mesh_index
                            mesh_index += 1
                            srtDraw["NNumIndices"] = n_indices
                            srtDraw["PIndexData"] = faces
                            srtMat = srtDraw["PRenderState"]
                            srtMat["SVertexDecl"]["UiVertexSize"] = offset_final
                            
                            # Write mesh material
                            textures_names.extend(getMaterial(main_coll, mat, srtMat))
                            if col == lod_colls[-1] and bb_coll: #or horiz_coll:
                                srtMat["BFadeToBillboard"] = True
                                
                            # Properties
                            properties_reshaped = np.array(properties).reshape(-1,4).tolist()
                            components_reshaped = np.array(components).reshape(-1,4).tolist()
                            offsets_reshaped = np.array(offsets).reshape(-1,4).tolist()
                            formats_reshaped = np.array(formats).reshape(-1,4).tolist()
                            for i, property in enumerate(srtMat["SVertexDecl"]["AsProperties"]):
                                property["AeProperties"] = properties_reshaped[i]
                                property["AePropertyComponents"] = components_reshaped[i]
                                property["AuiVertexOffsets"] = offsets_reshaped[i]
                                property["EFormat"] = formats_reshaped[i][-1]
                            
                            # Attributes
                            attributes_components = getAttributesComponents(attributes)
                            srtAttributes = srtMat["SVertexDecl"]["AsAttributes"]
                            # Attrib 0
                            setAttribute(srtAttributes, 0, "VERTEX_PROPERTY_POSITION", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 1
                            setAttribute(srtAttributes, 1, "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 2
                            setAttribute(srtAttributes, 2, "VERTEX_PROPERTY_NORMAL", "VERTEX_FORMAT_BYTE", properties, components, offsets, attributes_components, attributes)
                            # Attrib 3
                            setAttribute(srtAttributes, 3, "VERTEX_PROPERTY_LOD_POSITION", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 4
                            setAttribute(srtAttributes, 4, "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 5
                            setAttribute(srtAttributes, 5, "VERTEX_PROPERTY_LEAF_CARD_CORNER", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 6
                            setAttribute(srtAttributes, 6, "VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 8
                            setAttribute(srtAttributes, 8, "VERTEX_PROPERTY_WIND_BRANCH_DATA", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 9
                            setAttribute(srtAttributes, 9, "VERTEX_PROPERTY_WIND_EXTRA_DATA", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 10
                            setAttribute(srtAttributes, 10, "VERTEX_PROPERTY_WIND_FLAGS", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 11
                            setAttribute(srtAttributes, 11, "VERTEX_PROPERTY_LEAF_ANCHOR_POINT", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 13
                            setAttribute(srtAttributes, 13, "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 14
                            setAttribute(srtAttributes, 14, "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 15
                            setAttribute(srtAttributes, 15, "VERTEX_PROPERTY_DETAIL_TEXCOORDS", "VERTEX_FORMAT_HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 16
                            setAttribute(srtAttributes, 16, "VERTEX_PROPERTY_TANGENT", "VERTEX_FORMAT_BYTE", properties, components, offsets, attributes_components, attributes)
                            # Attrib 18
                            setAttribute(srtAttributes, 18, "VERTEX_PROPERTY_AMBIENT_OCCLUSION", "VERTEX_FORMAT_BYTE", properties, components, offsets, attributes_components, attributes)
                                
                            srtLod["PDrawCalls"].append(srtDraw)
                            
                            # Write P3dRenderStateMain 
                            srtMain["Geometry"]["P3dRenderStateMain"].append(srtMat)
                            
                            # Write P3dRenderStateDepth
                            srtDepth = deepcopy(srtDepthTemplate)
                            srtMain["Geometry"]["P3dRenderStateDepth"].append(srtDepth)
                            
                            # Write P3dRenderStateShadow
                            srtMain["Geometry"]["P3dRenderStateShadow"].append(deepcopy(srtMat))
                            for i, texture in enumerate(srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ApTextures"]):
                                if i:
                                    texture["Val"] = ""
                            srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ERenderPass"] = "RENDER_PASS_SHADOW_CAST"
                            srtMain["Geometry"]["P3dRenderStateShadow"][-1]["BFadeToBillboard"] = False
                            
                    #Join meshes back again  
                    JoinThem(meshes)
                    
                    # Write Extent
                    if col == lod_colls[0]:
                        Extent = np.array(objects[0].bound_box)
                        srtMain["Extents"]["m_cMin"] = list(Extent[0])
                        srtMain["Extents"]["m_cMax"] = list(Extent[6]) 
                    
                    n_meshes = len(meshes)
                    srtLod["NNumDrawCalls"] = n_meshes
                    meshesNum += n_meshes
                    srtMain["Geometry"]["PLods"].append(srtLod)                  
                          
        # Write lodsNum et meshesNum
        srtMain["Geometry"]["NNum3dRenderStates"] = meshesNum
        srtMain["Geometry"]["NNumLods"] = lodsNum
        
        # Write LodProfile
        for k in srtMain["LodProfile"]:
            if k in main_coll:
                srtMain["LodProfile"][k] = main_coll[k]
        if lodsNum > 0:
            srtMain["LodProfile"]["m_bLodIsPresent"] = True
            
        #Write Wind
        for k in srtMain["Wind"]:
            if k == 'Params':
                srtMain["Wind"][k] = main_coll[k].to_dict()
            elif k == 'm_abOptions':
                srtMain["Wind"][k] = list(map(bool, main_coll[k].to_list()))
            elif k == 'm_afBranchWindAnchor':
                srtMain["Wind"][k] = main_coll[k].to_list()
            else:
                srtMain["Wind"][k] = main_coll[k]
            
        # User Strings and StringTable
        srtMain["StringTable"] = [""]
        if main_coll["EBillboardRandomType"] != 'NoBillboard':
            srtMain["PUserStrings"].append(main_coll["EBillboardRandomType"])
            srtMain["StringTable"].append(main_coll["EBillboardRandomType"])
        if main_coll["ETerrainNormals"] != 'TerrainNormalsOff':
            srtMain["StringTable"].append(main_coll["ETerrainNormals"])
            srtMain["PUserStrings"].append(main_coll["ETerrainNormals"])
        srtMain["StringTable"].append("../../../../../bin/shaders/speedtree")
        srtMain["StringTable"].extend(list(np.unique(np.array(textures_names))))
        srtMain["StringTable"].extend(list(np.unique(np.array(bb_textures_names))))
        while len(srtMain["PUserStrings"]) < 5:
            srtMain["PUserStrings"].append("")
        
        # Get fileName
        fileName = os.path.splitext(os.path.basename(filepath))[0] + ".srt"
        srtMain["FileName"] = fileName
        
        # Write the template with generated values
        wkit_path = bpy.context.preferences.addons[__package__].preferences.wolvenkit_cli
        check_wkit_path = os.path.exists(wkit_path)
        if not check_wkit_path:
            filepath += ".json"
        with open(filepath, 'w', encoding = 'utf-8') as f:
            json.dump(srtMain, f, indent=2)
        
        if check_wkit_path:
            import subprocess
            command = [str(wkit_path), "--input", filepath, "--json2srt"]
            subprocess.run(command)