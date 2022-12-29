# -*- coding: utf-8 -*-
# import_srt_json.py

import bpy
import math
import json
import random, colorsys
import os.path
import re
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import object_data_add
from io_scene_srt_json.tools import generate_srt_billboards
from io_scene_srt_json.tools.generate_srt_billboards import generate_srt_billboards, generate_srt_horizontal_billboard
from io_scene_srt_json import export_srt_json
from io_scene_srt_json.export_srt_json import JoinThem

def GetVertValues(prop):
    size = prop["ValueCount"]
    type = prop["PropertyFormat"]
    prop_values = []
    if size > 0:
        if "ByteValues" in prop and "FloatValues" not in prop:
            values = prop["ByteValues"]
            for i in range(size):
                prop_values.append(int(values[i]))
        elif "ByteValues" in prop and not prop["FloatValues"]:
            values = prop["ByteValues"]
            for i in range(size):
                prop_values.append(int(values[i]))
        elif "FloatValues" in prop:
            values = prop["FloatValues"]
            for i in range(size):
                prop_values.append(float(values[i]))
    return prop_values

def read_srt_json(context, filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        srt = json.load(file)
        
    wm = bpy.context.window_manager  
        
    if wm.previewLod:
        wm.previewLod = False
    
    # Create Main Collection #
    parent_coll = bpy.context.view_layer.active_layer_collection
    main_coll = bpy.data.collections.new("SRT Asset")
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
        #setattr(main_coll, k, wind[k])
            
    # Apply User Settings
    userSettings2 = {}
    userSettings2['EBillboardRandomType'] = 'NoBillboard'
    userSettings2['ETerrainNormals'] = 'TerrainNormalsOff'
    userSettings = srt["PUserStrings"]
    for k in userSettings:
        if k in ["BillboardRandomTrees", "BillboardRandomBranch", "BillboardRandomOff"]:
            userSettings2['EBillboardRandomType'] = k
        if k == 'TerrainNormalsOn':
            userSettings2['ETerrainNormals'] = 'TerrainNormalsOn'
    for k in userSettings2:
            setattr(wm, k, userSettings2[k])
    
    # Collision Object #
    if "CollisionObjects" in srt:
        collisionObjects = srt["CollisionObjects"]
        spheres = []
        radii = []
        for collisionObject in collisionObjects:
            sphere1_pos = [float(collisionObject["m_vCenter1"]["x"]), float(collisionObject["m_vCenter1"]["y"]), float(collisionObject["m_vCenter1"]["z"])]
            sphere2_pos = [float(collisionObject["m_vCenter2"]["x"]), float(collisionObject["m_vCenter2"]["y"]), float(collisionObject["m_vCenter2"]["z"])]
            spheres_pos = [sphere1_pos, sphere2_pos]
            radius = float(collisionObject["m_fRadius"])
            spheres.append(spheres_pos)
            radii.append(radius)
    
        # Import collision objects
        for i in range(len(spheres)):
            #Sphere
            if spheres[i][0] == spheres[i][1]:
                bpy.ops.speed_tree.add_srt_collision_sphere(radius = radii[i], location = spheres[i][0])
            
            #Capsule
            else:
                bpy.ops.speed_tree.add_srt_collision_sphere(radius = radii[i], location = spheres[i][0])
                bpy.context.window_manager.collisionObject1 = bpy.context.active_object
                bpy.ops.speed_tree.add_srt_collision_sphere(radius = radii[i], location = spheres[i][1])
                bpy.context.window_manager.collisionObject2 = bpy.context.active_object
                bpy.ops.speed_tree.add_srt_sphere_connection()
            
    # Billboards #
    # Vertical Billboards
    if "VerticalBillboards" in srt:
        bb_width = float(srt["VerticalBillboards"]["FWidth"])
        bb_top = float(srt["VerticalBillboards"]["FTopPos"])
        bb_bottom = float(srt["VerticalBillboards"]["FBottomPos"])
        nbb = int(srt["VerticalBillboards"]["NNumBillboards"])
        bb_texCoords = srt["VerticalBillboards"]["PTexCoords"]
        bb_rotations = srt["VerticalBillboards"]["PRotated"]
        ncutout = srt["VerticalBillboards"]["NNumCutoutVertices"]
        cutout = srt["VerticalBillboards"]["PCutoutVertices"]
        ncutout_faces = srt["VerticalBillboards"]["NNumCutoutIndices"]
        cutout_faces = srt["VerticalBillboards"]["PCutoutIndices"]
        
        bb_tex_names = []
        bb_tex_paths = []
        #For each billboard texture
        for tex in srt["Geometry"]["ABillboardRenderStateMain"]["ApTextures"]:
            bb_tex_name = tex["Val"]
            bb_tex_names.append(bb_tex_name)
            bb_tex_path = os.path.dirname(filepath) + "\\" + bb_tex_name
            bb_tex_paths.append(bb_tex_path)
            if os.path.exists(bb_tex_path) and bb_tex_name:
                bpy.ops.image.open(filepath = bb_tex_path)      
 
        bbMat = srt["Geometry"]["ABillboardRenderStateMain"]
        bbMat.pop("ApTextures")
        bbMat.pop("BFadeToBillboard")
        bbMat.pop("BVertBillboard")
        bbMat.pop("BHorzBillboard")
        bbMat.pop("ERenderPass")
        bbMat.pop("SVertexDecl")
        bbMat.pop("PDescription")
        bbMat.pop("PUserData")
        bbMat.pop("WolvenKit_AlignedBytes")
        for k in ["VAmbientColor", "VDiffuseColor", "VSpecularColor", "VTransmissionColor"]:
            bbMat[k] = [bbMat[k]['x'], bbMat[k]['y'], bbMat[k]['z'], 1]
            
        # Organise UV Maps
        uvs_all = []
        for i in range(nbb):
            bb_uvs_data = [float(bb_texCoords[4*i]), float(bb_texCoords[4*i+1]),float(bb_texCoords[4*i+2]), float(bb_texCoords[4*i+3])]
            bb_uvs = [[bb_uvs_data[0], bb_uvs_data[1]],
            [bb_uvs_data[0]+bb_uvs_data[2], bb_uvs_data[1]],
            [bb_uvs_data[0]+bb_uvs_data[2], bb_uvs_data[1]+bb_uvs_data[3]],
            [bb_uvs_data[0], bb_uvs_data[1]+bb_uvs_data[3]]]
            if int(bb_rotations[i] == 0):
                uvs_all.append(bb_uvs)
            elif int(bb_rotations[i] == 1):
                uvs_rotated = []
                for j in range(4):
                    uvs_rotated.append([bb_uvs[j-1][0], bb_uvs[j-1][1]])
                uvs_all.append(uvs_rotated)
        
        # Create Billboards
        generate_srt_billboards(bpy.context, nbb, bb_width, bb_bottom, bb_top, uvs_all)  
            
        for k in bbMat:
            setattr(wm, k, bbMat[k])
            
        for k in range(len(bb_tex_names)):
            if bb_tex_names[k] and bb_tex_names[k] in bpy.data.images:
                if k == 0:
                    wm.diffuseTexture = bpy.data.images[bb_tex_names[k]]
                elif k == 1:
                    wm.normalTexture = bpy.data.images[bb_tex_names[k]]
                elif k == 4:
                    wm.specularTexture = bpy.data.images[bb_tex_names[k]]
            
        # Cutout 
        if ncutout > 0 and nbb > 0: 
            verts_cutout = []
            for j in range(0, ncutout*2, 2):
                verts_cutout.append([-bb_width/2 + bb_width * float(cutout[j]), 0, bb_bottom + (bb_top-bb_bottom) * float(cutout[j+1])])
                    
            faces_cutout = []
            for j in range(0, ncutout_faces, 3):
                faces_cutout.append([int(cutout_faces[j]), int(cutout_faces[j+1]), int(cutout_faces[j+2])])
        
            #Add the mesh to the scene
            mat = bpy.context.active_object.data.materials[0]
            for col in main_coll.children:
                if re.search("Vertical Billboards", col.name):
                    bb_coll = col
            bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name].children[bb_coll.name]
            bb = bpy.data.meshes.new(name="Mesh_cutout")
            bb.from_pydata(verts_cutout, [], faces_cutout)
            for k in bb.polygons:
                k.use_smooth = True
            object_data_add(context, bb)
            bpy.context.active_object.data.materials.append(mat)
            wm.BCutout = True
            
    #Horizontal Billboard
    if "HorizontalBillboard" in srt:
        if srt['HorizontalBillboard']['BPresent']:
            bb_horiz_verts = []
            for vert in srt['HorizontalBillboard']['AvPositions']:
                bb_horiz_verts.append([vert['x'], vert['y'], vert['z']])
            bb_horiz_uvs = []
            for k in range(0,len(srt['HorizontalBillboard']['AfTexCoords']),2):
                bb_horiz_uvs.append([srt['HorizontalBillboard']['AfTexCoords'][k], srt['HorizontalBillboard']['AfTexCoords'][k+1]])
            generate_srt_horizontal_billboard(bpy.context, bb_horiz_verts, bb_horiz_uvs)
           
    # Geometry Data #
    nlods = srt["Geometry"]["NNumLods"]

    # For each LOD
    for i in range(nlods):
        raw_mesh = srt["Geometry"]["PLods"][i]
        nmats = raw_mesh["NNumDrawCalls"]
        mesh_names = []
        mesh_lod_names = []

        # For each material
        for j in range(nmats):
            mesh_call = raw_mesh["PDrawCalls"][j]
            nverts = mesh_call["NNumVertices"]
            verts = []
            verts_lod = []
            normals = []
            uvs_diff = []
            uvs_det = []
            geom_types = []
            leaf_card_corners = []
            leaf_card_lod_scalars = []
            branches_wind = []
            wind_extras = []
            wind_flags = []
            leaf_anchor_points = []
            branches_seam_diff = []
            branches_seam_det = []
            tangents = []
            ambients = []
            faces = []
            tex_names = []
            tex_paths = []        
            
            # For each texture
            for tex in mesh_call["PRenderState"]["ApTextures"]:
                tex_name = tex["Val"]
                tex_names.append(tex_name)
                tex_path = os.path.dirname(filepath) + "\\" + tex_name
                tex_paths.append(tex_path)
                if os.path.exists(tex_path) and tex_name:
                    bpy.ops.image.open(filepath = tex_path)
            
            # Material Data
            srtMat = mesh_call["PRenderState"]
            srtMat.pop("ApTextures")
            srtMat.pop("BFadeToBillboard")
            srtMat.pop("BVertBillboard")
            srtMat.pop("BHorzBillboard")
            srtMat.pop("ERenderPass")
            srtMat.pop("SVertexDecl")
            srtMat.pop("PDescription")
            srtMat.pop("PUserData")
            srtMat.pop("WolvenKit_AlignedBytes")
            for k in ["VAmbientColor", "VDiffuseColor", "VSpecularColor", "VTransmissionColor"]:
                srtMat[k] = [srtMat[k]['x'], srtMat[k]['y'], srtMat[k]['z'], 1]
            
            # For each vertex
            for k in range(nverts):
                props = mesh_call["PVertexData"][k]["VertexProperties"]
                for prop in props:

                    # Position
                    if prop["PropertyName"] == "VERTEX_PROPERTY_POSITION":
                        if prop["ValueCount"] > 0:
                            verts.append(GetVertValues(prop))

                    # LOD Position
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_LOD_POSITION":
                        if prop["ValueCount"] > 0:
                            verts_lod.append(GetVertValues(prop))

                    # Normal
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_NORMAL":
                        if prop["ValueCount"] > 0:
                            normals.append(GetVertValues(prop))

                    # Tangent
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_TANGENT":
                        if prop["ValueCount"] > 0:
                            tangents.append(GetVertValues(prop))

                    # UV1
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS":
                        if prop["ValueCount"] > 0:
                            uvs_diff.append(GetVertValues(prop))

                    # UV2
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_DETAIL_TEXCOORDS":
                        if prop["ValueCount"] > 0:
                            uvs_det.append(GetVertValues(prop))

                    # Geom Type
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT":
                        if prop["ValueCount"] > 0:
                            geom_types.append(GetVertValues(prop))
                            
                    # Leaf Card Corner
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_LEAF_CARD_CORNER":
                        if prop["ValueCount"] > 0:
                            leaf_card_corners.append(GetVertValues(prop))
                            
                    # Leaf Card LOD Scalar
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR":
                        if prop["ValueCount"] > 0:
                            leaf_card_lod_scalars.append(GetVertValues(prop))

                    # Wind branch data
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_WIND_BRANCH_DATA":
                        if prop["ValueCount"] > 0:
                            branches_wind.append(GetVertValues(prop))
                            
                    # Wind extra data
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_WIND_EXTRA_DATA":
                        if prop["ValueCount"] > 0:
                            wind_extras.append(GetVertValues(prop))
                            
                    # Wind Flag
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_WIND_FLAGS":
                        if prop["ValueCount"] > 0:
                            wind_flags.append(GetVertValues(prop))
                            
                    # Leaf Anchor Point
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_LEAF_ANCHOR_POINT":
                        if prop["ValueCount"] > 0:
                            leaf_anchor_points.append(GetVertValues(prop))

                    # Branch seam diffuse
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE":
                        if prop["ValueCount"] > 0:
                            branches_seam_diff.append(GetVertValues(prop))

                    # Branch seam detail
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL":
                        if prop["ValueCount"] > 0:
                            branches_seam_det.append(GetVertValues(prop))

                    # Ambient occlusion
                    elif prop["PropertyName"] == "VERTEX_PROPERTY_AMBIENT_OCCLUSION":
                        if prop["ValueCount"] > 0:
                            ambients.append(GetVertValues(prop))

            # Face indices
            nindices = mesh_call["NNumIndices"]
            indices = mesh_call["PIndexData"]
            for k in range(0,nindices, 3):
                faces.append([int(indices[k]), int(indices[k+1]), int(indices[k+2])])
                
            # Collections creation
            match = 0
            for child in main_coll.children:
                if re.search("LOD"+str(i), child.name):
                    match = 1
                    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name].children[child.name]
                    break
            if match == 0:
                lod_coll = bpy.data.collections.new("LOD"+str(i))
                lod_coll_name = lod_coll.name
                main_coll.children.link(lod_coll)
                bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name].children[lod_coll_name]
                
            # Add the mesh to the scene
            mesh = bpy.data.meshes.new(name="Mesh_lod"+str(i))
            mesh.from_pydata(verts, [], faces)
            for k in mesh.polygons:
                k.use_smooth = True
            object_data_add(context, mesh)
            mesh_names.append(bpy.context.active_object.name)
            
            # Set Up the SRT Asset
            bpy.ops.speed_tree.srt_mesh_setup()
            
            # UVmaps creation
            if uvs_diff:
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["DiffuseUV"].data[loop_idx].uv = (uvs_diff[vert_idx][0], 1-uvs_diff[vert_idx][1])
                        
            if uvs_det:
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["DetailUV"].data[loop_idx].uv = (uvs_det[vert_idx][0], 1-uvs_det[vert_idx][1])
                        
            if branches_seam_diff:
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["SeamDiffuseUV"].data[loop_idx].uv = (branches_seam_diff[vert_idx][0], 1-branches_seam_diff[vert_idx][1])
                    
            if branches_seam_det:
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["SeamDetailUV"].data[loop_idx].uv = (branches_seam_det[vert_idx][0], 1-branches_seam_det[vert_idx][1])
                        
            # Normals
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh.normals_split_custom_set_from_vertices(normals)
            mesh.use_auto_smooth = True
            #Tangents are read-only in Blender, we can't import them
                    
            # Ambient Occlusion
            if ambients:
                for vert in mesh.vertices:
                    mesh.color_attributes["AmbientOcclusion"].data[vert.index].color = [ambients[vert.index][0]]*3 + [1]
                    
            # Seam Blending
            if branches_seam_diff:
                for vert in mesh.vertices:
                    mesh.color_attributes["SeamBlending"].data[vert.index].color = [branches_seam_diff[vert.index][2]]*3 + [1]
            
            mesh2 = bpy.data.objects[bpy.context.active_object.name]
            
            #Geometry type
            if geom_types:
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["GeomType"].add([mesh2.data.vertices[k].index], ((1 + geom_types[k][0])/5), 'REPLACE')
                    
            #Wind Data
            if branches_wind:
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["WindWeight1"].add([mesh2.data.vertices[k].index], branches_wind[k][0], 'REPLACE')
                    mesh2.vertex_groups["WindNormal1"].add([mesh2.data.vertices[k].index], branches_wind[k][1]/16, 'REPLACE')
                    mesh2.vertex_groups["WindWeight2"].add([mesh2.data.vertices[k].index], branches_wind[k][2], 'REPLACE')
                    mesh2.vertex_groups["WindNormal2"].add([mesh2.data.vertices[k].index], branches_wind[k][3]/16, 'REPLACE')
                    
            #Wind Extra Data
            if wind_extras:
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["WindExtra1"].add([mesh2.data.vertices[k].index], wind_extras[k][0]/16, 'REPLACE')
                    mesh2.vertex_groups["WindExtra2"].add([mesh2.data.vertices[k].index], wind_extras[k][1], 'REPLACE')
                    mesh2.vertex_groups["WindExtra3"].add([mesh2.data.vertices[k].index], wind_extras[k][2]/2, 'REPLACE')
                    
            #Wind Flag
            if wind_flags:
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["WindFlag"].add([mesh2.data.vertices[k].index], wind_flags[k][0], 'REPLACE')
                    
            # Leaf Card Corner
            if leaf_card_corners:
                for coords in leaf_card_corners:
                    leaf_card_coord_y = coords[1]
                    coords.pop(1)
                    coords.append(leaf_card_coord_y)
                leaf_card_corners = np.array(leaf_card_corners).flatten()
                mesh2.data.attributes['leafCardCorner'].data.foreach_set('vector', leaf_card_corners)
                
            # Leaf Card LOD Scalar
            if leaf_card_lod_scalars:
                leaf_card_lod_scalars = np.array(leaf_card_lod_scalars).flatten()
                mesh2.data.attributes['leafCardLodScalar'].data.foreach_set('value', leaf_card_lod_scalars)
                
            # Leaf Anchor Point
            if leaf_anchor_points:
                leaf_anchor_points = np.array(leaf_anchor_points).flatten()
                mesh2.data.attributes['leafAnchorPoint'].data.foreach_set('vector', leaf_anchor_points)
                
            # Add verts lod position as attributes   
            if verts_lod:
                verts_lod2 = np.array(verts_lod).flatten()
                mesh2.data.attributes['vertexLodPosition'].data.foreach_set('vector', verts_lod2)

            # Material Attribution #
            mat = bpy.context.object.active_material    
            
            for k in srtMat:
                setattr(wm, k, srtMat[k])
                
            for k in range(len(tex_names)):
                if tex_names[k] and tex_names[k] in bpy.data.images:
                    if k == 0:
                        wm.diffuseTexture = bpy.data.images[tex_names[k]]
                    elif k == 1:
                        wm.normalTexture = bpy.data.images[tex_names[k]]
                    elif k == 2:
                        wm.detailTexture = bpy.data.images[tex_names[k]]
                    elif k == 3:
                        wm.detailNormalTexture = bpy.data.images[tex_names[k]]
                    elif k == 4:
                        wm.specularTexture = bpy.data.images[tex_names[k]]
                
            
        # Join submeshes under the same LOD
        finalMeshes_names = []
        JoinThem(mesh_names)
        finalMeshes_names.append(bpy.context.active_object.name)
        
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]