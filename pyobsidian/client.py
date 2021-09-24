from enum import Enum
import ast
from pyobsidian.models import Node, NodeLink

from sentence_transformers import SentenceTransformer, util

from pyobsidian.util import flatten_list


class EncodeType(Enum):
    FILE = 1
    BLOCK = 2


class PyobsidianClient:
    def __init__(self, scopes=None, model_name="paraphrase-MiniLM-L6-v2"):
        self.scopes = scopes
        self.model = SentenceTransformer(model_name)
        self.blocks = None
        self.embeddings = None

    @property
    def files_in_scope(self):
        return flatten_list([scope.md_files for scope in self.scopes])

    def encode_notes(self, how=EncodeType.BLOCK, files=None, trim_fn=None):
        if not files:
            files = self.files_in_scope
        notes = [file.read_text() for file in files]
        if trim_fn:
            notes = [trim_fn(note) for note in notes]
        blocks = []
        if how == EncodeType.BLOCK:
            for note in notes:
                content = note.split("\n")
                blocks.extend([c for c in content if len(c) > 0])
        print(f"Encoding {len(notes)} note{'s' if len(notes) > 1 else ''}...")
        self.embeddings = self.model.encode(blocks, convert_to_tensor=True)
        self.blocks = blocks

    def query(self, query):
        qe = self.model.encode(query, convert_to_tensor=True)
        res = util.semantic_search(qe, self.embeddings, top_k=5)
        return res

    @staticmethod
    def format_links_literal(lit):
        return lit.replace("false,", "False,").replace("true,", "True,")

    def get_node_links(self, metadataframe, links):
        links = ast.literal_eval(self.format_links_literal(links))
        node_links = []
        for link in links:
            if link['path'].split('.')[-1] == 'md':
                try:
                    node_links.append(
                        NodeLink(
                            **{
                                "node_id": metadataframe[
                                    metadataframe["file.path"] == link["path"]
                                ].index[0],
                                "path": link["path"],
                            }
                        )
                    )
                except IndexError:
                    print(link)
                    print(f"Could not find node for {link['path']}")
                    break
        return node_links

    def get_nodes(self, metadataframe):
        nodes = [
            Node(
                **{
                    "node_id": idx,
                    "path": row["file.path"],
                    "inlinks": self.get_node_links(metadataframe, row["file.inlinks"]),
                    "outlinks": self.get_node_links(
                        metadataframe, row["file.outlinks"]
                    ),
                }
            )
            for idx, row in metadataframe.iterrows()
        ]
        return nodes
