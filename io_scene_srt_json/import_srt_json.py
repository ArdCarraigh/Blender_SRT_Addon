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

def make_cylinder(pos_1, R1, pos_2, R2):
    pos_1 = np.array(pos_1)
    pos_2 = np.array(pos_2)
    AB = np.linalg.norm(pos_2-pos_1)
    BE = abs(R2-R1)
    AE = (AB**2 - (R2-R1)**2)**.5
    cone_radius_1 = R1 * AE / AB
    cone_radius_2 = R2 * AE / AB
    AG = R1 * BE / AB
    BF = R2 * BE / AB
    
    AB_dir = (pos_2-pos_1)/AB
    if R1 > R2:
        cone_pos = pos_1 + AB_dir * AG
    else:
        cone_pos = pos_1 - AB_dir * AG
    
    cone_depth = AB - abs(AG-BF)
    cone_pos = cone_pos + AB_dir * cone_depth * .5 #cone pos is midpoint of centerline
    rotation = Vector([0,0,1]).rotation_difference(Vector(AB_dir)).to_euler("XYZ") ### may need to change
    
    bpy.ops.mesh.primitive_cone_add(
        vertices=24, 
        radius1=cone_radius_1, 
        radius2=cone_radius_2, 
        depth=cone_depth, 
        location=cone_pos, 
        rotation=rotation, 
        )
        
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
            
        # Add collision collection
        col_coll = bpy.data.collections.new("Collision Objects")
        col_coll_name = col_coll.name
        main_coll.children.link(col_coll)
        bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name].children[col_coll_name]
    
        # Impot collision objects
        for i in range(len(spheres)):
            #Sphere1
            bpy.ops.mesh.primitive_uv_sphere_add(radius = radii[i], location = spheres[i][0], segments=24, ring_count=16)
            sphere1_name = bpy.context.active_object.name
            bpy.context.active_object.display_type = 'WIRE'
            bpy.context.active_object.data.materials.append(sphere1_mat)
            
            #Sphere2
            bpy.ops.mesh.primitive_uv_sphere_add(radius = radii[i], location = spheres[i][1], segments=24, ring_count=16)
            sphere2_name = bpy.context.active_object.name
            bpy.context.active_object.display_type = 'WIRE'
            bpy.context.active_object.data.materials.append(sphere2_mat)
            
            #Cylinder in between
            make_cylinder(spheres[i][0], radii[i], spheres[i][1], radii[i])
            cylinder_name = bpy.context.active_object.name
            bpy.context.active_object.display_type = 'WIRE'
            bpy.context.active_object.data.materials.append(cylinder_mat)
            
            #Join them all
            col_names = [sphere1_name, sphere2_name,cylinder_name]
            JoinThem(col_names)
            bpy.context.active_object.name = "Mesh_col"+str(i)
            
            
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
            branches_wind = []
            wind_extras = []
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

                    # Geom Type?
                    if prop["PropertyName"] == "VERTEX_PROPERTY_GEOMETRY_TYPE_HINT":
                        if prop["ValueCount"] > 0:
                            geom_types.append(GetVertValues(prop))

                    # Wind branch data
                    if prop["PropertyName"] == "VERTEX_PROPERTY_WIND_BRANCH_DATA":
                        if prop["ValueCount"] > 0:
                            branches_wind.append(GetVertValues(prop))
                            
                    # Wind extra data
                    if prop["PropertyName"] == "VERTEX_PROPERTY_WIND_EXTRA_DATA":
                        if prop["ValueCount"] > 0:
                            wind_extras.append(GetVertValues(prop))

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
                        
            # Tangent and Normals #Looks like this part is kinda useless
            #mesh.calc_normals()
            #for k in range(len(mesh.vertices)):
                #mesh.vertices[k].normal = normals[k]
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh.normals_split_custom_set_from_vertices(normals)
            mesh.use_auto_smooth = True
            #mesh.calc_tangents()
            #for face in mesh.polygons:
                #for vert in [mesh.loops[k] for k in face.loop_indices]:
                    #vert.normal = normals[vert.vertex_index]
                    #Read-only... :(
                    #vert.tangent = tangents3[vert.vertex_index]
                    #vert.bitangent_sign = bitangent_sign0[vert.vertex_index]
                    
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

            
            # Materials attribution
            temp_mat = bpy.data.materials.new("Material"+str(j)+"_lod"+str(i))
            mesh2.data.materials.append(temp_mat)
            temp_mat.diffuse_color = (*colorsys.hsv_to_rgb(random.random(), .7, .9), 1) #random hue more pleasing than random rgb
            temp_mat.use_nodes = True
            temp_mat.blend_method = 'CLIP'
            temp_mat.shadow_method = 'CLIP'
            if cullType == "CULLTYPE_BACK":
                temp_mat.use_backface_culling = True
            node_main = temp_mat.node_tree.nodes[0]
            node_main.inputs["Specular"].default_value = 0
            node_main.inputs["Roughness"].default_value = 1.0
            node_main.location = (700, 300)   
            
            # Apply textures #
                
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
                temp_mat.node_tree.links.new(node_uv_diff.outputs["UV"], node_diff.inputs["Vector"])
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_main.inputs["Base Color"])
                temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_main.inputs["Alpha"])
                node_diff.location = (-1000, 1100)
                node_uv_diff.location = (-2000, 1100)
                
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
                if tex_names[5]:
                    temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_main.inputs["Transmission"])
                node_spec.location = (-1000, -1800)
                
            # Add Color Sets data to the material
            #Nodes
            node_light_path = temp_mat.node_tree.nodes.new(type = 'ShaderNodeLightPath')
            node_light_path.location = (-400, 2000)
            
            node_rgb_diffuseColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            node_rgb_diffuseColor.name = 'Diffuse Color'
            node_rgb_diffuseColor.outputs['Color'].default_value = diffuseColor
            node_rgb_diffuseColor.location = (-200, 750)
            node_diffuseScalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_diffuseScalar.name = 'Diffuse Scalar'
            node_diffuseScalar.outputs['Value'].default_value = diffuseScalar
            node_diffuseScalar.location = (-200, 500)
            node_diffuseScalar2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBrightContrast')
            node_diffuseScalar2.location = (0, 650)
            node_mix_diffuseScalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_diffuseScalar.blend_type = 'OVERLAY'
            node_mix_diffuseScalar.location = (200, 650)
            
            node_shader_mix_specular = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixShader')
            node_shader_mix_specular.inputs['Fac'].default_value = 0.1
            node_shader_mix_specular.location = (1500, 300)
            node_rgb_specularColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            node_rgb_specularColor.name = 'Specular Color'
            node_rgb_specularColor.outputs['Color'].default_value = specularColor
            node_rgb_specularColor.location = (500, 1000)
            node_mix_specular_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_mix_specular_alpha.inputs['Fac'].default_value = 1
            node_mix_specular_alpha.blend_type = 'MULTIPLY'
            node_mix_specular_alpha.location = (700, 1000)
            node_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
            node_shininess.name = 'Shininess'
            node_shininess.outputs['Value'].default_value = shininess
            node_shininess.location = (400, 800)
            node_map_range_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
            node_map_range_shininess.inputs['From Max'].default_value = 100.0
            node_map_range_shininess.location = (600, 800)
            node_invert_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeInvert')
            node_invert_shininess.location = (800, 800)
            node_shader_specular = temp_mat.node_tree.nodes.new(type = 'ShaderNodeEeveeSpecular')
            node_shader_specular.inputs['Base Color'].default_value = (0,0,0,0)
            node_shader_specular.inputs['Specular'].default_value = (0,0,0,0)
            node_shader_specular.inputs['Emissive Color'].default_value = (0,0,0,0)
            node_shader_specular.inputs['Roughness'].default_value = 1
            node_shader_specular.location = (1000, 1000)
            node_invert_diffuse_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeInvert')
            node_invert_diffuse_alpha.location = (600, 550)
            
            #node_rgb_ambientColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            #node_rgb_ambientColor.name = 'Ambient Color'
            #node_rgb_ambientColor.outputs['Color'].default_value = ambientColor
            #node_rgb_ambientColor.location = (100, 1250)
            #node_rgb_transmissionColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
            #node_rgb_transmissionColor.name = 'Transmission Color'
            #node_rgb_transmissionColor.outputs['Color'].default_value = transmissionColor
            #node_rgb_transmissionColor.location = (500, 600)
            #node_ambientContrast = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            #node_ambientContrast.name = 'Ambient Contrast'
            #if re.search("ON", ambientContrast_bool):
                #node_ambientContrast.blend_type = 'DARKEN'
            #node_ambientContrast.inputs['Fac'].default_value = ambientContrastFactor
            #node_ambientContrast.location = (500, 1350)
            
            node_shadow_brightness = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
            node_shadow_brightness.name = 'Shadow Brightness'
            node_shadow_brightness.inputs['Fac'].default_value = 0
            node_shadow_brightness.location = (1300, -200)
            node_shadow_shader = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBsdfTransparent')
            node_shadow_shader.location = (1500, -100)
            node_shader_mix_shadow = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixShader')
            node_shader_mix_shadow.location = (1750, 300)
            
            #Links
            temp_mat.node_tree.links.new(node_diffuseScalar.outputs["Value"], node_diffuseScalar2.inputs["Bright"])
            temp_mat.node_tree.links.new(node_diffuseScalar.outputs["Value"], node_diffuseScalar2.inputs["Contrast"])
            temp_mat.node_tree.links.new(node_rgb_diffuseColor.outputs["Color"], node_diffuseScalar2.inputs["Color"])
            temp_mat.node_tree.links.new(node_diffuseScalar2.outputs["Color"], node_mix_diffuseScalar.inputs["Color2"])
            temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diffuseScalar.inputs["Color1"])
            temp_mat.node_tree.links.new(node_mix_diffuseScalar.outputs["Color"], node_main.inputs["Base Color"])
            
            #temp_mat.node_tree.links.new(node_rgb_ambientColor.outputs["Color"], node_ambientContrast.inputs["Color2"])
            #temp_mat.node_tree.links.new(node_ambientContrast.outputs["Color"], node_shader_specular.inputs["Base Color"])
            
            temp_mat.node_tree.links.new(node_rgb_specularColor.outputs["Color"], node_mix_specular_alpha.inputs["Color2"])
            if tex_names[4]:
                    temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_mix_specular_alpha.inputs["Color1"])
            temp_mat.node_tree.links.new(node_shininess.outputs["Value"], node_map_range_shininess.inputs["Value"])
            temp_mat.node_tree.links.new(node_map_range_shininess.outputs["Result"], node_invert_shininess.inputs["Color"])
            if re.search("ON", specular_bool):
                temp_mat.node_tree.links.new(node_mix_specular_alpha.outputs["Color"], node_shader_specular.inputs["Specular"])
                temp_mat.node_tree.links.new(node_invert_shininess.outputs["Color"], node_shader_specular.inputs["Roughness"])
            temp_mat.node_tree.links.new(node_invert_diffuse_alpha.outputs["Color"], node_shader_specular.inputs["Transparency"])
            
            if re.search("ON", transmission_bool):
                #temp_mat.node_tree.links.new(node_rgb_transmissionColor.outputs["Color"], node_shader_specular.inputs["Emissive Color"])
                #temp_mat.node_tree.links.new(node_rgb_transmissionColor.outputs["Color"], node_shader_specular.inputs["Emissive Color"])
                node_shadow_brightness.inputs['Fac'].default_value = transmissionShadowBrightness
                if tex_names[5]:
                    temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_shadow_brightness.inputs["Color2"])
            temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_invert_diffuse_alpha.inputs["Color"])
            temp_mat.node_tree.links.new(node_invert_diffuse_alpha.outputs["Color"], node_shadow_brightness.inputs["Color1"])
            temp_mat.node_tree.links.new(node_shadow_brightness.outputs["Color"], node_shadow_shader.inputs["Color"])
            
            temp_mat.node_tree.links.new(node_main.outputs["BSDF"], node_shader_mix_specular.inputs[1])
            temp_mat.node_tree.links.new(node_shader_specular.outputs["BSDF"], node_shader_mix_specular.inputs[2])
            temp_mat.node_tree.links.new(node_shader_mix_specular.outputs["Shader"], node_shader_mix_shadow.inputs[1])
            temp_mat.node_tree.links.new(node_shadow_shader.outputs["BSDF"], node_shader_mix_shadow.inputs[2])
            #temp_mat.node_tree.links.new(node_shader_specular.outputs["BSDF"], node_shader_mix.inputs[1])
            
            #temp_mat.node_tree.links.new(node_shader_mix.outputs["Shader"], node_shader_mix_shadow.inputs[1])
            temp_mat.node_tree.links.new(node_light_path.outputs["Is Shadow Ray"], node_shader_mix_shadow.inputs[0])
            temp_mat.node_tree.links.new(node_shader_mix_shadow.outputs["Shader"], temp_mat.node_tree.nodes["Material Output"].inputs["Surface"])
        
            temp_mat.node_tree.nodes["Material Output"].location = (2000, 300)
            
            # Branch seam diffuse
            if tex_names[0] and uvs_diff and branches_seam_diff:
                node_seam_blending = temp_mat.node_tree.nodes.new(type = 'ShaderNodeVertexColor')
                node_seam_blending.layer_name = 'SeamBlending'
                node_uv_seam_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
                node_uv_seam_diff.uv_map = "SeamDiffuseUV"
                node_seam_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_diff.name = "Branch Seam Diffuse Texture"
                if tex_names[0] in bpy.data.images:
                    node_seam_diff.image = bpy.data.images[tex_names[0]]
                temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_diff.inputs["Vector"])
                node_mix_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_diff_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_diff.outputs["Color"], node_mix_diff.inputs["Color1"])
                temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_mix_diff_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_diff.outputs["Alpha"], node_mix_diff_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_diff.inputs["Fac"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_diff_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff.outputs["Color"], node_mix_diffuseScalar.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_diff_alpha.outputs["Color"], node_main.inputs["Alpha"])
                temp_mat.node_tree.links.new(node_mix_diff_alpha.outputs["Color"], node_invert_diffuse_alpha.inputs["Color"])
                node_seam_diff.location = (-1000, 1400)
                node_uv_seam_diff.location = (-2000, 1400)
                node_seam_blending.location = (-2000, 900)
                node_mix_diff.location = (-700, 1400)
                node_mix_diff_alpha.location = (-700, 1000)
                
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
                node_mix_normal_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_normal2.outputs["Color"], node_mix_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_normal.outputs["Alpha"], node_mix_normal_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_normal.outputs["Alpha"], node_mix_normal_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_normal.inputs["Fac"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_normal_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_normal.outputs["Color"], node_normal3.inputs["Color"])
                temp_mat.node_tree.links.new(node_mix_normal_alpha.outputs["Color"], node_normal4.inputs["Height"])
                node_seam_normal.location = (-1500, -100)
                node_seam_normal2.location = (-1200, -100)
                node_mix_normal.location = (-900, -100)
                node_mix_normal_alpha.location = (-900, -400)

            # Branch seam specular
            if tex_names[4] and uvs_diff and branches_seam_diff:
                node_seam_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                node_seam_spec.name = "Branch Seam Specular Texture"
                if tex_names[4] in bpy.data.images:
                    node_seam_spec.image = bpy.data.images[tex_names[4]]
                    node_seam_spec.image.colorspace_settings.name='Non-Color'
                temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_spec.inputs["Vector"])
                node_mix_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                node_mix_spec_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_mix_spec.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_spec.outputs["Color"], node_mix_spec.inputs["Color1"])
                temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_mix_spec_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_spec.outputs["Alpha"], node_mix_spec_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_spec.inputs["Fac"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_spec_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_spec.outputs["Color"], node_main.inputs["Specular"])
                temp_mat.node_tree.links.new(node_mix_spec_alpha.outputs["Color"], node_main.inputs["Transmission"])
                temp_mat.node_tree.links.new(node_mix_spec.outputs["Color"], node_mix_specular_alpha.inputs["Color1"])
                if re.search("ON", transmission_bool):
                    temp_mat.node_tree.links.new(node_mix_spec_alpha.outputs["Color"], node_shadow_brightness.inputs["Color2"])
                node_seam_spec.location = (-1000, -1500)
                node_mix_spec.location = (-700, -1500)
                node_mix_spec_alpha.location = (-700, -1800)
                
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
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff_det.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det.outputs["Color"], node_mix_diff_det.inputs["Color2"])
                temp_mat.node_tree.links.new(node_det.outputs["Alpha"], node_mix_diff_det.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff_det.outputs["Color"], node_mix_diffuseScalar.inputs["Color1"])
                node_det.location = (-1000, 340)
                node_uv_det.location = (-2000, 340)
                node_mix_diff_det.location = (-450, 600)
                
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
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_diff_det_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det_normal2.outputs["Color"], node_mix_diff_det_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_det_normal.outputs["Alpha"], node_mix_diff_det_normal.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff_det_normal.outputs["Color"], node_normal3.inputs["Color"])
                node_det_normal.location = (-1500, -1100)
                node_det_normal2.location = (-1200, -1100)
                node_mix_diff_det_normal.location = (-600, -600)
                
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
                node_mix_det_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                temp_mat.node_tree.links.new(node_det.outputs["Color"], node_mix_det.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det.outputs["Color"], node_mix_det.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det.outputs["Alpha"], node_mix_det_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det.outputs["Alpha"], node_mix_det_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_det.inputs["Fac"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_det_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff.inputs["Color2"])
                temp_mat.node_tree.links.new(node_mix_diff.outputs["Color"], node_mix_diff_det.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_det.outputs["Color"], node_mix_diff_det.inputs["Color2"])
                temp_mat.node_tree.links.new(node_mix_det_alpha.outputs["Color"], node_mix_diff_det.inputs["Fac"])
                node_seam_det.location = (-1000, 600)
                node_uv_seam_det.location = (-2000, 600)
                node_mix_det.location = (-700, 600)
                node_mix_det_alpha.location = (-700, 340)
                
            # Branch seam detain normal
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
                node_mix_det_normal_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
                temp_mat.node_tree.links.new(node_det_normal2.outputs["Color"], node_mix_det_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det_normal2.outputs["Color"], node_mix_det_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_det_normal.outputs["Alpha"], node_mix_det_normal_alpha.inputs["Color2"])
                temp_mat.node_tree.links.new(node_seam_det_normal.outputs["Alpha"], node_mix_det_normal_alpha.inputs["Color1"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_det_normal.inputs["Fac"])
                temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_mix_det_normal_alpha.inputs["Fac"])
                temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_mix_normal.outputs["Color"], node_mix_diff_det_normal.inputs["Color1"])
                temp_mat.node_tree.links.new(node_mix_det_normal.outputs["Color"], node_mix_diff_det_normal.inputs["Color2"])
                temp_mat.node_tree.links.new(node_mix_det_normal_alpha.outputs["Color"], node_mix_diff_det_normal.inputs["Fac"])
                temp_mat.node_tree.links.new(node_mix_diff_det_normal.outputs["Color"], node_normal3.inputs["Color"])
                node_seam_det_normal.location = (-1500, -800)
                node_seam_det_normal2.location = (-1200, -800)
                node_mix_det_normal.location = (-900, -1100)
                node_mix_det_normal_alpha.location = (-900, -800)
                
            # Add the lod mesh to the scene
            if verts_lod:
                mesh = bpy.data.meshes.new(name=mesh_names[-1]+"_LOD")
                mesh.from_pydata(verts_lod, [], faces)
                for k in mesh.polygons:
                    k.use_smooth = True
                object_data_add(context, mesh)
                mesh_lod_names.append(bpy.context.active_object.name)
                
            # Apply proper material to lod mesh
            mesh.materials.append(temp_mat)
            
        # Join submeshes under the same LOD
        finalMeshes_names = []
        JoinThem(mesh_names)
        finalMeshes_names.append(bpy.context.active_object.name)
        
        # Join lod submeshes under the same LOD
        finalMeshes_lod_names = []
        JoinThem(mesh_lod_names)
        finalMeshes_lod_names.append(bpy.context.active_object.name)
        
    bpy.context.view_layer.active_layer_collection = parent_coll.children[main_coll_name]
