import gdspy
from shapely.geometry.polygon import Polygon
from shapely.ops import cascaded_union
from shapely.affinity import translate, rotate, scale


class GDSIIImport:
    def __init__(self, filename, cell_name, layer=None, datatype=None):
        self.gdslib = gdspy.GdsLibrary(infile=filename)
        self.cell_name = cell_name
        self.layer = layer
        self.datatype = datatype

    def get_as_shapely(self, cell, layer=None, datatype=None):
        geometry = []

        gdspy_cell = self.gdslib.cell_dict[cell] if isinstance(cell, str) else cell
        for polygon in gdspy_cell.polygons:
            if self.layer is not None and layer != polygon.layers[0]:
                continue
            if self.datatype is not None and datatype != polygon.datatypes[0]:
                continue
            geometry.append(Polygon(polygon.polygons[0]).buffer(0))  # .buffer(0) for healing geometries

        for reference in gdspy_cell.references:
            sub_geometry = self.get_as_shapely(reference.ref_cell, layer, datatype)
            sub_geometry = scale(sub_geometry,
                                 *[reference.magnification] * 2) if reference.magnification else sub_geometry
            sub_geometry = scale(sub_geometry, -1) if reference.x_reflection else sub_geometry
            sub_geometry = rotate(sub_geometry, reference.rotation) if reference.rotation else sub_geometry
            sub_geometry = translate(sub_geometry, *reference.origin)
            geometry.extend(sub_geometry)

        return cascaded_union(geometry)

    def get_shapely_object(self):
        return self.get_as_shapely(self.cell_name, self.layer, self.datatype)


if __name__ == '__main__':
    from gdshelpers.parts.waveguide import _example
    from gdshelpers.geometry.chip import Cell

    _example()  # make sure the "output.gds" exists

    test_cell = Cell('test')
    test_cell.add_to_layer(1, GDSIIImport('output.gds', cell_name='TOP', layer=1))
    test_cell.show()
