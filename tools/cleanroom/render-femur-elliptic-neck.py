"""Render the page's real GLES2 shaders offscreen. No browser or UI automation.

Requires system Mesa EGL, numpy and Pillow. First generate a mesh dump with
BODYMAP_MESH_DUMP=/tmp/mesh.json node tools/cleanroom/check-femur-surface-study.cjs
then: python tools/cleanroom/render-femur-surface.py /tmp/mesh.json /tmp/previews
"""
import ctypes as C
import json
import math
import os
import pathlib
import re
import sys
import numpy as np
from PIL import Image, ImageDraw

os.environ.setdefault('EGL_PLATFORM', 'surfaceless')
root = pathlib.Path(__file__).resolve().parents[2]
page = (root / 'experiments/cleanroom-femur-study-v0.4.html').read_text()
mesh = json.loads(pathlib.Path(sys.argv[1]).read_text())
out = pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
E = C.CDLL('libEGL.so.1')


def egl(name, result, args):
    f = getattr(E, name)
    f.restype, f.argtypes = result, args
    return f


P, I, U, F = C.c_void_p, C.c_int, C.c_uint, C.c_float
display = egl('eglGetDisplay', P, [P])(None)
major, minor = I(), I()
assert egl('eglInitialize', U, [P, C.POINTER(I), C.POINTER(I)])(display, C.byref(major), C.byref(minor))
assert egl('eglBindAPI', U, [U])(0x30A0)
attrs = (I * 15)(0x3033, 1, 0x3040, 4, 0x3024, 8, 0x3023, 8, 0x3022, 8, 0x3021, 8, 0x3025, 24, 0x3038)
config, count = P(), I()
assert egl('eglChooseConfig', U, [P, C.POINTER(I), C.POINTER(P), I, C.POINTER(I)])(display, attrs, C.byref(config), 1, C.byref(count))
assert count.value
size = 720
surface = egl('eglCreatePbufferSurface', P, [P, P, C.POINTER(I)])(display, config, (I * 5)(0x3057, size, 0x3056, size, 0x3038))
context = egl('eglCreateContext', P, [P, P, P, C.POINTER(I)])(display, config, None, (I * 3)(0x3098, 2, 0x3038))
assert surface and context
assert egl('eglMakeCurrent', U, [P, P, P, P])(display, surface, surface, context)
address = egl('eglGetProcAddress', P, [C.c_char_p])


def gl(name, result, *args):
    ptr = address(name.encode())
    assert ptr, name
    return C.CFUNCTYPE(result, *args)(ptr)


get_string = gl('glGetString', C.c_char_p, U)
create_shader = gl('glCreateShader', U, U)
source = gl('glShaderSource', None, U, I, C.POINTER(C.c_char_p), C.POINTER(I))
compile_shader = gl('glCompileShader', None, U)
shader_iv = gl('glGetShaderiv', None, U, U, C.POINTER(I))
shader_log = gl('glGetShaderInfoLog', None, U, I, C.POINTER(I), P)


def shader(kind, name):
    text = re.search(r"const " + name + r"='([^']+)'", page)[1].encode()
    sh = create_shader(kind)
    ptr = C.c_char_p(text)
    source(sh, 1, C.byref(ptr), None)
    compile_shader(sh)
    ok = I()
    shader_iv(sh, 0x8B81, C.byref(ok))
    if not ok.value:
        log = C.create_string_buffer(4096)
        shader_log(sh, 4096, None, log)
        raise RuntimeError(log.value.decode())
    return sh


program = gl('glCreateProgram', U)()
attach = gl('glAttachShader', None, U, U)
attach(program, shader(0x8B31, 'vertexSource'))
attach(program, shader(0x8B30, 'fragmentSource'))
gl('glLinkProgram', None, U)(program)
linked = I()
gl('glGetProgramiv', None, U, U, C.POINTER(I))(program, 0x8B82, C.byref(linked))
assert linked.value, 'Shader program link failed'
gl('glUseProgram', None, U)(program)
gen_buffers = gl('glGenBuffers', None, I, C.POINTER(U))
bind_buffer = gl('glBindBuffer', None, U, U)
buffer_data = gl('glBufferData', None, U, C.c_ssize_t, P, U)
get_attrib = gl('glGetAttribLocation', I, U, C.c_char_p)
enable_attrib = gl('glEnableVertexAttribArray', None, U)
attrib_pointer = gl('glVertexAttribPointer', None, U, I, U, U, I, P)


