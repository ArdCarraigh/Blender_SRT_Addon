# -*- coding: utf-8 -*-
# import_srt_json.py

import bpy
import json
import os.path
import re
import numpy as np
import subprocess
from bpy_extras.object_utils import object_data_add
from io_mesh_srt.tools.collision_tools import add_srt_sphere, add_srt_connection
from io_mesh_srt.tools.billboard_tools import generate_srt_billboards, generate_srt_horizontal_billboard
from io_mesh_srt.tools.setup_tools import srt_mesh_setup
from io_mesh_srt.utils import JoinThem

def read_srt_json(context, filepath):
    file_name = os.path.splitext(os.path.basename(filepath))[0]
    wkit_path = bpy.context.preferences.addons[__package__].preferences.wolvenkit_cli
    if os.path.splitext(os.path.basename(filepath))[1] == ".srt":
        if os.path.exists(wkit_path):
            import subprocess
            command = [str(wkit_path), "--input", filepath, "--srt2json"]
            subprocess.run(command)
            filepath += ".json"
        else:
            print('Wolvenkit CLI .exe not found.')
            return
    
    dds_addon = False 
    if 'blender_dds_addon' in bpy.context.preferences.addons:
        from blender_dds_addon.ui.import_dds import load_dds
        dds_addon = True
    
    with open(filepath, 'r', encoding='utf-8') as file:
        srt = json.load(file)
        
    wm = bpy.context.window_manager  
        
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
        bb_width = srtBillboard["FWidth"]
        bb_top = srtBillboard["FTopPos"]
        bb_bottom = srtBillboard["FBottomPos"]
        nbb = srtBillboard["NNumBillboards"]
        bb_texCoords = np.array(srtBillboard["PTexCoords"]).reshape(-1,4)
        bb_rotations = srtBillboard["PRotated"]
        ncutout = srtBillboard["NNumCutoutVertices"]
        cutout = srtBillboard["PCutoutVertices"]
        cutout_faces = np.array(srtBillboard["PCutoutIndices"]).reshape(-1,3)
            
        # Organise UV Maps
        uvs_all = []
        for i, bb_uvs_data in enumerate(bb_texCoords):
            bb_uvs_data_0_2 = bb_uvs_data[0]+bb_uvs_data[2]
            bb_uvs_data_1_3 = bb_uvs_data[1]+bb_uvs_data[3]
            bb_uvs = np.array([[bb_uvs_data[0], bb_uvs_data[1]], [bb_uvs_data_0_2, bb_uvs_data[1]], [bb_uvs_data_0_2, bb_uvs_data_1_3], [bb_uvs_data[0], bb_uvs_data_1_3]])
            if bb_rotations[i]:
                bb_uvs = np.array([bb_uvs[j-1] for j in range(4)])
            bb_uvs = bb_uvs[[0,1,2,2,3,0]].flatten()
            bb_uvs[1::2] = 1 - bb_uvs[1::2]
            uvs_all.append(bb_uvs)
                
        # Create Billboards
        generate_srt_billboards(bpy.context, nbb, bb_width, bb_bottom, bb_top, uvs_all)
        
        # Set the Textures
        bbMat = srt["Geometry"]["ABillboardRenderStateMain"]
        for k, tex in enumerate(bbMat["ApTextures"]):
            tex_name = tex["Val"]
            if tex_name:
                tex_path = os.path.dirname(filepath) + "\\" + tex_name
                if os.path.exists(tex_path):
                    if tex_name.endswith(".dds") and dds_addon:
                        image = bpy.data.images.get(tex_name)
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
        for param in ["ApTextures", "BFadeToBillboard", "BVertBillboard", "BHorzBillboard", "ERenderPass", "SVertexDecl", "PDescription", "PUserData", "WolvenKit_AlignedBytes"]:
                bbMat.pop(param)
        for k in ["VAmbientColor", "VDiffuseColor", "VSpecularColor", "VTransmissionColor"]:
            bbMat[k] = (*list(bbMat[k].values()), 1)
            
        for k in bbMat:
            setattr(wm, k, bbMat[k])
            
        # Cutout 
        if ncutout and nbb:
            mat = bpy.context.active_object.data.materials[0]
            verts_cutout = [[-bb_width*0.5 + bb_width * cutout[j], 0, bb_bottom + (bb_top-bb_bottom) * cutout[j+1]] for j in range(0, ncutout*2, 2)]
            bb = bpy.data.meshes.new(name="Mesh_cutout")
            bb.from_pydata(verts_cutout, [], cutout_faces)
            object_data_add(context, bb)
            bb.shade_smooth()
            bb.materials.append(mat)
            wm.BCutout = True
            
    #Horizontal Billboard
    if "HorizontalBillboard" in srt:
        if srt['HorizontalBillboard']['BPresent']:
            bb_horiz_verts = [list(vert.values()) for vert in srt['HorizontalBillboard']['AvPositions']]
            bb_horiz_uvs = np.array(srt['HorizontalBillboard']['AfTexCoords']).reshape(-1,2)[[0,1,2,2,3,0]].flatten()
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
            
            # Get Vertex Data
            vert_data = [vert["VertexProperties"] for vert in mesh_call["PVertexData"]]
            properties = [props["PropertyName"] for props in vert_data[0]]
            float_data_array = np.array([[prop["FloatValues"] for prop in vert] for vert in vert_data], dtype=object).T
            byte_data_array = np.array([[prop["ByteValues"] for prop in vert] for vert in vert_data], dtype=object).T
            all_vert_data = [np.array(float_data_array[x].tolist()).astype(float).tolist() if float_data_array[x][0] else [] for x in range(len(float_data_array))]
            all_vert_data = dict(zip(properties, all_vert_data))
            if all_vert_data["VERTEX_PROPERTY_AMBIENT_OCCLUSION"]: #Deal with Ambient Occlusion Special Case
                if byte_data_array.size and byte_data_array[18].size:
                    all_vert_data["VERTEX_PROPERTY_AMBIENT_OCCLUSION"] = np.array(byte_data_array[18].tolist()).astype(float).tolist()
                else:
                    all_vert_data["VERTEX_PROPERTY_AMBIENT_OCCLUSION"] = (np.array(all_vert_data["VERTEX_PROPERTY_AMBIENT_OCCLUSION"]) * 255).tolist()

            # Face indices
            faces = np.array(mesh_call["PIndexData"]).reshape(-1,3)
                 
            # Add the mesh to the scene
            mesh = bpy.data.meshes.new(name="Mesh_lod"+str(i))
            mesh.from_pydata(all_vert_data["VERTEX_PROPERTY_POSITION"], [], faces)
            obj = object_data_add(context, mesh)
            mesh.shade_smooth()
            meshes.append(obj)
            
            # Set Up the SRT Asset
            srtMat = mesh_call["PRenderState"]
            geom_type = ['0.2', '0.4', '0.6', '0.8', '1.0'][np.argmax([srtMat["BBranchesPresent"], srtMat["BFrondsPresent"], srtMat["BLeavesPresent"], srtMat["BFacingLeavesPresent"], srtMat["BRigidMeshesPresent"]])]
            srt_mesh_setup(bpy.context, obj, geom_type, all_vert_data)
        
            # Normals
            #bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            #bpy.ops.mesh.normals_make_consistent(inside=False)
            #bpy.ops.object.mode_set(mode='OBJECT')
            mesh.normals_split_custom_set_from_vertices(all_vert_data["VERTEX_PROPERTY_NORMAL"])
            mesh.use_auto_smooth = True
            #Tangents are read-only in Blender, we can't import them
            
            # Set the Textures
            for k, tex in enumerate(srtMat["ApTextures"]):
                tex_name = tex["Val"]
                if tex_name:
                    tex_path = os.path.dirname(filepath) + "\\" + tex_name
                    if os.path.exists(tex_path):
                        if tex_name.endswith(".dds") and dds_addon:
                            image = bpy.data.images.get(tex_name)
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
            for param in ["ApTextures", "BFadeToBillboard", "BVertBillboard", "BHorzBillboard", "ERenderPass", "SVertexDecl", "PDescription", "PUserData", "WolvenKit_AlignedBytes"]:
                srtMat.pop(param)
            for k in ["VAmbientColor", "VDiffuseColor", "VSpecularColor", "VTransmissionColor"]:
                srtMat[k] = (*list(srtMat[k].values()), 1)
                
            for k in srtMat:
                setattr(wm, k, srtMat[k])
            
        # Join submeshes under the same LOD
        JoinThem(meshes)
        
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]