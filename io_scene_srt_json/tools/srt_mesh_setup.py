# -*- coding: utf-8 -*-
# tools/srt_mesh_setup.py

import bpy
import numpy as np
import re
import random, colorsys
import os

def get_parent_collection(collection, parent_colls):  
    for parent_collection in bpy.data.collections:
        if collection.name in parent_collection.children.keys():
            parent_colls.append(parent_collection)

def srt_mesh_setup(context, apply_geom_type, geom_type):
    
    # Deal with Collections
    parent_coll = bpy.context.view_layer.active_layer_collection
    for obj in bpy.context.selected_objects:
        sub_colls = []
        main_colls = []
        if obj.users_collection:
            sub_colls.append(obj.users_collection)
        if sub_colls:
            get_parent_collection(sub_colls[0][0], main_colls)
            
        if sub_colls and main_colls:
            if not re.search("LOD", sub_colls[0][0].name) or not re.search("SRT Asset", main_colls[0].name):
                srt_coll = bpy.data.collections.new("SRT Asset")
                srt_coll_name = srt_coll.name
                lod_coll = bpy.data.collections.new("LOD0")
                lod_coll_name = lod_coll.name
                parent_coll.collection.children.link(srt_coll)
                srt_coll.children.link(lod_coll)
                bpy.context.view_layer.active_layer_collection = parent_coll.children[srt_coll_name].children[lod_coll_name]
                bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)
                sub_colls[0][0].objects.unlink(obj)
        
        else:
            srt_coll = bpy.data.collections.new("SRT Asset")
            srt_coll_name = srt_coll.name
            lod_coll = bpy.data.collections.new("LOD0")
            lod_coll_name = lod_coll.name
            parent_coll.collection.children.link(srt_coll)
            srt_coll.children.link(lod_coll)
            bpy.context.view_layer.active_layer_collection = parent_coll.children[srt_coll_name].children[lod_coll_name]
            bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)
            if sub_colls:
                sub_colls[0][0].objects.unlink(obj)
                
        #Custom Properties for General User Settings
        if 'srt_coll' in locals():
            # User Settings
            srt_coll['EBillboardRandomType'] = 'NoBillboard'
            srt_coll['ETerrainNormals'] = 'TerrainNormalsOff'
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
                
        # Deal with Vertex Groups
        if 'GeomType' not in obj.vertex_groups:
            obj.vertex_groups.new(name="GeomType")
        for vert in obj.data.vertices:
            if apply_geom_type:
                obj.vertex_groups["GeomType"].add([vert.index], float(geom_type), 'REPLACE')
            else:
                obj.vertex_groups["GeomType"].add([vert.index], 0, 'REPLACE')
        if 'WindWeight1' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindWeight1')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindWeight1'].add([vert.index], 0, 'REPLACE')
        if 'WindNormal1' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindNormal1')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindNormal1'].add([vert.index], 0, 'REPLACE')
        if 'WindWeight2' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindWeight2')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindWeight2'].add([vert.index], 0, 'REPLACE')
        if 'WindNormal2' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindNormal2')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindNormal2'].add([vert.index], 0, 'REPLACE')
        if 'WindExtra1' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindExtra1')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindExtra1'].add([vert.index], 0, 'REPLACE')
        if 'WindExtra2' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindExtra2')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindExtra2'].add([vert.index], 0, 'REPLACE')
        if 'WindExtra3' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindExtra3')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindExtra3'].add([vert.index], 0, 'REPLACE')
        if 'WindFlag' not in obj.vertex_groups:
            obj.vertex_groups.new(name='WindFlag')
            for vert in obj.data.vertices:
                obj.vertex_groups['WindFlag'].add([vert.index], 0, 'REPLACE')
        #Add values if missing for new unpainted vertices
        for vert in obj.data.vertices:
            if not vert.groups:
                if apply_geom_type:
                    mesh.vertex_groups["GeomType"].add([vert.index], float(geom_type), 'REPLACE')
                else:
                    mesh.vertex_groups["GeomType"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindWeight1"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindWeight2"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindNormal1"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindNormal2"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindExtra1"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindExtra2"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindExtra3"].add([vert.index], 0, 'REPLACE')
                mesh.vertex_groups["WindFlag"].add([vert.index], 0, 'REPLACE')
                
        # Deal with UV maps
        if 'DiffuseUV' not in obj.data.uv_layers:
            obj.data.uv_layers.new(name="DiffuseUV")
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    obj.data.uv_layers["DiffuseUV"].data[loop_idx].uv = (0, 0)
        if 'DetailUV' not in obj.data.uv_layers:
            obj.data.uv_layers.new(name="DetailUV")
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    obj.data.uv_layers["DetailUV"].data[loop_idx].uv = (0, 0)
        if 'SeamDiffuseUV' not in obj.data.uv_layers:
            obj.data.uv_layers.new(name="SeamDiffuseUV")
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    obj.data.uv_layers["SeamDiffuseUV"].data[loop_idx].uv = (0, 0)
        if 'SeamDetailUV' not in obj.data.uv_layers:
            obj.data.uv_layers.new(name="SeamDetailUV")
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    obj.data.uv_layers["SeamDetailUV"].data[loop_idx].uv = (0, 0)
                    
        # Deal with Vertex Colors
        if "AmbientOcclusion" not in obj.data.vertex_colors:
            obj.data.vertex_colors.new(name="AmbientOcclusion")
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    obj.data.vertex_colors["AmbientOcclusion"].data[loop_idx].color = [1,1,1,1]
        if "SeamBlending" not in obj.data.vertex_colors:
            obj.data.vertex_colors.new(name="SeamBlending")
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    obj.data.vertex_colors["SeamBlending"].data[loop_idx].color = [1,1,1,1]
                    
        # Deal with Attributes
        verts = []
        for vert in obj.data.vertices:
            verts.append(vert.co)
        verts = np.array(verts).flatten()
        if 'vertexPosition' not in obj.data.attributes:
            obj.data.attributes.new(name='vertexPosition', type='FLOAT_VECTOR', domain='POINT')
            obj.data.attributes['vertexPosition'].data.foreach_set('vector', verts)
        if 'vertexLodPosition' not in obj.data.attributes:
            obj.data.attributes.new(name='vertexLodPosition', type='FLOAT_VECTOR', domain='POINT')
            obj.data.attributes['vertexLodPosition'].data.foreach_set('vector', verts)
        if 'leafCardCorner' not in obj.data.attributes:
            obj.data.attributes.new(name='leafCardCorner', type='FLOAT_VECTOR', domain='POINT')
            empty_array = np.zeros(len(obj.data.vertices) * 3, dtype=np.float32)
            obj.data.attributes['leafCardCorner'].data.foreach_set('vector', empty_array)
        if 'leafCardLodScalar' not in obj.data.attributes:
            obj.data.attributes.new(name='leafCardLodScalar', type='FLOAT', domain='POINT')
            empty_array = np.zeros(len(obj.data.vertices), dtype=np.float32)
            obj.data.attributes['leafCardLodScalar'].data.foreach_set('value', empty_array)
        if 'leafAnchorPoint' not in obj.data.attributes:
            obj.data.attributes.new(name='leafAnchorPoint', type='FLOAT_VECTOR', domain='POINT')
            empty_array = np.zeros(len(obj.data.vertices) * 3, dtype=np.float32)
            obj.data.attributes['leafAnchorPoint'].data.foreach_set('vector', empty_array)
            
        #SpeedTree Tag
        obj.data["SpeedTreeTag"] = 1
            
        # Deal with Geometry Nodes
        if obj.modifiers:
            for mod in obj.modifiers:
                obj.modifiers.remove(mod)
        bpy.context.active_object.modifiers.new(type='NODES', name = "Leaf Card")
        geom_nodes = bpy.context.active_object.modifiers[0]
        bpy.ops.node.new_geometry_node_group_assign()
        start_geom = geom_nodes.node_group.nodes['Group Input']
        end_geom = geom_nodes.node_group.nodes['Group Output']
        node_transform = geom_nodes.node_group.nodes.new(type = 'GeometryNodeSetPosition')
        node_transform.location = (20,0)
        leaf_card_transform = geom_nodes.node_group.nodes.new(type = 'GeometryNodeInputNamedAttribute')
        leaf_card_transform.name = 'Leaf Card Corner'
        leaf_card_transform.data_type = 'FLOAT_VECTOR'
        leaf_card_transform.inputs['Name'].default_value = "leafCardCorner"
        leaf_card_transform.location = (-330, -100)
        leaf_card_lod_scalar = geom_nodes.node_group.nodes.new(type = 'GeometryNodeInputNamedAttribute')
        leaf_card_lod_scalar.name = 'Leaf Card LOD Scalar'
        leaf_card_lod_scalar.data_type = 'FLOAT_VECTOR'
        leaf_card_lod_scalar.inputs['Name'].default_value = "leafCardLodScalar"
        leaf_card_lod_scalar.location = (-330, -220)
        vector_math = geom_nodes.node_group.nodes.new(type = 'ShaderNodeVectorMath')
        vector_math.operation = 'MULTIPLY'
        vector_math.inputs[1].default_value = (1,1,1)
        vector_math.location = (-150, -100)
        geom_nodes.node_group.links.new(start_geom.outputs['Geometry'], node_transform.inputs["Geometry"])
        geom_nodes.node_group.links.new(vector_math.outputs['Vector'], node_transform.inputs["Offset"])
        geom_nodes.node_group.links.new(node_transform.outputs['Geometry'], end_geom.inputs["Geometry"])
        geom_nodes.node_group.links.new(leaf_card_transform.outputs['Attribute'], vector_math.inputs[0])
        
        # Deal with the Material
        srt_mesh_material(obj, geom_type)
    
def srt_mesh_material(obj = None, geom_type = 0, is_bb = False):
    temp_mat = bpy.data.materials.new("SRT_Material")
    temp_mat.diffuse_color = (*colorsys.hsv_to_rgb(random.random(), .7, .9), 1) #random hue more pleasing than random rgb
    temp_mat.use_nodes = True
    temp_mat.blend_method = 'CLIP'
    temp_mat.shadow_method = 'CLIP'
    temp_mat.use_backface_culling = False
    temp_mat.node_tree.nodes.remove(temp_mat.node_tree.nodes['Principled BSDF'])
    node_main = temp_mat.node_tree.nodes.new(type = 'ShaderNodeEeveeSpecular')
    node_main.inputs['Base Color'].default_value = (0,0,0,0)
    node_main.inputs['Specular'].default_value = (0,0,0,0)
    node_main.inputs['Emissive Color'].default_value = (0,0,0,0)
    node_main.inputs['Roughness'].default_value = 1
    node_main.location = (700, 300)
    temp_mat.node_tree.nodes["Material Output"].location = (3200, 300)
        
    #Diffuse
    node_uv_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
    node_uv_diff.uv_map = "DiffuseUV"
    node_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_diff.name = "Diffuse Texture"
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
    node_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
    node_normal3 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeNormalMap')
    node_normal4 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeBump')
    node_normal.name = "Normal Texture"
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
    node_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_spec.name = "Specular Texture"
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
    node_rgb_diffuseColor.location = (-200, 750)
    node_frame_diffuse_color = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
    node_rgb_diffuseColor.parent = node_frame_diffuse_color
    node_frame_diffuse_color.use_custom_color = True
    node_frame_diffuse_color.color = (0.1,0.9,0.1)
    node_frame_diffuse_color.label = "Diffuse Color"
    node_frame_diffuse_color.label_size = 28
    node_diffuseScalar = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
    node_diffuseScalar.name = 'Diffuse Scalar'
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
    node_shininess.location = (-300, -950)
    node_frame_shininess = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
    node_shininess.parent = node_frame_shininess
    node_frame_shininess.use_custom_color = True
    node_frame_shininess.color = (0.1,0.9,0.1)
    node_frame_shininess.label = "Shininess"
    node_frame_shininess.label_size = 28
    node_map_range_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
    node_map_range_shininess.inputs['From Max'].default_value = 200.0
    node_map_range_shininess.location = (-100, -950)
    node_invert_shininess = temp_mat.node_tree.nodes.new(type = 'ShaderNodeInvert')
    node_invert_shininess.name = 'Invert Shininess'
    node_invert_shininess.location = (100, -950)
    
    node_rgb_transmissionColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
    node_rgb_transmissionColor.name = 'Transmission Color'
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
    node_transmissionColor_brightness.name = 'Transmission Color Brightness'
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
    if not is_bb:
        node_map_range_alpha_scalar.inputs['To Min'].default_value = 0.38
        node_map_range_alpha_scalar.inputs['To Max'].default_value = 8
    else:
        node_map_range_alpha_scalar.inputs['To Min'].default_value = 0.37
        node_map_range_alpha_scalar.inputs['To Max'].default_value = 5
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
    node_alpha_scalar.location = (-400, 200)
    node_frame_alpha_scalar = temp_mat.node_tree.nodes.new(type = 'NodeFrame')
    node_alpha_scalar.parent = node_frame_alpha_scalar
    node_frame_alpha_scalar.use_custom_color = True
    node_frame_alpha_scalar.color = (0.1,0.9,0.1)
    node_frame_alpha_scalar.label = "Alpha Scalar"
    node_frame_alpha_scalar.label_size = 28
    
    node_rgb_ambientColor = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
    node_rgb_ambientColor.name = 'Ambient Color'
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
    
    temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_mix_specular_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_shininess.outputs["Value"], node_map_range_shininess.inputs["Value"])
    temp_mat.node_tree.links.new(node_map_range_shininess.outputs["Result"], node_invert_shininess.inputs["Color"])
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
    temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_mix_transmission_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_shadow_brightness.inputs["Color2"])
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
    temp_mat.node_tree.links.new(node_ambientContrast.outputs["Value"], node_ambientContrast_mix.inputs["Fac"])
    
    temp_mat.node_tree.links.new(node_main.outputs["BSDF"], node_shader_mix_transmission.inputs[1])
    temp_mat.node_tree.links.new(node_shader_mix_transmission_fresnel.outputs["Shader"], node_shader_mix_transmission.inputs[2])
    temp_mat.node_tree.links.new(node_shader_mix_transmission.outputs["Shader"], node_shader_mix_shadow.inputs[1])
    temp_mat.node_tree.links.new(node_shadow_shader.outputs["BSDF"], node_shader_mix_shadow.inputs[2])
    
    temp_mat.node_tree.links.new(node_light_path.outputs["Is Shadow Ray"], node_shader_mix_shadow.inputs[0])
    temp_mat.node_tree.links.new(node_shader_mix_shadow.outputs["Shader"], temp_mat.node_tree.nodes["Material Output"].inputs["Surface"])
    
    # Branch seam diffuse
    node_seam_blending = temp_mat.node_tree.nodes.new(type = 'ShaderNodeVertexColor')
    node_seam_blending.layer_name = 'SeamBlending'
    node_seam_blending_weight = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMath')
    node_seam_blending_weight.name = 'Branch Seam Weight Mult'
    node_seam_blending_weight.operation = 'MULTIPLY'
    node_seam_blending_weight.use_clamp = True
    node_seam_blending_weight_value = temp_mat.node_tree.nodes.new(type = 'ShaderNodeValue')
    node_seam_blending_weight_value.name = 'Branch Seam Weight'
    node_seam_blending_weight_value.outputs['Value'].default_value = 1
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
    temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_diff.inputs["Vector"])
    node_mix_diff = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_diff.name = 'Mix Diffuse Seam Blending'
    node_mix_diff.inputs['Fac'].default_value = 1
    node_mix_diff_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_diff_alpha.name = 'Mix Diffuse Alpha Seam Blending'
    node_mix_diff_alpha.inputs['Fac'].default_value = 1
    temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_diff.outputs["Color"], node_mix_diff.inputs["Color1"])
    temp_mat.node_tree.links.new(node_diff.outputs["Alpha"], node_mix_diff_alpha.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_diff.outputs["Alpha"], node_mix_diff_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_seam_blending.outputs["Color"], node_seam_blending_weight.inputs[0])
    temp_mat.node_tree.links.new(node_seam_blending_weight_value.outputs["Value"], node_seam_blending_weight.inputs[1])
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
    node_seam_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_seam_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
    node_seam_normal.name = "Branch Seam Normal Texture"
    node_seam_normal2.mapping.curves[1].points[0].location = (0,1)
    node_seam_normal2.mapping.curves[1].points[1].location = (1,0)
    temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_normal.inputs["Vector"])
    temp_mat.node_tree.links.new(node_seam_normal.outputs["Color"], node_seam_normal2.inputs["Color"])
    node_mix_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_normal.name = 'Mix Normal Seam Blending'
    node_mix_normal.inputs['Fac'].default_value = 1
    node_mix_normal_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_normal_alpha.name = 'Mix Normal Alpha Seam Blending'
    node_mix_normal_alpha.inputs['Fac'].default_value = 1
    temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_normal.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_normal2.outputs["Color"], node_mix_normal.inputs["Color1"])
    temp_mat.node_tree.links.new(node_normal.outputs["Alpha"], node_mix_normal_alpha.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_normal.outputs["Alpha"], node_mix_normal_alpha.inputs["Color1"])
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
    node_seam_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_seam_spec.name = "Branch Seam Specular Texture"
    temp_mat.node_tree.links.new(node_uv_seam_diff.outputs["UV"], node_seam_spec.inputs["Vector"])
    node_mix_spec = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_spec.name = 'Mix Specular Seam Blending'
    node_mix_spec.inputs['Fac'].default_value = 1
    node_mix_spec_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_spec_alpha.name = 'Mix Specular Alpha Seam Blending'
    node_mix_spec_alpha.inputs['Fac'].default_value = 1
    temp_mat.node_tree.links.new(node_spec.outputs["Color"], node_mix_spec.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_spec.outputs["Color"], node_mix_spec.inputs["Color1"])
    temp_mat.node_tree.links.new(node_spec.outputs["Alpha"], node_mix_spec_alpha.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_spec.outputs["Alpha"], node_mix_spec_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_spec.inputs["Fac"])
    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_spec_alpha.inputs["Fac"])
    temp_mat.node_tree.links.new(node_mix_spec_alpha.outputs["Color"], node_mix_transmission_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_mix_spec.outputs["Color"], node_mix_specular_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_mix_spec_alpha.outputs["Color"], node_shadow_brightness.inputs["Color2"])
    node_seam_spec.location = (-1000, -1500)
    node_mix_spec.location = (-700, -1500)
    node_mix_spec_alpha.location = (-700, -1800)
    
    node_seam_spec.parent = node_frame_specular_texture
        
    # Detail
    node_uv_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
    node_uv_det.uv_map = "DetailUV"
    node_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_det.name = "Detail Texture"
    temp_mat.node_tree.links.new(node_uv_det.outputs["UV"], node_det.inputs["Vector"])
    node_mix_diff_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_diff_det.name = 'Mix Detail Diffuse'
    node_mix_diff_det.inputs['Fac'].default_value = 0
    temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff_det.inputs["Color1"])
    temp_mat.node_tree.links.new(node_det.outputs["Color"], node_mix_diff_det.inputs["Color2"])
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
    node_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_det_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
    node_det_normal.name = "Detail Normal Texture"
    node_det_normal2.mapping.curves[1].points[0].location = (0,1)
    node_det_normal2.mapping.curves[1].points[1].location = (1,0)
    temp_mat.node_tree.links.new(node_uv_det.outputs["UV"], node_det_normal.inputs["Vector"])
    temp_mat.node_tree.links.new(node_det_normal.outputs["Color"], node_det_normal2.inputs["Color"])
    node_mix_diff_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_diff_det_normal.name = 'Mix Detail Normal'
    node_mix_diff_det_normal.inputs['Fac'].default_value = 0
    temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_diff_det_normal.inputs["Color1"])
    temp_mat.node_tree.links.new(node_det_normal2.outputs["Color"], node_mix_diff_det_normal.inputs["Color2"])
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
    node_uv_seam_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeUVMap')
    node_uv_seam_det.uv_map = "SeamDetailUV"
    node_seam_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_seam_det.name = "Branch Seam Detail Texture"
    temp_mat.node_tree.links.new(node_uv_seam_det.outputs["UV"], node_seam_det.inputs["Vector"])
    node_mix_det = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_det.name = 'Mix Detail Seam Blending'
    node_mix_det.inputs['Fac'].default_value = 1
    node_mix_det_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_det_alpha.name = 'Mix Detail Alpha Seam Blending'
    node_mix_det_alpha.inputs['Fac'].default_value = 1
    temp_mat.node_tree.links.new(node_det.outputs["Color"], node_mix_det.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_det.outputs["Color"], node_mix_det.inputs["Color1"])
    temp_mat.node_tree.links.new(node_det.outputs["Alpha"], node_mix_det_alpha.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_det.outputs["Alpha"], node_mix_det_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det.inputs["Fac"])
    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det_alpha.inputs["Fac"])
    temp_mat.node_tree.links.new(node_diff.outputs["Color"], node_mix_diff.inputs["Color2"])
    temp_mat.node_tree.links.new(node_mix_diff.outputs["Color"], node_mix_diff_det.inputs["Color1"])
    temp_mat.node_tree.links.new(node_mix_det.outputs["Color"], node_mix_diff_det.inputs["Color2"])
    temp_mat.node_tree.links.new(node_mix_det_alpha.outputs["Color"], node_mix_diff_det.inputs["Fac"])
    node_seam_det.location = (-1000, 600)
    node_uv_seam_det.location = (-2000, 800)
    node_mix_det.location = (-700, 600)
    node_mix_det_alpha.location = (-700, 340)
    
    node_seam_det.parent = node_frame_detail_texture
        
    # Branch seam detail normal
    node_seam_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
    node_seam_det_normal2 = temp_mat.node_tree.nodes.new(type = 'ShaderNodeRGBCurve')
    node_seam_det_normal.name = "Branch Seam Detail Normal Texture"
    node_seam_det_normal2.mapping.curves[1].points[0].location = (0,1)
    node_seam_det_normal2.mapping.curves[1].points[1].location = (1,0)
    temp_mat.node_tree.links.new(node_uv_seam_det.outputs["UV"], node_seam_det_normal.inputs["Vector"])
    temp_mat.node_tree.links.new(node_seam_det_normal.outputs["Color"], node_seam_det_normal2.inputs["Color"])
    node_mix_det_normal = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_det_normal.name = 'Mix Detail Normal Seam Blending'
    node_mix_det_normal.inputs['Fac'].default_value = 1
    node_mix_det_normal_alpha = temp_mat.node_tree.nodes.new(type = 'ShaderNodeMixRGB')
    node_mix_det_normal_alpha.name = 'Mix Detail Normal Alpha Seam Blending'
    node_mix_det_normal_alpha.inputs['Fac'].default_value = 1
    temp_mat.node_tree.links.new(node_det_normal2.outputs["Color"], node_mix_det_normal.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_det_normal2.outputs["Color"], node_mix_det_normal.inputs["Color1"])
    temp_mat.node_tree.links.new(node_det_normal.outputs["Alpha"], node_mix_det_normal_alpha.inputs["Color2"])
    temp_mat.node_tree.links.new(node_seam_det_normal.outputs["Alpha"], node_mix_det_normal_alpha.inputs["Color1"])
    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det_normal.inputs["Fac"])
    temp_mat.node_tree.links.new(node_seam_blending_weight.outputs["Value"], node_mix_det_normal_alpha.inputs["Fac"])
    temp_mat.node_tree.links.new(node_normal2.outputs["Color"], node_mix_normal.inputs["Color2"])
    temp_mat.node_tree.links.new(node_mix_normal.outputs["Color"], node_mix_diff_det_normal.inputs["Color1"])
    temp_mat.node_tree.links.new(node_mix_det_normal.outputs["Color"], node_mix_diff_det_normal.inputs["Color2"])
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
    temp_mat.node_tree.links.new(node_ambient_occlusion.outputs["Color"], node_main.inputs["Ambient Occlusion"])
    
    # Custom properties to support all speedtree material specific variables, import and export
    if float(geom_type) == 0.2:
        temp_mat["BBranchesPresent"] = 1
    elif float(geom_type) == 0.4:
        temp_mat["BFrondsPresent"] = 1
    elif float(geom_type) == 0.6:
        temp_mat["BLeavesPresent"] = 1
    elif float(geom_type) == 0.8:
        temp_mat["BFacingLeavesPresent"] = 1
    elif float(geom_type) == 1.0:
        temp_mat["BRigidMeshesPresent"] = 1
        
    if "EAmbientContrast" not in temp_mat:
        temp_mat["EAmbientContrast"] = "EFFECT_OFF"
    if "EDetailLayer" not in temp_mat:
        temp_mat["EDetailLayer"] = "EFFECT_OFF"
    if "ESpecular" not in temp_mat:
        temp_mat["ESpecular"] = "EFFECT_OFF"
    if "ETransmission" not in temp_mat:
        temp_mat["ETransmission"] = "EFFECT_OFF"
    if "EBranchSeamSmoothing" not in temp_mat:
        temp_mat["EBranchSeamSmoothing"] = "EFFECT_OFF"
    if "EFaceCulling" not in temp_mat:
        temp_mat["EFaceCulling"] = "CULLTYPE_NONE"
    if "BBlending" not in temp_mat:
        temp_mat["BBlending"] = 0
    if "EAmbientImageLighting" not in temp_mat:
        temp_mat["EAmbientImageLighting"] = "EFFECT_OFF"
    if "EHueVariation" not in temp_mat:
        temp_mat["EHueVariation"] = "EFFECT_OFF"
    if "EFogCurve" not in temp_mat:
        temp_mat["EFogCurve"] = "FOG_CURVE_NONE"
    if "EFogColorStyle" not in temp_mat:
        temp_mat["EFogColorStyle"] = "FOG_COLOR_TYPE_CONSTANT"
    if "BReceivesShadows" not in temp_mat:
        temp_mat["BReceivesShadows"] = 0
    if "BShadowSmoothing" not in temp_mat:
        temp_mat["BShadowSmoothing"] = 0
    if "EWindLod" not in temp_mat:
        temp_mat["EWindLod"] = "WIND_LOD_NONE"
    if "BBranchesPresent" not in temp_mat:
        temp_mat["BBranchesPresent"] = 0
    if "BFrondsPresent" not in temp_mat:
        temp_mat["BFrondsPresent"] = 0
    if "BLeavesPresent" not in temp_mat:
        temp_mat["BLeavesPresent"] = 0
    if "BFacingLeavesPresent" not in temp_mat:
        temp_mat["BFacingLeavesPresent"] = 0
    if "BRigidMeshesPresent" not in temp_mat:
        temp_mat["BRigidMeshesPresent"] = 0
    
    if obj:
        obj.data.materials.append(temp_mat)
        # Get old material's params, if any
        if obj.data.materials[0] != temp_mat:
            old_mat = obj.data.materials[0]
            if "Diffuse Texture" in old_mat.node_tree.nodes:
                if old_mat.node_tree.nodes["Diffuse Texture"].image:
                    temp_mat.node_tree.nodes["Diffuse Texture"].image = old_mat.node_tree.nodes["Diffuse Texture"].image
                    temp_mat.node_tree.nodes["Branch Seam Diffuse Texture"].image = old_mat.node_tree.nodes["Diffuse Texture"].image
            if "Normal Texture" in old_mat.node_tree.nodes:
                if old_mat.node_tree.nodes["Normal Texture"].image:
                    temp_mat.node_tree.nodes["Normal Texture"].image = old_mat.node_tree.nodes["Normal Texture"].image
                    temp_mat.node_tree.nodes["Branch Seam Normal Texture"].image = old_mat.node_tree.nodes["Normal Texture"].image
            if "Detail Texture" in old_mat.node_tree.nodes:
                if old_mat.node_tree.nodes["Detail Texture"].image:
                    temp_mat.node_tree.nodes["Detail Texture"].image = old_mat.node_tree.nodes["Detail Texture"].image
                    temp_mat.node_tree.nodes["Branch Seam Detail Texture"].image = old_mat.node_tree.nodes["Detail Texture"].image
            if "Detail Normal Texture" in old_mat.node_tree.nodes:
                if old_mat.node_tree.nodes["Detail Normal Texture"].image:
                    temp_mat.node_tree.nodes["Detail Normal Texture"].image = old_mat.node_tree.nodes["Detail Normal Texture"].image
                    temp_mat.node_tree.nodes["Branch Seam Detail Normal Texture"].image = old_mat.node_tree.nodes["Detail Normal Texture"].image
            if "Specular Texture" in old_mat.node_tree.nodes:
                if old_mat.node_tree.nodes["Specular Texture"].image:
                    temp_mat.node_tree.nodes["Specular Texture"].image = old_mat.node_tree.nodes["Specular Texture"].image
                    temp_mat.node_tree.nodes["Branch Seam Specular Texture"].image = old_mat.node_tree.nodes["Specular Texture"].image
            if "Ambient Color" in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes["Ambient Color"].outputs['Color'].default_value = old_mat.node_tree.nodes["Ambient Color"].outputs['Color'].default_value
            if 'Ambient Contrast Factor' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Ambient Contrast Factor'].outputs['Value'].default_value = old_mat.node_tree.nodes['Ambient Contrast Factor'].outputs['Value'].default_value
            if 'Diffuse Color' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Diffuse Color'].outputs['Color'].default_value = old_mat.node_tree.nodes['Diffuse Color'].outputs['Color'].default_value
            if 'Diffuse Scalar' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Diffuse Scalar'].outputs['Value'].default_value = old_mat.node_tree.nodes['Diffuse Scalar'].outputs['Value'].default_value
            if 'Shininess' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Shininess'].outputs['Value'].default_value = old_mat.node_tree.nodes['Shininess'].outputs['Value'].default_value
            if 'Specular Color' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Specular Color'].outputs['Color'].default_value = old_mat.node_tree.nodes['Specular Color'].outputs['Color'].default_value
            if 'Transmission Color' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Transmission Color'].outputs['Color'].default_value = old_mat.node_tree.nodes['Transmission Color'].outputs['Color'].default_value
            if 'Transmission Shadow Brightness' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Transmission Shadow Brightness'].outputs['Value'].default_value = old_mat.node_tree.nodes['Transmission Shadow Brightness'].outputs['Value'].default_value
            if 'Transmission View Dependency' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Transmission View Dependency'].outputs['Value'].default_value = old_mat.node_tree.nodes['Transmission View Dependency'].outputs['Value'].default_value
            if 'Branch Seam Weight' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Branch Seam Weight'].outputs['Value'].default_value = old_mat.node_tree.nodes['Branch Seam Weight'].outputs['Value'].default_value
            if 'Alpha Scalar' in old_mat.node_tree.nodes:
                temp_mat.node_tree.nodes['Alpha Scalar'].outputs['Value'].default_value = old_mat.node_tree.nodes['Alpha Scalar'].outputs['Value'].default_value
            temp_mat.use_backface_culling = old_mat.use_backface_culling
            temp_mat.blend_method = old_mat.blend_method
            temp_mat.shadow_method = old_mat.shadow_method
            if 'Specular' in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes['Specular'].inputs["Ambient Occlusion"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes['Specular'].inputs["Ambient Occlusion"].links[0])
                if not old_mat.node_tree.nodes['Specular'].inputs['Roughness'].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes['Specular'].inputs['Roughness'].links[0])
            if 'Ambient Contrast' in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes['Ambient Contrast'].inputs["Fac"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes['Ambient Contrast'].inputs["Fac"].links[0])
            if 'Mix Detail Diffuse' in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes['Mix Detail Diffuse'].inputs["Fac"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes['Mix Detail Diffuse'].inputs["Fac"].links[0])
            if 'Mix Detail Normal' in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes['Mix Detail Normal'].inputs["Fac"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes['Mix Detail Normal'].inputs["Fac"].links[0])
            if "Mix Specular Color" in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes["Mix Specular Color"].inputs['Color2'].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes["Mix Specular Color"].inputs["Color2"].links[0])
            if "Mix Transmission Alpha" in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes["Mix Transmission Alpha"].inputs["Color2"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes["Mix Transmission Alpha"].inputs["Color2"].links[0])
            if "Mix Shader Fresnel" in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes["Mix Shader Fresnel"].inputs["Fac"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes["Mix Shader Fresnel"].inputs["Fac"].links[0])
            if "Mix Shadow Brightness" in old_mat.node_tree.nodes:
                if not old_mat.node_tree.nodes["Mix Shadow Brightness"].inputs["Fac"].links:
                    temp_mat.node_tree.links.remove(temp_mat.node_tree.nodes["Mix Shadow Brightness"].inputs["Fac"].links[0])
            if 'Branch Seam Weight Mult' in old_mat.node_tree.nodes:
                if len(old_mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'].links) != 10:
                    for link in temp_mat.node_tree.nodes['Branch Seam Weight Mult'].outputs['Value'].links:
                        temp_mat.node_tree.links.remove(link)
                        
            while obj.data.materials[0] != temp_mat:
                obj.data.materials.pop(index = 0)