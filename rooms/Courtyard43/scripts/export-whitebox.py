"""Export Courtyard43's neutral structural review pack through official MCP.

Run inside Blender Lab MCP only. This intentionally exports static whitebox
meshes, not textured/refined assets, animation, or the Yongwang scene. The
authoring stage must set room_id, web_revision and review_parameters first.
"""
from array import array
import gzip
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[3]
ROOM_ID = "Courtyard43"
OUT = ROOT / "room-site/dist/assets/rooms" / ROOM_ID
BLEND = ROOT / "rooms" / ROOM_ID / "assets/full-room/Courtyard43-whitebox.blend"
# Blender (x,y,z) -> browser (x,z,-y), applied to geometry and matrices.
TO_WEB = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def export_whitebox():
    scene = bpy.context.scene
    assert scene.get("room_id") == ROOM_ID, "Refuse to export another room"
    assert scene.get("stage") == "whitebox", "Refined scenes need their own exporter"
    assert scene.unit_settings.system == "METRIC"
    assert scene.unit_settings.scale_length == 1
    revision = scene["web_revision"]
    assert revision.startswith("courtyard43-whitebox"), "Independent revision required"
    review = json.loads(scene["review_parameters"])
    bpy.context.view_layer.update()
    objects = sorted((o for o in scene.objects if o.type == "MESH"), key=lambda o: o.name)
    assert objects, "No whitebox meshes"
    assert not any(o.data.shape_keys for o in objects), "No silent loss of shape keys"
    assert not any(o.constraints for o in objects), "No silent loss of constraints"
    buffer = bytearray()

    def pack(values, item_size, integer=False):
        while len(buffer) % 4:
            buffer.append(0)
        packed = array("I" if integer else "f", values)
        assert packed.itemsize == 4
        if sys.byteorder != "little":
            packed.byteswap()
        desc = dict(type="Uint32Array" if integer else "Float32Array",
                    offset=len(buffer), length=len(packed), itemSize=item_size)
        buffer.extend(packed.tobytes())
        return desc

    materials = []
    material_ids = {}
    for obj in objects:
        assert len(obj.material_slots) == 1 and obj.active_material, obj.name
        mat = obj.active_material
        if mat.name in material_ids:
            continue
        assert mat.get("whitebox"), "Do not discard a refined material's node graph"
        mid = len(materials)
        material_ids[mat.name] = mid
        color = list(mat.diffuse_color)
        materials.append(dict(id=mid, type="MeshStandardMaterial", name=mat.name,
                              props=dict(roughness=mat.roughness, metalness=0,
                                         side=2, transparent=color[3] < 1,
                                         opacity=color[3], depthWrite=color[3] == 1),
                              colors=dict(color=color[:3]), textures={}, vectors={},
                              userData=dict(authoring="Blender", stage="whitebox")))
    identity = [v for column in Matrix.Identity(4).transposed() for v in column]
    nodes = [dict(id=0, name="courtyard43-world", type="Group", parent=-1,
                  matrix=identity, visible=True, castShadow=False, receiveShadow=False,
                  renderOrder=0, frustumCulled=True, userData={})]
    geometries = []
    refs = dict(world=0, cutaway=[], ceilings=[], curtainPanels=[])
    triangles = 0
    bounds = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        try:
            mesh.calc_loop_triangles()
            uv = mesh.uv_layers.active
            assert uv, f"Missing UV: {obj.name}"
            positions, normals, uvs, indices = [], [], [], []
            unique = {}
            for tri in mesh.loop_triangles:
                for loop_index in tri.loops:
                    vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
                    p = TO_WEB.to_3x3() @ vertex.co
                    n = (TO_WEB.to_3x3() @ mesh.corner_normals[loop_index].vector).normalized()
                    tex = uv.data[loop_index].uv
                    key = tuple(round(v, 7) for v in (*p, *n, *tex))
                    if key not in unique:
                        unique[key] = len(unique)
                        positions.extend(p)
                        normals.extend(n)
                        uvs.extend(tex)
                    indices.append(unique[key])
            gid = len(geometries)
            geometries.append(dict(id=gid, attributes=dict(position=pack(positions, 3),
                                   normal=pack(normals, 3), uv=pack(uvs, 2)),
                                   index=pack(indices, 1, True), groups=[],
                                   userData=dict(authoring="Blender", stage="whitebox")))
            matrix = TO_WEB @ obj.matrix_world @ TO_WEB.inverted()
            nid = len(nodes)
            tags = json.loads(obj.get("web_tags", "{}"))
            nodes.append(dict(id=nid, name=obj.name, type="Mesh", parent=0,
                              geometry=gid, material=material_ids[obj.active_material.name],
                              matrix=[v for column in matrix.transposed() for v in column],
                              visible=not obj.hide_render, castShadow=True, receiveShadow=True,
                              renderOrder=0, frustumCulled=True,
                              userData=dict(authoring="Blender", **tags)))
            for key in ("cutaway", "ceilings", "curtainPanels"):
                if tags.get(key):
                    refs[key].append(nid)
            points = [TO_WEB @ (obj.matrix_world @ v.co) for v in mesh.vertices]
            bounds.append(dict(name=obj.name,
                               min=[min(p[a] for p in points) for a in range(3)],
                               max=[max(p[a] for p in points) for a in range(3)]))
            triangles += len(indices) // 3
        finally:
            evaluated.to_mesh_clear()

    namespace = f"./assets/rooms/{ROOM_ID}"
    manifest = dict(format="blender-room-pack-1", revision=revision, roomId=ROOM_ID,
                    stage="whitebox", structureApproved=False,
                    binary=f"{namespace}/geometry.bin", compressedBinary=f"{namespace}/geometry.bin.gz",
                    nodes=nodes, geometries=geometries, materials=materials, textures=[], refs=refs,
                    review=review, statistics=dict(meshes=len(objects), triangles=triangles,
                                                  vertices=sum(g["attributes"]["position"]["length"] // 3 for g in geometries)))
    OUT.mkdir(parents=True, exist_ok=True)
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    # No dependency on analysis/, private photographs, or another room at playback.
    (OUT / "geometry.bin").write_bytes(buffer)
    (OUT / "geometry.bin.gz").write_bytes(gzip.compress(buffer, mtime=0))
    (OUT / "scene.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report_dir = ROOT / "analysis/Courtyard43"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "whitebox-bounds.json").write_text(json.dumps(bounds, ensure_ascii=False, indent=2), encoding="utf-8")
    return dict(revision=revision, statistics=manifest["statistics"], source=str(BLEND),
                manifest=str(OUT / "scene.json"), structureApproved=False)


if __name__ == "__main__":
    result = export_whitebox()
