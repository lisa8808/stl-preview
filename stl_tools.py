#!/usr/bin/env python3
"""
STL Mesh Processing Tool using trimesh
Provides: simplify, smooth, hole punching, boolean operations
"""

import sys
import json
import trimesh
import numpy as np

def load_stl(filepath):
    """Load STL file"""
    try:
        mesh = trimesh.load_mesh(filepath)
        return mesh
    except Exception as e:
        return None, str(e)

def simplify_mesh(mesh, ratio=0.5):
    """Simplify mesh by reducing vertices"""
    # ratio: 0.0-1.0, percentage of original to keep
    ratio = max(0.1, min(1.0, ratio))
    
    # Use trimesh's built-in simplification
    try:
        simplified = mesh.copy()
        # Simple decimation
        target_faces = int(len(mesh.faces) * ratio)
        simplified.merge_vertices()
        simplified.remove_degenerate_faces()
        
        # If ratio is very low, use more aggressive simplification
        if ratio < 0.5:
            # Voxel-based simplification
            voxel_size = mesh.bounding_box.extents.max() * (1 - ratio) * 0.1
            voxelized = mesh.voxelized(voxel_size)
            simplified = voxelized.marching_cubes
        else:
            # Vertex clustering
            pitch = mesh.bounding_box.extents.max() * (1 - ratio) * 0.2
            simplified = mesh.split().merged(pitch)
        
        return simplified
    except Exception as e:
        return mesh, str(e)

def smooth_mesh(mesh, iterations=5):
    """Laplacian smoothing"""
    try:
        # Simple Laplacian smoothing
        smoothed = mesh.copy()
        vertices = smoothed.vertices.copy()
        
        for _ in range(iterations):
            new_vertices = vertices.copy()
            for i, vertex in enumerate(mesh.vertices):
                neighbors = smoothed.vertex_neighbors[i]
                if len(neighbors) > 0:
                    neighbor_coords = vertices[neighbors]
                    new_vertices[i] = vertex * 0.5 + neighbor_coords.mean(axis=0) * 0.5
            vertices = new_vertices
        
        smoothed.vertices = vertices
        return smoothed
    except Exception as e:
        return mesh, str(e)

def punch_hole(mesh, radius=5, axis='z'):
    """Punch a hole through the mesh along an axis"""
    try:
        # Get mesh bounds
        bounds = mesh.bounding_box.bounds
        
        # Center of the mesh
        center = mesh.centroid
        
        # Create a cylinder for boolean difference
        if axis == 'z':
            height = bounds[1][2] - bounds[0][2] + 10
            transform = trimesh.transformations.translation_matrix(
                [center[0], center[1], bounds[0][2] - 5]
            )
        elif axis == 'x':
            height = bounds[1][0] - bounds[0][0] + 10
            transform = trimesh.transformations.translation_matrix(
                [bounds[0][0] - 5, center[1], center[2]]
            )
        else:  # y
            height = bounds[1][1] - bounds[0][1] + 10
            transform = trimesh.transformations.translation_matrix(
                [center[0], bounds[0][1] - 5, center[2]]
            )
        
        # Create cylinder
        cylinder = trimesh.creation.cylinder(radius=radius, height=height, transform=transform)
        
        # Boolean difference
        result = mesh.difference(cylinder)
        
        return result if result is not None else mesh
    except Exception as e:
        # Try alternative approach
        try:
            # Just scale down center vertices
            result = mesh.copy()
            center = mesh.centroid
            hole_radius = radius * 3
            
            for i, vertex in enumerate(result.vertices):
                dist = np.sqrt(
                    (vertex[0] - center[0])**2 + 
                    (vertex[1] - center[1])**2 + 
                    (vertex[2] - center[2])**2
                )
                if dist < hole_radius:
                    # Scale down
                    scale = 0.1
                    result.vertices[i] = center + (vertex - center) * scale
            
            result.remove_degenerate_faces()
            result.merge_vertices()
            return result
        except Exception as e2:
            return mesh, str(e2)

def punch_box_hole(mesh, size=10, axis='z'):
    """Punch a rectangular hole through the mesh"""
    try:
        bounds = mesh.bounding_box.bounds
        center = mesh.centroid
        
        # Create a box
        if axis == 'z':
            box_size = [size, size, bounds[1][2] - bounds[0][2] + 10]
            transform = trimesh.transformations.translation_matrix(
                [center[0] - size/2, center[1] - size/2, center[2] - 5]
            )
        elif axis == 'x':
            box_size = [bounds[1][0] - bounds[0][0] + 10, size, size]
            transform = trimesh.transformations.translation_matrix(
                [center[0] - 5, center[1] - size/2, center[2] - size/2]
            )
        else:
            box_size = [size, bounds[1][1] - bounds[0][1] + 10, size]
            transform = trimesh.transformations.translation_matrix(
                [center[0] - size/2, center[1] - 5, center[2] - size/2]
            )
        
        box = trimesh.creation.box(extents=box_size, transform=transform)
        
        result = mesh.difference(box)
        return result if result is not None else mesh
    except Exception as e:
        return mesh, str(e)

def punch_sphere_hole(mesh, radius=10):
    """Punch a spherical hole through the mesh"""
    try:
        center = mesh.centroid
        transform = trimesh.transformations.translation_matrix(center)
        
        # Create sphere
        sphere = trimesh.creation.icosphere(radius=radius, subdivisions=2)
        sphere.apply_transform(trimesh.transformations.translation_matrix(center))
        
        # Boolean difference
        result = mesh.difference(sphere)
        return result if result is not None else mesh
    except Exception as e:
        return mesh, str(e)

