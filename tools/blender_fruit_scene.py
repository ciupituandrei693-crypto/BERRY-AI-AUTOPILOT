"""Run inside Blender: blender -b --python blender_fruit_scene.py -- --config FILE.

Procedural original fruit characters with a named armature and animated mouth
shape keys. No external assets, no downloads, no cloud access.
"""
import argparse
import json
import math
import sys
from pathlib import Path


def arguments():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    return parser.parse_args(argv)


def main():
    import bpy
    from mathutils import Vector

    config = json.loads(Path(arguments().config).read_text(encoding='utf-8'))
    channel = config['channel']
    if channel not in ('mind', 'wealth', 'beats', 'lab', 'heart'):
        raise ValueError('Unknown channel')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if bpy.app.version >= (4, 2, 0) else 'BLENDER_EEVEE'
    scene.render.resolution_x = int(config['width'])
    scene.render.resolution_y = round(int(config['width']) * 16 / 9)
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.fps = int(config['fps'])
    scene.frame_start = 1
    scene.frame_end = max(2, round(float(config['duration']) * scene.render.fps))
    scene.render.filepath = config['output']
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = 'AgX' if bpy.app.version >= (4, 0, 0) else 'Filmic'

    def material(name, color, metallic=0, roughness=.4):
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        return mat

    palette = {
        'mind': (.23, .065, .43), 'wealth': (.95, .70, .07),
        'beats': (.10, .19, .77), 'lab': (.07, .30, .80), 'heart': (.25, .77, .28),
    }
    skin = material('Original fruit skin', palette[channel], .06, .28)
    dark = material('Eyes and mouth', (.009, .012, .024), 0, .25)
    white = material('Eye whites', (.96, .95, .88), 0, .16)
    blush = material('Cheeks', (.88, .17, .24), 0, .42)
    leaf = material('Leaf green', (.08, .45, .13), 0, .36)
    stem = material('Stem', (.28, .13, .04), 0, .8)
    gold = material('Studio gold', (.93, .55, .10), .65, .2)
    backdrop = material('Studio midnight', (.012, .022, .07), .1, .6)

    def sphere(name, loc, scale, mat, seg=32, rings=20):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            poly.use_smooth = True
        return obj

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    rig = bpy.context.object
    rig.name = 'BERRY_FRUIT_RIG'
    rig.show_in_front = True
    bones = rig.data.edit_bones
    bones.remove(bones[0])
    positions = {
        'Root': ((0, 0, .1), (0, 0, .65), None),
        'Body': ((0, 0, .65), (0, 0, 2.25), 'Root'),
        'Head': ((0, 0, 2.1), (0, 0, 2.85), 'Body'),
        'Arm.L': ((-.82, 0, 1.95), (-1.55, 0, 1.3), 'Body'),
        'Arm.R': ((.82, 0, 1.95), (1.55, 0, 1.3), 'Body'),
        'Leg.L': ((-.43, 0, .88), (-.48, 0, .18), 'Root'),
        'Leg.R': ((.43, 0, .88), (.48, 0, .18), 'Root'),
    }
    for name, (head, tail, parent) in positions.items():
        b = bones.new(name)
        b.head, b.tail = head, tail
        if parent:
            b.parent = bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')

    def armature_skin(obj, bone):
        vg = obj.vertex_groups.new(name=bone)
        vg.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
        mod = obj.modifiers.new('BERRY Armature Skin', 'ARMATURE')
        mod.object = rig
        obj.parent = rig
        return obj

    def bind_bone(obj, bone):
        matrix = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = bone
        obj.matrix_world = matrix
        return obj

    # Head/body deform by named armature vertex groups. Banana uses elongated stylized form.
    proportions = (1.0, .85, 1.05) if channel != 'wealth' else (.75, .65, 1.35)
    body = sphere('Fruit body SKINNED', (0, 0, 1.86), proportions, skin)
    armature_skin(body, 'Body')
    if channel == 'mind':
        for i, (x, z) in enumerate([(-.62, 2.35), (.62, 2.35), (0, 2.62), (-.72, 1.72), (.72, 1.72)]):
            bind_bone(sphere('Grape berry %02d' % i, (x, -.08, z), (.42, .38, .42), skin), 'Body')
    if channel == 'heart':
        bind_bone(sphere('Cherry companion', (.86, .24, 1.35), (.45, .44, .48), blush), 'Body')
    bind_bone(sphere('Leaf', (.30, .0, 3.0), (.45, .19, .09), leaf), 'Head')
    bind_bone(sphere('Stem', (0, 0, 2.96), (.10, .10, .32), stem), 'Head')
    for side in (-1, 1):
        arm = sphere('Arm ' + str(side), (side * 1.12, -.06, 1.55), (.16, .18, .52), skin)
        arm.rotation_euler[1] = side * -.62
        bind_bone(arm, 'Arm.L' if side < 0 else 'Arm.R')
        bind_bone(sphere('Hand ' + str(side), (side * 1.47, -.12, 1.25), (.21, .19, .20), skin), 'Arm.L' if side < 0 else 'Arm.R')
        bind_bone(sphere('Foot ' + str(side), (side * .48, -.17, .18), (.28, .40, .18), dark), 'Leg.L' if side < 0 else 'Leg.R')
        bind_bone(sphere('Eye white ' + str(side), (side * .34, -.76, 2.30), (.23, .13, .27), white), 'Head')
        bind_bone(sphere('Pupil ' + str(side), (side * .34, -.88, 2.31), (.12, .08, .18), dark), 'Head')
    bind_bone(sphere('Nose', (0, -.90, 2.03), (.07, .07, .06), blush), 'Head')
    mouth = sphere('MOUTH_SHAPE_KEYS', (0, -.86, 1.73), (.32, .10, .17), dark)
    bind_bone(mouth, 'Head')
    basis = mouth.shape_key_add(name='Basis')
    base = [v.co.copy() for v in basis.data]
    visemes = {
        'A': (1.00, .50), 'B': (.83, .32), 'C': (.83, 1.12),
        'D': (.74, 1.80), 'E': (1.26, .55), 'F': (.75, .62),
        'G': (.67, 1.35), 'H': (1.20, .35), 'X': (.95, .12),
    }
    for name, (wide, open_) in visemes.items():
        key = mouth.shape_key_add(name=name)
        for i, v in enumerate(base):
            key.data[i].co = (v.x * wide, v.y, v.z * open_)
    keys = mouth.data.shape_keys.key_blocks
    cues = config.get('cues', [])
    for cue in cues:
        name = cue['value']
        if name not in visemes:
            continue
        start = max(1, round(float(cue['start']) * scene.render.fps) + 1)
        end = min(scene.frame_end, max(start + 1, round(float(cue['end']) * scene.render.fps) + 1))
        for frame, active in ((max(1, start - 1), 0), (start, 1), (end, 1), (min(scene.frame_end, end + 1), 0)):
            for keyname in visemes:
                keys[keyname].value = float(active if keyname == name else 0)
                keys[keyname].keyframe_insert(data_path='value', frame=frame)

    for frame in range(1, scene.frame_end + 1, max(12, scene.render.fps * 2)):
        t = (frame - 1) / scene.render.fps
        rig.pose.bones['Body'].rotation_mode = 'XYZ'
        rig.pose.bones['Body'].rotation_euler[1] = .045 * math.sin(t * 2.3)
        rig.pose.bones['Body'].keyframe_insert('rotation_euler', frame=frame)
        rig.pose.bones['Head'].rotation_mode = 'XYZ'
        rig.pose.bones['Head'].rotation_euler[2] = .08 * math.sin(t * 1.6)
        rig.pose.bones['Head'].keyframe_insert('rotation_euler', frame=frame)
        for side in ('L', 'R'):
            arm = rig.pose.bones['Arm.' + side]
            arm.rotation_mode = 'XYZ'
            arm.rotation_euler[0] = .20 * math.sin(t * 1.5 + (0 if side == 'L' else math.pi))
            arm.keyframe_insert('rotation_euler', frame=frame)

    sphere('Floor', (0, 0, -.4), (20, 20, .28), backdrop, 32, 16)
    def light(name, loc, power, color, size):
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.color, data.shape, data.size = power, color, 'DISK', size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        direction = Vector((0, 0, 1.9)) - obj.location
        obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    light('Key softbox', (-3, -4, 6), 850, (1, .86, .74), 4)
    light('Fill', (3, -2, 4), 550, (.45, .65, 1), 4)
    light('Rim', (1, 3, 5), 1100, (1, .3, .55), 3)
    bpy.ops.object.camera_add(location=(0, -9.2, 3.0))
    cam = bpy.context.object
    direction = Vector((0, 0, 1.72)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 5.0
    scene.camera = cam
    scene.world.color = (.012, .02, .05)
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=config['blend'])
    bpy.ops.render.render(animation=True)
    print('BERRY_RIG3D_DONE', config['output'])


if __name__ == '__main__':
    main()
