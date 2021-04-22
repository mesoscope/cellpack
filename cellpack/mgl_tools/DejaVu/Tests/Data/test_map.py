from DejaVu.colorMap import ColorMap
cm = ColorMap('5val')
cfg = {'legend': None, 'name': '5val', 'ramp': [[0.0, 0.0, 1.0, 1.0], [0.0, 0.80000001192092896, 1.0, 1.0], [0.0, 1.0, 0.40000000596046448, 1.0], [0.40000000596046448, 1.0, 0.0, 1.0], [1.0, 0.80000001192092896, 0.0, 1.0]], 'maxi': 10.0, 'mini': 0.0}
apply( cm.configure, (), cfg)
