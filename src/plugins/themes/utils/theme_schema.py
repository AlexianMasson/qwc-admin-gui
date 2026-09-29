import os

from urllib.parse import urljoin


class ThemeSchema():
    """JSON schema of a theme item, from theme.json and the schemas it
    references, published by qwc2 and listed in schema-versions.json"""

    ROOT = "theme.json"

    @staticmethod
    def bundle(documents):
        """Return the root schema as a single schema: every document is added
        to its definitions, keyed by file name without extension, and every
        $ref is rewritten to point there.

        :param dict documents: Schema documents by file name
        """
        root = ThemeSchema.ROOT
        names = {
            document["$id"]: os.path.splitext(file_name)[0]
            for file_name, document in documents.items()
        }
        definitions = {
            names[document["$id"]]: ThemeSchema.local_refs(
                document, document["$id"], names
            )
            for document in documents.values()
        }
        schema = dict(definitions[names[documents[root]["$id"]]])
        schema["$schema"] = documents[root]["$schema"]
        schema["definitions"] = definitions
        return schema

    @staticmethod
    def local_refs(node, base_uri, names):
        """Return a copy of a schema node with its $refs pointing to the
        bundled documents, and without the $id and $schema keys.

        :param obj node: Schema node
        :param str base_uri: $id of the document of the node
        :param dict names: Bundled document names by $id
        """
        if isinstance(node, list):
            return [
                ThemeSchema.local_refs(item, base_uri, names) for item in node
            ]
        if not isinstance(node, dict):
            return node

        result = {}
        for key, value in node.items():
            if key == "$ref":
                uri, _, fragment = urljoin(base_uri, value).partition("#")
                if uri not in names:
                    raise ValueError("Unknown $ref %s" % value)
                result[key] = "#/definitions/%s%s" % (names[uri], fragment)
            elif key not in ("$id", "$schema"):
                result[key] = ThemeSchema.local_refs(value, base_uri, names)
        return result
