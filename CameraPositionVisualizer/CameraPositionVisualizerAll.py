import argparse
import os
import copy
import io
import sys
from pathlib import Path

import json
import numpy as np
import open3d as o3d


def visualize_transforms(camera_array):
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(window_name='Showing camera transforms', width=800, height=800)
    coordinates = o3d.geometry.TriangleMesh.create_coordinate_frame(size=500, origin=[0, 0, 0])
    vis.add_geometry(coordinates)

    # TODO Add cylinder and rotate per cylindercrop file!

    for camera_model, transform_mat in camera_array:
        # print(transform_mat)
        model_copy = copy.deepcopy(camera_model)
        model_copy.transform(transform_mat)
        vis.add_geometry(model_copy)

    vis.run()
    vis.destroy_window()


def read_transform_file(file_name: str) -> np.array:
    with io.open(file_name, "rt") as f:
        all_lines = f.readlines()

        floats_array = []

        for line in all_lines:
            float_strings = line.split(' ')

            for item in float_strings:
                floats_array.append(float(item.strip()))

        np_floats = np.array(floats_array)
        new_transform = np_floats.reshape((4, 4))
        return new_transform

def read_json_file(file_name: str) -> np.array:
    with io.open(file_name) as f:
        data = json.load(f)

        new_transform =  np.array(data["color"]["rotation"])
        translation = np.array(data["color"]["translation"])
        new_transform[0,3] = translation[0]
        new_transform[1,3] = translation[1]
        new_transform[2,3] = translation[2]
        return new_transform

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f'Visualize camera transform matrices in space')
    parser.add_argument('--transforms',
                        default="./StudioExport", help='input camera transforms within a folder tree')
    parser.add_argument('--cameraModel',
                        default="./vidcam.obj", help='MV camera model')
    args = parser.parse_args()

    if not Path(args.cameraModel).exists():
        raise ValueError('Missing input camera model')

    camera_model_ir = o3d.io.read_triangle_mesh(args.cameraModel)
    camera_model_ir.paint_uniform_color([1, 0, 0])
    camera_model_ir.scale(scale=100, center=camera_model_ir.get_center())

    camera_model_clr = o3d.io.read_triangle_mesh(args.cameraModel)
    camera_model_clr.paint_uniform_color([0, 1, 0])
    camera_model_clr.scale(scale=100, center=camera_model_clr.get_center())

    if not Path(args.transforms).exists():
        raise ValueError('Missing input transforms folders')

    camera_array = []

    for root, dirs, files in os.walk(args.transforms):
        for item in dirs:
            try:
                stream_id = int(item)
                txt_file_path = Path(root, item, 'transform.txt')
                json_file_path = Path(root, item, 'CameraParams_Primary.json')
                if txt_file_path.exists() and json_file_path.exists():
                    print('Adding ' + str(txt_file_path))
                    transform_mat_ir = read_transform_file(txt_file_path)
                    camera_array.append((camera_model_ir, transform_mat_ir))

                    print('Adding ' + str(json_file_path))
                    transform_mat_clr = read_json_file(json_file_path)
                    camera_array.append((camera_model_clr, transform_mat_ir @ transform_mat_clr))

            except Exception:
                pass
        break  # Walk only one sub-folder level deep

    visualize_transforms(camera_array)
