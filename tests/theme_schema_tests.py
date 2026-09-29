import unittest

from plugins.themes.utils import ThemeSchema


BASE_URL = "https://example.com/schemas/"

# small schema documents with the same kinds of $refs as the qwc2 schemas
DOCUMENTS = {
    "theme.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": BASE_URL + "theme.json",
        "definitions": {
            "bbox": {"type": "array", "items": {"type": "number"}}
        },
        "type": "object",
        "properties": {
            "extent": {
                "description": "Initial extent.",
                "allOf": [{"$ref": "#/definitions/bbox"}]
            },
            "backgroundLayers": {
                "type": "array",
                "items": {"$ref": "layer.json"}
            }
        }
    },
    "layer.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": BASE_URL + "layer.json",
        "definitions": {
            "name": {"type": "string"}
        },
        "type": "object",
        "properties": {
            "name": {"$ref": "#/definitions/name"},
            "extent": {"$ref": "theme.json#/definitions/bbox"}
        }
    }
}


class ThemeSchemaBundleTestCase(unittest.TestCase):
    """Test bundling the theme schema documents into one schema"""

    def test_bundles_documents_with_local_refs(self):
        schema = ThemeSchema.bundle(DOCUMENTS)

        bbox_ref = {"$ref": "#/definitions/theme/definitions/bbox"}
        theme = {
            "definitions": {
                "bbox": {"type": "array", "items": {"type": "number"}}
            },
            "type": "object",
            "properties": {
                "extent": {"description": "Initial extent.", "allOf": [bbox_ref]},
                "backgroundLayers": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/layer"}
                }
            }
        }
        layer = {
            "definitions": {
                "name": {"type": "string"}
            },
            "type": "object",
            "properties": {
                "name": {"$ref": "#/definitions/layer/definitions/name"},
                "extent": bbox_ref
            }
        }
        self.assertEqual(schema, {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": theme["properties"],
            "definitions": {"theme": theme, "layer": layer}
        })

    def test_keeps_recursive_refs(self):
        documents = {
            "theme.json": {
                **DOCUMENTS["theme.json"],
                "definitions": {"group": {
                    "type": "object",
                    "properties": {"items": {"$ref": "#/definitions/group"}}
                }},
                "properties": {"group": {"$ref": "#/definitions/group"}}
            }
        }

        schema = ThemeSchema.bundle(documents)

        self.assertEqual(
            schema["definitions"]["theme"]["definitions"]["group"]["properties"],
            {"items": {"$ref": "#/definitions/theme/definitions/group"}}
        )

    def test_rejects_refs_to_other_documents(self):
        documents = {
            "theme.json": {
                **DOCUMENTS["theme.json"],
                "properties": {"layer": {"$ref": "other.json"}}
            }
        }

        with self.assertRaises(ValueError):
            ThemeSchema.bundle(documents)