def buffer(target, data):
    handle = U()
    gen_buffers(1, C.byref(handle))
    bind_buffer(target, handle.value)
    buffer_data(target, data.nbytes, data.ctypes.data, 0x88E4)


for name, key, components in [('aPosition', 'positions', 3), ('aNormal', 'normals', 3), ('aPart', 'parts', 1)]:
    data = np.array(mesh[key], dtype=np.float32)
    buffer(0x8892, data)
    loc = get_attrib(program, name.encode())
    enable_attrib(loc)
    attrib_pointer(loc, components, 0x1406, 0, 0, None)
indices = np.array(mesh['indices'], dtype=np.uint16)
buffer(0x8893, indices)
enable = gl('glEnable', None, U)
enable(0x0B71)
enable(0x0B44)
gl('glCullFace', None, U)(0x0405)
gl('glFrontFace', None, U)(0x0901)
gl('glClearColor', None, F, F, F, F)(.947, .968, .968, 1)
gl('glViewport', None, I, I, I, I)(0, 0, size, size)
uniform_location = gl('glGetUniformLocation', I, U, C.c_char_p)
uniform1 = gl('glUniform1f', None, I, F)
uniform3 = gl('glUniform3fv', None, I, I, C.POINTER(F))
clear = gl('glClear', None, U)
draw = gl('glDrawElements', None, U, I, U, P)
read = gl('glReadPixels', None, I, I, I, I, U, U, P)
frames = []
settings = [('Posterior / whole', 0, .04, 1.02, [25, 0, -70], 0),
            ('Posteromedial / surface', .85, .24, 1.02 * 2.3, [43, -8, -18], 5),
            ('Medial / surface', math.pi / 2, .18, 1.02 * 2.3, [43, -8, -18], 5)]
for number, (label, yaw, pitch, zoom, center, selected) in enumerate(settings):
    clear(0x4000 | 0x0100)
    for key, val in {'uYaw': yaw, 'uPitch': pitch, 'uZoom': zoom, 'uAspect': 1, 'uSelected': selected}.items():
        uniform1(uniform_location(program, key.encode()), val)
    uniform3(uniform_location(program, b'uCenter'), 1, (F * 3)(*center))
    draw(0x0004, len(indices), 0x1403, None)
    pixels = np.empty((size, size, 4), dtype=np.uint8)
    read(0, 0, size, size, 0x1908, 0x1401, pixels.ctypes.data)
    assert gl('glGetError', U)() == 0
    rgb = np.flipud(pixels[:, :, :3]).copy()
    green = (rgb[:, :, 1].astype(int) > rgb[:, :, 0].astype(int) + 25) & (rgb[:, :, 1].astype(int) > rgb[:, :, 2].astype(int) + 5)
    image = Image.fromarray(rgb)
    image.save(out / f'view-{number}.png')
    frames.append((label, image, int(green.sum())))
assert frames[1][2] > 40, 'Schematic fossa not visible in selected close view'
sheet = Image.new('RGB', (size * len(frames), size + 40), '#edf3f4')
for n, (label, image, _) in enumerate(frames):
    sheet.paste(image, (n * size, 40))
    ImageDraw.Draw(sheet).text((n * size + 20, 14), label, fill='#254f5b')
sheet.save(out / 'surface-review.png')
print(json.dumps({'status': 'passed', 'scope': 'Offscreen GLES2 rendering of actual page shaders, not a browser test',
                  'egl': f'{major.value}.{minor.value}', 'renderer': get_string(0x1F01).decode(),
                  'glVersion': get_string(0x1F02).decode(), 'shadersCompiledAndLinked': True,
                  'views': [{'view': x[0], 'highlightPixels': x[2]} for x in frames],
                  'anatomyAccuracy': 'not approved', 'iPhoneNewVersion': 'not tested'}, indent=2))

