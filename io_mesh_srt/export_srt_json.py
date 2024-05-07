# -*- coding: utf-8 -*-
# export_srt_json.py

import bpy
import json
import os
import re
import numpy as np
import subprocess
from copy import deepcopy
from io_mesh_srt.utils import GetLoopDataPerVertex, GetCollection, JoinThem, getAttributesComponents, selectOnly, setAttribute, getSphere, TriangulateActiveMesh, SplitMesh, getMaterial, checkWeightPaint, updateVertexProperties

def write_srt_json(context, filepath):
    wm = bpy.context.window_manager.speedtree
    collision_coll = None
    bb_coll = None
    #horiz_coll = []
    lod_colls = []
    main_coll = GetCollection()
            
    if main_coll:
        main_coll["EShaderGenerationMode"] = 'UNIFIED_SHADERS'
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
        with open("templates/drawTemplate.json", 'r', encoding='utf-8') as drawfile:
            srtDrawTemplate = json.load(drawfile)
        with open("templates/renderTemplate.json", 'r', encoding='utf-8') as renderfile:
            srtRenderTemplate = json.load(renderfile)
            
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
                number_billboards = len(billboards)
                for i, billboard in enumerate(billboards):
                    bb = bb_coll.objects[billboard].data
                    if not i:
                        verts = bb.vertices
                        bb_width = verts[2].co[0] - verts[0].co[0]
                        bb_top = verts[2].co[2]
                        bb_bottom = verts[0].co[2]
                        mat = bb.materials[0]
                        
                    bb.attributes["DiffuseUV"].data.foreach_get("vector", uv_array)
                    billboard_uv_x = uv_array[::2]
                    billboard_uv_y = uv_array[1::2]
                    index = np.argmin(billboard_uv_x + billboard_uv_y)
                    if index == 4:
                        billboard_rotated.append(True)
                    else:
                        billboard_rotated.append(False)
                    billboard_uv_y = 1 - billboard_uv_y
                    billboard_uvs.append({"x" : billboard_uv_x[0], "y" : billboard_uv_y[0], "z" : billboard_uv_x[2] - billboard_uv_x[0], "w" : billboard_uv_y[2] - billboard_uv_y[0]})
            
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
                billboard_cutout_verts = [dict(zip(["x", "y"], x)) for x in cutout_vert_array.reshape(-1,3)[:,[0,2]]]
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
            srtBBMat["ELodMethod"] = "POP"
            srtBBMat["EShaderGenerationMode"] = "STANDARD"
            srtBBMat["EDetailLayer"] = "OFF"
            srtBBMat["EBranchSeamSmoothing"] = "OFF"
            srtBBMat["EWindLod"] = "NONE"
            srtBBMat["BBranchesPresent"] = False
            srtBBMat["BFrondsPresent"] = False
            srtBBMat["BLeavesPresent"] = False
            srtBBMat["BFacingLeavesPresent"] = False
            srtBBMat["BRigidMeshesPresent"] = False
            #if horiz_coll:
            #    srtMain["Geometry"]["ABillboardRenderStateMain"]["BHorzBillboard"] = True
                        
            #Write ABillboardRenderStateShadow
            srtMain["Geometry"]["ABillboardRenderStateShadow"] = deepcopy(srtBBMat)
            for i,_ in enumerate(srtMain["Geometry"]["ABillboardRenderStateShadow"]["ApTextures"]):
                if i:
                    srtMain["Geometry"]["ABillboardRenderStateShadow"]["ApTextures"][i] = ""
            srtMain["Geometry"]["ABillboardRenderStateShadow"]["ERenderPass"] = "SHADOW_CAST"
            srtMain["Geometry"]["ABillboardRenderStateShadow"]["BFadeToBillboard"] = False
            
        #Get and Write Meshes#
        lodsNum = 0
        mesh_index = 0
        textures_names = []
        if lod_colls:
            for col in lod_colls:
                objects = col.objects
                if objects:
                    srtLod = {"PDrawCalls":[]}
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
                        meshes.append(mesh)
                        mesh_data = mesh.data
                        mat = mesh_data.materials[0]
                        if not mat["BRigidMeshesPresent"] or (mat["BFacingLeavesPresent"] and mat["BRigidMeshesPresent"]): #Dont export pure rigid meshes because not supported by RedEngine
                            srtRender = deepcopy(srtRenderTemplate)
                            srtDraw = deepcopy(srtDrawTemplate)
                            srtDraw["RenderStateIdx"] = mesh_index
                            mesh_index += 1

                            # Deal with Grass
                            if main_coll["BUsedAsGrass"]:
                                mat["BBranchesPresent"] = False
                                mat["BFrondsPresent"] = True
                                mat["BLeavesPresent"] = True
                                mat["BFacingLeavesPresent"] = True
                                mat["BRigidMeshesPresent"] = True
                                
                            # Compute Tangents
                            mesh_data.uv_layers.active = mesh_data.uv_layers["DiffuseUV"]
                            mesh_data.calc_tangents()

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
                            leaf_card_corners = leaf_card_corners.reshape(-1,3)[:,[1,2,0]].tolist()
                            
                            # Leaf Card LOD Scalar
                            leaf_card_lod_scalars = np.zeros(n_verts)
                            mesh_data.attributes["leafCardLodScalar"].data.foreach_get("value", leaf_card_lod_scalars)
                            leaf_card_lod_scalars = leaf_card_lod_scalars.tolist()
                            
                            # Leaf Anchor Point
                            leaf_anchor_points = np.zeros(n_verts_3)
                            mesh_data.attributes["leafAnchorPoint"].data.foreach_get("vector", leaf_anchor_points)
                            leaf_anchor_points = leaf_anchor_points.reshape(-1,3).tolist()
                            
                            # Normals
                            normals = np.round((np.array(GetLoopDataPerVertex(mesh_data, "NORMAL")) / 2 + 0.5) * 255).tolist()
                            
                            # Tangents
                            tangents = np.round((np.array(GetLoopDataPerVertex(mesh_data, "TANGENT")) / 2 + 0.5) * 255).tolist()
                            
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
                                            ambients.append(round((1 - g.weight) * 255))
                                        case "SeamBlending":
                                            seam_blending.append(1 - g.weight)
                                            
                            # Assemble different data types
                            branches_seam_diff = np.c_[branches_seam_diff, seam_blending].tolist()
                            wind_branch = np.c_[wind_weight1, wind_normal1, wind_weight2, wind_normal2].tolist()
                            wind_extra = np.c_[wind_extra1, wind_extra2, wind_extra3].tolist()
                                        
                            # Geom Types for GRASS
                            if main_coll["BUsedAsGrass"]:
                                geom_types = np.ones(n_verts).tolist()
                                
                            # Write Mesh Data
                            srtDraw["IndexData"] = faces
                            vert_data = srtDraw["VertexData"]
                            vert_data["count"] = n_verts
                            
                            properties = []
                            components = []
                            offsets = []
                            formats = []
                            attributes = []
                            num_attrib = 0
                            offset = 0
                            attrib_name0 = None
                            attrib_name1 = None
                            attrib_name2 = None
                            attrib_name3 = None
                            attrib_name4 = None
                            attrib_name5 = None
                            attrib_name6 = None
                            attrib_name7 = None
                            attrib_name8 = None
                            
                            #Vert position
                            vert_data["pos"] = verts
                            offset = updateVertexProperties("POSITION", "HALF_FLOAT", 3, offset, [0,2,4], properties, components, offsets, formats)
                            attrib_name0 = "ATTRIBUE"+str(num_attrib)
                            num_attrib += 1
                            attributes.extend([attrib_name0, attrib_name0, attrib_name0])
                            
                            # Lod position
                            if not mat["BFacingLeavesPresent"] or (mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                vert_data["lod_pos"] = verts_lod
                                offset = updateVertexProperties("LOD_POSITION", "HALF_FLOAT", 3, offset, [0,6,8], properties, components, offsets, formats)
                                if attrib_name0 is None:
                                    attrib_name0 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attrib_name1 = "ATTRIBUE"+str(num_attrib)
                                num_attrib += 1
                                attributes.extend([attrib_name0, attrib_name1, attrib_name1])
                                
                            # Leaf Card Corner
                            if mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]:
                                vert_data["leaf_card_corner"] = leaf_card_corners
                                offset = updateVertexProperties("LEAF_CARD_CORNER", "HALF_FLOAT", 3, offset, [0,6,8], properties, components, offsets, formats)
                                if attrib_name0 is None:
                                    attrib_name0 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                if attrib_name1 is None:
                                    attrib_name1 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attributes.extend([attrib_name0, attrib_name1, attrib_name1])
                                
                            # Diffuse UV #Sneaky Special Case
                            vert_data["diffuse"] =  uvs_diff   
                            properties [-2:-2] = ["DIFFUSE_TEXTURE_COORDINATES", "DIFFUSE_TEXTURE_COORDINATES"]
                            components [-2:-2] = ["X", "Y"]
                            offsets [-2:-2] = [offset-4, offset -2]
                            formats [-2:-2] = ["HALF_FLOAT", "HALF_FLOAT"]
                            if attrib_name1 is None:
                                attrib_name1 = "ATTRIBUE"+str(num_attrib)
                                num_attrib += 1
                            attributes [-2:-2] = [attrib_name1, attrib_name1]
                            offset += 4
                                
                            # Geometry Type
                            if (not mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]) or (mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                vert_data["geometry_type_hint"] = geom_types
                                offset = updateVertexProperties("GEOMETRY_TYPE_HINT", "HALF_FLOAT", 1, offset, [0], properties, components, offsets, formats)
                                attrib_name2 = "ATTRIBUE"+str(num_attrib)
                                num_attrib += 1
                                attributes.append(attrib_name2)
                                
                            ### Leaf Card Corner FOR GRASS ###
                            if mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]:
                                vert_data["leaf_card_corner"] = leaf_card_corners
                                offset = updateVertexProperties("LEAF_CARD_CORNER", "HALF_FLOAT", 3, offset, [0,2,4], properties, components, offsets, formats)
                                if attrib_name2 is None:
                                    attrib_name2 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attributes.extend([attrib_name2, attrib_name2, attrib_name2])
                                
                            # Leaf Card Lod Scalar
                            if mat["BFacingLeavesPresent"]:
                                vert_data["leaf_card_lod_scalar"] = leaf_card_lod_scalars
                                offset = updateVertexProperties("LEAF_CARD_LOD_SCALAR", "HALF_FLOAT", 1, offset, [0], properties, components, offsets, formats)
                                if mat["BLeavesPresent"]: #Exception for Grass
                                    if attrib_name3 is None:
                                        attrib_name3 = "ATTRIBUE"+str(num_attrib)
                                        num_attrib += 1
                                    attributes.append(attrib_name3)
                                else:
                                    if attrib_name2 is None:
                                        attrib_name2 = "ATTRIBUE"+str(num_attrib)
                                        num_attrib += 1
                                    attributes.append(attrib_name2)
                                
                            ### Wind Branch Data FOR LEAVES ###
                            if not mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]:
                                vert_data["wind_branch"] = wind_branch
                                offset = updateVertexProperties("WIND_BRANCH_DATA", "HALF_FLOAT", 4, offset, [0,2,4,6], properties, components, offsets, formats)
                                attrib_name2 = "ATTRIBUE"+str(num_attrib)
                                attributes.extend([attrib_name2, attrib_name2, attrib_name2, attrib_name2])
                                num_attrib += 1
                                
                            # Wind Extra Data
                            if not mat["BBranchesPresent"]:
                                vert_data["wind_extra"] = wind_extra
                                offset = updateVertexProperties("WIND_EXTRA_DATA", "HALF_FLOAT", 3, offset, [0,2,4], properties, components, offsets, formats)
                                if mat["BLeavesPresent"]: #Exception for Grass and Leaves
                                    if attrib_name3 is None:
                                        attrib_name3 = "ATTRIBUE"+str(num_attrib)
                                        num_attrib += 1
                                    attributes.extend([attrib_name3, attrib_name3, attrib_name3])
                                else:
                                    if attrib_name2 is None:
                                        attrib_name2 = "ATTRIBUE"+str(num_attrib)
                                        num_attrib += 1
                                    attributes.extend([attrib_name2, attrib_name2, attrib_name2])
                                
                            # Branch Seam Diffuse
                            if mat["BBranchesPresent"]:
                                vert_data["branch_seam_diffuse"] = branches_seam_diff
                                offset = updateVertexProperties("BRANCH_SEAM_DIFFUSE", "HALF_FLOAT", 3, offset, [0,2,4], properties, components, offsets, formats)
                                if attrib_name2 is None:
                                    attrib_name2 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attributes.extend([attrib_name2, attrib_name2, attrib_name2])
                                
                            # Wind Branch Data
                            if not mat["BLeavesPresent"] or (mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                vert_data["wind_branch"] = wind_branch
                                offset = updateVertexProperties("WIND_BRANCH_DATA", "HALF_FLOAT", 4, offset, [0,2,4,6], properties, components, offsets, formats)
                                if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                    attrib_name4 = "ATTRIBUE"+str(num_attrib)
                                    attributes.extend([attrib_name4, attrib_name4, attrib_name4, attrib_name4])
                                    num_attrib += 1
                                else:
                                    attrib_name3 = "ATTRIBUE"+str(num_attrib)
                                    attributes.extend([attrib_name3, attrib_name3, attrib_name3, attrib_name3])
                                    num_attrib += 1
                                
                            # Branch Seam Detail
                            if mat["BBranchesPresent"]:
                                vert_data["branch_seam_detail"] = branches_seam_det
                                offset = updateVertexProperties("BRANCH_SEAM_DETAIL", "HALF_FLOAT", 2, offset, [0,2], properties, components, offsets, formats)
                                attrib_name4 = "ATTRIBUE"+str(num_attrib)
                                attributes.extend([attrib_name4, attrib_name4])
                                num_attrib += 1
                                
                            # Detail UV
                            if mat["BBranchesPresent"]:
                                vert_data["branch_detail_texture"] = uvs_det
                                offset = updateVertexProperties("DETAIL_TEXTURE_COORDINATES", "HALF_FLOAT", 2, offset, [0,2], properties, components, offsets, formats)
                                if attrib_name4 is None:
                                    attrib_name4 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attributes.extend([attrib_name4, attrib_name4])
                                
                            # Wind Flags
                            if (mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]) or (not mat["BFacingLeavesPresent"] and mat["BLeavesPresent"]):
                                vert_data["wind_flags"] = wind_flags
                                offset = updateVertexProperties("WIND_FLAGS", "HALF_FLOAT", 1, offset, [0], properties, components, offsets, formats)
                                if mat["BLeavesPresent"] and not mat["BFacingLeavesPresent"]: # Exception for Leaves
                                    if attrib_name3 is None:
                                        attrib_name3 = "ATTRIBUE"+str(num_attrib)
                                        num_attrib += 1
                                    attributes.append(attrib_name3)
                                elif mat["BFacingLeavesPresent"] and not mat["BLeavesPresent"]: # Exception for Facing Leaves
                                    if attrib_name4 is None:
                                        attrib_name4 = "ATTRIBUE"+str(num_attrib)
                                        num_attrib += 1
                                    attributes.append(attrib_name4)
                                
                            # Leaf Anchor Point
                            if (mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]) or (mat["BLeavesPresent"] and not mat["BFacingLeavesPresent"]):
                                vert_data["leaf_anchor_point"] = leaf_anchor_points
                                offset = updateVertexProperties("LEAF_ANCHOR_POINT", "HALF_FLOAT", 3, offset, [0,2,4], properties, components, offsets, formats)
                                if mat["BLeavesPresent"] and not mat["BFacingLeavesPresent"]: #Exception for Leaves
                                    attrib_name4 = "ATTRIBUE"+str(num_attrib)
                                    attributes.extend([attrib_name4, attrib_name4, attrib_name4])
                                    num_attrib += 1
                                elif mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                    attrib_name5 = "ATTRIBUE"+str(num_attrib)
                                    attributes.extend([attrib_name5, attrib_name5, attrib_name5])
                                    num_attrib += 1
                                
                            # half float padding
                            prop_count = len(properties)
                            if prop_count/4 != int(prop_count/4):
                                if (prop_count/4) % 1 == 0.25:
                                    properties.extend(["MISC_SEMANTIC", "UNASSIGNED","UNASSIGNED"])
                                    components.extend(["X", "UNASSIGNED", "UNASSIGNED"])
                                    offsets.extend([offset, 0, 0])
                                    formats.extend(["HALF_FLOAT", "HALF_FLOAT", "HALF_FLOAT"])
                                    attributes.extend(["UNASSIGNED", "UNASSIGNED", "UNASSIGNED"])
                                    offset += 2
                                elif (prop_count/4) % 1 == 0.5:
                                    properties.extend(["UNASSIGNED", "UNASSIGNED"])
                                    components.extend(["UNASSIGNED", "UNASSIGNED"])
                                    offsets.extend([0,0])
                                    formats.extend(["HALF_FLOAT", "HALF_FLOAT"])
                                    attributes.extend(["UNASSIGNED", "UNASSIGNED"])
                                elif (prop_count/4) % 1 == 0.75:
                                    properties.append("MISC_SEMANTIC")
                                    components.append("X")
                                    offsets.append(offset)
                                    formats.append("HALF_FLOAT")
                                    attributes.append("UNASSIGNED")
                                    offset += 2
                                         
                            # Normals
                            vert_data["normals"] = normals
                            offset = updateVertexProperties("NORMAL", "BYTE", 3, offset, [0,1,2], properties, components, offsets, formats)
                            if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                attrib_name6 = "ATTRIBUE"+str(num_attrib)
                                attributes.extend([attrib_name6, attrib_name6, attrib_name6])
                                num_attrib += 1
                            else:
                                attrib_name5 = "ATTRIBUE"+str(num_attrib)
                                attributes.extend([attrib_name5, attrib_name5, attrib_name5])
                                num_attrib += 1
                                
                            # Ambient Occlusion
                            vert_data["ambient_occlusion"] = ambients
                            offset = updateVertexProperties("AMBIENT_OCCLUSION", "BYTE", 1, offset, [0], properties, components, offsets, formats)
                            if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                if attrib_name6 is None:
                                    attrib_name6 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attributes.append(attrib_name6)
                            else:
                                if attrib_name5 is None:
                                    attrib_name5 = "ATTRIBUE"+str(num_attrib)
                                    num_attrib += 1
                                attributes.append(attrib_name5)
                                
                            # Tangents
                            vert_data["tangents"] = tangents
                            offset = updateVertexProperties("TANGENT", "BYTE", 3, offset, [0,1,2], properties, components, offsets, formats)
                            if mat["BLeavesPresent"] and mat["BFacingLeavesPresent"]: #Exception for Grass
                                attrib_name7 = "ATTRIBUE"+str(num_attrib)
                                attributes.extend([attrib_name7, attrib_name7, attrib_name7])
                                num_attrib += 1
                            else:
                                attrib_name6 = "ATTRIBUE"+str(num_attrib)
                                attributes.extend([attrib_name6, attrib_name6, attrib_name6])
                                num_attrib += 1
                                    
                            # byte padding
                            prop_count = len(properties)
                            if prop_count/4 != int(prop_count/4):
                                if (prop_count/4) % 1 == 0.25:
                                    properties.extend(["MISC_SEMANTIC", "UNASSIGNED","UNASSIGNED"])
                                    components.extend(["X", "UNASSIGNED", "UNASSIGNED"])
                                    offsets.extend([offset, 0, 0])
                                    formats.extend(["BYTE", "BYTE", "BYTE"])
                                    attributes.extend(["UNASSIGNED", "UNASSIGNED", "UNASSIGNED"])
                                    offset += 1
                                elif (prop_count/4) % 1 == 0.5:
                                    properties.extend(["UNASSIGNED", "UNASSIGNED"])
                                    components.extend(["UNASSIGNED","UNASSIGNED"])
                                    offsets.extend([0,0])
                                    formats.extend(["BYTE", "BYTE"])
                                    attributes.extend(["UNASSIGNED", "UNASSIGNED"])
                                elif (prop_count/4) % 1 == 0.75:
                                    properties.append("MISC_SEMANTIC")
                                    components.append("X")
                                    offsets.append(offset)
                                    formats.append("BYTE")
                                    attributes.append("UNASSIGNED")
                                    offset += 1
                                    
                            while len(properties) < 64:
                                properties.append("UNASSIGNED")
                                components.append("UNASSIGNED")
                                formats.append("UNASSIGNED")
                                attributes.append("UNASSIGNED")
                                offsets.append(0)
                            
                            # Write mesh material
                            srtRender["SVertexDecl"]["size"] = offset
                            textures_names.extend(getMaterial(main_coll, mat, srtRender))
                            if col == lod_colls[-1] and bb_coll: #or horiz_coll:
                                srtRender["BFadeToBillboard"] = True 
                            if mat["BFacingLeavesPresent"]: #Ensure that Facing leaves have no culling method
                                srtRender["EFaceCulling"] = "NONE"
                                
                            # Properties
                            properties_reshaped = np.array(properties).reshape(-1,4).tolist()
                            components_reshaped = np.array(components).reshape(-1,4).tolist()
                            offsets_reshaped = np.array(offsets).reshape(-1,4).tolist()
                            formats_reshaped = np.array(formats).reshape(-1,4).tolist()
                            asProperties = srtRender["SVertexDecl"]["AsAttributes"]
                            for i,_ in enumerate(asProperties):
                                if properties_reshaped[i][0] != "UNASSIGNED":
                                    asProperties[i] = {'format': formats_reshaped[i][-1], 'properties': properties_reshaped[i], 'components': components_reshaped[i], 'offsets': offsets_reshaped[i]}
                            
                            # Attributes
                            attributes_components = getAttributesComponents(attributes)
                            srtAttributes = srtRender["SVertexDecl"]["AsProperties"]
                            # Attrib 0
                            setAttribute(srtAttributes, 0, "POSITION", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 1
                            setAttribute(srtAttributes, 1, "DIFFUSE_TEXTURE_COORDINATES", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 2
                            setAttribute(srtAttributes, 2, "NORMAL", "BYTE", properties, components, offsets, attributes_components, attributes)
                            # Attrib 3
                            setAttribute(srtAttributes, 3, "LOD_POSITION", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 4
                            setAttribute(srtAttributes, 4, "GEOMETRY_TYPE_HINT", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 5
                            setAttribute(srtAttributes, 5, "LEAF_CARD_CORNER", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 6
                            setAttribute(srtAttributes, 6, "LEAF_CARD_LOD_SCALAR", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 8
                            setAttribute(srtAttributes, 8, "WIND_BRANCH_DATA", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 9
                            setAttribute(srtAttributes, 9, "WIND_EXTRA_DATA", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 10
                            setAttribute(srtAttributes, 10, "WIND_FLAGS", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 11
                            setAttribute(srtAttributes, 11, "LEAF_ANCHOR_POINT", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 13
                            setAttribute(srtAttributes, 13, "BRANCH_SEAM_DIFFUSE", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 14
                            setAttribute(srtAttributes, 14, "BRANCH_SEAM_DETAIL", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 15
                            setAttribute(srtAttributes, 15, "DETAIL_TEXTURE_COORDINATES", "HALF_FLOAT", properties, components, offsets, attributes_components, attributes)
                            # Attrib 16
                            setAttribute(srtAttributes, 16, "TANGENT", "BYTE", properties, components, offsets, attributes_components, attributes)
                            # Attrib 18
                            setAttribute(srtAttributes, 18, "AMBIENT_OCCLUSION", "BYTE", properties, components, offsets, attributes_components, attributes)
                                
                            srtLod["PDrawCalls"].append(srtDraw)
                            
                            # Write P3dRenderStateMain 
                            srtMain["Geometry"]["P3dRenderStateMain"].append(srtRender)
                            
                            # Write P3dRenderStateShadow
                            srtMain["Geometry"]["P3dRenderStateShadow"].append(deepcopy(srtRender))
                            for i,_ in enumerate(srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ApTextures"]):
                                if i:
                                    srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ApTextures"][i] = ""
                            srtMain["Geometry"]["P3dRenderStateShadow"][-1]["ERenderPass"] = "SHADOW_CAST"
                            srtMain["Geometry"]["P3dRenderStateShadow"][-1]["BFadeToBillboard"] = False
                            
                    #Join meshes back again  
                    JoinThem(meshes)
                    
                    # Write Lod Data
                    srtMain["Geometry"]["PLods"].append(srtLod)     
                    
                    # Write Extent
                    if col == lod_colls[0]:
                        Extent = np.array(objects[0].bound_box)
                        srtMain["Extents"]["m_cMin"] = list(Extent[0])
                        srtMain["Extents"]["m_cMax"] = list(Extent[6]) 
                    
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
            
        # UserStrings and StringTable
        strings = main_coll["PUserStrings"]
        if not strings:
            strings = []
        srtMain["PUserStrings"] = strings
        srtMain["StringTable"] = [""]
        srtMain["StringTable"].extend(strings)
        srtMain["StringTable"].append("../../../../../bin/shaders/speedtree")
        srtMain["StringTable"].extend(list(np.unique(np.array(textures_names))))
        srtMain["StringTable"].extend(list(np.unique(np.array(bb_textures_names))))
        while len(srtMain["PUserStrings"]) < 5:
            srtMain["PUserStrings"].append("")
        
        # Write the template with generated values
        short_filepath = filepath[:-4]
        with open(short_filepath, 'w', encoding = 'utf-8') as f:
            json.dump(srtMain, f, indent=2)
        command = [os.path.dirname(__file__) +"/converter/srt_json_converter.exe", "-e", short_filepath, "-o", os.path.dirname(filepath)]
        subprocess.run(command)
        os.remove(short_filepath)