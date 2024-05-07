# -*- coding: utf-8 -*-
# import_srt_json.py

import bpy
import json
import os.path
import re
import numpy as np
import subprocess
from copy import deepcopy
from bpy_extras.object_utils import object_data_add
from io_mesh_srt.tools.collision_tools import add_srt_sphere, add_srt_connection
from io_mesh_srt.tools.billboard_tools import generate_srt_billboards, generate_srt_horizontal_billboard
from io_mesh_srt.tools.setup_tools import srt_mesh_setup
from io_mesh_srt.utils import JoinThem

def read_srt_json(context, filepath):
    file_name = os.path.splitext(os.path.basename(filepath))[0]
    if os.path.splitext(os.path.basename(filepath))[1] == ".srt":
        import subprocess
        command = [os.path.dirname(__file__) +"/converter/srt_json_converter.exe", "-d", filepath, "-o", os.path.dirname(filepath)]
        subprocess.run(command)
        filepath += ".json"
    
    dds_addon = False 
    if 'blender_dds_addon' in bpy.context.preferences.addons:
        from blender_dds_addon.ui.import_dds import load_dds
        dds_addon = True
    
    with open(filepath, 'r', encoding='utf-8') as file:
        srt = json.load(file)
        
    wm = bpy.context.window_manager.speedtree  
        
    if wm.previewLod:
        wm.previewLod = False
    
    # Create Main Collection #
    parent_coll = bpy.context.view_layer.active_layer_collection
    main_coll = bpy.data.collections.new(file_name)
    main_coll["SpeedTreeMainCollection"] = "SpeedTreeMainCollection"
    main_coll_name = main_coll.name
    parent_coll.collection.children.link(main_coll)
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]
    
    # Apply Lod Profile
    lodProfile = srt["LodProfile"]
    lodProfile.pop("m_bLodIsPresent")
    for k in lodProfile:
        setattr(wm, k, lodProfile[k])
            
    # Apply Wind
    wind = srt["Wind"]
    for k in wind:
        main_coll[k] = wind[k]
            
    # User Strings
    userStrings = srt["PUserStrings"]
    main_coll['PUserStrings'] = [item for item in userStrings if item]
    
    # Collision Object #
    if "CollisionObjects" in srt:
        collisionObjects = srt["CollisionObjects"]
        spheres = []
        radii = []
        for collisionObject in collisionObjects:
            spheres = [list(collisionObject["m_vCenter1"].values()), list(collisionObject["m_vCenter2"].values())]
            radius = collisionObject["m_fRadius"]
    
            # Import collision objects
            #Sphere
            if spheres[0] == spheres[1]:
                add_srt_sphere(context = bpy.context, radius = radius, location = spheres[0])
            
            #Capsule
            else:
                sphere1 = add_srt_sphere(context = bpy.context, radius = radius, location = spheres[0])
                sphere2 = add_srt_sphere(context = bpy.context, radius = radius, location = spheres[1])
                add_srt_connection(context = bpy.context, objects = [sphere1, sphere2])
            
    # Billboards #
    # Vertical Billboards
    if "VerticalBillboards" in srt:
        srtBillboard = srt["VerticalBillboards"]
        nbb = srtBillboard["NNumBillboards"]
        if nbb:
            bb_width = srtBillboard["FWidth"]
            bb_top = srtBillboard["FTopPos"]
            bb_bottom = srtBillboard["FBottomPos"]
            bb_texCoords = [list(x.values()) for x in srtBillboard["PTexCoords"]]
            bb_rotations = srtBillboard["PRotated"]
            ncutout = srtBillboard["NNumCutoutVertices"]
            cutout = np.array([list(x.values()) for x in srtBillboard["PCutoutVertices"]]).flatten()
            cutout_faces = np.array(srtBillboard["PCutoutIndices"]).reshape(-1,3)
                
            # Organise UV Maps
            uvs_all = []
            for i, bb_uvs_data in enumerate(bb_texCoords):
                bb_uvs_data_0_2 = bb_uvs_data[0]+bb_uvs_data[2]
                bb_uvs_data_1_3 = bb_uvs_data[1]+bb_uvs_data[3]
                bb_uvs = np.array([[bb_uvs_data[0], bb_uvs_data[1]], [bb_uvs_data_0_2, bb_uvs_data[1]], [bb_uvs_data_0_2, bb_uvs_data_1_3], [bb_uvs_data[0], bb_uvs_data_1_3]])
                if bb_rotations[i]:
                    bb_uvs = bb_uvs[[0,3,2,1]]
                bb_uvs = bb_uvs[[0,1,2,2,3,0]].flatten()
                bb_uvs[1::2] = 1 - bb_uvs[1::2]
                uvs_all.append(bb_uvs)
                    
            # Create Billboards
            generate_srt_billboards(bpy.context, nbb, bb_width, bb_bottom, bb_top, uvs_all)
            
            # Set the Textures
            bbMat = srt["Geometry"]["ABillboardRenderStateMain"]
            for k, tex in enumerate(bbMat["ApTextures"]):
                if tex:
                    tex_path = os.path.dirname(filepath) + "\\" + tex
                    if os.path.exists(tex_path):
                        if tex.endswith(".dds") and dds_addon:
                            image = bpy.data.images.get(tex)
                            if not image:
                                image = load_dds(tex_path)
                                image.name += ".dds"
                                image.filepath = tex_path
                            match k:
                                case 0:
                                    image.colorspace_settings.name = 'sRGB'
                                    wm.diffuseTexture = image
                                case 1:
                                    image.colorspace_settings.name = 'Non-Color'
                                    wm.normalTexture = image
                                case 4:
                                    image.colorspace_settings.name = 'Non-Color'
                                    wm.specularTexture = image
                        else:
                            match k:
                                case 0:
                                    wm.diffuseTexture = bpy.data.images.load(tex_path, check_existing = True)
                                case 1:
                                    wm.normalTexture = bpy.data.images.load(tex_path, check_existing = True)
                                case 4:
                                    wm.specularTexture = bpy.data.images.load(tex_path, check_existing = True)
            
            # Set the Material
            for param in ["ApTextures", "BFadeToBillboard", "BVertBillboard", "BHorzBillboard", "ERenderPass", "SVertexDecl", "PDescription", "PUserData"]:
                    bbMat.pop(param)
            for k in ["VAmbientColor", "VDiffuseColor", "VSpecularColor", "VTransmissionColor"]:
                bbMat[k] = (*list(bbMat[k].values()), 1)
            bbMat["FShininess"] /= 128
                
            for k in bbMat:
                setattr(wm, k, bbMat[k])
                
            # Cutout 
            if ncutout and nbb:
                mat = bpy.context.active_object.data.materials[0]
                verts_cutout = [[-bb_width*0.5 + bb_width * cutout[j], 0, bb_bottom + (bb_top-bb_bottom) * cutout[j+1]] for j in range(0, ncutout*2, 2)]
                bb = bpy.data.meshes.new(name="Mesh_cutout")
                bb.from_pydata(verts_cutout, [], cutout_faces)
                obj = object_data_add(context, bb)
                bb.shade_smooth()
                bb.materials.append(mat)
                wm.BCutout = True
            
    #Horizontal Billboard
    if "HorizontalBillboard" in srt:
        if srt['HorizontalBillboard']['BPresent']:
            bb_horiz_verts = [list(vert.values()) for vert in srt['HorizontalBillboard']['AvPositions']]
            bb_horiz_uvs = np.array([list(x.values()) for x in srt['HorizontalBillboard']['AfTexCoords']])[[0,1,2,2,3,0]].flatten()
            bb_horiz_uvs[1::2] = 1 - bb_horiz_uvs[1::2]
            generate_srt_horizontal_billboard(bpy.context, verts = bb_horiz_verts, uvs = bb_horiz_uvs)
           
    # Geometry Data #
    # For each LOD
    for i, lod in enumerate(srt["Geometry"]["PLods"]):
        meshes = []
        
        # Collections creation
        lod_coll = bpy.data.collections.new("LOD"+str(i))
        main_coll.children.link(lod_coll)
        bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name].children[lod_coll.name]

        # For each material
        for mesh_call in lod["PDrawCalls"]:
            srtMat = deepcopy(srt["Geometry"]["P3dRenderStateMain"][mesh_call["RenderStateIdx"]])
            
            # Get Vertex Data
            vert_data = mesh_call["VertexData"]
            
            # Deal with int to byte to float conversion if needed
            for attr in srtMat["SVertexDecl"]["AsAttributes"]:
                if isinstance(attr, dict) and attr["format"] == "BYTE":
                    if "NORMAL" in attr["properties"]:
                        vert_data["normals"] = (np.array(vert_data["normals"]) / 255 - 0.5) * 2
                    #if "TANGENT" in attr["properties"]:
                    #    vert_data["tangents"] = (np.array(vert_data["tangents"]) / 255 - 0.5) * 2)
                    #Tangents are read-only in Blender, we can't import them
                    if "AMBIENT_OCCLUSION" in attr["properties"]:
                        vert_data["ambient_occlusion"] = np.array(vert_data["ambient_occlusion"]) / 255

            # Face indices
            faces = np.array(mesh_call["IndexData"]).reshape(-1,3)
                 
            # Add the mesh to the scene
            mesh = bpy.data.meshes.new(name="Mesh_lod"+str(i))
            mesh.from_pydata(vert_data["pos"], [], faces)
            obj = object_data_add(context, mesh)
            mesh.shade_smooth()
            meshes.append(obj)
            
            # Set Up the SRT Asset
            geom_type = ['0.2', '0.4', '0.6', '0.8', '1.0'][np.argmax([srtMat["BBranchesPresent"], srtMat["BFrondsPresent"], srtMat["BLeavesPresent"], srtMat["BFacingLeavesPresent"], srtMat["BRigidMeshesPresent"]])]
            srt_mesh_setup(bpy.context, obj, geom_type, vert_data)
        
            # Normals
            #bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            #bpy.ops.mesh.normals_make_consistent(inside=False)
            #bpy.ops.object.mode_set(mode='OBJECT')
            mesh.normals_split_custom_set_from_vertices(vert_data["normals"])
            #Tangents are read-only in Blender, we can't import them
            
            # Set the Textures
            for k, tex in enumerate(srtMat["ApTextures"]):
                if tex:
                    tex_path = os.path.dirname(filepath) + "\\" + tex
                    if os.path.exists(tex_path):
                        if tex.endswith(".dds") and dds_addon:
                            image = bpy.data.images.get(tex)
                            if not image:
                                image = load_dds(tex_path)
                                image.name += ".dds"
                                image.filepath = tex_path
                            match k:
                                case 0:
                                    image.colorspace_settings.name = 'sRGB'
                                    wm.diffuseTexture = image
                                case 1:
                                    image.colorspace_settings.name = 'Non-Color'
                                    wm.normalTexture = image
                                case 2:
                                    image.colorspace_settings.name = 'sRGB'
                                    wm.detailTexture = image
                                case 3:
                                    image.colorspace_settings.name = 'Non-Color'
                                    wm.detailNormalTexture = image
                                case 4:
                                    image.colorspace_settings.name = 'Non-Color'
                                    wm.specularTexture = image
                        else:
                            match k:
                                case 0:
                                    wm.diffuseTexture = bpy.data.images.load(tex_path, check_existing = True)
                                case 1:
                                    wm.normalTexture = bpy.data.images.load(tex_path, check_existing = True)
                                case 2:
                                    wm.detailTexture = bpy.data.images.load(tex_path, check_existing = True)
                                case 3:
                                    wm.detailNormalTexture = bpy.data.images.load(tex_path, check_existing = True)
                                case 4:
                                    wm.specularTexture = bpy.data.images.load(tex_path, check_existing = True)
            
            # Set the Material
            for param in ["ApTextures", "BFadeToBillboard", "BVertBillboard", "BHorzBillboard", "ERenderPass", "SVertexDecl", "PDescription", "PUserData"]:
                srtMat.pop(param)
            for k in ["VAmbientColor", "VDiffuseColor", "VSpecularColor", "VTransmissionColor"]:
                srtMat[k] = (*list(srtMat[k].values()), 1)
            srtMat["FShininess"] /= 128
                
            for k in srtMat:
                setattr(wm, k, srtMat[k])
            
        # Join submeshes under the same LOD
        JoinThem(meshes)
        
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]