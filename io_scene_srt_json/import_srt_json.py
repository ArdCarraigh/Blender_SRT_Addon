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
    return(prop_values)
        
def JoinThem(mesh_names):
    bpy.context.view_layer.objects.active = None
    bpy.ops.object.select_all(action='DESELECT')
    for j in reversed(range(len(mesh_names))):
        bpy.context.view_layer.objects.active = bpy.data.objects[mesh_names[j]]
        bpy.context.active_object.select_set(state=True)
    bpy.ops.object.join()

def read_srt_json(context, filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        srt = json.load(file)
        
    if bpy.data.window_managers['WinMan'].previewLod:
        bpy.data.window_managers['WinMan'].previewLod = False
    
    # Create Main Collection #
    parent_coll = bpy.context.view_layer.active_layer_collection
    main_coll = bpy.data.collections.new("SRT Asset")
    main_coll_name = main_coll.name
    parent_coll.collection.children.link(main_coll)
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]
    
    
    # Collision Object #
    if "CollisionObjects" in srt:
        collisionObjects = srt["CollisionObjects"]
        spheres = []
        radii = []
        sphere1_mat = bpy.data.materials.new("Material_Sphere1")
        sphere2_mat = bpy.data.materials.new("Material_Sphere2")
        cylinder_mat = bpy.data.materials.new("Material_Cylinder")
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
                sphere_to_connect = []
                bpy.ops.speed_tree.add_srt_collision_sphere(radius = radii[i], location = spheres[i][0])
                sphere_to_connect.append(bpy.context.active_object)
                bpy.ops.speed_tree.add_srt_collision_sphere(radius = radii[i], location = spheres[i][1])
                sphere_to_connect.append(bpy.context.active_object)
                bpy.context.view_layer.objects.active = None
                bpy.ops.object.select_all(action='DESELECT')
                for sphere in sphere_to_connect:
                    bpy.context.view_layer.objects.active = sphere
                    bpy.context.active_object.select_set(state=True)
                bpy.ops.speed_tree.add_srt_sphere_connection()
            
    # Billboards #
    if "VerticalBillboards" in srt:
        # Add vertical billboard collection
        vbb_coll = bpy.data.collections.new("Vertical Billboards")
        vbb_coll_name = vbb_coll.name
        main_coll.children.link(vbb_coll)
        bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name].children[vbb_coll_name]
        
        bb_width = float(srt["VerticalBillboards"]["FWidth"])
        bb_width2 = bb_width/2
        bb_top = float(srt["VerticalBillboards"]["FTopPos"])
        bb_bottom = float(srt["VerticalBillboards"]["FBottomPos"])
        nbb = int(srt["VerticalBillboards"]["NNumBillboards"])
        angle_diff = 360/nbb
        bb_texCoords = srt["VerticalBillboards"]["PTexCoords"]
        bb_rotations = srt["VerticalBillboards"]["PRotated"]
        ncutout = srt["VerticalBillboards"]["NNumCutoutVertices"]
        cutout = srt["VerticalBillboards"]["PCutoutVertices"]
        ncutout_faces = srt["VerticalBillboards"]["NNumCutoutIndices"]
        cutout_faces = srt["VerticalBillboards"]["PCutoutIndices"]
        bb_tex_names = []
        bb_tex_paths = []
        finalBb_names = []
        
        verts_cutout = []
        for j in range(0, ncutout*2, 2):
            verts_cutout.append([-bb_width2 + bb_width * float(cutout[j]), 0, bb_bottom + (bb_top-bb_bottom) * float(cutout[j+1])])
                
        faces_cutout = []
        for j in range(0, ncutout_faces, 3):
            faces_cutout.append([int(cutout_faces[j]), int(cutout_faces[j+1]), int(cutout_faces[j+2])])
        
        #For each billboard texture
        for tex in srt["Geometry"]["ABillboardRenderStateMain"]["ApTextures"]:
            bb_tex_name = tex["Val"]
            bb_tex_names.append(bb_tex_name)
            bb_tex_path = os.path.dirname(filepath) + "\\" + bb_tex_name
            bb_tex_paths.append(bb_tex_path)
        
        for i in range(nbb):
            bb_names = []
            verts = [[-bb_width2, 0, bb_bottom], [bb_width2, 0, bb_bottom], [bb_width2, 0, bb_top], [-bb_width2, 0, bb_top]]
            faces = [[0,1,2], [2,3,0]]
            # Add the mesh to the scene
            bb = bpy.data.meshes.new(name="Mesh_billboard"+str(i))
            bb.from_pydata(verts, [],faces)
            for k in bb.polygons:
                k.use_smooth = True
            object_data_add(context, bb)
            bb_names.append(bpy.context.active_object.name)
            bpy.context.active_object.rotation_euler[2] = math.radians(angle_diff * i)
            
            bb_uvs_data = [float(bb_texCoords[4*i]), float(bb_texCoords[4*i+1]),float(bb_texCoords[4*i+2]), float(bb_texCoords[4*i+3])]
            bb_uvs = [[bb_uvs_data[0], bb_uvs_data[1]],
            [bb_uvs_data[0]+bb_uvs_data[2], bb_uvs_data[1]],
            [bb_uvs_data[0]+bb_uvs_data[2], bb_uvs_data[1]+bb_uvs_data[3]],
            [bb_uvs_data[0], bb_uvs_data[1]+bb_uvs_data[3]]]
            if int(bb_rotations[i]) == 1:
                bb_uvs_data = [bb_uvs[3][1], bb_uvs[3][0], bb_uvs[1][1] - bb_uvs[3][1], bb_uvs[1][0] - bb_uvs[3][0]]
            bb.uv_layers.new(name="DiffuseUV")
            for face in bb.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    if int(bb_rotations[i]) == 1:
                        bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (bb_uvs[vert_idx-1][0], 1-bb_uvs[vert_idx-1][1])
                    else:
                        bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (bb_uvs[vert_idx][0], 1-bb_uvs[vert_idx][1])
            
            # Materials attribution
            temp_mat = bpy.data.materials.new("Material_billboard"+str(i))
            bb.materials.append(temp_mat)
            temp_mat.diffuse_color = (*colorsys.hsv_to_rgb(random.random(), .7, .9), 1) #random hue more pleasing than random rgb
            temp_mat.use_nodes = True
            temp_mat.blend_method = 'CLIP'
            node_main = temp_mat.node_tree.nodes[0]
            node_main.inputs["Specular"].default_value = 0
            
            # Apply textures
            # Diffuse
            if bb_tex_names[0] and bb_uvs:
                if os.path.exists(bb_tex_paths[0]):
                    bpy.ops.image.open(filepath = bb_tex_paths[0])
                node_uv_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
                node_uv_diff.uv_map = "DiffuseUV"
                node_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_diff.name = "Billboard Diffuse Texture"
                if bb_tex_names[0] in bpy.data.images:
                    node_diff.image = bpy.data.images[bb_tex_names[0]]
                temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_diff.inputs["Vector"])
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_main.inputs["Base Color"])
                temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_main.inputs["Alpha"])
                node_diff.location = (-600, 500)
                node_uv_diff.location = (-1500, 400)
                
            # Normal
            if bb_tex_names[1] and bb_uvs:
                if os.path.exists(bb_tex_paths[1]):
                    bpy.ops.image.open(filepath = bb_tex_paths[1])
                node_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
                node_normal3 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeNormalMap')
                node_normal4 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBump')
                node_normal.name = "Billboard Normal Texture"
                if bb_tex_names[1] in bpy.data.images:
                    node_normal.image = bpy.data.images[bb_tex_names[1]]
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
            
            # Cutouts   
            # Add the mesh to the scene
            bb = bpy.data.meshes.new(name=bb_names[-1]+"_cutout")
            bb.from_pydata(verts_cutout, [], faces_cutout)
            for k in bb.polygons:
                k.use_smooth = True
            object_data_add(context, bb)
            bb_names.append(bpy.context.active_object.name)
            bpy.context.active_object.rotation_euler[2] = math.radians(angle_diff * i)
            #UVmap
            bb_uvs_cutout = []
            for j in range(0, ncutout*2, 2):
                bb_uvs_cutout.append([bb_uvs_data[0] + bb_uvs_data[2] * float(cutout[j]), bb_uvs_data[1] + bb_uvs_data[3] * float(cutout[j+1])])
            bb.uv_layers.new(name="DiffuseUV")
            for face in bb.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    if int(bb_rotations[i]) == 1:
                        bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (bb_uvs_cutout[vert_idx][1], 1-bb_uvs_cutout[vert_idx][0])
                    else:
                        bb.uv_layers["DiffuseUV"].data[loop_idx].uv = (bb_uvs_cutout[vert_idx][0], 1-bb_uvs_cutout[vert_idx][1])
            # Apply proper material to lod mesh
            bb.materials.append(temp_mat)
        
           
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
            
            # Material Data
            ambientColor = [mesh_call["PRenderState"]["VAmbientColor"]["x"],
                            mesh_call["PRenderState"]["VAmbientColor"]["y"],
                            mesh_call["PRenderState"]["VAmbientColor"]["z"], 1]
            ambientContrastFactor = mesh_call["PRenderState"]["FAmbientContrastFactor"]
            diffuseColor = [mesh_call["PRenderState"]["VDiffuseColor"]["x"],
                            mesh_call["PRenderState"]["VDiffuseColor"]["y"],
                            mesh_call["PRenderState"]["VDiffuseColor"]["z"], 1]
            diffuseScalar = mesh_call["PRenderState"]["FDiffuseScalar"]
            shininess = mesh_call["PRenderState"]["FShininess"]
            specularColor = [mesh_call["PRenderState"]["VSpecularColor"]["x"],
                            mesh_call["PRenderState"]["VSpecularColor"]["y"],
                            mesh_call["PRenderState"]["VSpecularColor"]["z"], 1]
            transmissionColor = [mesh_call["PRenderState"]["VTransmissionColor"]["x"],
                            mesh_call["PRenderState"]["VTransmissionColor"]["y"],
                            mesh_call["PRenderState"]["VTransmissionColor"]["z"], 1]
            transmissionShadowBrightness = mesh_call["PRenderState"]["FTransmissionShadowBrightness"]
            transmissionViewDependency = mesh_call["PRenderState"]["FTransmissionViewDependency"]
            branchSeamWeight = mesh_call["PRenderState"]["FBranchSeamWeight"]
            alphaScalar = mesh_call["PRenderState"]["FAlphaScalar"]
            cullType = mesh_call["PRenderState"]["EFaceCulling"]
            ambientContrast_bool = mesh_call["PRenderState"]["EAmbientContrast"]
            specular_bool = mesh_call["PRenderState"]["ESpecular"]
            transmission_bool = mesh_call["PRenderState"]["ETransmission"]
            seamSmoothing_bool = mesh_call["PRenderState"]["EBranchSeamSmoothing"]
            detailLayer_bool = mesh_call["PRenderState"]["EDetailLayer"]
            ambientOcclusion_bool = mesh_call["PRenderState"]["BAmbientOcclusion"]
            castShadows_bool = mesh_call["PRenderState"]["BCastsShadows"]
            alphaMaskOpaque_bool = mesh_call["PRenderState"]["BDiffuseAlphaMaskIsOpaque"]
            leafCard_bool = mesh_call["PRenderState"]["BFacingLeavesPresent"]

            # For each vertex
            for k in range(nverts):
                props = mesh_call["PVertexData"][k]["VertexProperties"]
                for prop in props:

                    # Position
                    if prop["PropertyName"] == "VERTEX_PROPERTY_POSITION":
                        if prop["ValueCount"] > 0:
                            verts.append(GetVertValues(prop))

                    # LOD Position
                    if prop["PropertyName"] == "VERTEX_PROPERTY_LOD_POSITION":
                        if prop["ValueCount"] > 0:
                            verts_lod.append(GetVertValues(prop))

                    # Normal
                    if prop["PropertyName"] == "VERTEX_PROPERTY_NORMAL":
                        if prop["ValueCount"] > 0:
                            normals.append(GetVertValues(prop))

                    # Tangent
                    if prop["PropertyName"] == "VERTEX_PROPERTY_TANGENT":
                        if prop["ValueCount"] > 0:
                            tangents.append(GetVertValues(prop))

                    # UV1
                    if prop["PropertyName"] == "VERTEX_PROPERTY_DIFFUSE_TEXCOORDS":
                        if prop["ValueCount"] > 0:
                            uvs_diff.append(GetVertValues(prop))

                    # UV2
                    if prop["PropertyName"] == "VERTEX_PROPERTY_DETAIL_TEXCOORDS":
                        if prop["ValueCount"] > 0:
                            uvs_det.append(GetVertValues(prop))

                    # Geom Type
                    if prop["PropertyName"] == "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT":
                        if prop["ValueCount"] > 0:
                            geom_types.append(GetVertValues(prop))
                            
                    # Leaf Card Corner
                    if prop["PropertyName"] == "VERTEX_PROPERTY_LEAF_CARD_CORNER":
                        if prop["ValueCount"] > 0:
                            leaf_card_corners.append(GetVertValues(prop))
                            
                    # Leaf Card LOD Scalar
                    if prop["PropertyName"] == "VERTEX_PROPERTY_LEAF_CARD_LOD_SCALAR":
                        if prop["ValueCount"] > 0:
                            leaf_card_lod_scalars.append(GetVertValues(prop))

                    # Wind branch data
                    if prop["PropertyName"] == "VERTEX_PROPERTY_WIND_BRANCH_DATA":
                        if prop["ValueCount"] > 0:
                            branches_wind.append(GetVertValues(prop))
                            
                    # Wind extra data
                    if prop["PropertyName"] == "VERTEX_PROPERTY_WIND_EXTRA_DATA":
                        if prop["ValueCount"] > 0:
                            wind_extras.append(GetVertValues(prop))
                            
                    # Wind Flag
                    if prop["PropertyName"] == "VERTEX_PROPERTY_WIND_FLAGS":
                        if prop["ValueCount"] > 0:
                            wind_flags.append(GetVertValues(prop))

                    # Branch seam diffuse
                    if prop["PropertyName"] == "VERTEX_PROPERTY_BRANCH_SEAM_DIFFUSE":
                        if prop["ValueCount"] > 0:
                            branches_seam_diff.append(GetVertValues(prop))

                    # Branch seam detail
                    if prop["PropertyName"] == "VERTEX_PROPERTY_BRANCH_SEAM_DETAIL":
                        if prop["ValueCount"] > 0:
                            branches_seam_det.append(GetVertValues(prop))

                    # Ambient occlusion
                    if prop["PropertyName"] == "VERTEX_PROPERTY_AMBIENT_OCCLUSION":
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
            
            # UVmaps creation
            if uvs_diff:
                mesh.uv_layers.new(name="DiffuseUV")
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["DiffuseUV"].data[loop_idx].uv = (uvs_diff[vert_idx][0], 1-uvs_diff[vert_idx][1])
                        
            if uvs_det:
                mesh.uv_layers.new(name="DetailUV")
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["DetailUV"].data[loop_idx].uv = (uvs_det[vert_idx][0], 1-uvs_det[vert_idx][1])
                        
            if branches_seam_diff:
                mesh.uv_layers.new(name="SeamDiffuseUV")
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.uv_layers["SeamDiffuseUV"].data[loop_idx].uv = (branches_seam_diff[vert_idx][0], 1-branches_seam_diff[vert_idx][1])
                    
            if branches_seam_det:
                mesh.uv_layers.new(name="SeamDetailUV")
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
                mesh.vertex_colors.new(name="AmbientOcclusion")
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.vertex_colors["AmbientOcclusion"].data[loop_idx].color = [ambients[vert_idx][0], ambients[vert_idx][0], ambients[vert_idx][0], 1]
                    
            # Seam Blending
            if branches_seam_diff:
                mesh.vertex_colors.new(name="SeamBlending")
                for face in mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        mesh.vertex_colors["SeamBlending"].data[loop_idx].color = [branches_seam_diff[vert_idx][2], branches_seam_diff[vert_idx][2], branches_seam_diff[vert_idx][2], 1]
            
            mesh2 = bpy.data.objects[bpy.context.active_object.name]
            
            #Geometry type
            if not geom_types and leafCard_bool:
                for vert in verts:
                    geom_types.append([3])
            if geom_types:
                mesh2.vertex_groups.new(name="GeomType")
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["GeomType"].add([mesh2.data.vertices[k].index], ((1 + geom_types[k][0])/5), 'REPLACE')
                    
            #Wind Data
            if branches_wind:
                mesh2.vertex_groups.new(name="WindWeight1")
                mesh2.vertex_groups.new(name="WindNormal1")
                mesh2.vertex_groups.new(name="WindWeight2")
                mesh2.vertex_groups.new(name="WindNormal2")
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["WindWeight1"].add([mesh2.data.vertices[k].index], branches_wind[k][0], 'REPLACE')
                    mesh2.vertex_groups["WindNormal1"].add([mesh2.data.vertices[k].index], branches_wind[k][1]/16, 'REPLACE')
                    mesh2.vertex_groups["WindWeight2"].add([mesh2.data.vertices[k].index], branches_wind[k][2], 'REPLACE')
                    mesh2.vertex_groups["WindNormal2"].add([mesh2.data.vertices[k].index], branches_wind[k][3]/16, 'REPLACE')
                    
            #Wind Extra Data
            if wind_extras:
                mesh2.vertex_groups.new(name="WindExtra1")
                mesh2.vertex_groups.new(name="WindExtra2")
                mesh2.vertex_groups.new(name="WindExtra3")
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["WindExtra1"].add([mesh2.data.vertices[k].index], wind_extras[k][0]/16, 'REPLACE')
                    mesh2.vertex_groups["WindExtra2"].add([mesh2.data.vertices[k].index], wind_extras[k][1], 'REPLACE')
                    mesh2.vertex_groups["WindExtra3"].add([mesh2.data.vertices[k].index], wind_extras[k][2]/2, 'REPLACE')
                    
            #Wind Flag
            if wind_flags:
                mesh2.vertex_groups.new(name="WindFlag")
                for k in range(len(mesh2.data.vertices)):
                    mesh2.vertex_groups["WindFlag"].add([mesh2.data.vertices[k].index], wind_flags[k][0], 'REPLACE')
                    
            # Leaf Card Corner
            if leaf_card_corners:
                for coords in leaf_card_corners:
                    leaf_card_coord_y = coords[1]
                    coords.pop(1)
                    coords.append(leaf_card_coord_y)
                leaf_card_corners = np.array(leaf_card_corners).flatten()
                mesh2.data.attributes.new(name='leafCardCorner', type='FLOAT_VECTOR', domain='POINT')
                mesh2.data.attributes['leafCardCorner'].data.foreach_set('vector', leaf_card_corners)
                
            # Leaf Card LOD Scalar
            if leaf_card_lod_scalars:
                leaf_card_lod_scalars = np.array(leaf_card_lod_scalars).flatten()
                mesh2.data.attributes.new(name='leafCardLodScalar', type='FLOAT', domain='POINT')
                mesh2.data.attributes['leafCardLodScalar'].data.foreach_set('value', leaf_card_lod_scalars)
                
            # Add verts position and lod position as attributes   
            if verts:
                verts2 = np.array(verts).flatten()
                mesh2.data.attributes.new(name='vertexPosition', type='FLOAT_VECTOR', domain='POINT')
                mesh2.data.attributes['vertexPosition'].data.foreach_set('vector', verts2)
            if not verts_lod:
                verts_lod = verts
            if verts_lod:
                verts_lod2 = np.array(verts_lod).flatten()
                mesh2.data.attributes.new(name='vertexLodPosition', type='FLOAT_VECTOR', domain='POINT')
                mesh2.data.attributes['vertexLodPosition'].data.foreach_set('vector', verts_lod2)

            # Material creation #
            
            # Materials attribution
            temp_mat = bpy.data.materials.new("Material"+str(j)+"_lod"+str(i))
            mesh2.data.materials.append(temp_mat)
            temp_mat.diffuse_color = (*colorsys.hsv_to_rgb(random.random(), .7, .9), 1) #random hue more pleasing than random rgb
            temp_mat.use_nodes = True
            if alphaMaskOpaque_bool == False:
                temp_mat.blend_method = 'CLIP'
            elif alphaMaskOpaque_bool == True:
                temp_mat.blend_method = 'OPAQUE'
            if castShadows_bool == True:
                temp_mat.shadow_method = 'CLIP'
            elif castShadows_bool == False:
                temp_mat.shadow_method = 'NONE'
            if cullType == "CULLTYPE_BACK":
                temp_mat.use_backface_culling = True
            temp_mat.node_tree.nodes.remove(temp_mat.node_tree.nodes['Principled BSDF'])
            node_main = temp_mat.node_tree.nodes.new(type = 'ShaderNodeEeveeSpecular')
            node_main.inputs['Base Color'].default_value = (0,0,0,0)
            node_main.inputs['Specular'].default_value = (0,0,0,0)
            node_main.inputs['Emissive Color'].default_value = (0,0,0,0)
            node_main.inputs['Roughness'].default_value = 1
            node_main.location = (700, 300)
            temp_mat.node_tree.nodes["Material Output"].location = (3200, 300)
                
            # Diffuse
            if tex_names[0] and uvs_diff:
                if os.path.exists(tex_paths[0]):
                    bpy.ops.image.open(filepath = tex_paths[0])
                node_uv_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
                node_uv_diff.uv_map = "DiffuseUV"
                node_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_diff.name = "Diffuse Texture"
                if tex_names[0] in bpy.data.images:
                    node_diff.image = bpy.data.images[tex_names[0]]
                node_invert_diffuse_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeInvert')
                node_invert_diffuse_alpha.location = (400, 200)
                temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_diff.inputs["Vector"])
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_main.inputs["Base Color"])
                temp_mat.node_tree.links.new(node_invert_diffuse_alpha.outputs["Color"], node_main.inputs["Transparency"])
                node_diff.location = (-1000, 1100)
                node_uv_diff.location = (-2000, 1100)
                
                node_frame_diffuse_texture = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
                node_diff.parent = node_frame_diffuse_texture
                node_frame_diffuse_texture.use_custom_color = True
                node_frame_diffuse_texture.color = (0.1,0.9,0.1)
                node_frame_diffuse_texture.label = "Diffuse Texture"
                node_frame_diffuse_texture.label_size = 28
                
            # Normal
            if tex_names[1] and uvs_diff:
                if os.path.exists(tex_paths[1]):
                    bpy.ops.image.open(filepath = tex_paths[1])
                node_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
                node_normal3 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeNormalMap')
                node_normal4 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBump')
                node_normal.name = "Normal Texture"
                if tex_names[1] in bpy.data.images:
                    node_normal.image = bpy.data.images[tex_names[1]]
                    node_normal.image.colorspace_settings.name='Non-Color'
                node_normal2.mapping.curves[1].points[0].location = (0,1)
                node_normal2.mapping.curves[1].points[1].location = (1,0)
                temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_normal.inputs["Vector"])
                temp_mat.node_tree.links.new(node_normal.outputs["Color"], node_normal2.inputs["Color"])
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_normal3.inputs["Color"])
                temp_mat.node_tree.links.new(node_normal3.outputs["Normal"], node_normal4.inputs["Normal"])
                temp_mat.node_tree.links.new(node_normal.outputs["Alpha"], node_normal4.inputs["Height"])
                temp_mat.node_tree.links.new(node_normal4.outputs["Normal"], node_main.inputs["Normal"])
                node_normal.location = (-1500, -400)
                node_normal2.location = (-1200, -400)
                node_normal3.location = (-500, -100)
                node_normal4.location = (-300, -100)
                
                node_frame_normal_texture = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
                node_normal.parent = node_frame_normal_texture
                node_frame_normal_texture.use_custom_color = True
                node_frame_normal_texture.color = (0.1,0.9,0.1)
                node_frame_normal_texture.label = "Normal Texture"
                node_frame_normal_texture.label_size = 28
                
            # Specular
            if tex_names[4] and uvs_diff:
                if os.path.exists(tex_paths[4]):
                    bpy.ops.image.open(filepath = tex_paths[4])
                node_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_spec.name = "Specular Texture"
                if tex_names[4] in bpy.data.images:
                    node_spec.image = bpy.data.images[tex_names[4]]
                    node_spec.image.colorspace_settings.name='Non-Color'
                temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_spec.inputs["Vector"])
                temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_main.inputs["Specular"])
                node_spec.location = (-1000, -1800)
                
                node_frame_specular_texture = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
                node_spec.parent = node_frame_specular_texture
                node_frame_specular_texture.use_custom_color = True
                node_frame_specular_texture.color = (0.1,0.9,0.1)
                node_frame_specular_texture.label = "Specular Texture"
                node_frame_specular_texture.label_size = 28
                
            # Add Color Sets data to the material
            #Nodes
            node_light_path = temp_mat.node_tree.nodes.new(type = 'ShaderNodeLightPath')
            node_light_path.location = (2700, 700)
            
            node_rgb_diffuseColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            node_rgb_diffuseColor.name = 'Diffuse Color'
            node_rgb_diffuseColor.outputs['Color'].default_value = diffuseColor
            node_rgb_diffuseColor.location = (-200, 750)
            node_frame_diffuse_color = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_rgb_diffuseColor.parent = node_frame_diffuse_color
            node_frame_diffuse_color.use_custom_color = True
            node_frame_diffuse_color.color = (0.1,0.9,0.1)
            node_frame_diffuse_color.label = "Diffuse Color"
            node_frame_diffuse_color.label_size = 28
            node_diffuseScalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_diffuseScalar.name = 'Diffuse Scalar'
            node_diffuseScalar.outputs['Value'].default_value = diffuseScalar
            node_diffuseScalar.location = (-200, 500)
            node_frame_diffuse_scalar = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_diffuseScalar.parent = node_frame_diffuse_scalar
            node_frame_diffuse_scalar.use_custom_color = True
            node_frame_diffuse_scalar.color = (0.1,0.9,0.1)
            node_frame_diffuse_scalar.label = "Diffuse Scalar"
            node_frame_diffuse_scalar.label_size = 28
            node_diffuseScalar_minus_one = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMath')
            node_diffuseScalar_minus_one.operation = 'SUBTRACT'
            node_diffuseScalar_minus_one.inputs[1].default_value = 1
            node_diffuseScalar_minus_one.location = (0, 500)
            node_diffuseScalar2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBrightContrast')
            node_diffuseScalar2.location = (200, 650)
            node_mix_diffuseScalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_diffuseScalar.blend_type = 'OVERLAY'
            node_mix_diffuseScalar.location = (400, 650)
            
            node_rgb_specularColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            node_rgb_specularColor.name = 'Specular Color'
            node_rgb_specularColor.outputs['Color'].default_value = specularColor
            node_rgb_specularColor.location = (-300, -700)
            node_frame_specular_color = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_rgb_specularColor.parent = node_frame_specular_color
            node_frame_specular_color.use_custom_color = True
            node_frame_specular_color.color = (0.1,0.9,0.1)
            node_frame_specular_color.label = "Specular Color"
            node_frame_specular_color.label_size = 28
            node_mix_specular_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_specular_alpha.name = "Mix Specular Color"
            node_mix_specular_alpha.inputs['Fac'].default_value = 1
            node_mix_specular_alpha.blend_type = 'MULTIPLY'
            node_mix_specular_alpha.location = (-100, -700)
            node_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_shininess.name = 'Shininess'
            node_shininess.outputs['Value'].default_value = shininess
            node_shininess.location = (-300, -950)
            node_frame_shininess = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_shininess.parent = node_frame_shininess
            node_frame_shininess.use_custom_color = True
            node_frame_shininess.color = (0.1,0.9,0.1)
            node_frame_shininess.label = "Shininess"
            node_frame_shininess.label_size = 28
            node_map_range_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_map_range_shininess.inputs['From Max'].default_value = 100.0
            node_map_range_shininess.location = (-100, -950)
            node_invert_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeInvert')
            node_invert_shininess.name = 'Invert Shininess'
            node_invert_shininess.location = (100, -950)
            
            node_rgb_transmissionColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            node_rgb_transmissionColor.name = 'Transmission Color'
            node_rgb_transmissionColor.outputs['Color'].default_value = transmissionColor
            node_rgb_transmissionColor.location = (700, 1050)
            node_frame_transmission_color = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_rgb_transmissionColor.parent = node_frame_transmission_color
            node_frame_transmission_color.use_custom_color = True
            node_frame_transmission_color.color = (0.1,0.9,0.1)
            node_frame_transmission_color.label = "Transmission Color"
            node_frame_transmission_color.label_size = 28
            node_rgb_separate_transmissionColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeSeparateRGB')
            node_rgb_separate_transmissionColor.location = (900, 1050)
            node_map_range_transmission_red = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_map_range_transmission_red.inputs['From Min'].default_value = 0.33333
            node_map_range_transmission_red.location = (1100, 1300)
            node_map_range_transmission_green = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_map_range_transmission_green.inputs['From Min'].default_value = 0.33333
            node_map_range_transmission_green.location = (1100, 1050)
            node_map_range_transmission_blue = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_map_range_transmission_blue.inputs['From Min'].default_value = 0.33333
            node_map_range_transmission_blue.location = (1100, 800)
            node_rgb_combine_transmissionColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeCombineRGB')
            node_rgb_combine_transmissionColor.location = (1300, 1050)
            node_transmissionColor_brightness = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBrightContrast')
            node_transmissionColor_brightness.inputs['Bright'].default_value = 1
            node_transmissionColor_brightness.inputs['Contrast'].default_value = 1
            node_transmissionColor_brightness.location = (1500, 1050)
            node_mix_transmissionColor_diffuse = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_transmissionColor_diffuse.name = 'Mix Transmission Color'
            node_mix_transmissionColor_diffuse.inputs['Fac'].default_value = 1
            node_mix_transmissionColor_diffuse.blend_type = 'OVERLAY'
            node_mix_transmissionColor_diffuse.location = (1700, 1050)
            node_mix_transmission_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_transmission_alpha.inputs['Fac'].default_value = 1
            node_mix_transmission_alpha.inputs['Color1'].default_value = (0,0,0,1)
            node_mix_transmission_alpha.blend_type = 'SUBTRACT'
            node_mix_transmission_alpha.use_clamp = True
            node_mix_transmission_alpha.location = (700, 550)
            node_mix_transmissionColor_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_transmissionColor_alpha.name = "Mix Transmission Alpha"
            node_mix_transmissionColor_alpha.inputs['Fac'].default_value = 1
            node_mix_transmissionColor_alpha.blend_type = 'MULTIPLY'
            node_mix_transmissionColor_alpha.location = (1900, 800)
            node_transluscent_shader = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBsdfTranslucent')
            node_transluscent_shader.location = (2100, 800)
            node_transparent_shader = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBsdfTransparent')
            node_transparent_shader.location = (2100, 1000)
            node_shader_mix_transmission_fresnel = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixShader')
            node_shader_mix_transmission_fresnel.name = 'Mix Shader Fresnel'
            node_shader_mix_transmission_fresnel.inputs['Fac'].default_value = 0
            node_shader_mix_transmission_fresnel.location = (2300, 700)
            node_transmission_fresnel_value = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_transmission_fresnel_value.name = 'Transmission View Dependency'
            node_transmission_fresnel_value.outputs['Value'].default_value = transmissionViewDependency
            node_transmission_fresnel_value.location = (1700, 600)
            node_frame_transmission_view_dependency = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_transmission_fresnel_value.parent = node_frame_transmission_view_dependency
            node_frame_transmission_view_dependency.use_custom_color = True
            node_frame_transmission_view_dependency.color = (0.1,0.9,0.1)
            node_frame_transmission_view_dependency.label = "Transmission View Dependency"
            node_frame_transmission_view_dependency.label_size = 28
            node_transmission_fresnel_map_range = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_transmission_fresnel_map_range.inputs['To Min'].default_value = 1
            node_transmission_fresnel_map_range.inputs['To Max'].default_value = 2.2
            node_transmission_fresnel_map_range.location = (1900, 600)
            node_transmission_fresnel = temp_mat.node_tree.nodes.new(type = 'ShaderNodeFresnel')
            node_transmission_fresnel.name = 'Transmission Fresnel'
            node_transmission_fresnel.location = (2100, 600)
            node_shader_mix_transmission = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixShader')
            node_shader_mix_transmission.inputs['Fac'].default_value = 0.2
            node_shader_mix_transmission.location = (2500, 300)
            
            node_shadow_brightness = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_shadow_brightness.name = 'Mix Shadow Brightness'
            node_shadow_brightness.inputs['Fac'].default_value = 0
            node_shadow_brightness.inputs['Color2'].default_value = (0,0,0,0)
            node_shadow_brightness.location = (2500, -200)
            node_shadow_brightness_value = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_shadow_brightness_value.name = 'Transmission Shadow Brightness'
            node_shadow_brightness_value.outputs['Value'].default_value = 0
            if re.search("ON", transmission_bool):
                node_shadow_brightness_value.outputs['Value'].default_value = transmissionShadowBrightness
            node_shadow_brightness_value.location = (2300, -200)
            node_frame_shadow_brightness = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_shadow_brightness_value.parent = node_frame_shadow_brightness
            node_frame_shadow_brightness.use_custom_color = True
            node_frame_shadow_brightness.color = (0.1,0.9,0.1)
            node_frame_shadow_brightness.label = "Transmission Shadow Brightness"
            node_frame_shadow_brightness.label_size = 28
            node_shadow_shader = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBsdfTransparent')
            node_shadow_shader.location = (2700, -100)
            node_shader_mix_shadow = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixShader')
            node_shader_mix_shadow.location = (3000, 300)
            
            node_map_range_alpha_scalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_map_range_alpha_scalar.inputs['From Max'].default_value = 3
            node_map_range_alpha_scalar.inputs['To Min'].default_value = 0.38
            node_map_range_alpha_scalar.inputs['To Max'].default_value = 8
            node_map_range_alpha_scalar.location = (-200, 200)
            node_add_alpha_scalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMath')
            node_add_alpha_scalar.use_clamp = True
            node_add_alpha_scalar.inputs[1].default_value = 0.1
            node_add_alpha_scalar.location = (0, 200)
            node_mult_alpha_scalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMath')
            node_mult_alpha_scalar.use_clamp = True
            node_mult_alpha_scalar.operation = 'MULTIPLY'
            node_mult_alpha_scalar.location = (200, 200)
            node_alpha_scalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_alpha_scalar.name = 'Alpha Scalar'
            node_alpha_scalar.outputs['Value'].default_value = alphaScalar
            node_alpha_scalar.location = (-400, 200)
            node_frame_alpha_scalar = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_alpha_scalar.parent = node_frame_alpha_scalar
            node_frame_alpha_scalar.use_custom_color = True
            node_frame_alpha_scalar.color = (0.1,0.9,0.1)
            node_frame_alpha_scalar.label = "Alpha Scalar"
            node_frame_alpha_scalar.label_size = 28
            
            node_rgb_ambientColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            node_rgb_ambientColor.name = 'Ambient Color'
            node_rgb_ambientColor.outputs['Color'].default_value = ambientColor
            node_rgb_ambientColor.location = (900, -200)
            node_frame_ambientColor = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_rgb_ambientColor.parent = node_frame_ambientColor
            node_frame_ambientColor.use_custom_color = True
            node_frame_ambientColor.color = (0.1,0.9,0.1)
            node_frame_ambientColor.label = "Ambient Color"
            node_frame_ambientColor.label_size = 28
            node_ambientContrast_mix = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_ambientContrast_mix.name = "Ambient Contrast"
            node_ambientContrast_mix.location = (1100, -200)
            node_ambientContrast = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_ambientContrast.name = 'Ambient Contrast Factor'
            node_ambientContrast.outputs['Value'].default_value = ambientContrastFactor
            node_ambientContrast.location = (900, -450)
            node_frame_ambientContrast = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
            node_ambientContrast.parent = node_frame_ambientContrast
            node_frame_ambientContrast.use_custom_color = True
            node_frame_ambientContrast.color = (0.1,0.9,0.1)
            node_frame_ambientContrast.label = "Ambient Contrast Factor"
            node_frame_ambientContrast.label_size = 28
            
            #Links
            temp_mat.node_tree.links.new(node_diffuseScalar.outputs["Value"], node_diffuseScalar_minus_one.inputs[0])
            temp_mat.node_tree.links.new(node_diffuseScalar_minus_one.outputs["Value"], node_diffuseScalar2.inputs["Bright"])
            temp_mat.node_tree.links.new(node_diffuseScalar_minus_one.outputs["Value"], node_diffuseScalar2.inputs["Contrast"])
            temp_mat.node_tree.links.new(node_rgb_diffuseColor.outputs["Color"], node_diffuseScalar2.inputs["Color"])
            temp_mat.node_tree.links.new(node_diffuseScalar2.outputs["Color"], node_mix_diffuseScalar.inputs["Color2"])
            temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diffuseScalar.inputs["Color1"])
            temp_mat.node_tree.links.new(node_mix_diffuseScalar.outputs["Color"], node_main.inputs["Base Color"])
            
            #temp_mat.node_tree.links.new(node_rgb_ambientColor.outputs["Color"], node_ambientContrast.inputs["Color2"])
            #temp_mat.node_tree.links.new(node_ambientContrast.outputs["Color"], node_shader_specular.inputs["Base Color"])
            
            if tex_names[4]:
                    temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_mix_specular_alpha.inputs["Color1"])
            temp_mat.node_tree.links.new(node_shininess.outputs["Value"], node_map_range_shininess.inputs["Value"])
            temp_mat.node_tree.links.new(node_map_range_shininess.outputs["Result"], node_invert_shininess.inputs["Color"])
            if re.search("ON", specular_bool):
                temp_mat.node_tree.links.new(node_rgb_specularColor.outputs["Color"], node_mix_specular_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_invert_shininess.outputs["Color"], node_main.inputs["Roughness"])
            temp_mat.node_tree.links.new(node_mix_specular_alpha.outputs["Color"], node_main.inputs["Specular"])
            
            temp_mat.node_tree.links.new(node_invert_diffuse_alpha.outputs["Color"], node_mix_transmission_alpha.inputs["Color2"])
            temp_mat.node_tree.links.new(node_mix_transmission_alpha.outputs["Color"], node_mix_transmissionColor_alpha.inputs["Color1"])
            temp_mat.node_tree.links.new(node_mix_transmissionColor_alpha.outputs["Color"], node_transluscent_shader.inputs["Color"])
            temp_mat.node_tree.links.new(node_mix_diffuseScalar.outputs["Color"], node_mix_transmissionColor_alpha.inputs["Color2"])
            temp_mat.node_tree.links.new(node_rgb_transmissionColor.outputs["Color"], node_rgb_separate_transmissionColor.inputs["Image"])
            temp_mat.node_tree.links.new(node_rgb_separate_transmissionColor.outputs["R"], node_map_range_transmission_red.inputs["Value"])
            temp_mat.node_tree.links.new(node_rgb_separate_transmissionColor.outputs["G"], node_map_range_transmission_green.inputs["Value"])
            temp_mat.node_tree.links.new(node_rgb_separate_transmissionColor.outputs["B"], node_map_range_transmission_blue.inputs["Value"])
            temp_mat.node_tree.links.new(node_map_range_transmission_red.outputs["Result"], node_rgb_combine_transmissionColor.inputs["R"])
            temp_mat.node_tree.links.new(node_map_range_transmission_green.outputs["Result"], node_rgb_combine_transmissionColor.inputs["G"])
            temp_mat.node_tree.links.new(node_map_range_transmission_blue.outputs["Result"], node_rgb_combine_transmissionColor.inputs["B"])
            temp_mat.node_tree.links.new(node_rgb_combine_transmissionColor.outputs["Image"], node_transmissionColor_brightness.inputs["Color"])
            temp_mat.node_tree.links.new(node_transmissionColor_brightness.outputs["Color"], node_mix_transmissionColor_diffuse.inputs["Color2"])
            temp_mat.node_tree.links.new(node_mix_diffuseScalar.outputs["Color"], node_mix_transmissionColor_diffuse.inputs["Color1"])
            temp_mat.node_tree.links.new(node_transmission_fresnel_value.outputs["Value"], node_transmission_fresnel_map_range.inputs["Value"])
            temp_mat.node_tree.links.new(node_transmission_fresnel_map_range.outputs["Result"], node_transmission_fresnel.inputs["IOR"])
            temp_mat.node_tree.links.new(node_transparent_shader.outputs["BSDF"], node_shader_mix_transmission_fresnel.inputs[2])
            temp_mat.node_tree.links.new(node_transluscent_shader.outputs["BSDF"], node_shader_mix_transmission_fresnel.inputs[1])
            if tex_names[5]:
                temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_mix_transmission_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_shadow_brightness.inputs["Color2"])
            if re.search("ON", transmission_bool):
                temp_mat.node_tree.links.new(node_mix_transmissionColor_diffuse.outputs["Color"], node_mix_transmissionColor_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_transmission_fresnel.outputs["Fac"], node_shader_mix_transmission_fresnel.inputs["Fac"])
                temp_mat.node_tree.links.new(node_shadow_brightness_value.outputs["Value"], node_shadow_brightness.inputs["Fac"])
                    
            temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_add_alpha_scalar.inputs[0])
            temp_mat.node_tree.links.new(node_add_alpha_scalar.outputs["Value"], node_mult_alpha_scalar.inputs[0])
            temp_mat.node_tree.links.new(node_mult_alpha_scalar.outputs["Value"], node_invert_diffuse_alpha.inputs["Color"])
            temp_mat.node_tree.links.new(node_alpha_scalar.outputs["Value"], node_map_range_alpha_scalar.inputs["Value"])
            temp_mat.node_tree.links.new(node_map_range_alpha_scalar.outputs["Result"], node_mult_alpha_scalar.inputs[1])
            temp_mat.node_tree.links.new(node_invert_diffuse_alpha.outputs["Color"], node_shadow_brightness.inputs["Color1"])
            temp_mat.node_tree.links.new(node_shadow_brightness.outputs["Color"], node_shadow_shader.inputs["Color"])
            
            temp_mat.node_tree.links.new(node_rgb_ambientColor.outputs["Color"], node_ambientContrast_mix.inputs["Color1"])
            if re.search("ON", ambientContrast_bool):
                temp_mat.node_tree.links.new(node_ambientContrast.outputs["Value"], node_ambientContrast_mix.inputs["Fac"])
            
            temp_mat.node_tree.links.new(node_main.outputs["BSDF"], node_shader_mix_transmission.inputs[1])
            temp_mat.node_tree.links.new(node_shader_mix_transmission_fresnel.outputs["Shader"], node_shader_mix_transmission.inputs[2])
            temp_mat.node_tree.links.new(node_shader_mix_transmission.outputs["Shader"], node_shader_mix_shadow.inputs[1])
            temp_mat.node_tree.links.new(node_shadow_shader.outputs["BSDF"], node_shader_mix_shadow.inputs[2])
            
            temp_mat.node_tree.links.new(node_light_path.outputs["Is Shadow Ray"], node_shader_mix_shadow.inputs[0])
            temp_mat.node_tree.links.new(node_shader_mix_shadow.outputs["Shader"], temp_mat.node_tree.nodes["Material Output"].inputs["Surface"])
            
            # Branch seam diffuse
            if tex_names[0] and uvs_diff and branches_seam_diff:
                node_seam_blending = temp_mat.node_tree.nodes.new(type = 'ShaderNodeVertexColor')
                node_seam_blending.layer_name = 'SeamBlending'
                node_seam_blending_weight = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMath')
                node_seam_blending_weight.name = 'Branch Seam Weight Mult'
                node_seam_blending_weight.operation = 'MULTIPLY'
                node_seam_blending_weight.use_clamp = True
                node_seam_blending_weight_value = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
                node_seam_blending_weight_value.name = 'Branch Seam Weight'
                node_seam_blending_weight_value.outputs['Value'].default_value = branchSeamWeight
                node_frame_seam_blending_weight = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
                node_seam_blending_weight_value.parent = node_frame_seam_blending_weight
                node_frame_seam_blending_weight.use_custom_color = True
                node_frame_seam_blending_weight.color = (0.1,0.9,0.1)
                node_frame_seam_blending_weight.label = 'Branch Seam Weight'
                node_frame_seam_blending_weight.label_size = 28
                node_uv_seam_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
                node_uv_seam_diff.uv_map = "SeamDiffuseUV"
                node_seam_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_diff.name = "Branch Seam Diffuse Texture"
                if tex_names[0] in bpy.data.images:
                    node_seam_diff.image = bpy.data.images[tex_names[0]]
                temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_diff.inputs["Vector"])
                node_mix_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_diff.inputs['Fac'].default_value = 1
                node_mix_diff_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_diff_alpha.inputs['Fac'].default_value = 1
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_diff.outputs["Color"], node_mix_diff.inputs["Color1"])
                temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_mix_diff_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_diff.outputs["Alpha"], node_mix_diff_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_seam_blending_weight.inputs[0])
                temp_mat.node_tree.links.new(node_seam_blending_weight_value.outputs["Value"], node_seam_blending_weight.inputs[1])
                if re.search("ON", seamSmoothing_bool):
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_diff.inputs["Fac"])
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_diff_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff.outputs["Color"], node_mix_diffuseScalar.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_diff_alpha.outputs["Color"], node_add_alpha_scalar.inputs[0])
                node_seam_diff.location = (-1000, 1400)
                node_uv_seam_diff.location = (-2000, 1400)
                node_seam_blending.location = (-2200, 0)
                node_mix_diff.location = (-700, 1400)
                node_mix_diff_alpha.location = (-700, 1000)
                node_seam_blending_weight.location = (-2000, 0)
                node_seam_blending_weight_value.location = (-2200, -200)
                
                node_seam_diff.parent = node_frame_diffuse_texture
                
            # Branch seam normal
            if tex_names[1] and uvs_diff and branches_seam_diff:
                node_seam_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
                node_seam_normal.name = "Branch Seam Normal Texture"
                if tex_names[1] in bpy.data.images:
                    node_seam_normal.image = bpy.data.images[tex_names[1]]
                    node_seam_normal.image.colorspace_settings.name='Non-Color'
                node_seam_normal2.mapping.curves[1].points[0].location = (0,1)
                node_seam_normal2.mapping.curves[1].points[1].location = (1,0)
                temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_normal.inputs["Vector"])
                temp_mat.node_tree.links.new(node_seam_normal.outputs["Color"], node_seam_normal2.inputs["Color"])
                node_mix_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_normal.inputs['Fac'].default_value = 1
                node_mix_normal_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_normal_alpha.inputs['Fac'].default_value = 1
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_normal2.outputs["Color"], node_mix_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_normal.outputs["Alpha"], node_mix_normal_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_normal.outputs["Alpha"], node_mix_normal_alpha.inputs["Color1"])
                if re.search("ON", seamSmoothing_bool):
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_normal.inputs["Fac"])
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_normal_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_normal.outputs["Color"], node_normal3.inputs["Color"])
                temp_mat.node_tree.links.new(node_mix_normal_alpha.outputs["Color"], node_normal4.inputs["Height"])
                node_seam_normal.location = (-1500, -100)
                node_seam_normal2.location = (-1200, -100)
                node_mix_normal.location = (-900, -100)
                node_mix_normal_alpha.location = (-900, -400)
                
                node_seam_normal.parent = node_frame_normal_texture

            # Branch seam specular
            if tex_names[4] and uvs_diff and branches_seam_diff:
                node_seam_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_spec.name = "Branch Seam Specular Texture"
                if tex_names[4] in bpy.data.images:
                    node_seam_spec.image = bpy.data.images[tex_names[4]]
                    node_seam_spec.image.colorspace_settings.name='Non-Color'
                temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_spec.inputs["Vector"])
                node_mix_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_spec.inputs['Fac'].default_value = 1
                node_mix_spec_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_spec_alpha.inputs['Fac'].default_value = 1
                temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_mix_spec.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_spec.outputs["Color"], node_mix_spec.inputs["Color1"])
                temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_mix_spec_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_spec.outputs["Alpha"], node_mix_spec_alpha.inputs["Color1"])
                if re.search("ON", seamSmoothing_bool):
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_spec.inputs["Fac"])
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_spec_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_spec_alpha.outputs["Color"], node_mix_transmission_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_spec.outputs["Color"], node_mix_specular_alpha.inputs["Color1"])
                if re.search("ON", transmission_bool):
                    temp_mat.node_tree.links.new(node_mix_spec_alpha.outputs["Color"], node_shadow_brightness.inputs["Color2"])
                node_seam_spec.location = (-1000, -1500)
                node_mix_spec.location = (-700, -1500)
                node_mix_spec_alpha.location = (-700, -1800)
                
                node_seam_spec.parent = node_frame_specular_texture
                
            # Detail
            if tex_names[2] and uvs_det:
                if os.path.exists(tex_paths[2]):
                    bpy.ops.image.open(filepath = tex_paths[2])
                node_uv_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
                node_uv_det.uv_map = "DetailUV"
                node_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_det.name = "Detail Texture"
                if tex_names[2] in bpy.data.images:
                    node_det.image = bpy.data.images[tex_names[2]]
                temp_mat.node_tree.links.new(node_uv_det.outputs["UV"], node_det.inputs["Vector"])
                node_mix_diff_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_diff_det.name = 'Mix Detail Diffuse'
                node_mix_diff_det.inputs['Fac'].default_value = 0
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff_det.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det.outputs["Color"], node_mix_diff_det.inputs["Color2"])
                if re.search("ON", detailLayer_bool):
                    temp_mat.node_tree.links.new(node_det.outputs["Alpha"], node_mix_diff_det.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff_det.outputs["Color"], node_mix_diffuseScalar.inputs["Color1"])
                node_det.location = (-1000, 340)
                node_uv_det.location = (-2000, 500)
                node_mix_diff_det.location = (-450, 600)
                
                node_frame_detail_texture = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
                node_det.parent = node_frame_detail_texture
                node_frame_detail_texture.use_custom_color = True
                node_frame_detail_texture.color = (0.1,0.9,0.1)
                node_frame_detail_texture.label = "Detail Texture"
                node_frame_detail_texture.label_size = 28
                
            # Detail normal
            if tex_names[3] and uvs_det:
                if os.path.exists(tex_paths[3]):
                    bpy.ops.image.open(filepath = tex_paths[3])
                node_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_det_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
                node_det_normal.name = "Detail Normal Texture"
                if tex_names[3] in bpy.data.images:
                    node_det_normal.image = bpy.data.images[tex_names[3]]
                    node_det_normal.image.colorspace_settings.name='Non-Color'
                node_det_normal2.mapping.curves[1].points[0].location = (0,1)
                node_det_normal2.mapping.curves[1].points[1].location = (1,0)
                temp_mat.node_tree.links.new(node_uv_det.outputs["UV"], node_det_normal.inputs["Vector"])
                temp_mat.node_tree.links.new(node_det_normal.outputs["Color"], node_det_normal2.inputs["Color"])
                node_mix_diff_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_diff_det_normal.name = 'Mix Detail Normal'
                node_mix_diff_det_normal.inputs['Fac'].default_value = 0
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_diff_det_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det_normal2.outputs["Color"], node_mix_diff_det_normal.inputs["Color2"])
                if re.search("ON", detailLayer_bool):
                    temp_mat.node_tree.links.new(node_det_normal.outputs["Alpha"], node_mix_diff_det_normal.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff_det_normal.outputs["Color"], node_normal3.inputs["Color"])
                node_det_normal.location = (-1500, -1100)
                node_det_normal2.location = (-1200, -1100)
                node_mix_diff_det_normal.location = (-700, -600)
                
                node_frame_detail_normal_texture = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
                node_det_normal.parent = node_frame_detail_normal_texture
                node_frame_detail_normal_texture.use_custom_color = True
                node_frame_detail_normal_texture.color = (0.1,0.9,0.1)
                node_frame_detail_normal_texture.label = "Detail Normal Texture"
                node_frame_detail_normal_texture.label_size = 28
                
            # Branch seam detail
            if tex_names[2] and uvs_det and branches_seam_det:
                node_uv_seam_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
                node_uv_seam_det.uv_map = "SeamDetailUV"
                node_seam_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_det.name = "Branch Seam Detail Texture"
                if tex_names[2] in bpy.data.images:
                    node_seam_det.image = bpy.data.images[tex_names[2]]
                temp_mat.node_tree.links.new(node_uv_seam_det.outputs["UV"], node_seam_det.inputs["Vector"])
                node_mix_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_det.inputs['Fac'].default_value = 1
                node_mix_det_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_det_alpha.name = 'Mix Detail Seam'
                node_mix_det_alpha.inputs['Fac'].default_value = 1
                temp_mat.node_tree.links.new(node_det.outputs["Color"], node_mix_det.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det.outputs["Color"], node_mix_det.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det.outputs["Alpha"], node_mix_det_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det.outputs["Alpha"], node_mix_det_alpha.inputs["Color1"])
                if re.search("ON", seamSmoothing_bool):
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det.inputs["Fac"])
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff.inputs["Color2"])
                temp_mat.node_tree.links.new(node_mix_diff.outputs["Color"], node_mix_diff_det.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_det.outputs["Color"], node_mix_diff_det.inputs["Color2"])
                if re.search("ON", detailLayer_bool):
                    temp_mat.node_tree.links.new(node_mix_det_alpha.outputs["Color"], node_mix_diff_det.inputs["Fac"])
                node_seam_det.location = (-1000, 600)
                node_uv_seam_det.location = (-2000, 800)
                node_mix_det.location = (-700, 600)
                node_mix_det_alpha.location = (-700, 340)
                
                node_seam_det.parent = node_frame_detail_texture
                
            # Branch seam detail normal
            if tex_names[3] and uvs_det and branches_seam_det:
                node_seam_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_det_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
                node_seam_det_normal.name = "Branch Seam Detail Normal Texture"
                if tex_names[3] in bpy.data.images:
                    node_seam_det_normal.image = bpy.data.images[tex_names[3]]
                    node_seam_det_normal.image.colorspace_settings.name='Non-Color'
                node_seam_det_normal2.mapping.curves[1].points[0].location = (0,1)
                node_seam_det_normal2.mapping.curves[1].points[1].location = (1,0)
                temp_mat.node_tree.links.new(node_uv_seam_det.outputs["UV"], node_seam_det_normal.inputs["Vector"])
                temp_mat.node_tree.links.new(node_seam_det_normal.outputs["Color"], node_seam_det_normal2.inputs["Color"])
                node_mix_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_det_normal.inputs['Fac'].default_value = 1
                node_mix_det_normal_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_det_normal_alpha.name = 'Mix Detail Normal Seam'
                node_mix_det_normal_alpha.inputs['Fac'].default_value = 1
                temp_mat.node_tree.links.new(node_det_normal2.outputs["Color"], node_mix_det_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det_normal2.outputs["Color"], node_mix_det_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det_normal.outputs["Alpha"], node_mix_det_normal_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det_normal.outputs["Alpha"], node_mix_det_normal_alpha.inputs["Color1"])
                if re.search("ON", seamSmoothing_bool):
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det_normal.inputs["Fac"])
                    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det_normal_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_mix_normal.outputs["Color"], node_mix_diff_det_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_det_normal.outputs["Color"], node_mix_diff_det_normal.inputs["Color2"])
                if re.search("ON", detailLayer_bool):
                    temp_mat.node_tree.links.new(node_mix_det_normal_alpha.outputs["Color"], node_mix_diff_det_normal.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff_det_normal.outputs["Color"], node_normal3.inputs["Color"])
                node_seam_det_normal.location = (-1500, -800)
                node_seam_det_normal2.location = (-1200, -800)
                node_mix_det_normal.location = (-900, -1100)
                node_mix_det_normal_alpha.location = (-900, -800)
                
                node_seam_det_normal.parent = node_frame_detail_normal_texture
                
            # Ambient Occlusion
            node_ambient_occlusion_vertex_color = temp_mat.node_tree.nodes.new(type = 'ShaderNodeVertexColor')
            node_ambient_occlusion_vertex_color.layer_name = 'AmbientOcclusion'
            node_ambient_occlusion_vertex_color.location = (-500, -2300)
            node_ambient_occlusion = temp_mat.node_tree.nodes.new(type = 'ShaderNodeAmbientOcclusion')
            node_ambient_occlusion.name = 'Ambient Occlusion'
            node_ambient_occlusion.location = (-300, -2300)
            temp_mat.node_tree.links.new(node_ambient_occlusion_vertex_color.outputs["Color"], node_ambient_occlusion.inputs["Color"])
            if ambientOcclusion_bool == True:
                temp_mat.node_tree.links.new(node_ambient_occlusion.outputs["Color"], node_main.inputs["Ambient Occlusion"])
            
        # Join submeshes under the same LOD
        finalMeshes_names = []
        JoinThem(mesh_names)
        finalMeshes_names.append(bpy.context.active_object.name)
        
        # Geometry nodes for Facing Leaves
        bpy.context.active_object.modifiers.new(type='NODES', name = "Leaf Card")
        geom_nodes = bpy.context.active_object.modifiers[0]
        start_geom = geom_nodes.node_group.nodes['Group Input']
        end_geom = geom_nodes.node_group.nodes['Group Output']
        leaf_card_transform = geom_nodes.node_group.nodes.new(type = "GeometryNodePointTranslate")
        leaf_card_transform.name = 'Leaf Card Corner'
        leaf_card_transform.inputs['Translation'].default_value = "leafCardCorner"
        leaf_card_transform.location = (50, 0)
        leaf_card_lod_scalar = geom_nodes.node_group.nodes.new(type = "GeometryNodeAttributeVectorMath")
        leaf_card_lod_scalar.name = 'Leaf Card LOD Scalar'
        leaf_card_lod_scalar.operation = 'MULTIPLY'
        leaf_card_lod_scalar.input_type_b = 'VECTOR'
        leaf_card_lod_scalar.inputs['A'].default_value = "leafCardCorner"
        leaf_card_lod_scalar.inputs['B'].default_value = 'leafCardLodScalar'
        leaf_card_lod_scalar.inputs[4].default_value = (1,1,1)
        leaf_card_lod_scalar.inputs['Result'].default_value = "leafCardCorner"
        leaf_card_lod_scalar.location = (-150, 0)
        geom_nodes.node_group.links.new(start_geom.outputs['Geometry'], leaf_card_lod_scalar.inputs["Geometry"])
        geom_nodes.node_group.links.new(leaf_card_lod_scalar.outputs['Geometry'], leaf_card_transform.inputs["Geometry"])
        geom_nodes.node_group.links.new(leaf_card_transform.outputs['Geometry'], end_geom.inputs["Geometry"])
        
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]