def scale_mesh(mesh, factor):
    """Scale mesh by a factor"""
    try:
        scaled = mesh.copy()
        scaled.apply_scale(factor)
        return scaled
    except Exception as e:
        return mesh, str(e)

def rotate_mesh(mesh, angle, axis='z'):
    """Rotate mesh by angle (degrees) around axis"""
    try:
        rotated = mesh.copy()
        angle_rad = np.radians(angle)
        if axis == 'z':
            matrix = trimesh.transformations.rotation_matrix(angle_rad, [0, 0, 1])
        elif axis == 'x':
            matrix = trimesh.transformations.rotation_matrix(angle_rad, [1, 0, 0])
        else:
            matrix = trimesh.transformations.rotation_matrix(angle_rad, [0, 1, 0])
        
        rotated.apply_transform(matrix)
        return rotated
    except Exception as e:
        return mesh, str(e)

def get_mesh_info(mesh):
    """Get mesh information"""
    return {
        'vertices': len(mesh.vertices),
        'faces': len(mesh.faces),
        'bounds': mesh.bounding_box.bounds.tolist(),
        'centroid': mesh.centroid.tolist(),
        'volume': mesh.volume if hasattr(mesh, 'volume') and mesh.volume is not None else 0,
        'is_watertight': mesh.is_watertight if hasattr(mesh, 'is_watertight') else None
    }

def process_command(input_file, output_file, command):
    """Process STL file based on command"""
    # Load mesh
    mesh, error = load_stl(input_file)
    if error:
        return {'success': False, 'error': error}
    
    original_info = get_mesh_info(mesh)
    
    # Parse and execute command
    cmd_lower = command.lower().strip()
    
    # Hole commands
    if '洞' in cmd_lower or 'hole' in cmd_lower or 'punch' in cmd_lower:
        if '方' in cmd_lower or 'box' in cmd_lower:
            # Extract size if present
            size_match = [s for s in cmd_lower if s.isdigit()]
            size = int(size_match[0]) if size_match else 10
            mesh = punch_box_hole(mesh, size=size)
        elif '球' in cmd_lower or 'sphere' in cmd_lower:
            size_match = [s for s in cmd_lower if s.isdigit()]
            radius = int(size_match[0]) if size_match else 10
            mesh = punch_sphere_hole(mesh, radius=radius)
        else:
            # Round hole
            size_match = [s for s in cmd_lower if s.isdigit()]
            radius = int(size_match[0]) if size_match else 5
            mesh = punch_hole(mesh, radius=radius)
    
    # Scale commands
    elif '%' in cmd_lower:
        # e.g., "20%", "200%"
        import re
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', cmd_lower)
        if match:
            ratio = float(match.group(1)) / 100
            mesh = scale_mesh(mesh, ratio)
    
    elif '倍' in cmd_lower:
        match = re.search(r'(\d+(?:\.\d+)?)\s*倍', cmd_lower)
        if match:
            factor = float(match.group(1))
            mesh = scale_mesh(mesh, factor)
    
    elif '放大' in cmd_lower or 'scale' in cmd_lower or 'bigger' in cmd_lower or 'larger' in cmd_lower:
        match = re.search(r'(\d+(?:\.\d+)?)', cmd_lower)
        if match:
            factor = float(match.group(1))
            if factor < 10:  # Likely a multiplier like 2x
                mesh = scale_mesh(mesh, factor)
            else:  # Likely a percentage like 200%
                mesh = scale_mesh(mesh, factor / 100)
    
    elif '缩小' in cmd_lower or '缩小' in cmd_lower or '缩小' in cmd_lower or 'smaller' in cmd_lower or 'shrink' in cmd_lower:
        match = re.search(r'(\d+(?:\.\d+)?)', cmd_lower)
        if match:
            ratio = float(match.group(1)) / 100
            mesh = scale_mesh(mesh, ratio)
    
    # Rotate commands
    elif '旋转' in cmd_lower or 'rotate' in cmd_lower:
        match = re.search(r'(\d+(?:\.\d+)?)', cmd_lower)
        if match:
            angle = float(match.group(1))
            if 'y轴' in cmd_lower or 'y轴' in cmd_lower or 'y axis' in cmd_lower:
                mesh = rotate_mesh(mesh, angle, 'y')
            elif 'x轴' in cmd_lower or 'x轴' in cmd_lower or 'x axis' in cmd_lower:
                mesh = rotate_mesh(mesh, angle, 'x')
            elif 'z轴' in cmd_lower or 'z轴' in cmd_lower or 'z axis' in cmd_lower:
                mesh = rotate_mesh(mesh, angle, 'z')
            else:
                mesh = rotate_mesh(mesh, angle, 'z')
    
    # Simplify commands
    elif '简化' in cmd_lower or 'simplif' in cmd_lower or 'reduce' in cmd_lower:
        # Try to extract ratio
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', cmd_lower)
        if match:
            ratio = float(match.group(1)) / 100
        else:
            ratio = 0.5  # Default 50%
        mesh = simplify_mesh(mesh, ratio)
    
    # Smooth commands
    elif '平滑' in cmd_lower or 'smooth' in cmd_lower or '光滑' in cmd_lower:
        mesh = smooth_mesh(mesh, iterations=3)
    
    # Try to repair if needed
    try:
        mesh.remove_degenerate_faces()
        mesh.merge_vertices()
    except:
        pass
    
    # Get result info
    result_info = get_mesh_info(mesh)
    
    # Save result
    try:
        mesh.export(output_file)
        return {
            'success': True,
            'original': original_info,
            'result': result_info,
            'output': output_file
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(json.dumps({'error': 'Usage: stl_tools.py <input.stl> <output.stl> <command>'}))
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    command = sys.argv[3]
    
    result = process_command(input_file, output_file, command)
    print(json.dumps(result, indent=2))